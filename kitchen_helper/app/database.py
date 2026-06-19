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
