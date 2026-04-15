import difflib
import json
import sqlite3
from datetime import date

DB_NAME = "smart_chef.db"

INGREDIENT_CATALOG = {
    # eggs / dairy
    "eggs": {"display": "Eggs", "category": "Protein", "kcal": 143, "protein": 12.6, "carbs": 0.7, "fats": 9.5, "piece_g": 50},
    "milk": {"display": "Milk", "category": "Dairy", "kcal": 61, "protein": 3.2, "carbs": 4.8, "fats": 3.3, "density": 1.03},
    "yogurt": {"display": "Yogurt", "category": "Dairy", "kcal": 63, "protein": 3.5, "carbs": 4.7, "fats": 3.3, "density": 1.03},
    "greek yogurt": {"display": "Greek yogurt", "category": "Dairy", "kcal": 97, "protein": 9.0, "carbs": 3.9, "fats": 5.0, "density": 1.03},
    "cottage cheese": {"display": "Cottage cheese", "category": "Dairy", "kcal": 98, "protein": 11.1, "carbs": 3.4, "fats": 4.3, "density": 1.0},
    "cream cheese": {"display": "Cream cheese", "category": "Dairy", "kcal": 342, "protein": 6.2, "carbs": 4.1, "fats": 34.4, "tbsp_g": 15, "piece_g": 30},
    "cheese": {"display": "Cheese", "category": "Dairy", "kcal": 402, "protein": 25.0, "carbs": 1.3, "fats": 33.0, "piece_g": 30},
    "feta cheese": {"display": "Feta cheese", "category": "Dairy", "kcal": 265, "protein": 14.2, "carbs": 4.1, "fats": 21.5, "piece_g": 30},
    "kackavalj": {"display": "Kackavalj", "category": "Dairy", "kcal": 356, "protein": 25.0, "carbs": 2.0, "fats": 27.0, "piece_g": 30},
    "protein pudding": {"display": "Protein pudding", "category": "Protein desserts", "kcal": 75, "protein": 10.0, "carbs": 6.0, "fats": 1.0, "density": 1.0, "piece_g": 200},
    "pudding": {"display": "Pudding", "category": "Desserts", "kcal": 120, "protein": 3.0, "carbs": 20.0, "fats": 3.0, "density": 1.0, "piece_g": 125},

    # meat / fish
    "chicken breast": {"display": "Chicken breast", "category": "Meat", "kcal": 165, "protein": 31.0, "carbs": 0.0, "fats": 3.6, "piece_g": 170},
    "chicken": {"display": "Chicken", "category": "Meat", "kcal": 200, "protein": 27.0, "carbs": 0.0, "fats": 8.0, "piece_g": 200},
    "turkey": {"display": "Turkey", "category": "Meat", "kcal": 189, "protein": 29.0, "carbs": 0.0, "fats": 7.0, "piece_g": 180},
    "beef": {"display": "Beef", "category": "Meat", "kcal": 250, "protein": 26.0, "carbs": 0.0, "fats": 15.0, "piece_g": 180},
    "ground beef": {"display": "Ground beef", "category": "Meat", "kcal": 254, "protein": 17.0, "carbs": 0.0, "fats": 20.0, "piece_g": 150},
    "pork": {"display": "Pork", "category": "Meat", "kcal": 242, "protein": 27.0, "carbs": 0.0, "fats": 14.0, "piece_g": 180},
    "ham": {"display": "Ham", "category": "Meat", "kcal": 145, "protein": 21.0, "carbs": 1.5, "fats": 5.5, "piece_g": 30},
    "bacon": {"display": "Bacon", "category": "Meat", "kcal": 541, "protein": 37.0, "carbs": 1.4, "fats": 42.0, "piece_g": 20},
    "sausage": {"display": "Sausage", "category": "Meat", "kcal": 301, "protein": 12.0, "carbs": 2.0, "fats": 27.0, "piece_g": 75},
    "pecenica": {"display": "Pecenica", "category": "Meat", "kcal": 180, "protein": 24.0, "carbs": 1.0, "fats": 9.0, "piece_g": 30},
    "roast meat": {"display": "Roast meat", "category": "Meat", "kcal": 260, "protein": 24.0, "carbs": 0.0, "fats": 18.0, "piece_g": 180},
    "tuna": {"display": "Tuna", "category": "Fish", "kcal": 116, "protein": 25.0, "carbs": 0.0, "fats": 1.0, "piece_g": 120},
    "salmon": {"display": "Salmon", "category": "Fish", "kcal": 208, "protein": 20.0, "carbs": 0.0, "fats": 13.0, "piece_g": 150},
    "white fish": {"display": "White fish", "category": "Fish", "kcal": 96, "protein": 20.0, "carbs": 0.0, "fats": 1.7, "piece_g": 150},

    # grains / carbs
    "bread": {"display": "Bread", "category": "Grains", "kcal": 265, "protein": 9.0, "carbs": 49.0, "fats": 3.2, "piece_g": 30},
    "toast bread": {"display": "Toast bread", "category": "Grains", "kcal": 265, "protein": 9.0, "carbs": 49.0, "fats": 3.2, "piece_g": 25},
    "rice": {"display": "Rice", "category": "Grains", "kcal": 365, "protein": 7.1, "carbs": 80.0, "fats": 0.7, "cup_g": 185, "tbsp_g": 12},
    "pasta": {"display": "Pasta", "category": "Grains", "kcal": 371, "protein": 13.0, "carbs": 75.0, "fats": 1.5, "cup_g": 140, "tbsp_g": 8},
    "oats": {"display": "Oats", "category": "Grains", "kcal": 389, "protein": 16.9, "carbs": 66.3, "fats": 6.9, "cup_g": 90, "tbsp_g": 5},
    "flour": {"display": "Flour", "category": "Baking", "kcal": 364, "protein": 10.0, "carbs": 76.0, "fats": 1.0, "cup_g": 120, "tbsp_g": 8},
    "potato": {"display": "Potato", "category": "Vegetables", "kcal": 77, "protein": 2.0, "carbs": 17.0, "fats": 0.1, "piece_g": 170},

    # vegetables
    "tomato": {"display": "Tomato", "category": "Vegetables", "kcal": 18, "protein": 0.9, "carbs": 3.9, "fats": 0.2, "piece_g": 120},
    "cucumber": {"display": "Cucumber", "category": "Vegetables", "kcal": 15, "protein": 0.7, "carbs": 3.6, "fats": 0.1, "piece_g": 200},
    "lettuce": {"display": "Lettuce", "category": "Vegetables", "kcal": 15, "protein": 1.4, "carbs": 2.9, "fats": 0.2, "piece_g": 100},
    "spinach": {"display": "Spinach", "category": "Vegetables", "kcal": 23, "protein": 2.9, "carbs": 3.6, "fats": 0.4, "cup_g": 30},
    "onion": {"display": "Onion", "category": "Vegetables", "kcal": 40, "protein": 1.1, "carbs": 9.3, "fats": 0.1, "piece_g": 110},
    "garlic": {"display": "Garlic", "category": "Vegetables", "kcal": 149, "protein": 6.4, "carbs": 33.1, "fats": 0.5, "piece_g": 5},
    "mushrooms": {"display": "Mushrooms", "category": "Vegetables", "kcal": 22, "protein": 3.1, "carbs": 3.3, "fats": 0.3, "piece_g": 18},
    "bell pepper": {"display": "Bell pepper", "category": "Vegetables", "kcal": 31, "protein": 1.0, "carbs": 6.0, "fats": 0.3, "piece_g": 120},
    "carrot": {"display": "Carrot", "category": "Vegetables", "kcal": 41, "protein": 0.9, "carbs": 9.6, "fats": 0.2, "piece_g": 60},
    "beans": {"display": "Beans", "category": "Legumes", "kcal": 127, "protein": 8.7, "carbs": 22.8, "fats": 0.5, "cup_g": 170, "tbsp_g": 15},

    # fruit
    "banana": {"display": "Banana", "category": "Fruit", "kcal": 89, "protein": 1.1, "carbs": 22.8, "fats": 0.3, "piece_g": 120},
    "apple": {"display": "Apple", "category": "Fruit", "kcal": 52, "protein": 0.3, "carbs": 13.8, "fats": 0.2, "piece_g": 180},
    "strawberries": {"display": "Strawberries", "category": "Fruit", "kcal": 32, "protein": 0.7, "carbs": 7.7, "fats": 0.3, "cup_g": 150},
    "blueberries": {"display": "Blueberries", "category": "Fruit", "kcal": 57, "protein": 0.7, "carbs": 14.5, "fats": 0.3, "cup_g": 148},

    # sauces / fats / proteins
    "olive oil": {"display": "Olive oil", "category": "Fats", "kcal": 884, "protein": 0.0, "carbs": 0.0, "fats": 100.0, "density": 0.91, "tbsp_g": 13.5, "tsp_g": 4.5},
    "butter": {"display": "Butter", "category": "Fats", "kcal": 717, "protein": 0.9, "carbs": 0.1, "fats": 81.0, "tbsp_g": 14, "tsp_g": 5},
    "peanut butter": {"display": "Peanut butter", "category": "Spreads", "kcal": 588, "protein": 25.0, "carbs": 20.0, "fats": 50.0, "tbsp_g": 16, "tsp_g": 5},
    "ketchup": {"display": "Ketchup", "category": "Sauces", "kcal": 112, "protein": 1.3, "carbs": 26.0, "fats": 0.2, "tbsp_g": 17, "tsp_g": 5.5},
    "mayonnaise": {"display": "Mayonnaise", "category": "Sauces", "kcal": 680, "protein": 1.0, "carbs": 1.0, "fats": 75.0, "tbsp_g": 14, "tsp_g": 5},
    "tartar sauce": {"display": "Tartar sauce", "category": "Sauces", "kcal": 482, "protein": 1.0, "carbs": 6.0, "fats": 50.0, "tbsp_g": 15, "tsp_g": 5},
    "protein powder": {"display": "Protein powder", "category": "Protein supplements", "kcal": 400, "protein": 80.0, "carbs": 8.0, "fats": 6.0, "tbsp_g": 10, "piece_g": 30},
    "protein bar": {"display": "Protein bar", "category": "Protein snacks", "kcal": 350, "protein": 30.0, "carbs": 30.0, "fats": 8.0, "piece_g": 60},
    "honey": {"display": "Honey", "category": "Sweeteners", "kcal": 304, "protein": 0.3, "carbs": 82.4, "fats": 0.0, "tbsp_g": 21, "tsp_g": 7},
}

