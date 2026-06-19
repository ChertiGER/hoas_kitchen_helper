import os
import base64
import gc
import ctypes
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query, status, File, UploadFile, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .database import (
    init_db,
    get_all_recipes,
    get_recipe_by_id,
    create_recipe,
    update_recipe,
    delete_recipe,
    get_pantry_ingredients,
    add_pantry_ingredient,
    delete_pantry_ingredient,
    is_staple_ingredient,
    get_setting,
    set_setting
)
from .ha_api import (
    get_calendars,
    get_todo_lists,
    create_calendar_event,
    add_to_todo_list,
    add_to_legacy_shopping_list,
    is_ha_available
)
from .llm import (
    generate_recipe_via_ai,
    scrape_recipe_from_url,
    import_recipe_from_image,
    generate_recipe_from_leftovers_image
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialisiere die Datenbank beim Start
    init_db()
    # Begrenze den AnyIO-Thread-Pool, um RAM auf dem Raspberry Pi zu sparen
    try:
        from anyio.to_thread import current_default_thread_limiter
        limiter = current_default_thread_limiter()
        limiter.total_tokens = 4
    except Exception as e:
        print(f"Konnte AnyIO Thread-Limit nicht setzen: {e}")
    yield


app = FastAPI(
    title="Küchenhelfer API",
    description="Backend-Dienste für das Küchenhelfer Home Assistant Addon",
    version="1.6.1",
    lifespan=lifespan
)


@app.middleware("http")
async def memory_cleanup_middleware(request: Request, call_next):
    response = await call_next(request)
    # Nach jedem Request Speicher aufräumen
    gc.collect()
    try:
        # malloc_trim ist eine glibc-Funktion auf Linux (Raspberry Pi)
        try:
            libc = ctypes.CDLL("libc.so.6")
        except OSError:
            libc = ctypes.CDLL(None)
        
        if hasattr(libc, "malloc_trim"):
            libc.malloc_trim(0)
    except Exception:
        pass
    return response

# API Schemas
class PantryItem(BaseModel):
    name: str


class SettingsSchema(BaseModel):
    default_calendar: Optional[str] = None
    default_shopping_list: Optional[str] = None


class IngredientSchema(BaseModel):
    name: str
    amount: Optional[float] = None
    unit: Optional[str] = ""


class RecipeSchema(BaseModel):
    title: str
    description: Optional[str] = ""
    servings: int = 4
    instructions: str
    source: Optional[str] = "Manuell"
    ingredients: List[IngredientSchema]
    tags: List[str] = []


class ScrapeRequest(BaseModel):
    url: str


class GenerateRecipeRequest(BaseModel):
    prompt: str
    dietary: str = "keine"
    style: str = "keine"
    servings: int = 4


class CalendarPlanRequest(BaseModel):
    calendar_entity: str
    recipe_id: int
    date: str  # YYYY-MM-DD
    servings: int


class ShoppingListRequest(BaseModel):
    todo_entity: str  # "legacy" oder "todo.xxx"
    items: List[str]  # Liste von fertig formatierten Zutaten, z.B. ["250g Mehl", "1 Prise Salz"]


# ---- Rezept-Datenbank API Endpunkte ----

@app.get("/api/recipes", response_model=List[Dict[str, Any]])
def read_recipes(search: Optional[str] = Query(None, description="Suche nach Rezepttitel oder Beschreibung")):
    recipes = get_all_recipes(search)
    try:
        pantry = get_pantry_ingredients()
    except Exception:
        pantry = []
    for r in recipes:
        for ing in r.get("ingredients", []):
            ing["always_at_home"] = is_staple_ingredient(ing["name"], pantry)
    return recipes


@app.get("/api/recipes/{recipe_id}", response_model=Dict[str, Any])
def read_recipe(recipe_id: int):
    recipe = get_recipe_by_id(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Rezept nicht gefunden")
    try:
        pantry = get_pantry_ingredients()
    except Exception:
        pantry = []
    for ing in recipe.get("ingredients", []):
        ing["always_at_home"] = is_staple_ingredient(ing["name"], pantry)
    return recipe


# ---- Pantry / Standardvorrat Endpunkte ----

@app.get("/api/pantry", response_model=List[str])
def read_pantry():
    try:
        return get_pantry_ingredients()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden des Standardvorrats: {e}")


@app.post("/api/pantry", status_code=status.HTTP_201_CREATED)
def create_pantry_item(item: PantryItem):
    if not item.name.strip():
        raise HTTPException(status_code=400, detail="Name darf nicht leer sein.")
    success = add_pantry_ingredient(item.name)
    if not success:
        raise HTTPException(status_code=400, detail=f"Zutat '{item.name}' ist bereits im Standardvorrat.")
    return {"message": "Zutat erfolgreich hinzugefügt"}


@app.delete("/api/pantry", status_code=status.HTTP_200_OK)
def remove_pantry_item(name: str = Query(..., description="Name der zu löschenden Zutat")):
    if not name.strip():
        raise HTTPException(status_code=400, detail="Name darf nicht leer sein.")
    deleted = delete_pantry_ingredient(name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Zutat '{name}' nicht im Standardvorrat gefunden.")
    return {"message": "Zutat erfolgreich gelöscht"}


@app.post("/api/recipes", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def add_new_recipe(recipe: RecipeSchema):
    try:
        recipe_dict = recipe.model_dump()
        return create_recipe(recipe_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Erstellen des Rezepts: {e}")


@app.put("/api/recipes/{recipe_id}", response_model=Dict[str, Any])
def edit_recipe(recipe_id: int, recipe: RecipeSchema):
    try:
        recipe_dict = recipe.model_dump()
        updated = update_recipe(recipe_id, recipe_dict)
        if not updated:
            raise HTTPException(status_code=404, detail="Rezept nicht gefunden")
        return updated
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Aktualisieren des Rezepts: {e}")


@app.delete("/api/recipes/{recipe_id}", status_code=status.HTTP_200_OK)
def remove_recipe(recipe_id: int):
    deleted = delete_recipe(recipe_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Rezept nicht gefunden")
    return {"message": "Rezept erfolgreich gelöscht"}


# ---- AI/LLM Rezept-Generierung ----

@app.post("/api/recipes/generate")
def generate_ai_recipe(req: GenerateRecipeRequest):
    try:
        recipe_data = generate_recipe_via_ai(
            prompt_text=req.prompt,
            dietary=req.dietary,
            style=req.style,
            servings=req.servings
        )
        return recipe_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/recipes/scrape")
def scrape_recipe(req: ScrapeRequest):
    try:
        return scrape_recipe_from_url(req.url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/recipes/import-image")
async def import_recipe_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Die hochgeladene Datei muss ein Bild sein.")
    try:
        image_bytes = await file.read()
        image_data_b64 = base64.b64encode(image_bytes).decode("utf-8")
        return import_recipe_from_image(image_data_b64, file.content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/recipes/visual-leftovers")
async def visual_leftovers(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Die hochgeladene Datei muss ein Bild sein.")
    try:
        image_bytes = await file.read()
        image_data_b64 = base64.b64encode(image_bytes).decode("utf-8")
        return generate_recipe_from_leftovers_image(image_data_b64, file.content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---- Home Assistant Integration ----

@app.get("/api/ha/status")
def ha_status():
    """Gibt den Status der Home Assistant API-Verbindung zurück."""
    from .llm import load_config
    cfg = load_config()
    db_calendar = get_setting("default_calendar", cfg.get("default_calendar", ""))
    db_shopping_list = get_setting("default_shopping_list", cfg.get("default_shopping_list", ""))
    return {
        "connected": is_ha_available(),
        "using_token": bool(os.environ.get("SUPERVISOR_TOKEN")),
        "default_calendar": db_calendar,
        "default_shopping_list": db_shopping_list
    }


@app.post("/api/settings")
def save_settings(settings: SettingsSchema):
    try:
        if settings.default_calendar is not None:
            set_setting("default_calendar", settings.default_calendar)
        if settings.default_shopping_list is not None:
            set_setting("default_shopping_list", settings.default_shopping_list)
        return {"message": "Einstellungen erfolgreich gespeichert"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Speichern der Einstellungen: {e}")


@app.get("/api/ha/calendars")
def read_ha_calendars():
    """Gibt die verfügbaren Kalender aus HA zurück."""
    return get_calendars()


@app.get("/api/ha/todo-lists")
def read_ha_todo_lists():
    """Gibt die verfügbaren To-Do-Listen aus HA zurück."""
    return get_todo_lists()


@app.post("/api/ha/calendar-plan")
def plan_meal_in_calendar(req: CalendarPlanRequest):
    """Trägt ein Rezept als ganztägiges Ereignis in den HA-Kalender ein."""
    recipe = get_recipe_by_id(req.recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Rezept nicht gefunden")

    # Beschreibung für das Kalenderereignis generieren (mit skalierten Zutaten)
    # Berechne Skalierungsfaktor
    orig_servings = recipe["servings"]
    scale = req.servings / orig_servings if orig_servings > 0 else 1.0

    desc_lines = []
    desc_lines.append(recipe["description"])
    desc_lines.append("")
    desc_lines.append(f"Geplante Portionen: {req.servings} (Original: {orig_servings})")
    desc_lines.append("")
    desc_lines.append("ZUTATEN:")
    for ing in recipe["ingredients"]:
        name = ing["name"]
        amount = ing["amount"]
        unit = ing["unit"] or ""
        if amount is not None:
            scaled_amount = amount * scale
            # Schön formatieren (z.B. keine Nachkommastellen bei .0)
            if scaled_amount.is_integer():
                scaled_amount = int(scaled_amount)
            else:
                scaled_amount = round(scaled_amount, 2)
            desc_lines.append(f"- {scaled_amount} {unit} {name}")
        else:
            desc_lines.append(f"- {unit} {name}".strip())

    desc_lines.append("")
    desc_lines.append("ZUBEREITUNG:")
    desc_lines.append(recipe["instructions"])

    full_description = "\n".join(desc_lines)

    success = create_calendar_event(
        calendar_entity=req.calendar_entity,
        title=f"Kochplan: {recipe['title']}",
        date_str=req.date,
        description=full_description
    )

    if not success:
        raise HTTPException(status_code=500, detail="Ereignis konnte nicht im Kalender erstellt werden.")

    return {"message": "Ereignis erfolgreich im Kalender eingetragen."}


@app.post("/api/ha/shopping-list-add")
def add_ingredients_to_list(req: ShoppingListRequest):
    """Fügt ausgewählte und bereits skalierte Zutaten zur Einkaufsliste hinzu."""
    success_count = 0
    fail_count = 0

    for item in req.items:
        if req.todo_entity == "legacy":
            success = add_to_legacy_shopping_list(item)
        else:
            success = add_to_todo_list(req.todo_entity, item)

        if success:
            success_count += 1
        else:
            fail_count += 1

    if fail_count > 0 and success_count == 0:
        raise HTTPException(status_code=500, detail="Zutaten konnten nicht zur Einkaufsliste hinzugefügt werden.")

    return {
        "message": f"{success_count} Zutaten zur Einkaufsliste hinzugefügt.",
        "failed": fail_count
    }


# ---- Statische Web-Dateien servieren ----
# Wir hängen statische Dateien am Ende an, damit die API-Routen Vorrang haben
app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
