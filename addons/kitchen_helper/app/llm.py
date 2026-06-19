import os
import json
import httpx
from typing import Optional, Dict, Any

SUPERVISOR_TOKEN = os.environ.get("SUPERVISOR_TOKEN")
USE_HA_CONVERSATION = os.environ.get("USE_HA_CONVERSATION", "false").lower() in ("1", "true", "yes")
HA_CONVERSATION_ENTITY = os.environ.get("HA_CONVERSATION_ENTITY", "conversation.google_ai_conversation")
HOMEASSISTANT_URL = os.environ.get("HOMEASSISTANT_URL", "http://supervisor/core/api")


def generate_recipe_prompt(prompt_text: str, dietary: str, style: str, servings: int) -> str:
    parts = [f"Erstelle ein Rezept für: {prompt_text}"]
    if dietary:
        parts.append(f"Ernährungsform: {dietary}")
    if style:
        parts.append(f"Stil: {style}")
    parts.append(f"Portionen: {servings}")
    parts.append("Bitte gebe Zutaten in einer Liste mit Mengenangaben und eine Schritt-für-Schritt Zubereitung zurück. Antwort als JSON mit keys title, description, servings, ingredients (name, amount, unit), instructions.")
    return "\n".join(parts)


def call_openai(prompt: str, model: str = "gpt-4o-mini", api_key: Optional[str] = None, base_url: Optional[str] = None) -> Dict[str, Any]:
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    url = (base_url.rstrip('/') if base_url else "https://api.openai.com") + "/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 800
    }
    r = httpx.post(url, headers=headers, json=payload, timeout=30.0)
    r.raise_for_status()
    return r.json()


def call_ha_conversation(entity_id: str, text: str) -> Optional[str]:
    if not SUPERVISOR_TOKEN:
        return None
    svc = f"{HOMEASSISTANT_URL}/services/conversation/process"
    payload = {"text": text}
    r = httpx.post(svc, headers={"Authorization": f"Bearer {SUPERVISOR_TOKEN}"}, json=payload, timeout=30.0)
    if r.status_code != 200:
        return None
    try:
        data = r.json()
        # If the service returns text in 'response' or similar
        return data.get("response") or data.get("text")
    except Exception:
        return None


def generate_recipe_via_ai(prompt_text: str, dietary: str, style: str, servings: int) -> Dict[str, Any]:
    prompt = generate_recipe_prompt(prompt_text, dietary, style, servings)
    # Try HA conversation first if configured
    if USE_HA_CONVERSATION:
        resp = call_ha_conversation(HA_CONVERSATION_ENTITY, prompt)
        if resp:
            try:
                return json.loads(resp)
            except Exception:
                # Fallback to plain text parsing
                return {"title": "KI-Rezept", "description": resp, "servings": servings, "ingredients": [], "instructions": resp}

    # Default: use OpenAI
    api_key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    base_url = os.environ.get("CUSTOM_OPENAI_URL")
    data = call_openai(prompt, model=model, api_key=api_key, base_url=base_url)
    # Extract text
    try:
        content = data["choices"][0]["message"]["content"]
        try:
            return json.loads(content)
        except Exception:
            return {"title": "KI-Rezept", "description": content, "servings": servings, "ingredients": [], "instructions": content}
    except Exception as e:
        raise RuntimeError(f"LLM call failed: {e}")
