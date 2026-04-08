
import json
import sqlite3
from datetime import date

DB_NAME = "smart_chef.db"


PRESET_RECIPES = [
    {
        "name": "Oatmeal with Banana and Honey",
        "meal_type": "breakfast",
        "taste_type": "sweet",
        "diet_type": "light",
        "prep_time": 10,
        "calories": 350,
        "protein": 12,
        "carbs": 55,
        "fats": 8,
        "description": "A quick sweet breakfast rich in fiber.",
        "instructions": "Cook oats with milk. Add sliced banana and honey on top.",
        "ingredients": [
            {"ingredient_name": "oats", "quantity": 80, "unit": "g"},
            {"ingredient_name": "milk", "quantity": 250, "unit": "ml"},
            {"ingredient_name": "banana", "quantity": 1, "unit": "piece"},
            {"ingredient_name": "honey", "quantity": 1, "unit": "tbsp"},
        ],
    },
    {
        "name": "Greek Yogurt Bowl",
        "meal_type": "breakfast",
        "taste_type": "sweet",
        "diet_type": "high-protein",
        "prep_time": 5,
        "calories": 320,
        "protein": 24,
        "carbs": 28,
        "fats": 10,
        "description": "High-protein breakfast with fruit and yogurt.",
        "instructions": "Place yogurt in a bowl, add banana and strawberries, then drizzle honey.",
        "ingredients": [
            {"ingredient_name": "greek yogurt", "quantity": 200, "unit": "g"},
            {"ingredient_name": "banana", "quantity": 1, "unit": "piece"},
            {"ingredient_name": "strawberries", "quantity": 100, "unit": "g"},
            {"ingredient_name": "honey", "quantity": 1, "unit": "tbsp"},
        ],
    },
    {
        "name": "Vegetable Omelette",
        "meal_type": "breakfast",
        "taste_type": "savory",
        "diet_type": "vegetarian",
        "prep_time": 15,
        "calories": 410,
        "protein": 24,
        "carbs": 10,
        "fats": 28,
        "description": "Egg-based savory breakfast with vegetables.",
        "instructions": "Whisk eggs. Saute onion, mushrooms and pepper. Pour eggs and cook until set.",
        "ingredients": [
            {"ingredient_name": "eggs", "quantity": 3, "unit": "piece"},
            {"ingredient_name": "onion", "quantity": 80, "unit": "g"},
            {"ingredient_name": "mushrooms", "quantity": 100, "unit": "g"},
            {"ingredient_name": "bell pepper", "quantity": 80, "unit": "g"},
            {"ingredient_name": "olive oil", "quantity": 1, "unit": "tbsp"},
        ],
    },
    {
        "name": "Chicken Rice Bowl",
        "meal_type": "lunch",
        "taste_type": "savory",
        "diet_type": "high-protein",
        "prep_time": 30,
        "calories": 620,
        "protein": 42,
        "carbs": 58,
        "fats": 18,
        "description": "Balanced lunch with chicken, rice and vegetables.",
        "instructions": "Cook rice. Grill chicken. Saute vegetables and serve everything in one bowl.",
        "ingredients": [
            {"ingredient_name": "chicken breast", "quantity": 180, "unit": "g"},
            {"ingredient_name": "rice", "quantity": 90, "unit": "g"},
            {"ingredient_name": "bell pepper", "quantity": 100, "unit": "g"},
            {"ingredient_name": "spinach", "quantity": 80, "unit": "g"},
            {"ingredient_name": "olive oil", "quantity": 1, "unit": "tbsp"},
        ],
    },
    {
        "name": "Tuna Pasta",
        "meal_type": "lunch",
        "taste_type": "savory",
        "diet_type": "standard",
        "prep_time": 25,
        "calories": 590,
        "protein": 34,
        "carbs": 68,
        "fats": 18,
        "description": "Quick pasta with tuna and tomato.",
        "instructions": "Boil pasta. Mix tuna, tomato and olive oil. Combine and serve.",
        "ingredients": [
            {"ingredient_name": "pasta", "quantity": 90, "unit": "g"},
            {"ingredient_name": "tuna", "quantity": 150, "unit": "g"},
            {"ingredient_name": "tomato", "quantity": 150, "unit": "g"},
            {"ingredient_name": "olive oil", "quantity": 1, "unit": "tbsp"},
            {"ingredient_name": "garlic", "quantity": 10, "unit": "g"},
        ],
    },
    {
        "name": "Beans and Potato Stew",
        "meal_type": "lunch",
        "taste_type": "savory",
        "diet_type": "vegan",
        "prep_time": 35,
        "calories": 480,
        "protein": 18,
        "carbs": 72,
        "fats": 10,
        "description": "Comforting vegan lunch with beans and potatoes.",
        "instructions": "Saute onion and garlic, add potatoes and beans, simmer until potatoes are tender.",
        "ingredients": [
            {"ingredient_name": "beans", "quantity": 200, "unit": "g"},
            {"ingredient_name": "potato", "quantity": 250, "unit": "g"},
            {"ingredient_name": "onion", "quantity": 100, "unit": "g"},
            {"ingredient_name": "garlic", "quantity": 10, "unit": "g"},
            {"ingredient_name": "olive oil", "quantity": 1, "unit": "tbsp"},
        ],
    },
    {
        "name": "Chicken Salad",
        "meal_type": "dinner",
        "taste_type": "savory",
        "diet_type": "light",
        "prep_time": 20,
        "calories": 430,
        "protein": 36,
        "carbs": 12,
        "fats": 24,
        "description": "Light dinner with chicken and fresh vegetables.",
        "instructions": "Grill chicken, chop vegetables, mix with olive oil and serve.",
        "ingredients": [
            {"ingredient_name": "chicken breast", "quantity": 160, "unit": "g"},
            {"ingredient_name": "lettuce", "quantity": 100, "unit": "g"},
            {"ingredient_name": "cucumber", "quantity": 120, "unit": "g"},
            {"ingredient_name": "tomato", "quantity": 120, "unit": "g"},
            {"ingredient_name": "olive oil", "quantity": 1, "unit": "tbsp"},
        ],
    },
    {
        "name": "Mushroom Cheese Toast",
        "meal_type": "dinner",
        "taste_type": "savory",
        "diet_type": "vegetarian",
        "prep_time": 15,
        "calories": 450,
        "protein": 20,
        "carbs": 35,
        "fats": 24,
        "description": "Warm toast with mushrooms and cheese.",
        "instructions": "Saute mushrooms, place on bread, add cheese and toast until melted.",
        "ingredients": [
            {"ingredient_name": "bread", "quantity": 2, "unit": "piece"},
            {"ingredient_name": "mushrooms", "quantity": 120, "unit": "g"},
            {"ingredient_name": "cheese", "quantity": 70, "unit": "g"},
            {"ingredient_name": "butter", "quantity": 10, "unit": "g"},
        ],
    },
    {
        "name": "Banana Peanut Snack",
        "meal_type": "snack",
        "taste_type": "sweet",
        "diet_type": "high-protein",
        "prep_time": 5,
        "calories": 290,
        "protein": 10,
        "carbs": 24,
        "fats": 16,
        "description": "Fast snack with banana and peanut butter.",
        "instructions": "Slice banana and serve with peanut butter.",
        "ingredients": [
            {"ingredient_name": "banana", "quantity": 1, "unit": "piece"},
            {"ingredient_name": "peanut butter", "quantity": 2, "unit": "tbsp"},
        ],
    },
    {
        "name": "Apple Yogurt Snack",
        "meal_type": "snack",
        "taste_type": "sweet",
        "diet_type": "light",
        "prep_time": 5,
        "calories": 230,
        "protein": 14,
        "carbs": 28,
        "fats": 6,
        "description": "Simple light snack with apple and yogurt.",
        "instructions": "Chop apple and serve with Greek yogurt.",
        "ingredients": [
            {"ingredient_name": "apple", "quantity": 1, "unit": "piece"},
            {"ingredient_name": "greek yogurt", "quantity": 150, "unit": "g"},
        ],
    },
]