ALIASES = {
    "egg": "eggs",
    "jaje": "eggs",
    "jaja": "eggs",
    "grcki jogurt": "greek yogurt",
    "obican jogurt": "yogurt",
    "jogurt": "yogurt",
    "sir": "cheese",
    "kackavalj": "kackavalj",
    "mladi sir": "cottage cheese",
    "krem sir": "cream cheese",
    "pilece belo": "chicken breast",
    "pilece grudi": "chicken breast",
    "piletina": "chicken",
    "batak": "chicken",
    "pilece meso": "chicken",
    "govedina": "beef",
    "mleveno meso": "ground beef",
    "svinjetina": "pork",
    "slanina": "bacon",
    "kobasica": "sausage",
    "pecenica": "pecenica",
    "pecenje": "roast meat",
    "sunka": "ham",
    "tunjevina": "tuna",
    "losos": "salmon",
    "riba": "white fish",
    "pirinac": "rice",
    "testenina": "pasta",
    "spagete": "pasta",
    "ovsene": "oats",
    "hleb": "bread",
    "tost": "toast bread",
    "krompir": "potato",
    "paradajz": "tomato",
    "krastavac": "cucumber",
    "zelena salata": "lettuce",
    "zelena": "lettuce",
    "spanac": "spinach",
    "luk": "onion",
    "beli luk": "garlic",
    "sampinjoni": "mushrooms",
    "paprika": "bell pepper",
    "sargarepa": "carrot",
    "pasulj": "beans",
    "jabuka": "apple",
    "banana": "banana",
    "jagode": "strawberries",
    "borovnice": "blueberries",
    "maslinovo ulje": "olive oil",
    "puter": "butter",
    "kikiriki puter": "peanut butter",
    "kecap": "ketchup",
    "majonez": "mayonnaise",
    "tartar": "tartar sauce",
    "protein": "protein powder",
    "whey": "protein powder",
    "proteinska cokoladica": "protein bar",
    "proteinski puding": "protein pudding",
    "puding": "pudding",
    "med": "honey",
}


