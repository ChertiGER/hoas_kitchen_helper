import os
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.environ.get("DB_PATH", "/data/kitchen_helper.db")

# Fallback für lokale Entwicklung außerhalb von HA
if not os.path.exists(os.path.dirname(DB_PATH)) and os.path.dirname(DB_PATH) != "":
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_db_connection():
    """Erstellt eine Verbindung zur SQLite-Datenbank und aktiviert Fremdschlüssel-Unterstützung."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Initialisiert die Datenbank-Tabellen, falls sie noch nicht existieren."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Rezepte-Tabelle
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        servings INTEGER NOT NULL DEFAULT 4,
        instructions TEXT NOT NULL,
        source TEXT DEFAULT 'Manuell',
        created_at TEXT NOT NULL
    );
    """)

    # Zutaten-Tabelle
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ingredients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipe_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        amount REAL,
        unit TEXT,
        FOREIGN KEY (recipe_id) REFERENCES recipes (id) ON DELETE CASCADE
    );
    """)

    # Pantry-Tabelle (Standardzutaten)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pantry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );
    """)

    conn.commit()
    conn.close()


def get_all_recipes(search_query: Optional[str] = None) -> List[Dict[str, Any]]:
    """Gibt alle Rezepte aus der Datenbank zurück, optional gefiltert nach Suchbegriff."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if search_query:
        cursor.execute(
            "SELECT * FROM recipes WHERE title LIKE ? OR description LIKE ? ORDER BY title ASC",
            (f"%{search_query}%", f"%{search_query}%")
        )
    else:
        cursor.execute("SELECT * FROM recipes ORDER BY title ASC")

    recipes = [dict(row) for row in cursor.fetchall()]

    for r in recipes:
        cursor.execute("SELECT name, amount, unit FROM ingredients WHERE recipe_id = ?", (r["id"],))
        r["ingredients"] = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return recipes


def get_recipe_by_id(recipe_id: int) -> Optional[Dict[str, Any]]:
    """Gibt ein bestimmtes Rezept anhand der ID inklusive aller Zutaten zurück."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    recipe = dict(row)

    cursor.execute("SELECT name, amount, unit FROM ingredients WHERE recipe_id = ?", (recipe_id,))
    recipe["ingredients"] = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return recipe


def create_recipe(recipe_data: Dict[str, Any]) -> Dict[str, Any]:
    """Erstellt ein neues Rezept mit Zutaten in einer Transaktion."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        title = recipe_data["title"]
        description = recipe_data.get("description", "")
        servings = recipe_data.get("servings", 4)
        instructions = recipe_data["instructions"]
        source = recipe_data.get("source", "Manuell")
        created_at = datetime.now().isoformat()

        cursor.execute(
            "INSERT INTO recipes (title, description, servings, instructions, source, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (title, description, servings, instructions, source, created_at)
        )
        recipe_id = cursor.lastrowid

        ingredients = recipe_data.get("ingredients", [])
        for ing in ingredients:
            name = ing["name"]
            # amount kann None oder leer sein für Zutaten wie "Salz nach Geschmack"
            amount = ing.get("amount")
            if amount == "":
                amount = None
            elif amount is not None:
                try:
                    amount = float(amount)
                except ValueError:
                    amount = None
            unit = ing.get("unit", "")
            cursor.execute(
                "INSERT INTO ingredients (recipe_id, name, amount, unit) VALUES (?, ?, ?, ?)",
                (recipe_id, name, amount, unit)
            )

        conn.commit()
        recipe_data["id"] = recipe_id
        recipe_data["created_at"] = created_at
        return recipe_data
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def update_recipe(recipe_id: int, recipe_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Aktualisiert ein Rezept und seine Zutaten."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Prüfen, ob Rezept existiert
    cursor.execute("SELECT id FROM recipes WHERE id = ?", (recipe_id,))
    if not cursor.fetchone():
        conn.close()
        return None

    try:
        title = recipe_data["title"]
        description = recipe_data.get("description", "")
        servings = recipe_data.get("servings", 4)
        instructions = recipe_data["instructions"]
        source = recipe_data.get("source", "Manuell")

        cursor.execute(
            "UPDATE recipes SET title = ?, description = ?, servings = ?, instructions = ?, source = ? WHERE id = ?",
            (title, description, servings, instructions, source, recipe_id)
        )

        # Alte Zutaten löschen und neu anlegen (einfachster Weg für Updates)
        cursor.execute("DELETE FROM ingredients WHERE recipe_id = ?", (recipe_id,))

        ingredients = recipe_data.get("ingredients", [])
        for ing in ingredients:
            name = ing["name"]
            amount = ing.get("amount")
            if amount == "":
                amount = None
            elif amount is not None:
                try:
                    amount = float(amount)
                except ValueError:
                    amount = None
            unit = ing.get("unit", "")
            cursor.execute(
                "INSERT INTO ingredients (recipe_id, name, amount, unit) VALUES (?, ?, ?, ?)",
                (recipe_id, name, amount, unit)
            )

        conn.commit()
        return get_recipe_by_id(recipe_id)
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def delete_recipe(recipe_id: int) -> bool:
    """Löscht ein Rezept (Kaskadierendes Löschen der Zutaten durch FOREIGN KEY)."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id FROM recipes WHERE id = ?", (recipe_id,))
        if not cursor.fetchone():
            return False

        cursor.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


