import os
import json
import httpx
import re
from typing import Dict, Any, Optional
from .ha_api import call_conversation_entity

OPTIONS_PATH = "/data/options.json"


def load_config() -> Dict[str, Any]:
    """
    Lädt die Addon-Konfiguration von Home Assistant.
    Falls nicht vorhanden (lokale Entwicklung), wird auf Umgebungsvariablen zurückgegriffen.
    """
    config = {
        "llm_provider": os.environ.get("LLM_PROVIDER", "openai"),
        "openai_api_key": os.environ.get("OPENAI_API_KEY", ""),
        "openai_model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        "custom_openai_url": os.environ.get("CUSTOM_OPENAI_URL", ""),
        "anthropic_api_key": os.environ.get("ANTHROPIC_API_KEY", ""),
        "anthropic_model": os.environ.get("ANTHROPIC_MODEL", "claude-3-5-haiku-latest"),
        "use_ha_conversation": os.environ.get("USE_HA_CONVERSATION", "false").lower() in ("1","true","yes"),
        "ha_conversation_entity": os.environ.get("HA_CONVERSATION_ENTITY", "conversation.google_ai_conversation"),
    }

    if os.path.exists(OPTIONS_PATH):
        try:
            with open(OPTIONS_PATH, "r") as f:
                ha_options = json.load(f)
                for key in config.keys():
                    if key in ha_options and ha_options[key] != "":
                        config[key] = ha_options[key]
        except Exception as e:
            print(f"Fehler beim Laden der options.json: {e}")

    return config


def clean_json_response(text: str) -> str:
    """Bereinigt eventuelle Markdown-Fences (```json ... ```) aus der LLM-Antwort."""
    text = text.strip()
    # Entferne ```json am Anfang und ``` am Ende
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()
    return text


def generate_recipe_prompt(prompt_text: str, dietary: str, style: str, servings: int) -> str:
    """Erstellt den System- und User-Prompt für die Rezeptgenerierung."""
    system_prompt = (
        "Du bist ein professioneller Chefkoch und Küchenhelfer. Deine Aufgabe ist es, ein hochwertiges Rezept "
        "auf Deutsch basierend auf den Wünschen des Benutzers zu erstellen.\n"
        "Du MÜSST exakt im folgenden JSON-Format antworten. Gib keinen Text vor oder nach dem JSON aus. "
        "Verwende keine Markdown-Formatierung um das JSON herum (keine Backticks), es sei denn, es ist absolut notwendig. "
        "Achte darauf, das JSON valide zu halten.\n\n"
        "EXAKTES JSON-FORMAT:\n"
        "{\n"
        '  "title": "Name des Rezepts",\n'
        '  "description": "Eine kurze, ansprechende Beschreibung (1-2 Sätze)",\n'
        '  "servings": 4,\n'
        '  "ingredients": [\n'
        '    {"name": "Zutat 1", "amount": 100.0, "unit": "g"},\n'
        '    {"name": "Zutat 2", "amount": 2, "unit": "Stück"},\n'
        '    {"name": "Zutat 3", "amount": null, "unit": "Prise"}\n'
        "  ],\n"
        '  "instructions": "1. Schritt...\\n2. Schritt...\\n3. Schritt..."\n'
        "}\n\n"
        "WICHTIG:\n"
        "- 'ingredients' ist eine Liste von Objekten mit 'name' (String), 'amount' (Float oder null, falls nicht quantifizierbar) "
        "und 'unit' (String, z.B. g, ml, EL, TL, Stück, Zehe, Bund, Prise, nach Geschmack, oder leeres Feld '').\n"
        "- Trage keine Textphrasen in 'amount' ein, sondern verwende dort nur Zahlen oder null. Text wie 'eine Handvoll' gehört in 'unit' oder 'name'.\n"
        "- 'instructions' ist ein einzelner zusammenhängender String mit Zeilenumbrüchen (\\n)."
    )

    user_details = f"Rezept-Idee / Zutaten: {prompt_text}\n"
    if dietary and dietary != "keine":
        user_details += f"Ernährungsform: {dietary}\n"
    if style and style != "keine":
        user_details += f"Stil / Besonderheit: {style}\n"
    user_details += f"Portionen: {servings}\n"

    return system_prompt, user_details


