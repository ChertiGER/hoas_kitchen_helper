import os
import sqlite3
from typing import List, Dict, Any, Optional

DB_PATH = os.environ.get("DB_PATH", "/data/kitchen_helper.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        servings INTEGER DEFAULT 4,
        instructions TEXT,
        source TEXT
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS ingredients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipe_id INTEGER,
        name TEXT,
        amount REAL,
        unit TEXT,
        FOREIGN KEY(recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
    )
    ''')
    conn.commit()
    conn.close()


def get_all_recipes(search: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    if search:
        like = f"%{search}%"
        cur.execute("SELECT * FROM recipes WHERE title LIKE ? OR description LIKE ?", (like, like))
    else:
        cur.execute("SELECT * FROM recipes")
    rows = cur.fetchall()
    recipes = []
    for r in rows:
        cur.execute("SELECT name, amount, unit FROM ingredients WHERE recipe_id = ?", (r["id"],))
        ings = [dict(i) for i in cur.fetchall()]
        recipes.append({
            "id": r["id"],
            "title": r["title"],
            "description": r["description"],
            "servings": r["servings"],
            "instructions": r["instructions"],
            "source": r["source"],
            "ingredients": ings
        })
    conn.close()
    return recipes


def get_recipe_by_id(recipe_id: int) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
    r = cur.fetchone()
    if not r:
        conn.close()
        return None
    cur.execute("SELECT name, amount, unit FROM ingredients WHERE recipe_id = ?", (recipe_id,))
    ings = [dict(i) for i in cur.fetchall()]
    recipe = {
        "id": r["id"],
        "title": r["title"],
        "description": r["description"],
        "servings": r["servings"],
        "instructions": r["instructions"],
        "source": r["source"],
        "ingredients": ings
    }
    conn.close()
    return recipe


def create_recipe(recipe: Dict[str, Any]) -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO recipes (title, description, servings, instructions, source) VALUES (?, ?, ?, ?, ?)",
                (recipe.get("title"), recipe.get("description"), recipe.get("servings", 4), recipe.get("instructions"), recipe.get("source", "Manuell")))
    rid = cur.lastrowid
    for ing in recipe.get("ingredients", []):
        cur.execute("INSERT INTO ingredients (recipe_id, name, amount, unit) VALUES (?, ?, ?, ?)",
                    (rid, ing.get("name"), ing.get("amount"), ing.get("unit")))
    conn.commit()
    conn.close()
    return get_recipe_by_id(rid)


def update_recipe(recipe_id: int, recipe: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE recipes SET title = ?, description = ?, servings = ?, instructions = ?, source = ? WHERE id = ?",
                (recipe.get("title"), recipe.get("description"), recipe.get("servings", 4), recipe.get("instructions"), recipe.get("source", "Manuell"), recipe_id))
    cur.execute("DELETE FROM ingredients WHERE recipe_id = ?", (recipe_id,))
    for ing in recipe.get("ingredients", []):
        cur.execute("INSERT INTO ingredients (recipe_id, name, amount, unit) VALUES (?, ?, ?, ?)",
                    (recipe_id, ing.get("name"), ing.get("amount"), ing.get("unit")))
    conn.commit()
    conn.close()
    return get_recipe_by_id(recipe_id)


def delete_recipe(recipe_id: int) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
    changed = cur.rowcount
    conn.commit()
    conn.close()
    return changed > 0