def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        age INTEGER,
        gender TEXT,
        height INTEGER,
        weight INTEGER,
        goal TEXT,
        daily_calorie_limit INTEGER,
        diet_type TEXT,
        favorite_cuisines TEXT,
        disliked_ingredients TEXT,
        allergies TEXT,
        meals_per_day INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fridge_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        category TEXT,
        quantity REAL,
        unit TEXT,
        expiration_date TEXT,
        calories INTEGER,
        protein INTEGER,
        carbs INTEGER,
        fats INTEGER,
        is_favorite INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        meal_type TEXT,
        taste_type TEXT,
        diet_type TEXT,
        prep_time INTEGER,
        calories INTEGER,
        protein INTEGER,
        carbs INTEGER,
        fats INTEGER,
        description TEXT,
        instructions TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS recipe_ingredients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipe_id INTEGER NOT NULL,
        ingredient_name TEXT,
        quantity REAL,
        unit TEXT,
        FOREIGN KEY (recipe_id) REFERENCES recipes(id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS favorite_recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        recipe_id INTEGER NOT NULL,
        UNIQUE(user_id, recipe_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS meal_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        recipe_id INTEGER NOT NULL,
        prepared_date TEXT NOT NULL
    )
    """)

    conn.commit()
    _seed_recipes(conn)
    conn.close()


def _seed_recipes(conn):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM recipes")
    count = cur.fetchone()[0]
    if count > 0:
        return

    for recipe in PRESET_RECIPES:
        cur.execute("""
            INSERT INTO recipes (
                name, meal_type, taste_type, diet_type, prep_time,
                calories, protein, carbs, fats, description, instructions
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            recipe["name"],
            recipe["meal_type"],
            recipe["taste_type"],
            recipe["diet_type"],
            recipe["prep_time"],
            recipe["calories"],
            recipe["protein"],
            recipe["carbs"],
            recipe["fats"],
            recipe["description"],
            recipe["instructions"],
        ))
        recipe_id = cur.lastrowid

        for ingredient in recipe["ingredients"]:
            cur.execute("""
                INSERT INTO recipe_ingredients (recipe_id, ingredient_name, quantity, unit)
                VALUES (?, ?, ?, ?)
            """, (
                recipe_id,
                ingredient["ingredient_name"],
                ingredient["quantity"],
                ingredient["unit"],
            ))
    conn.commit()