# suggestions for substring matching
SUBSTRING_HINTS = {
    "chicken": "chicken",
    "breast": "chicken breast",
    "yogurt": "yogurt",
    "cheese": "cheese",
    "tuna": "tuna",
    "salmon": "salmon",
    "bread": "bread",
    "toast": "toast bread",
    "egg": "eggs",
    "sausage": "sausage",
    "ham": "ham",
    "bacon": "bacon",
    "rice": "rice",
    "pasta": "pasta",
    "oat": "oats",
    "tomato": "tomato",
    "cucumber": "cucumber",
    "lettuce": "lettuce",
    "spinach": "spinach",
    "onion": "onion",
    "garlic": "garlic",
    "pepper": "bell pepper",
    "bean": "beans",
    "protein pudding": "protein pudding",
    "protein powder": "protein powder",
    "protein bar": "protein bar",
    "ketchup": "ketchup",
    "mayo": "mayonnaise",
    "mayonnaise": "mayonnaise",
    "tartar": "tartar sauce",
}



def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def normalize_text(value):
    if value is None:
        return ""
    return str(value).strip().lower()


def canonicalize_ingredient_name(name: str) -> str:
    normalized = normalize_text(name)
    if not normalized:
        return ""
    if normalized in INGREDIENT_CATALOG:
        return normalized
    if normalized in ALIASES:
        return ALIASES[normalized]
    for key, value in ALIASES.items():
        if key in normalized:
            return value
    for key, value in SUBSTRING_HINTS.items():
        if key in normalized:
            return value
    close = difflib.get_close_matches(normalized, list(INGREDIENT_CATALOG.keys()) + list(ALIASES.keys()), n=1, cutoff=0.72)
    if close:
        guess = close[0]
        return ALIASES.get(guess, guess)
    return normalized


