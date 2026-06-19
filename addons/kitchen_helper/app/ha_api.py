import os
import requests
from typing import List, Dict, Any

SUPERVISOR_TOKEN = os.environ.get("SUPERVISOR_TOKEN")
HOMEASSISTANT_URL = os.environ.get("HOMEASSISTANT_URL", "http://supervisor/core/api")


def is_ha_available() -> bool:
    if not SUPERVISOR_TOKEN:
        return False
    try:
        r = requests.get(f"{HOMEASSISTANT_URL}/states", headers={"Authorization": f"Bearer {SUPERVISOR_TOKEN}"}, timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def get_calendars() -> List[str]:
    # Einfaches Listing: filter states that start with calendar.
    if not SUPERVISOR_TOKEN:
        return []
    r = requests.get(f"{HOMEASSISTANT_URL}/states", headers={"Authorization": f"Bearer {SUPERVISOR_TOKEN}"}, timeout=5)
    if r.status_code != 200:
        return []
    states = r.json()
    return [s["entity_id"] for s in states if s["entity_id"].startswith("calendar.")]


def get_todo_lists() -> List[str]:
    if not SUPERVISOR_TOKEN:
        return []
    r = requests.get(f"{HOMEASSISTANT_URL}/states", headers={"Authorization": f"Bearer {SUPERVISOR_TOKEN}"}, timeout=5)
    if r.status_code != 200:
        return []
    states = r.json()
    # To-Do lists may be todo.xxx or shopping_list.xxx depending on integration
    return [s["entity_id"] for s in states if s["entity_id"].startswith("todo.") or s["entity_id"].startswith("shopping_list.")]


def create_calendar_event(calendar_entity: str, title: str, date_str: str, description: str) -> bool:
    # Call the calendar.add_event service
    # calendar_entity: calendar.my_calendar
    if not SUPERVISOR_TOKEN:
        return False
    service_url = f"{HOMEASSISTANT_URL}/services/calendar/add_event"
    payload = {
        "entity_id": calendar_entity,
        "title": title,
        "start_date": date_str,
        "end_date": date_str,
        "all_day": True,
        "description": description
    }
    r = requests.post(service_url, headers={"Authorization": f"Bearer {SUPERVISOR_TOKEN}", "Content-Type": "application/json"}, json=payload, timeout=5)
    return r.status_code in (200, 201)


def add_to_todo_list(todo_entity: str, item: str) -> bool:
    if not SUPERVISOR_TOKEN:
        return False
    service_url = f"{HOMEASSISTANT_URL}/services/todoist/add_task" if todo_entity.startswith("todoist.") else f"{HOMEASSISTANT_URL}/services/homeassistant/append_to_list"
    payload = {"entity_id": todo_entity, "message": item}
    r = requests.post(service_url, headers={"Authorization": f"Bearer {SUPERVISOR_TOKEN}", "Content-Type": "application/json"}, json=payload, timeout=5)
    return r.status_code in (200, 201)


def add_to_legacy_shopping_list(item: str) -> bool:
    # Old-style shopping list: append to input_text or use the shopping_list service if available
    if not SUPERVISOR_TOKEN:
        return False
    # We'll try the shopping_list.add_item service
    service_url = f"{HOMEASSISTANT_URL}/services/shopping_list/add_item"
    payload = {"name": item}
    r = requests.post(service_url, headers={"Authorization": f"Bearer {SUPERVISOR_TOKEN}", "Content-Type": "application/json"}, json=payload, timeout=5)
    return r.status_code in (200, 201)
