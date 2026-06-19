import os
import json
import httpx
import re
from typing import Dict, Any, Optional

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
        "gemini_api_key": os.environ.get("GEMINI_API_KEY", ""),
        "gemini_model": os.environ.get("GEMINI_MODEL", "gemini-1.5-flash"),
        "default_calendar": os.environ.get("DEFAULT_CALENDAR", ""),
        "default_shopping_list": os.environ.get("DEFAULT_SHOPPING_LIST", ""),
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

    # Deaktiviere die anderen AI-Anbieter basierend auf der Auswahl
    provider = config["llm_provider"]
    if provider == "openai":
        config["anthropic_api_key"] = ""
        config["anthropic_model"] = ""
        config["gemini_api_key"] = ""
        config["gemini_model"] = ""
    elif provider == "anthropic":
        config["openai_api_key"] = ""
        config["openai_model"] = ""
        config["custom_openai_url"] = ""
        config["gemini_api_key"] = ""
        config["gemini_model"] = ""
    elif provider == "openai_compatible":
        config["anthropic_api_key"] = ""
        config["anthropic_model"] = ""
        config["gemini_api_key"] = ""
        config["gemini_model"] = ""
    elif provider == "gemini":
        config["openai_api_key"] = ""
        config["openai_model"] = ""
        config["custom_openai_url"] = ""
        config["anthropic_api_key"] = ""
        config["anthropic_model"] = ""

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
        '  "instructions": "1. Schritt...\\n2. Schritt...\\n3. Schritt...",\n'
        '  "tags": ["tag1", "tag2"]\n'
        "}\n\n"
        "WICHTIG:\n"
        "- 'ingredients' ist eine Liste von Objekten mit 'name' (String), 'amount' (Float oder null, falls nicht quantifizierbar) "
        "und 'unit' (String, z.B. g, ml, EL, TL, Stück, Zehe, Bund, Prise, nach Geschmack, oder leeres Feld '').\n"
        "- Trage keine Textphrasen in 'amount' ein, sondern verwende dort nur Zahlen oder null. Text wie 'eine Handvoll' gehört in 'unit' oder 'name'.\n"
        "- 'instructions' ist ein einzelner zusammenhängender String mit Zeilenumbrüchen (\\n).\n"
        "- 'tags' ist ein Array von Strings. Wähle passende Tags ausschließlich aus dieser Liste aus (du kannst mehrere wählen oder ein leeres Array []): "
        "vegetarisch, vegan, glutenfrei, laktosefrei, low-carb, schnell & einfach, kinderfreundlich, festlich, gesund & leicht, deftig."
    )

    user_details = f"Rezept-Idee / Zutaten: {prompt_text}\n"
    if dietary and dietary != "keine":
        user_details += f"Ernährungsform: {dietary}\n"
    if style and style != "keine":
        user_details += f"Stil / Besonderheit: {style}\n"
    user_details += f"Portionen: {servings}\n"

    return system_prompt, user_details


def call_openai(
    config: Dict[str, Any],
    system_prompt: str,
    user_prompt: str,
    image_data_b64: Optional[str] = None,
    image_mime_type: Optional[str] = None
) -> str:
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

    if image_data_b64 and image_mime_type:
        user_content = [
            {"type": "text", "text": user_prompt},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{image_mime_type};base64,{image_data_b64}"
                }
            }
        ]
    else:
        user_content = user_prompt

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
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


def call_anthropic(
    config: Dict[str, Any],
    system_prompt: str,
    user_prompt: str,
    image_data_b64: Optional[str] = None,
    image_mime_type: Optional[str] = None
) -> str:
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

    if image_data_b64 and image_mime_type:
        user_content = [
            {"type": "text", "text": user_prompt},
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": image_mime_type,
                    "data": image_data_b64
                }
            }
        ]
    else:
        user_content = user_prompt

    payload = {
        "model": model,
        "max_tokens": 4000,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.7,
    }

    url = "https://api.anthropic.com/v1/messages"
    response = httpx.post(url, headers=headers, json=payload, timeout=45.0)

    if response.status_code != 200:
        raise Exception(f"Anthropic API Fehler ({response.status_code}): {response.text}")

    result = response.json()
    return result["content"][0]["text"]