def display_name_for(name: str) -> str:
    key = canonicalize_ingredient_name(name)
    return INGREDIENT_CATALOG.get(key, {}).get("display", name.strip().title() if name else "")


def get_catalog_display_names():
    return sorted({meta["display"] for meta in INGREDIENT_CATALOG.values()})


def _table_columns(cur, table_name):
    cur.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cur.fetchall()}


def _ensure_column(cur, table_name, column_name, sql_type, default_sql=None):
    columns = _table_columns(cur, table_name)
    if column_name not in columns:
        query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {sql_type}"
        if default_sql is not None:
            query += f" DEFAULT {default_sql}"
        cur.execute(query)


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            goal TEXT,
            daily_calorie_limit INTEGER,
            meals_per_day INTEGER,
            diet_type TEXT,
            allergies TEXT,
            disliked_ingredients TEXT
        )
        """
    )
    _ensure_column(cur, "users", "goal", "TEXT", "'maintenance'")
    _ensure_column(cur, "users", "daily_calorie_limit", "INTEGER", "2000")
    _ensure_column(cur, "users", "meals_per_day", "INTEGER", "3")
    _ensure_column(cur, "users", "diet_type", "TEXT", "'standard'")
    _ensure_column(cur, "users", "allergies", "TEXT", "'[]'")
    _ensure_column(cur, "users", "disliked_ingredients", "TEXT", "'[]'")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS fridge_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            canonical_name TEXT,
            category TEXT,
            quantity REAL,
            unit TEXT,
            calories REAL,
            protein REAL,
            carbs REAL,
            fats REAL,
            nutrition_known INTEGER,
            expiration_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )
    for col, typ, default in [
        ("canonical_name", "TEXT", None),
        ("category", "TEXT", None),
        ("quantity", "REAL", "0"),
        ("unit", "TEXT", None),
        ("calories", "REAL", "0"),
        ("protein", "REAL", "0"),
        ("carbs", "REAL", "0"),
        ("fats", "REAL", "0"),
        ("nutrition_known", "INTEGER", "0"),
        ("expiration_date", "TEXT", None),
    ]:
        _ensure_column(cur, "fridge_items", col, typ, default)

    conn.commit()
    conn.close()


UNIT_OPTIONS = ["g", "kg", "ml", "dl", "l", "piece", "cup", "tbsp", "tsp"]


def quantity_to_grams(canonical_name: str, quantity: float, unit: str):
    meta = INGREDIENT_CATALOG.get(canonical_name)
    if not meta or quantity is None:
        return None
    unit = normalize_text(unit)
    q = float(quantity)
    if unit == "g":
        return q
    if unit == "kg":
        return q * 1000
    if unit == "ml":
        return q * meta.get("density", 1.0)
    if unit == "dl":
        return q * 100 * meta.get("density", 1.0)
    if unit == "l":
        return q * 1000 * meta.get("density", 1.0)
    if unit == "piece":
        return q * meta.get("piece_g") if meta.get("piece_g") else None
    if unit == "cup":
        return q * meta.get("cup_g") if meta.get("cup_g") else None
    if unit == "tbsp":
        return q * meta.get("tbsp_g") if meta.get("tbsp_g") else None
    if unit == "tsp":
        return q * meta.get("tsp_g") if meta.get("tsp_g") else None
    return None


def build_fridge_item(name: str, quantity: float, unit: str, manual_nutrition: dict | None = None):
    raw_name = (name or "").strip()
    canonical_name = canonicalize_ingredient_name(raw_name)
    meta = INGREDIENT_CATALOG.get(canonical_name)

    if manual_nutrition is not None:
        return {
            "name": display_name_for(raw_name),
            "canonical_name": canonical_name,
            "category": meta["category"] if meta else "Other",
            "quantity": float(quantity),
            "unit": unit,
            "calories": float(manual_nutrition.get("calories", 0) or 0),
            "protein": float(manual_nutrition.get("protein", 0) or 0),
            "carbs": float(manual_nutrition.get("carbs", 0) or 0),
            "fats": float(manual_nutrition.get("fats", 0) or 0),
            "nutrition_known": True,
        }

    if not meta:
        return {
            "name": raw_name.title(),
            "canonical_name": canonical_name,
            "category": "Other",
            "quantity": float(quantity),
            "unit": unit,
            "calories": 0.0,
            "protein": 0.0,
            "carbs": 0.0,
            "fats": 0.0,
            "nutrition_known": False,
        }

    grams = quantity_to_grams(canonical_name, quantity, unit)
    if grams is None:
        return {
            "name": meta["display"],
            "canonical_name": canonical_name,
            "category": meta["category"],
            "quantity": float(quantity),
            "unit": unit,
            "calories": 0.0,
            "protein": 0.0,
            "carbs": 0.0,
            "fats": 0.0,
            "nutrition_known": False,
        }

    factor = grams / 100.0
    return {
        "name": meta["display"],
        "canonical_name": canonical_name,
        "category": meta["category"],
        "quantity": float(quantity),
        "unit": unit,
        "calories": round(meta["kcal"] * factor, 1),
        "protein": round(meta["protein"] * factor, 1),
        "carbs": round(meta["carbs"] * factor, 1),
        "fats": round(meta["fats"] * factor, 1),
        "nutrition_known": True,
    }


def get_all_user_names():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM users ORDER BY name")
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows


def get_user_by_name(name):
    if not name:
        return None
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, name, goal, daily_calorie_limit, meals_per_day, diet_type, allergies, disliked_ingredients
        FROM users
        WHERE name = ?
        """,
        (name,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "name": row[1],
        "goal": row[2] or "maintenance",
        "daily_calorie_limit": row[3] if row[3] is not None else 2000,
        "meals_per_day": row[4] if row[4] is not None else 3,
        "diet_type": row[5] or "standard",
        "allergies": json.loads(row[6]) if row[6] else [],
        "disliked_ingredients": json.loads(row[7]) if row[7] else [],
    }


