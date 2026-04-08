
import pandas as pd
import streamlit as st
from datetime import date, timedelta

from database import (
    init_db,
    get_all_user_names,
    get_user_by_name,
    create_or_update_user,
    delete_user,
    add_fridge_item,
    get_fridge_for_user,
    update_fridge_item,
    delete_fridge_item,
    delete_all_fridge_for_user,
    get_all_recipes,
    get_recipe_details,
    toggle_favorite_recipe,
    get_favorite_recipe_ids,
    save_meal_to_history,
    get_recent_history_for_user,
)
from recommender import recommend_meals

st.set_page_config(page_title="Smart Chef", page_icon="🍳", layout="wide")
init_db()

if "selected_user_name" not in st.session_state:
    st.session_state.selected_user_name = None

if "meal_filters" not in st.session_state:
    st.session_state.meal_filters = {
        "meal_type": "breakfast",
        "taste_type": "savory",
        "diet_type": "standard",
        "max_calories": 600,
        "max_prep_time": 30,
        "servings": 1,
        "prefer_expiring": True,
    }

CATEGORY_OPTIONS = {
    "dairy": "Dairy",
    "meat": "Meat",
    "fish": "Fish",
    "vegetables": "Vegetables",
    "fruit": "Fruit",
    "grains": "Grains",
    "legumes": "Legumes",
    "spices": "Spices",
    "oils": "Oils",
    "drinks": "Drinks",
    "other": "Other",
}

UNIT_OPTIONS = ["g", "kg", "ml", "l", "piece", "cup", "tbsp", "tsp"]

MEAL_TYPE_LABELS = {
    "breakfast": "Breakfast",
    "lunch": "Lunch",
    "dinner": "Dinner",
    "snack": "Snack",
}

TASTE_TYPE_LABELS = {
    "savory": "Savory",
    "sweet": "Sweet",
    "any": "Any",
}

DIET_TYPE_LABELS = {
    "standard": "Standard",
    "vegetarian": "Vegetarian",
    "vegan": "Vegan",
    "high-protein": "High protein",
    "light": "Light",
    "any": "Any",
}

GOAL_LABELS = {
    "maintenance": "Maintenance",
    "weight-loss": "Weight loss",
    "muscle-gain": "Muscle gain",
}

PRESET_INGREDIENTS = [
    "Eggs", "Milk", "Greek yogurt", "Cheese", "Chicken breast", "Tuna",
    "Rice", "Pasta", "Oats", "Bread", "Tomato", "Cucumber", "Lettuce",
    "Potato", "Onion", "Garlic", "Mushrooms", "Bell pepper", "Spinach",
    "Banana", "Apple", "Strawberries", "Peanut butter", "Olive oil",
    "Butter", "Flour", "Sugar", "Honey", "Dark chocolate", "Beans"
]