def call_gemini(
    config: Dict[str, Any],
    system_prompt: str,
    user_prompt: str,
    image_data_b64: Optional[str] = None,
    image_mime_type: Optional[str] = None
) -> str:
    """Ruft die Google Gemini-API auf."""
    api_key = config["gemini_api_key"]
    model = config["gemini_model"]

    if not api_key:
        raise ValueError("Gemini API Key ist nicht konfiguriert.")

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }

    parts = [{"text": user_prompt}]
    if image_data_b64 and image_mime_type:
        parts.append({
            "inlineData": {
                "mimeType": image_mime_type,
                "data": image_data_b64
            }
        })

    # Gemini 1.5/2.0 systemInstruction und contents Payload
    payload = {
        "contents": [{"parts": parts}],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    response = httpx.post(url, headers=headers, json=payload, timeout=45.0)

    if response.status_code != 200:
        raise Exception(f"Gemini API Fehler ({response.status_code}): {response.text}")

    result = response.json()
    try:
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise Exception(f"Unerwartetes Gemini API Antwortformat: {result}")


def generate_recipe_via_ai(
    prompt_text: str,
    dietary: str = "keine",
    style: str = "keine",
    servings: int = 4,
    image_data_b64: Optional[str] = None,
    image_mime_type: Optional[str] = None
) -> Dict[str, Any]:
    """Generiert ein Rezept über den konfigurierten LLM-Anbieter (unterstützt optional Bild-Input)."""
    config = load_config()
    provider = config["llm_provider"]

    system_prompt, user_prompt = generate_recipe_prompt(prompt_text, dietary, style, servings)

    if provider == "openai":
        raw_response = call_openai(config, system_prompt, user_prompt, image_data_b64, image_mime_type)
    elif provider == "openai_compatible":
        raw_response = call_openai(config, system_prompt, user_prompt, image_data_b64, image_mime_type)
    elif provider == "anthropic":
        raw_response = call_anthropic(config, system_prompt, user_prompt, image_data_b64, image_mime_type)
    elif provider == "gemini":
        raw_response = call_gemini(config, system_prompt, user_prompt, image_data_b64, image_mime_type)
    else:
        raise ValueError(f"Unbekannter LLM-Provider: {provider}")

    cleaned_response = clean_json_response(raw_response)

    try:
        recipe_data = json.loads(cleaned_response)
        recipe_data["source"] = "KI-generiert"
        recipe_data["servings"] = recipe_data.get("servings") or servings
        if "tags" not in recipe_data:
            recipe_data["tags"] = []
        return recipe_data
    except json.JSONDecodeError as e:
        print(f"JSON-Parsing-Fehler der LLM-Antwort: {e}")
        print(f"Roh-Antwort war: {raw_response}")
        raise Exception("Die KI hat kein gültiges Rezept-JSON geliefert. Bitte versuche es erneut.")


# ---- NEUE SCRAPER- & MULTIMODALE FUNKTIONEN ----

from html.parser import HTMLParser

class HTMLTextExtractor(HTMLParser):
    """Extrahiert lesbaren Fließtext aus einem HTML-Dokument und ignoriert Boilerplate."""
    def __init__(self):
        super().__init__()
        self.result = []
        self.ignore = False
        self.ignore_tags = {"script", "style", "head", "nav", "footer", "noscript"}

    def handle_starttag(self, tag, attrs):
        if tag in self.ignore_tags:
            self.ignore = True

    def handle_endtag(self, tag):
        if tag in self.ignore_tags:
            self.ignore = False

    def handle_data(self, data):
        if not self.ignore:
            text = data.strip()
            if text:
                self.result.append(text)

    def get_text(self):
        return " ".join(self.result)


def scrape_recipe_from_url(url: str) -> Dict[str, Any]:
    """Scrapt den Text einer Webseite und lässt das LLM ein Rezept daraus extrahieren."""
    try:
        # Lade die Webseite mit Standard User-Agent
        response = httpx.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=15.0)
        if response.status_code != 200:
            raise Exception(f"Fehler beim Laden der Webseite ({response.status_code})")
        
        # HTML Text extrahieren
        parser = HTMLTextExtractor()
        parser.feed(response.text)
        page_text = parser.get_text()
        
        # Text kürzen um Tokengrenzen zu wahren
        page_text = page_text[:15000]
    except Exception as e:
        raise Exception(f"Fehler beim Scrapen der Webseite: {e}")

    system_prompt = (
        "Du bist ein präziser Rezept-Extraktor. Deine Aufgabe ist es, aus dem übergebenen Text einer Webseite "
        "ein Kochrezept zu extrahieren und im exakten JSON-Format zurückzugeben.\n"
        "Du MÜSST exakt im folgenden JSON-Format antworten. Gib keinen Text vor oder nach dem JSON aus.\n\n"
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
        '  "instructions": "1. Schritt...\\n2. Schritt...\\n3. Schritt...",\n'
        '  "tags": ["tag1", "tag2"]\n'
        "}\n\n"
        "WICHTIG:\n"
        "- Extrahiere den korrekten Titel, Portionen, Zutaten und die Schritt-für-Schritt-Anleitung.\n"
        "- Falls keine Portionen angegeben sind, nimm standardmäßig 4.\n"
        "- 'ingredients' ist eine Liste von Objekten mit 'name', 'amount' (Float oder null) und 'unit'.\n"
        "- 'instructions' ist ein einzelner String mit Zeilenumbrüchen (\\n).\n"
        "- 'tags' ist ein Array von passenden Tags, gewählt aus dieser Liste (oder leeres Array []): "
        "vegetarisch, vegan, glutenfrei, laktosefrei, low-carb, schnell & einfach, kinderfreundlich, festlich, gesund & leicht, deftig."
    )

    user_prompt = f"Hier ist der extrahierte Text der Webseite:\n\n{page_text}"

    config = load_config()
    provider = config["llm_provider"]

    if provider == "openai":
        raw_response = call_openai(config, system_prompt, user_prompt)
    elif provider == "openai_compatible":
        raw_response = call_openai(config, system_prompt, user_prompt)
    elif provider == "anthropic":
        raw_response = call_anthropic(config, system_prompt, user_prompt)
    elif provider == "gemini":
        raw_response = call_gemini(config, system_prompt, user_prompt)
    else:
        raise ValueError(f"Unbekannter LLM-Provider: {provider}")

    cleaned_response = clean_json_response(raw_response)

    try:
        recipe_data = json.loads(cleaned_response)
        recipe_data["source"] = "Importiert von Webseite"
        if "tags" not in recipe_data:
            recipe_data["tags"] = []
        return recipe_data
    except json.JSONDecodeError as e:
        print(f"JSON-Parsing-Fehler der LLM-Antwort: {e}")
        print(f"Roh-Antwort war: {raw_response}")
        raise Exception("Die KI konnte kein gültiges Rezept aus der Webseite extrahieren. Versuche es mit einer anderen URL.")