def create_or_update_user(profile):
    existing = get_user_by_name(profile["name"])
    conn = get_connection()
    cur = conn.cursor()
    allergies = json.dumps(profile.get("allergies", []), ensure_ascii=False)
    disliked = json.dumps(profile.get("disliked_ingredients", []), ensure_ascii=False)
    values = (
        profile.get("goal", "maintenance"),
        int(profile.get("daily_calorie_limit", 2000)),
        int(profile.get("meals_per_day", 3)),
        profile.get("diet_type", "standard"),
        allergies,
        disliked,
        profile["name"],
    )
    if existing:
        cur.execute(
            """
            UPDATE users
            SET goal = ?, daily_calorie_limit = ?, meals_per_day = ?, diet_type = ?, allergies = ?, disliked_ingredients = ?
            WHERE name = ?
            """,
            values,
        )
    else:
        cur.execute(
            """
            INSERT INTO users (goal, daily_calorie_limit, meals_per_day, diet_type, allergies, disliked_ingredients, name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            values,
        )
    conn.commit()
    conn.close()


def delete_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM fridge_items WHERE user_id = ?", (user_id,))
    cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def add_fridge_item(user_id, name, quantity, unit, expiration_date=None, manual_nutrition=None):
    item = build_fridge_item(name, quantity, unit, manual_nutrition)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO fridge_items (
            user_id, name, canonical_name, category, quantity, unit, calories, protein, carbs, fats, nutrition_known, expiration_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            item["name"],
            item["canonical_name"],
            item["category"],
            item["quantity"],
            item["unit"],
            item["calories"],
            item["protein"],
            item["carbs"],
            item["fats"],
            int(item["nutrition_known"]),
            expiration_date,
        ),
    )
    conn.commit()
    conn.close()


def get_fridge_for_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, name, canonical_name, category, quantity, unit, calories, protein, carbs, fats, nutrition_known, expiration_date
        FROM fridge_items
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "id": row[0],
            "name": row[1],
            "canonical_name": row[2],
            "category": row[3],
            "quantity": row[4],
            "unit": row[5],
            "calories": row[6],
            "protein": row[7],
            "carbs": row[8],
            "fats": row[9],
            "nutrition_known": bool(row[10]),
            "expiration_date": row[11],
        }
        for row in rows
    ]


def update_fridge_item(item_id, name, quantity, unit, expiration_date=None, manual_nutrition=None):
    item = build_fridge_item(name, quantity, unit, manual_nutrition)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE fridge_items
        SET name = ?, canonical_name = ?, category = ?, quantity = ?, unit = ?, calories = ?, protein = ?, carbs = ?, fats = ?, nutrition_known = ?, expiration_date = ?
        WHERE id = ?
        """,
        (
            item["name"],
            item["canonical_name"],
            item["category"],
            item["quantity"],
            item["unit"],
            item["calories"],
            item["protein"],
            item["carbs"],
            item["fats"],
            int(item["nutrition_known"]),
            expiration_date,
            item_id,
        ),
    )
    conn.commit()
    conn.close()


def delete_fridge_item(item_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM fridge_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()


def delete_all_fridge_for_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM fridge_items WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