def themed_header(title: str, subtitle: str, gradient: str):
    st.markdown(
        f"""
        <div style="
            background:{gradient};
            color:white;
            border-radius:24px;
            padding:34px 30px 28px 30px;
            margin-bottom:24px;
            box-shadow:0 10px 24px rgba(0,0,0,0.10);
        ">
            <div style="font-size:2.5rem;font-weight:800;line-height:1.15;">{title}</div>
            <div style="margin-top:12px;font-size:1.08rem;opacity:0.96;">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(title, value, subtitle=""):
    st.markdown(
        f"""
        <div style="
            background:white;
            border-radius:18px;
            padding:18px;
            box-shadow:0 8px 18px rgba(0,0,0,0.06);
            border:1px solid rgba(0,0,0,0.06);
            margin-bottom:16px;
            min-height:120px;
        ">
            <div style="font-size:0.95rem;color:#6b7280;font-weight:600;">{title}</div>
            <div style="font-size:1.8rem;font-weight:800;color:#111827;margin-top:8px;">{value}</div>
            <div style="font-size:0.95rem;color:#6b7280;margin-top:8px;">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def days_until(expiration_date):
    if not expiration_date:
        return None
    return (date.fromisoformat(expiration_date) - date.today()).days


def fridge_preview_dataframe(items):
    rows = []
    for item in items:
        due = days_until(item["expiration_date"])
        exp_text = "Not set" if due is None else ("Expired" if due < 0 else f"{due} day(s)")
        rows.append({
            "Name": item["name"],
            "Category": CATEGORY_OPTIONS.get(item["category"], item["category"]),
            "Quantity": f'{item["quantity"]} {item["unit"]}',
            "Expires in": exp_text,
            "Calories": item["calories"],
            "Protein": item["protein"],
        })
    return pd.DataFrame(rows)


def recipe_card(recipe, is_favorite=False):
    badge = "⭐ Favorite" if is_favorite else ""
    st.markdown(
        f"""
        <div style="
            background:white;
            border-radius:22px;
            padding:20px;
            box-shadow:0 8px 18px rgba(0,0,0,0.06);
            border:1px solid rgba(0,0,0,0.06);
            margin-bottom:18px;
        ">
            <div style="font-size:1.3rem;font-weight:800;color:#111827;">{recipe['name']}</div>
            <div style="font-size:0.95rem;color:#6b7280;margin-top:4px;">
                {MEAL_TYPE_LABELS.get(recipe['meal_type'], recipe['meal_type'])} •
                {TASTE_TYPE_LABELS.get(recipe['taste_type'], recipe['taste_type'])} •
                {DIET_TYPE_LABELS.get(recipe['diet_type'], recipe['diet_type'])}
            </div>
            <div style="font-size:1rem;color:#6b7280;margin-top:10px;">
                {recipe.get('description', '')}
            </div>
            <div style="font-size:1rem;font-weight:700;color:#ea580c;margin-top:10px;">{badge}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def recommendation_card(rec, fav_ids):
    recipe = rec["recipe"]
    match_percent = rec["match_percent"]
    with st.container():
        st.markdown(
            f"""
            <div style="
                background:white;
                border-radius:22px;
                padding:20px;
                box-shadow:0 8px 18px rgba(0,0,0,0.06);
                border:1px solid rgba(0,0,0,0.06);
                margin-bottom:18px;
            ">
                <div style="font-size:1.35rem;font-weight:800;color:#111827;">{recipe['name']}</div>
                <div style="font-size:1rem;color:#6b7280;margin-top:6px;">{rec['explanation']}</div>
                <div style="font-size:1rem;font-weight:700;color:#7c3aed;margin-top:10px;">Match: {match_percent}%</div>
                <div style="margin-top:10px;color:#374151;">
                    <b>Calories:</b> {recipe['calories']} kcal &nbsp; | &nbsp;
                    <b>Protein:</b> {recipe['protein']} g &nbsp; | &nbsp;
                    <b>Carbs:</b> {recipe['carbs']} g &nbsp; | &nbsp;
                    <b>Fats:</b> {recipe['fats']} g &nbsp; | &nbsp;
                    <b>Prep:</b> {recipe['prep_time']} min
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns(2)
        with c1:
            st.write("**Ingredients you already have**")
            if rec["available_ingredients"]:
                st.write(", ".join(rec["available_ingredients"]))
            else:
                st.write("—")
        with c2:
            st.write("**Missing ingredients**")
            if rec["missing_ingredients"]:
                st.write(", ".join(rec["missing_ingredients"]))
            else:
                st.write("None")

        with st.expander("Preparation and nutrition details"):
            st.write(f"**Meal type:** {MEAL_TYPE_LABELS.get(recipe['meal_type'], recipe['meal_type'])}")
            st.write(f"**Taste:** {TASTE_TYPE_LABELS.get(recipe['taste_type'], recipe['taste_type'])}")
            st.write(f"**Diet:** {DIET_TYPE_LABELS.get(recipe['diet_type'], recipe['diet_type'])}")
            st.write(f"**Description:** {recipe['description']}")
            st.write("**Preparation:**")
            st.write(recipe["instructions"])
            st.write("**Scoring details:**")
            st.json(rec["details"])

        a, b = st.columns(2)
        with a:
            if st.button(
                "Unfavorite recipe" if recipe["id"] in fav_ids else "Favorite recipe",
                key=f'fav_{recipe["id"]}',
            ):
                toggle_favorite_recipe(st.session_state.selected_user_name, recipe["id"])
                st.rerun()
        with b:
            if st.button("Mark as prepared today", key=f'prep_{recipe["id"]}'):
                save_meal_to_history(st.session_state.selected_user_name, recipe["id"])
                st.success("Meal saved to history.")
                st.rerun()


st.markdown(
    """
    <style>
    .stApp { background: #f8fafc; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #111827 0%, #1f2937 100%); }
    [data-testid="stSidebar"] * { color: white !important; }
    [data-testid="stSidebar"] div[data-baseweb="select"] * { color: #111827 !important; }
    [data-testid="stSidebar"] input { color: #111827 !important; }
    .stButton > button, .stFormSubmitButton > button {
        width: 100% !important;
        min-height: 46px !important;
        border-radius: 14px !important;
        border: none !important;
        background: linear-gradient(90deg, #f97316, #ef4444, #8b5cf6) !important;
        color: white !important;
        font-weight: 700 !important;
    }
    .block-container { padding-top: 3rem; padding-bottom: 2rem; }
    div[role="radiogroup"] label { margin-bottom: 0.35rem !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## Smart Chef")
    st.caption("Personalized meal recommendation platform")

    users = get_all_user_names()
    if users:
        default_user_index = 0
        if st.session_state.selected_user_name in users:
            default_user_index = users.index(st.session_state.selected_user_name)
        selected_user = st.selectbox("Active user", users, index=default_user_index)
        st.session_state.selected_user_name = selected_user
    else:
        st.info("No users yet. Create one in Profile.")
        st.session_state.selected_user_name = None

    page = st.radio(
        "Navigation",
        ["Dashboard", "Profile", "Fridge", "Meal Planner", "Recommendations", "Recipes"],
    )

current_user = get_user_by_name(st.session_state.selected_user_name) if st.session_state.selected_user_name else None
current_items = get_fridge_for_user(current_user["id"]) if current_user else []
all_recipes = get_all_recipes()
favorite_recipe_ids = get_favorite_recipe_ids(st.session_state.selected_user_name) if current_user else set()

if page == "Dashboard":
    themed_header("Dashboard", "Your nutrition assistant at a glance.", "linear-gradient(135deg, #fb923c 0%, #f97316 100%)")

    available_now = recommend_meals(
        current_items,
        current_user if current_user else {},
        st.session_state.meal_filters,
        all_recipes,
        top_n=10,
    ) if current_user else []
    exact_matches = sum(1 for x in available_now if not x["missing_ingredients"])
    expiring_count = sum(1 for x in current_items if (days_until(x["expiration_date"]) is not None and days_until(x["expiration_date"]) <= 2))
    recent_history = get_recent_history_for_user(st.session_state.selected_user_name) if current_user else []

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Active user", current_user["name"] if current_user else "None", "Currently selected profile")
    with c2:
        metric_card("Fridge items", len(current_items), "Saved ingredients")
    with c3:
        metric_card("Meals available now", exact_matches, "Recipes with no missing ingredients")
    with c4:
        metric_card("Expiring soon", expiring_count, "Items that should be used first")

    if current_user:
        p1, p2 = st.columns(2)
        with p1:
            goal_text = GOAL_LABELS.get(current_user["goal"], current_user["goal"])
            metric_card("Goal", goal_text, f'Daily limit: {current_user["daily_calorie_limit"]} kcal')
            st.write("**Diet type**")
            st.info(DIET_TYPE_LABELS.get(current_user["diet_type"], current_user["diet_type"]))
            st.write("**Disliked ingredients**")
            st.write(", ".join(current_user["disliked_ingredients"]) if current_user["disliked_ingredients"] else "—")
            st.write("**Allergies**")
            st.write(", ".join(current_user["allergies"]) if current_user["allergies"] else "—")

        with p2:
            if available_now:
                best = available_now[0]
                metric_card("Recommendation of the day", best["recipe"]["name"], f'Match: {best["match_percent"]}%')
                st.write("**Why this meal?**")
                st.write(best["explanation"])
            else:
                st.info("Add a user profile and ingredients to see recommendations.")

            st.write("**Recent meal history**")
            if recent_history:
                for item in recent_history:
                    st.write(f"- {item['prepared_date']} — {item['recipe_name']}")
            else:
                st.write("No meals prepared yet.")

elif page == "Profile":
    themed_header("Profile", "Create a new user or update an existing one.", "linear-gradient(135deg, #60a5fa 0%, #2563eb 100%)")

    default = current_user or {
        "name": "",
        "age": 22,
        "gender": "female",
        "height": 170,
        "weight": 60,
        "goal": "maintenance",
        "daily_calorie_limit": 2000,
        "diet_type": "standard",
        "favorite_cuisines": [],
        "disliked_ingredients": [],
        "allergies": [],
        "meals_per_day": 3,
    }

    name = st.text_input("User name", value=default["name"])
    c1, c2, c3 = st.columns(3)
    with c1:
        age = st.number_input("Age", 10, 100, int(default["age"]))
    with c2:
        height = st.number_input("Height (cm)", 100, 230, int(default["height"]))
    with c3:
        weight = st.number_input("Weight (kg)", 30, 200, int(default["weight"]))

    gender = st.selectbox("Gender", ["female", "male"], index=0 if default["gender"] == "female" else 1)
    goal = st.selectbox("Goal", list(GOAL_LABELS.keys()), index=list(GOAL_LABELS.keys()).index(default["goal"]), format_func=lambda x: GOAL_LABELS[x])
    diet_type = st.selectbox("Diet type", ["standard", "vegetarian", "vegan", "high-protein", "light"], index=["standard", "vegetarian", "vegan", "high-protein", "light"].index(default["diet_type"]), format_func=lambda x: DIET_TYPE_LABELS[x])

    daily_calorie_limit = st.number_input("Daily calorie limit", 800, 5000, int(default["daily_calorie_limit"]))
    meals_per_day = st.slider("Meals per day", 1, 6, int(default["meals_per_day"]))

    favorite_cuisines = st.multiselect(
        "Favorite cuisines",
        ["serbian", "italian", "mediterranean", "asian", "american", "healthy"],
        default=default["favorite_cuisines"],
    )
    disliked_ingredients = st.text_input("Disliked ingredients (comma separated)", value=", ".join(default["disliked_ingredients"]))
    allergies = st.text_input("Allergies / forbidden ingredients (comma separated)", value=", ".join(default["allergies"]))

    if st.button("Save user"):
        if not name.strip():
            st.error("Enter a user name.")
        else:
            create_or_update_user({
                "name": name.strip(),
                "age": age,
                "gender": gender,
                "height": height,
                "weight": weight,
                "goal": goal,
                "daily_calorie_limit": daily_calorie_limit,
                "diet_type": diet_type,
                "favorite_cuisines": [x.strip() for x in favorite_cuisines if x.strip()],
                "disliked_ingredients": [x.strip().lower() for x in disliked_ingredients.split(",") if x.strip()],
                "allergies": [x.strip().lower() for x in allergies.split(",") if x.strip()],
                "meals_per_day": meals_per_day,
            })
            st.session_state.selected_user_name = name.strip()
            st.success("User saved.")
            st.rerun()

    if current_user and st.button("Delete selected user"):
        delete_user(current_user["id"])
        st.session_state.selected_user_name = None
        st.success("User deleted.")
        st.rerun()

elif page == "Fridge":
    themed_header("Fridge", "Add, edit and manage ingredients.", "linear-gradient(135deg, #22c55e 0%, #16a34a 100%)")

    if not current_user:
        st.warning("Create or select a user first.")
    else:
        st.subheader("Add new ingredient")
        c1, c2 = st.columns(2)
        with c1:
            preset_item = st.selectbox("Quick ingredient picker", PRESET_INGREDIENTS)
            custom_item = st.text_input("Or type your own ingredient")
            category = st.selectbox("Category", list(CATEGORY_OPTIONS.keys()), format_func=lambda x: CATEGORY_OPTIONS[x])
            quantity = st.number_input("Quantity", min_value=0.0, value=1.0, step=0.5)
            unit = st.selectbox("Unit", UNIT_OPTIONS)
        with c2:
            expiration_mode = st.checkbox("Set expiration date", value=True)
            expiration_date = st.date_input("Expiration date", value=date.today() + timedelta(days=3), disabled=not expiration_mode)
            calories = st.number_input("Calories (for entered quantity)", 0, 2000, 100)
            protein = st.number_input("Protein (g)", 0, 300, 5)
            carbs = st.number_input("Carbs (g)", 0, 300, 5)
            fats = st.number_input("Fats (g)", 0, 300, 2)
        is_favorite = st.checkbox("Frequently used ingredient")

        final_item_name = custom_item.strip() if custom_item.strip() else preset_item

        if st.button("Add ingredient"):
            if not final_item_name:
                st.error("Choose an ingredient from the list or type your own.")
            else:
                add_fridge_item(
                    current_user["id"],
                    {
                        "name": final_item_name,
                        "category": category,
                        "quantity": quantity,
                        "unit": unit,
                        "expiration_date": expiration_date.isoformat() if expiration_mode else None,
                        "calories": calories,
                        "protein": protein,
                        "carbs": carbs,
                        "fats": fats,
                        "is_favorite": is_favorite,
                    },
                )
                st.success("Ingredient added.")
                st.rerun()

        st.write("### Saved ingredients")
        if current_items:
            df = fridge_preview_dataframe(current_items)
            df.index = range(1, len(df) + 1)
            st.dataframe(df, use_container_width=True)

            item_labels = [f"{x['name']} | {x['quantity']} {x['unit']}" for x in current_items]
            selected_label = st.selectbox("Choose ingredient to edit", item_labels)
            selected_item = current_items[item_labels.index(selected_label)]

            e1, e2 = st.columns(2)
            with e1:
                edit_name = st.text_input("Edit name", value=selected_item["name"])
                edit_category = st.selectbox("Edit category", list(CATEGORY_OPTIONS.keys()), index=list(CATEGORY_OPTIONS.keys()).index(selected_item["category"]), format_func=lambda x: CATEGORY_OPTIONS[x])
                edit_quantity = st.number_input("Edit quantity", min_value=0.0, value=float(selected_item["quantity"]), step=0.5)
                edit_unit = st.selectbox("Edit unit", UNIT_OPTIONS, index=UNIT_OPTIONS.index(selected_item["unit"]))
            with e2:
                edit_expiration_mode = st.checkbox("Edit expiration date", value=selected_item["expiration_date"] is not None)
                default_exp = date.fromisoformat(selected_item["expiration_date"]) if selected_item["expiration_date"] else date.today() + timedelta(days=3)
                edit_expiration_date = st.date_input("Edit expiration date", value=default_exp, disabled=not edit_expiration_mode)
                edit_calories = st.number_input("Edit calories", 0, 2000, int(selected_item["calories"]))
                edit_protein = st.number_input("Edit protein", 0, 300, int(selected_item["protein"]))
                edit_carbs = st.number_input("Edit carbs", 0, 300, int(selected_item["carbs"]))
                edit_fats = st.number_input("Edit fats", 0, 300, int(selected_item["fats"]))
            edit_favorite = st.checkbox("Edit frequently used ingredient", value=selected_item["is_favorite"])

            a, b, c = st.columns(3)
            with a:
                if st.button("Save changes"):
                    update_fridge_item(
                        selected_item["id"],
                        {
                            "name": edit_name.strip(),
                            "category": edit_category,
                            "quantity": edit_quantity,
                            "unit": edit_unit,
                            "expiration_date": edit_expiration_date.isoformat() if edit_expiration_mode else None,
                            "calories": edit_calories,
                            "protein": edit_protein,
                            "carbs": edit_carbs,
                            "fats": edit_fats,
                            "is_favorite": edit_favorite,
                        },
                    )
                    st.success("Ingredient updated.")
                    st.rerun()
            with b:
                if st.button("Delete selected ingredient"):
                    delete_fridge_item(selected_item["id"])
                    st.success("Ingredient deleted.")
                    st.rerun()
            with c:
                if st.button("Delete all ingredients"):
                    delete_all_fridge_for_user(current_user["id"])
                    st.success("All ingredients deleted.")
                    st.rerun()
        else:
            st.info("No ingredients yet.")

elif page == "Meal Planner":
    themed_header("Meal Planner", "Choose conditions for your next meal.", "linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)")

    filters = st.session_state.meal_filters

    meal_type = st.selectbox("Meal type", list(MEAL_TYPE_LABELS.keys()), index=list(MEAL_TYPE_LABELS.keys()).index(filters["meal_type"]), format_func=lambda x: MEAL_TYPE_LABELS[x])
    taste_type = st.selectbox("Taste type", list(TASTE_TYPE_LABELS.keys()), index=list(TASTE_TYPE_LABELS.keys()).index(filters["taste_type"]), format_func=lambda x: TASTE_TYPE_LABELS[x])
    diet_type = st.selectbox("Diet filter", list(DIET_TYPE_LABELS.keys()), index=list(DIET_TYPE_LABELS.keys()).index(filters["diet_type"]), format_func=lambda x: DIET_TYPE_LABELS[x])

    c1, c2, c3 = st.columns(3)
    with c1:
        max_calories = st.number_input("Maximum calories", 100, 2000, int(filters["max_calories"]))
    with c2:
        max_prep_time = st.number_input("Maximum prep time (min)", 5, 180, int(filters["max_prep_time"]))
    with c3:
        servings = st.number_input("Servings", 1, 10, int(filters["servings"]))

    prefer_expiring = st.checkbox("Prioritize ingredients that expire soon", value=filters["prefer_expiring"])

    if st.button("Save planner settings"):
        st.session_state.meal_filters = {
            "meal_type": meal_type,
            "taste_type": taste_type,
            "diet_type": diet_type,
            "max_calories": max_calories,
            "max_prep_time": max_prep_time,
            "servings": servings,
            "prefer_expiring": prefer_expiring,
        }
        st.success("Planner settings saved.")

    st.info(
        "These filters will be used on the Recommendations page to generate top meal suggestions."
    )

elif page == "Recommendations":
    themed_header("Recommendations", "Generate personalized meal suggestions.", "linear-gradient(135deg, #f43f5e 0%, #ef4444 100%)")

    if not current_user:
        st.warning("Create or select a user first.")
    elif not current_items:
        st.warning("Add some ingredients first.")
    else:
        if st.button("Generate recommendations"):
            st.session_state["generated_recommendations"] = recommend_meals(
                current_items,
                current_user,
                st.session_state.meal_filters,
                all_recipes,
                top_n=3,
            )

        recommendations = st.session_state.get("generated_recommendations", [])
        if recommendations:
            for rec in recommendations:
                recommendation_card(rec, favorite_recipe_ids)
        else:
            st.info("Click the button above to generate recommendations.")

elif page == "Recipes":
    themed_header("Recipes", "Browse the built-in recipe library.", "linear-gradient(135deg, #14b8a6 0%, #0f766e 100%)")

    query = st.text_input("Search recipe by name")
    filtered = [r for r in all_recipes if query.lower() in r["name"].lower()] if query.strip() else all_recipes

    for recipe in filtered:
        recipe_card(recipe, recipe["id"] in favorite_recipe_ids)
        with st.expander("View recipe details"):
            details = get_recipe_details(recipe["id"])
            ingredients_text = ", ".join(
                f"{x['ingredient_name']} ({x['quantity']} {x['unit']})"
                for x in details["ingredients"]
            )
            st.write(f"**Ingredients:** {ingredients_text}")
            st.write(f"**Preparation:** {details['instructions']}")
            c1, c2 = st.columns(2)
            with c1:
                if current_user and st.button(
                    "Unfavorite recipe" if recipe["id"] in favorite_recipe_ids else "Favorite recipe",
                    key=f"recipes_page_fav_{recipe['id']}"
                ):
                    toggle_favorite_recipe(st.session_state.selected_user_name, recipe["id"])
                    st.rerun()
            with c2:
                if current_user and st.button("Mark as prepared today", key=f"recipes_page_prep_{recipe['id']}"):
                    save_meal_to_history(st.session_state.selected_user_name, recipe["id"])
                    st.success("Meal saved to history.")
                    st.rerun()