def import_recipe_from_image(image_data_b64: str, image_mime_type: str) -> Dict[str, Any]:
    """Extrahiert ein Rezept aus einem hochgeladenen Bild (Foto oder Screenshot) per LLM."""
    system_prompt = (
        "Du bist ein Experte für die Digitalisierung von Rezepten. Deine Aufgabe ist es, das auf dem Bild dargestellte "
        "Rezept präzise zu lesen, zu transkribieren und als strukturiertes JSON zurückzugeben.\n"
        "Antworte ausschließlich im angegebenen JSON-Format. Gib keinen Text vor oder nach dem JSON aus.\n\n"
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
        '  "instructions": "1. Schritt...\\n2. Schritt...\\n3. Schritt...",\n'
        '  "tags": ["tag1", "tag2"]\n'
        "}\n\n"
        "WICHTIG:\n"
        "- Falls keine Portionen angegeben sind, nimm standardmäßig 4.\n"
        "- 'ingredients' ist eine Liste von Objekten mit 'name', 'amount' (Float oder null) und 'unit'.\n"
        "- 'instructions' ist ein einzelner String mit Zeilenumbrüchen (\\n).\n"
        "- 'tags' ist ein Array von passenden Tags, gewählt aus dieser Liste (oder leeres Array []): "
        "vegetarisch, vegan, glutenfrei, laktosefrei, low-carb, schnell & einfach, kinderfreundlich, festlich, gesund & leicht, deftig."
    )

    user_prompt = "Lies dieses Rezeptbild und extrahiere alle Informationen in das JSON-Format."

    config = load_config()
    provider = config["llm_provider"]

    if provider == "openai":
        raw_response = call_openai(config, system_prompt, user_prompt, image_data_b64, image_mime_type)
    elif provider == "openai_compatible":
        raw_response = call_openai(config, system_prompt, user_prompt, image_data_b64, image_mime_type)
    elif provider == "anthropic":
        raw_response = call_anthropic(config, system_prompt, user_prompt, image_data_b64, image_mime_type)
    elif provider == "gemini":
        raw_response = call_gemini(config, system_prompt, user_prompt, image_data_b64, image_mime_type)
    else:
        raise ValueError(f"Unbekannter LLM-Provider: {provider}")

    cleaned_response = clean_json_response(raw_response)

    try:
        recipe_data = json.loads(cleaned_response)
        recipe_data["source"] = "Bild-Scan"
        if "tags" not in recipe_data:
            recipe_data["tags"] = []
        return recipe_data
    except json.JSONDecodeError as e:
        print(f"JSON-Parsing-Fehler der LLM-Antwort: {e}")
        print(f"Roh-Antwort war: {raw_response}")
        raise Exception("Die KI konnte das Bild nicht lesen oder kein gültiges Rezept-JSON generieren.")