def get_all_user_names():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM users ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]


def get_user_by_name(name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, age, gender, height, weight, goal, daily_calorie_limit,
               diet_type, favorite_cuisines, disliked_ingredients, allergies, meals_per_day
        FROM users
        WHERE name = ?
    """, (name,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "name": row[1],
        "age": row[2] if row[2] is not None else 22,
        "gender": row[3] or "female",
        "height": row[4] if row[4] is not None else 170,
        "weight": row[5] if row[5] is not None else 60,
        "goal": row[6] or "maintenance",
        "daily_calorie_limit": row[7] if row[7] is not None else 2000,
        "diet_type": row[8] or "standard",
        "favorite_cuisines": json.loads(row[9]) if row[9] else [],
        "disliked_ingredients": json.loads(row[10]) if row[10] else [],
        "allergies": json.loads(row[11]) if row[11] else [],
        "meals_per_day": row[12] if row[12] is not None else 3,
    }


def create_or_update_user(profile):
    existing = get_user_by_name(profile["name"])
    conn = get_connection()
    cur = conn.cursor()

    favorite_cuisines_json = json.dumps(profile.get("favorite_cuisines", []), ensure_ascii=False)
    disliked_json = json.dumps(profile.get("disliked_ingredients", []), ensure_ascii=False)
    allergies_json = json.dumps(profile.get("allergies", []), ensure_ascii=False)

    if existing:
        cur.execute("""
            UPDATE users
            SET age = ?, gender = ?, height = ?, weight = ?, goal = ?,
                daily_calorie_limit = ?, diet_type = ?, favorite_cuisines = ?,
                disliked_ingredients = ?, allergies = ?, meals_per_day = ?
            WHERE name = ?
        """, (
            profile.get("age"),
            profile.get("gender"),
            profile.get("height"),
            profile.get("weight"),
            profile.get("goal"),
            profile.get("daily_calorie_limit"),
            profile.get("diet_type"),
            favorite_cuisines_json,
            disliked_json,
            allergies_json,
            profile.get("meals_per_day", 3),
            profile["name"],
        ))
    else:
        cur.execute("""
            INSERT INTO users (
                name, age, gender, height, weight, goal, daily_calorie_limit,
                diet_type, favorite_cuisines, disliked_ingredients, allergies, meals_per_day
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            profile["name"],
            profile.get("age"),
            profile.get("gender"),
            profile.get("height"),
            profile.get("weight"),
            profile.get("goal"),
            profile.get("daily_calorie_limit"),
            profile.get("diet_type"),
            favorite_cuisines_json,
            disliked_json,
            allergies_json,
            profile.get("meals_per_day", 3),
        ))

    conn.commit()
    conn.close()


def delete_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM fridge_items WHERE user_id = ?", (user_id,))
    cur.execute("DELETE FROM favorite_recipes WHERE user_id = ?", (user_id,))
    cur.execute("DELETE FROM meal_history WHERE user_id = ?", (user_id,))
    cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def add_fridge_item(user_id, item):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO fridge_items (
            user_id, name, category, quantity, unit, expiration_date,
            calories, protein, carbs, fats, is_favorite
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        item["name"],
        item["category"],
        item["quantity"],
        item["unit"],
        item.get("expiration_date"),
        item.get("calories", 0),
        item.get("protein", 0),
        item.get("carbs", 0),
        item.get("fats", 0),
        int(item.get("is_favorite", False)),
    ))
    conn.commit()
    conn.close()


