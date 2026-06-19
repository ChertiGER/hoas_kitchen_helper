import os
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

SUPERVISOR_TOKEN = os.environ.get("SUPERVISOR_TOKEN", "")
HA_URL = os.environ.get("HOMEASSISTANT_URL", "http://supervisor/core/api")


def get_headers() -> Dict[str, str]:
    """Erstellt die Authentifizierungs-Header für die Home Assistant API."""
    return {
        "Authorization": f"Bearer {SUPERVISOR_TOKEN}",
        "Content-Type": "application/json",
    }


def is_ha_available() -> bool:
    """Prüft, ob die Home Assistant API erreichbar ist (nützlich für Fehlerbehandlung)."""
    if not SUPERVISOR_TOKEN:
        return False
    try:
        # Einfacher Ping auf das API-Discovery-Endpoint
        url = f"{HA_URL}/"
        response = httpx.get(url, headers=get_headers(), timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


def get_calendars() -> List[Dict[str, str]]:
    """Ruft alle verfügbaren Kalender-Entitäten aus Home Assistant ab."""
    if not SUPERVISOR_TOKEN:
        # Mock-Daten für lokale Entwicklung
        return [
            {"entity_id": "calendar.meals", "name": "Essensplaner (Mock)"},
            {"entity_id": "calendar.personal", "name": "Persönlicher Kalender (Mock)"},
        ]

    try:
        url = f"{HA_URL}/states"
        response = httpx.get(url, headers=get_headers(), timeout=5.0)
        if response.status_code != 200:
            return []

        states = response.json()
        calendars = []
        for state in states:
            entity_id = state.get("entity_id", "")
            if entity_id.startswith("calendar."):
                friendly_name = state.get("attributes", {}).get("friendly_name", entity_id)
                calendars.append({
                    "entity_id": entity_id,
                    "name": friendly_name
                })
        return calendars
    except Exception as e:
        print(f"Fehler beim Laden der Kalender: {e}")
        return []


def get_todo_lists() -> List[Dict[str, str]]:
    """Ruft alle To-Do-Listen (Einkaufslisten) aus Home Assistant ab (ab HA 2023.11)."""
    if not SUPERVISOR_TOKEN:
        # Mock-Daten für lokale Entwicklung
        return [
            {"entity_id": "todo.shopping_list", "name": "Einkaufsliste (Mock)"},
            {"entity_id": "todo.kitchen_helper_todo", "name": "Küchenliste (Mock)"},
        ]

    try:
        url = f"{HA_URL}/states"
        response = httpx.get(url, headers=get_headers(), timeout=5.0)
        if response.status_code != 200:
            return []

        states = response.json()
        todo_lists = []
        for state in states:
            entity_id = state.get("entity_id", "")
            if entity_id.startswith("todo."):
                friendly_name = state.get("attributes", {}).get("friendly_name", entity_id)
                todo_lists.append({
                    "entity_id": entity_id,
                    "name": friendly_name
                })
        return todo_lists
    except Exception as e:
        print(f"Fehler beim Laden der To-Do-Listen: {e}")
        return []


def create_calendar_event(
    calendar_entity: str,
    title: str,
    date_str: str,
    description: str = ""
) -> bool:
    """
    Erstellt ein ganztägiges Kalenderereignis in Home Assistant.
    Format für date_str: 'YYYY-MM-DD'
    """
    if not SUPERVISOR_TOKEN:
        print(f"[Mock] Kalendereintrag erstellt: {title} am {date_str} in {calendar_entity}")
        return True

    try:
        # Berechnung des Folgetags für exklusives Enddatum
        start_date = datetime.strptime(date_str, "%Y-%m-%d")
        end_date = start_date + timedelta(days=1)
        end_date_str = end_date.strftime("%Y-%m-%d")

        url = f"{HA_URL}/services/calendar/create_event"
        payload = {
            "entity_id": calendar_entity,
            "summary": title,
            "description": description,
            "start_date": date_str,
            "end_date": end_date_str,
        }

        response = httpx.post(url, headers=get_headers(), json=payload, timeout=5.0)
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"Fehler beim Erstellen des Kalendereintrags: {e}")
        return False


def add_to_todo_list(todo_entity: str, item_text: str) -> bool:
    """Fügt einen Eintrag zu einer To-Do-Liste hinzu."""
    if not SUPERVISOR_TOKEN:
        print(f"[Mock] To-Do-Eintrag hinzugefügt: '{item_text}' in {todo_entity}")
        return True

    try:
        url = f"{HA_URL}/services/todo/add_item"
        payload = {
            "entity_id": todo_entity,
            "item": item_text
        }
        response = httpx.post(url, headers=get_headers(), json=payload, timeout=5.0)
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"Fehler beim Hinzufügen zur To-Do-Liste: {e}")
        return False


def add_to_legacy_shopping_list(item_text: str) -> bool:
    """Fügt einen Eintrag zur klassischen Home Assistant Einkaufsliste (shopping_list) hinzu."""
    if not SUPERVISOR_TOKEN:
        print(f"[Mock] Legacy Einkaufsliste: '{item_text}' hinzugefügt")
        return True

    try:
        url = f"{HA_URL}/services/shopping_list/add_item"
        payload = {
            "name": item_text
        }
        response = httpx.post(url, headers=get_headers(), json=payload, timeout=5.0)
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"Fehler beim Hinzufügen zur Legacy Einkaufsliste: {e}")
        return False