def generate_recipe_from_leftovers_image(image_data_b64: str, image_mime_type: str) -> Dict[str, Any]:
    """Generiert ein Rezept basierend auf einem hochgeladenen Foto des Kühlschranks/Vorrats per LLM."""
    system_prompt = (
        "Du bist ein kreativer Resteverwertungs-Chefkoch. Deine Aufgabe ist es, das Foto eines Kühlschranks oder Vorrats "
        "zu analysieren, alle erkennbaren Lebensmittel/Zutaten zu identifizieren, und daraus ein kreatives, leckeres Rezept "
        "zu kreieren, das diese Zutaten sinnvoll nutzt.\n"
        "Zutaten, die typischerweise im Haushalt vorhanden sind (Gewürze, Öl, Mehl, Salz), darfst du frei ergänzen.\n"
        "Antworte ausschließlich im angegebenen JSON-Format. Gib keinen Text vor oder nach dem JSON aus.\n\n"
        "EXAKTES JSON-FORMAT:\n"
        "{\n"
        '  "title": "Name des kreativen Restegerichts",\n'
        '  "description": "Erklärung, welche erkannten Zutaten hier verwendet wurden (1-2 Sätze)",\n'
        '  "servings": 4,\n'
        '  "ingredients": [\n'
        '    {"name": "Zutat 1", "amount": 100.0, "unit": "g"},\n'
        '    {"name": "Zutat 2", "amount": 2, "unit": "Stück"}\n'
        "  ],\n"
        '  "instructions": "1. Schritt...\\n2. Schritt...\\n3. Schritt...",\n'
        '  "tags": ["tag1", "tag2"]\n'
        "}\n\n"
        "WICHTIG:\n"
        "- 'ingredients' ist eine Liste von Objekten mit 'name', 'amount' (Float oder null) und 'unit'.\n"
        "- 'instructions' ist ein einzelner String mit Zeilenumbrüchen (\\n).\n"
        "- 'tags' ist ein Array von passenden Tags, gewählt aus dieser Liste (oder leeres Array []): "
        "vegetarisch, vegan, glutenfrei, laktosefrei, low-carb, schnell & einfach, kinderfreundlich, festlich, gesund & leicht, deftig."
    )

    user_prompt = "Analysiere dieses Foto und erstelle ein tolles Rezept aus den darauf erkennbaren Zutaten."

    config = load_config()
    provider = config["llm_provider"]

    if provider == "openai":
        raw_response = call_openai(config, system_prompt, user_prompt, image_data_b64, image_mime_type)
    elif provider == "openai_compatible":
        raw_response = call_openai(config, system_prompt, user_prompt, image_data_b64, image_mime_type)
    elif provider == "anthropic":
        raw_response = call_anthropic(config, system_prompt, user_prompt, image_data_b64, image_mime_type)
    elif provider == "gemini":
        raw_response = call_gemini(config, system_prompt, user_prompt, image_data_b64, image_mime_type)
    else:
        raise ValueError(f"Unbekannter LLM-Provider: {provider}")

    cleaned_response = clean_json_response(raw_response)

    try:
        recipe_data = json.loads(cleaned_response)
        recipe_data["source"] = "Visuelle Resteverwertung"
        if "tags" not in recipe_data:
            recipe_data["tags"] = []
        return recipe_data
    except json.JSONDecodeError as e:
        print(f"JSON-Parsing-Fehler der LLM-Antwort: {e}")
        print(f"Roh-Antwort war: {raw_response}")
        raise Exception("Die KI konnte das Foto nicht analysieren oder kein Rezept daraus kreieren.")