# ---- PANTRY & DEUTSCHES STANDARD-REPERTOIRE LOGIK ----

GERMAN_KITCHEN_STAPLES = {
    # Gewürze & Würzmittel
    "salz", "pfeffer", "zucker", "essig", "öl", "speiseöl", "rapsöl", "sonnenblumenöl", "olivenöl", "senf", "ketchup", "mayonnaise",
    "brühwürfel", "gemüsebrühe", "paprikapulver", "paprika edelsüß", "paprika rosenscharf", "zimt", "muskatnuss", "currypulver", "oregano",
    "thymian", "rosmarin", "majoran", "lorbeerblatt", "lorbeerblätter", "tomatenmark", "sojasauce",
    # Backzutaten
    "mehl", "weizenmehl", "backpulver", "vanillezucker", "hefe", "trockenhefe", "speisestärke",
    # Frische Basics
    "wasser", "leitungswasser", "zwiebel", "zwiebeln", "knoblauch", "knoblauchzehe", "knoblauchzehen", "ingwer",
    # Fette & Milchprodukte
    "butter", "milch", "speisequark", "quark", "schmand", "sahne", "schlagsahne",
    # Sonstiges
    "ei", "eier"
}

import re

def normalize_ingredient_name(name: str) -> str:
    # In Kleinbuchstaben umwandeln
    name = name.lower()
    # Entferne Zahlen und Sonderzeichen
    name = re.sub(r'[^\w\s]', ' ', name)
    # Entferne Mengenangaben & häufige Maßeinheiten/Zubereitungsarten
    stopwords = {"prise", "el", "tl", "g", "ml", "kg", "stk", "stück", "zehe", "zehen", "bund", "dose", "dosen", "becher", "packung", "frisch", "gemahlen", "getrocknet", "gehackt"}
    words = [w for w in name.split() if w not in stopwords]
    return " ".join(words).strip()

def is_staple_ingredient(name: str, custom_pantry: List[str]) -> bool:
    normalized_name = normalize_ingredient_name(name)
    if not normalized_name:
        return False
        
    pantry_set = {p.lower().strip() for p in custom_pantry}
    
    # 1. Prüfe exakte Übereinstimmung
    if normalized_name in GERMAN_KITCHEN_STAPLES or normalized_name in pantry_set:
        return True
        
    # 2. Prüfe, ob eines der Wörter in den Staples/Pantry vorkommt
    for word in normalized_name.split():
        if word in GERMAN_KITCHEN_STAPLES or word in pantry_set:
            return True
            
        # Prüfe Ähnlichkeit (z.B. Zwiebel/Zwiebeln, Knoblauch/Knoblauchzehe)
        for staple in GERMAN_KITCHEN_STAPLES.union(pantry_set):
            if word.startswith(staple) or staple.startswith(word):
                if len(word) >= 3 and len(staple) >= 3 and abs(len(word) - len(staple)) <= 2:
                    return True
                    
    return False


def get_pantry_ingredients() -> List[str]:
    """Gibt alle Standardzutaten aus der Pantry zurück."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM pantry ORDER BY name ASC")
    items = [row["name"] for row in cursor.fetchall()]
    conn.close()
    return items


def add_pantry_ingredient(name: str) -> bool:
    """Fügt eine neue Zutat zur Pantry hinzu."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO pantry (name) VALUES (?)", (name.strip(),))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Bereits vorhanden
        return False
    finally:
        conn.close()


def delete_pantry_ingredient(name: str) -> bool:
    """Löscht eine Zutat aus der Pantry."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pantry WHERE name = ?", (name.strip(),))
    rows = cursor.rowcount
    conn.commit()
    conn.close()
    return rows > 0