def call_openai(config: Dict[str, Any], system_prompt: str, user_prompt: str) -> str:
    """Ruft die OpenAI-API oder ein kompatibles Endpoint auf."""
    api_key = config["openai_api_key"]
    model = config["openai_model"]
    base_url = config["custom_openai_url"] or "https://api.openai.com/v1"

    if not api_key and "api.openai.com" in base_url:
        raise ValueError("OpenAI API Key ist nicht konfiguriert.")

    headers = {
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
    }

    # response_format wird nur für echte OpenAI oder fähige Endpunkte gesetzt
    if "api.openai.com" in base_url:
        payload["response_format"] = {"type": "json_object"}

    url = f"{base_url.rstrip('/')}/chat/completions"
    response = httpx.post(url, headers=headers, json=payload, timeout=45.0)

    if response.status_code != 200:
        raise Exception(f"OpenAI API Fehler ({response.status_code}): {response.text}")

    result = response.json()
    return result["choices"][0]["message"]["content"]


def call_anthropic(config: Dict[str, Any], system_prompt: str, user_prompt: str) -> str:
    """Ruft die Anthropic (Claude) API auf."""
    api_key = config["anthropic_api_key"]
    model = config["anthropic_model"]

    if not api_key:
        raise ValueError("Anthropic API Key ist nicht konfiguriert.")

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    payload = {
        "model": model,
        "max_tokens": 4000,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
    }

    url = "https://api.anthropic.com/v1/messages"
    response = httpx.post(url, headers=headers, json=payload, timeout=45.0)

    if response.status_code != 200:
        raise Exception(f"Anthropic API Fehler ({response.status_code}): {response.text}")

    result = response.json()
    return result["content"][0]["text"]


def generate_recipe_via_ai(
    prompt_text: str,
    dietary: str = "keine",
    style: str = "keine",
    servings: int = 4
) -> Dict[str, Any]:
    """Generiert ein Rezept über den konfigurierten LLM-Anbieter."""
    config = load_config()
    provider = config["llm_provider"]

    system_prompt, user_prompt = generate_recipe_prompt(prompt_text, dietary, style, servings)

    # Option: verwende vorhandene Home Assistant Conversation-Entity falls konfiguriert
    if config.get("use_ha_conversation"):
        entity = config.get("ha_conversation_entity") or "conversation.google_ai_conversation"
        # Kombiniere System- und User-Prompt zu einem String für die HA-Konversation
        combined = system_prompt + "\n\n" + user_prompt
        raw = call_conversation_entity(entity, combined)
        if not raw:
            raise Exception("Keine Antwort von der Home Assistant Conversation-Entity erhalten.")
        raw_response = raw
    else:
        if provider == "openai":
            raw_response = call_openai(config, system_prompt, user_prompt)
        elif provider == "openai_compatible":
            raw_response = call_openai(config, system_prompt, user_prompt)
        elif provider == "anthropic":
            raw_response = call_anthropic(config, system_prompt, user_prompt)
        else:
            raise ValueError(f"Unbekannter LLM-Provider: {provider}")

    cleaned_response = clean_json_response(raw_response)

    try:
        recipe_data = json.loads(cleaned_response)
        recipe_data["source"] = "KI-generiert"
        # Portionsanzahl validieren
        recipe_data["servings"] = recipe_data.get("servings") or servings
        return recipe_data
    except json.JSONDecodeError as e:
        print(f"JSON-Parsing-Fehler der LLM-Antwort: {e}")
        print(f"Roh-Antwort war: {raw_response}")
        raise Exception("Die KI hat kein gültiges Rezept-JSON geliefert. Bitte versuche es erneut.")