def get_fridge_for_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, category, quantity, unit, expiration_date,
               calories, protein, carbs, fats, is_favorite
        FROM fridge_items
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,))
    rows = cur.fetchall()
    conn.close()

    items = []
    for row in rows:
        items.append({
            "id": row[0],
            "name": row[1],
            "category": row[2],
            "quantity": row[3],
            "unit": row[4],
            "expiration_date": row[5],
            "calories": row[6],
            "protein": row[7],
            "carbs": row[8],
            "fats": row[9],
            "is_favorite": bool(row[10]),
        })
    return items


def update_fridge_item(item_id, item):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE fridge_items
        SET name = ?, category = ?, quantity = ?, unit = ?, expiration_date = ?,
            calories = ?, protein = ?, carbs = ?, fats = ?, is_favorite = ?
        WHERE id = ?
    """, (
        item["name"],
        item["category"],
        item["quantity"],
        item["unit"],
        item.get("expiration_date"),
        item.get("calories", 0),
        item.get("protein", 0),
        item.get("carbs", 0),
        item.get("fats", 0),
        int(item.get("is_favorite", False)),
        item_id,
    ))
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


def get_all_recipes():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, meal_type, taste_type, diet_type, prep_time,
               calories, protein, carbs, fats, description, instructions
        FROM recipes
        ORDER BY name
    """)
    rows = cur.fetchall()
    conn.close()

    recipes = []
    for row in rows:
        recipes.append({
            "id": row[0],
            "name": row[1],
            "meal_type": row[2],
            "taste_type": row[3],
            "diet_type": row[4],
            "prep_time": row[5],
            "calories": row[6],
            "protein": row[7],
            "carbs": row[8],
            "fats": row[9],
            "description": row[10],
            "instructions": row[11],
        })
    return recipes


def get_recipe_details(recipe_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, meal_type, taste_type, diet_type, prep_time,
               calories, protein, carbs, fats, description, instructions
        FROM recipes
        WHERE id = ?
    """, (recipe_id,))
    row = cur.fetchone()

    cur.execute("""
        SELECT ingredient_name, quantity, unit
        FROM recipe_ingredients
        WHERE recipe_id = ?
        ORDER BY id
    """, (recipe_id,))
    ingredients_rows = cur.fetchall()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "name": row[1],
        "meal_type": row[2],
        "taste_type": row[3],
        "diet_type": row[4],
        "prep_time": row[5],
        "calories": row[6],
        "protein": row[7],
        "carbs": row[8],
        "fats": row[9],
        "description": row[10],
        "instructions": row[11],
        "ingredients": [
            {
                "ingredient_name": x[0],
                "quantity": x[1],
                "unit": x[2],
            }
            for x in ingredients_rows
        ],
    }


def get_favorite_recipe_ids(user_name):
    user = get_user_by_name(user_name)
    if not user:
        return set()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT recipe_id FROM favorite_recipes WHERE user_id = ?", (user["id"],))
    rows = cur.fetchall()
    conn.close()
    return {x[0] for x in rows}


def toggle_favorite_recipe(user_name, recipe_id):
    user = get_user_by_name(user_name)
    if not user:
        return

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id FROM favorite_recipes
        WHERE user_id = ? AND recipe_id = ?
    """, (user["id"], recipe_id))
    row = cur.fetchone()

    if row:
        cur.execute("DELETE FROM favorite_recipes WHERE id = ?", (row[0],))
    else:
        cur.execute("""
            INSERT OR IGNORE INTO favorite_recipes (user_id, recipe_id)
            VALUES (?, ?)
        """, (user["id"], recipe_id))

    conn.commit()
    conn.close()


def save_meal_to_history(user_name, recipe_id):
    user = get_user_by_name(user_name)
    if not user:
        return

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO meal_history (user_id, recipe_id, prepared_date)
        VALUES (?, ?, ?)
    """, (user["id"], recipe_id, date.today().isoformat()))
    conn.commit()
    conn.close()


def get_recent_history_for_user(user_name, limit=5):
    user = get_user_by_name(user_name)
    if not user:
        return []

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT mh.prepared_date, r.name
        FROM meal_history mh
        JOIN recipes r ON mh.recipe_id = r.id
        WHERE mh.user_id = ?
        ORDER BY mh.id DESC
        LIMIT ?
    """, (user["id"], limit))
    rows = cur.fetchall()
    conn.close()

    return [
        {"prepared_date": x[0], "recipe_name": x[1]}
        for x in rows
    ]
