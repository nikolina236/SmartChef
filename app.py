from datetime import date
from urllib.parse import quote_plus

import pandas as pd
import streamlit as st

from database import (
    add_fridge_item,
    create_or_update_user,
    delete_all_fridge_for_user,
    delete_fridge_item,
    delete_user,
    get_all_user_names,
    get_catalog_display_names,
    get_fridge_for_user,
    get_user_by_name,
    init_db,
    update_fridge_item,
)
from recommender import recommend_meals

st.set_page_config(page_title="Smart Chef", page_icon="🍳", layout="wide")
init_db()

if "selected_user_name" not in st.session_state:
    st.session_state.selected_user_name = None
if "fridge_form_version" not in st.session_state:
    st.session_state.fridge_form_version = 0

GOAL_LABELS = {
    "maintenance": "Maintenance",
    "weight-loss": "Weight loss",
    "weight-gain": "Weight gain",
    "muscle-gain": "Muscle gain",
}

DIET_TYPE_LABELS = {
    "standard": "Standard",
    "vegetarian": "Vegetarian",
    "high-protein": "High protein",
    "light": "Light",
    "any": "Any",
}

MEAL_TYPE_LABELS = {
    "breakfast": "Breakfast",
    "lunch": "Lunch",
    "dinner": "Dinner",
    "snack": "Snack",
    "any": "Any",
}

TASTE_TYPE_LABELS = {
    "savory": "Savory",
    "sweet": "Sweet",
    "any": "Any",
}

UNIT_OPTIONS = ["g", "kg", "ml", "dl", "l", "piece", "cup", "tbsp", "tsp"]
INGREDIENT_OPTIONS = get_catalog_display_names()
INGREDIENT_SELECT_OPTIONS = ["Custom ingredient"] + INGREDIENT_OPTIONS


def themed_header(title: str, subtitle: str, gradient: str):
    st.markdown(
        f"""
        <div style="background:{gradient};color:white;border-radius:24px;padding:32px 28px 24px 28px;margin-bottom:22px;box-shadow:0 10px 24px rgba(0,0,0,0.10);">
            <div style="font-size:2.25rem;font-weight:800;line-height:1.15;">{title}</div>
            <div style="margin-top:10px;font-size:1.02rem;opacity:0.95;">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(title, value, subtitle=""):
    st.markdown(
        f"""
        <div style="background:white;border-radius:18px;padding:18px;box-shadow:0 8px 18px rgba(0,0,0,0.06);border:1px solid rgba(0,0,0,0.06);margin-bottom:16px;min-height:120px;">
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
    try:
        return (date.fromisoformat(expiration_date) - date.today()).days
    except Exception:
        return None


def fridge_preview_dataframe(items):
    rows = []
    for item in items:
        due = days_until(item.get("expiration_date"))
        exp_text = "Not set" if due is None else ("Expired" if due < 0 else f"{due} day(s)")
        rows.append(
            {
                "Ingredient": item["name"],
                "Category": item.get("category", "Other"),
                "Quantity": f"{item['quantity']} {item['unit']}",
                "Expires in": exp_text,
                "Calories": "—" if not item.get("nutrition_known") else item.get("calories", 0),
                "Protein": "—" if not item.get("nutrition_known") else item.get("protein", 0),
            }
        )
    return pd.DataFrame(rows)


def _show_recipe_image(recipe):
    image_url = recipe.get("image_url")
    if image_url:
        try:
            st.image(image_url, width=220)
            return
        except Exception:
            pass
    st.markdown(
        """
        <div style="width:220px;height:180px;border-radius:20px;background:linear-gradient(135deg,#f97316,#8b5cf6);display:flex;flex-direction:column;align-items:center;justify-content:center;color:white;box-shadow:0 8px 18px rgba(0,0,0,0.08);">
            <div style="font-size:3rem;line-height:1;">🍽️</div>
            <div style="margin-top:12px;font-size:1rem;font-weight:800;text-align:center;padding:0 12px;">Smart Chef</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def recipe_card(recipe):
    source_badge = "Smart idea" if recipe.get("source") == "smart" else "Online recipe"
    cal_text = "—" if recipe.get("calories") is None else f"{recipe['calories']} kcal"
    protein_text = "—" if recipe.get("protein") is None else f"{recipe['protein']} g protein"
    prep_text = "—" if recipe.get("prep_time") is None else f"{recipe['prep_time']} min"

    st.markdown(
        f"""
        <div style="background:white;border-radius:22px;padding:20px;box-shadow:0 8px 18px rgba(0,0,0,0.06);border:1px solid rgba(0,0,0,0.06);margin-bottom:14px;">
            <div style="display:flex;justify-content:space-between;gap:16px;align-items:flex-start;">
                <div style="font-size:1.28rem;font-weight:800;color:#111827;">{recipe['name']}</div>
                <div style="font-size:0.9rem;font-weight:700;color:#7c3aed;">{source_badge}</div>
            </div>
            <div style="font-size:1rem;color:#6b7280;margin-top:8px;">{recipe['explanation']}</div>
            <div style="margin-top:10px;color:#374151;"><b>Match:</b> {recipe.get('match_percent', 0)}% &nbsp; | &nbsp; <b>Calories:</b> {cal_text} &nbsp; | &nbsp; <b>Protein:</b> {protein_text} &nbsp; | &nbsp; <b>Prep:</b> {prep_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1, 2])
    with left:
        _show_recipe_image(recipe)
    with right:
        st.write("**Ingredients**")
        ingredient_lines = recipe.get("ingredient_lines") or recipe.get("available_ingredients") or []
        if ingredient_lines:
            for line in ingredient_lines:
                st.write(f"• {line}")
        else:
            st.write("—")

        if recipe.get("missing_ingredients"):
            st.write("**Need to buy**")
            st.write(", ".join(recipe.get("missing_ingredients", [])))

        st.write("**How to prepare**")
        instructions = recipe.get("instructions", [])
        if isinstance(instructions, str):
            st.write(instructions)
        else:
            for i, step in enumerate(instructions, start=1):
                st.write(f"{i}. {step}")

        available = recipe.get("available_ingredients") or []
        if available:
            st.caption("You already have: " + ", ".join(available))

        if recipe.get("source_url"):
            st.markdown(f"[Open recipe source]({recipe['source_url']})")
    st.markdown("---")


st.markdown(
    """
    <style>
    .stApp { background: #f8fafc; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #0f172a 0%, #111827 100%); }
    [data-testid="stSidebar"] * { color: white !important; }
    [data-testid="stSidebar"] div[data-baseweb="select"] * { color: #111827 !important; }
    [data-testid="stSidebar"] input { color: #111827 !important; }
    .stButton > button, .stFormSubmitButton > button {
        width: 100% !important;
        min-height: 44px !important;
        border-radius: 14px !important;
        border: none !important;
        background: linear-gradient(90deg, #f97316, #ec4899, #8b5cf6) !important;
        color: white !important;
        font-weight: 700 !important;
    }
    .block-container { padding-top: 2.6rem; padding-bottom: 2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## Smart Chef")
    st.caption("Simple, fast and personalized meal assistant")
    users = get_all_user_names()
    if users:
        default_idx = 0
        if st.session_state.selected_user_name in users:
            default_idx = users.index(st.session_state.selected_user_name)
        selected_user = st.selectbox("Active user", users, index=default_idx)
        st.session_state.selected_user_name = selected_user
    else:
        st.info("No users yet. Create one in Profile.")
        st.session_state.selected_user_name = None
    page = st.radio("Navigation", ["Dashboard", "Profile", "Fridge", "Recommendations"])

current_user = get_user_by_name(st.session_state.selected_user_name) if st.session_state.selected_user_name else None
current_items = get_fridge_for_user(current_user["id"]) if current_user else []

if page == "Dashboard":
    themed_header("Dashboard", "Your meal planning overview.", "linear-gradient(135deg, #fb7185 0%, #f59e0b 100%)")
    expiring = sum(1 for x in current_items if (days_until(x.get("expiration_date")) is not None and 0 <= days_until(x.get("expiration_date")) <= 3))
    total_protein = round(sum(float(x.get("protein") or 0) for x in current_items), 1)
    total_calories = round(sum(float(x.get("calories") or 0) for x in current_items), 1)

    a, b, c, d = st.columns(4)
    with a:
        metric_card("Active user", current_user["name"] if current_user else "None", "Currently selected profile")
    with b:
        metric_card("Saved ingredients", len(current_items), "Items in fridge / pantry")
    with c:
        metric_card("Expiring soon", expiring, "Within the next 3 days")
    with d:
        metric_card("Protein available", f"{total_protein} g", f"Approx. {total_calories} kcal total")

    if current_user:
        st.info(
            f"Goal: {GOAL_LABELS.get(current_user['goal'], current_user['goal'])} | "
            f"Diet: {DIET_TYPE_LABELS.get(current_user['diet_type'], current_user['diet_type'])} | "
            f"Daily calorie limit: {current_user['daily_calorie_limit']} kcal | Meals per day: {current_user['meals_per_day']}"
        )
        if current_items:
            st.write("### Saved ingredients")
            df = fridge_preview_dataframe(current_items)
            df.index = range(1, len(df) + 1)
            st.dataframe(df, use_container_width=True)

elif page == "Profile":
    themed_header("Profile", "Set user goal, diet and preferences.", "linear-gradient(135deg, #60a5fa 0%, #2563eb 100%)")

    default_name = current_user["name"] if current_user else ""
    default_goal = current_user["goal"] if current_user else "maintenance"
    default_limit = current_user["daily_calorie_limit"] if current_user else 2000
    default_meals = current_user["meals_per_day"] if current_user else 3
    default_diet = current_user["diet_type"] if current_user else "standard"
    default_allergies = ", ".join(current_user["allergies"]) if current_user else ""
    default_disliked = ", ".join(current_user["disliked_ingredients"]) if current_user else ""

    name = st.text_input("User name", value=default_name)
    goal_options = ["maintenance", "weight-loss", "weight-gain", "muscle-gain"]
    goal = st.selectbox(
        "Goal",
        goal_options,
        index=goal_options.index(default_goal) if default_goal in goal_options else 0,
        format_func=lambda x: GOAL_LABELS[x],
    )
    daily_limit = st.number_input("Daily calorie limit", min_value=1000, max_value=5000, value=int(default_limit), step=100)
    meals_per_day = st.number_input("Meals per day", min_value=1, max_value=8, value=int(default_meals), step=1)
    diet_type = st.selectbox(
        "Diet type",
        ["standard", "vegetarian", "high-protein", "light"],
        index=["standard", "vegetarian", "high-protein", "light"].index(default_diet) if default_diet in ["standard", "vegetarian", "high-protein", "light"] else 0,
        format_func=lambda x: DIET_TYPE_LABELS[x],
    )
    allergies = st.text_input("Allergies (comma separated)", value=default_allergies)
    disliked = st.text_input("Ingredients you dislike (comma separated)", value=default_disliked)

    if st.button("Save user"):
        if not name.strip():
            st.error("Enter a user name.")
        else:
            create_or_update_user(
                {
                    "name": name.strip(),
                    "goal": goal,
                    "daily_calorie_limit": int(daily_limit),
                    "meals_per_day": int(meals_per_day),
                    "diet_type": diet_type,
                    "allergies": [x.strip() for x in allergies.split(",") if x.strip()],
                    "disliked_ingredients": [x.strip() for x in disliked.split(",") if x.strip()],
                }
            )
            st.session_state.selected_user_name = name.strip()
            st.success("User saved.")
            st.rerun()

    if current_user and st.button("Delete selected user"):
        delete_user(current_user["id"])
        st.session_state.selected_user_name = None
        st.success("User deleted.")
        st.rerun()

elif page == "Fridge":
    themed_header("Fridge", "Add ingredients quickly. The app calculates category and nutrition automatically.", "linear-gradient(135deg, #a78bfa 0%, #7c3aed 100%)")
    if not current_user:
        st.warning("Create or select a user first.")
    else:
        st.subheader("Add ingredient")
        fv = st.session_state.fridge_form_version

        c1, c2 = st.columns(2)
        with c1:
            selected = st.selectbox("Choose ingredient", INGREDIENT_SELECT_OPTIONS, key=f"fridge_selected_{fv}")
            custom_enabled = selected == "Custom ingredient"
            custom_name = st.text_input(
                "Or type your own ingredient",
                key=f"custom_ingredient_{fv}",
                placeholder="Type here only if you chose Custom ingredient",
                disabled=not custom_enabled,
            )
        with c2:
            quantity = st.number_input("Quantity", min_value=0.1, max_value=10000.0, value=250.0, step=10.0, key=f"fridge_qty_{fv}")
            unit = st.selectbox("Unit", UNIT_OPTIONS, index=0, key=f"fridge_unit_{fv}")

        add_exp = st.checkbox("Add expiration date", key=f"fridge_add_exp_{fv}")
        exp_value = None
        if add_exp:
            exp_value = st.date_input("Expiration date", value=date.today(), key=f"fridge_exp_date_{fv}")

        is_custom = selected == "Custom ingredient"
        custom_search_query = quote_plus((custom_name or "ingredient") + " calories protein")
        st.markdown(f"[Open calorie and protein search](https://www.google.com/search?q={custom_search_query})")

        manual_mode = False
        manual_calories = None
        manual_protein = None
        if is_custom:
            st.caption("Use manual nutrition only if the ingredient is very specific and the app cannot estimate it well.")
            manual_mode = st.checkbox("Manually enter calories and protein for this ingredient", key=f"fridge_manual_mode_{fv}")
            if manual_mode:
                m1, m2 = st.columns(2)
                with m1:
                    manual_calories = st.number_input("Calories", min_value=0.0, max_value=5000.0, value=0.0, step=1.0, key=f"fridge_manual_cal_{fv}")
                with m2:
                    manual_protein = st.number_input("Protein (g)", min_value=0.0, max_value=500.0, value=0.0, step=0.1, key=f"fridge_manual_pro_{fv}")

        if st.button("Add ingredient", key=f"add_ingredient_btn_{fv}"):
            final_name = custom_name.strip() if is_custom else selected
            if not final_name or final_name == "Custom ingredient":
                st.error("Choose an ingredient or type your own.")
            else:
                manual_nutrition = None
                if manual_mode:
                    manual_nutrition = {
                        "calories": manual_calories or 0,
                        "protein": manual_protein or 0,
                        "carbs": 0,
                        "fats": 0,
                    }

                add_fridge_item(
                    current_user["id"],
                    final_name,
                    quantity,
                    unit,
                    expiration_date=exp_value.isoformat() if add_exp and exp_value else None,
                    manual_nutrition=manual_nutrition,
                )
                st.success("Ingredient added.")
                st.session_state.fridge_form_version += 1
                st.rerun()

        if current_items:
            st.write("### Saved ingredients")
            df = fridge_preview_dataframe(current_items)
            df.index = range(1, len(df) + 1)
            st.dataframe(df, use_container_width=True)

            st.write("### Edit ingredient")
            labels = [f"{x['name']} | {x['quantity']} {x['unit']}" for x in current_items]
            selected_label = st.selectbox("Choose ingredient to edit", labels)
            idx = labels.index(selected_label)
            item = current_items[idx]

            e1, e2 = st.columns(2)
            with e1:
                edit_name = st.text_input("Ingredient name", value=item["name"])
                edit_quantity = st.number_input("Edit quantity", min_value=0.1, max_value=10000.0, value=float(item["quantity"]), step=10.0)
            with e2:
                unit_index = UNIT_OPTIONS.index(item["unit"]) if item["unit"] in UNIT_OPTIONS else 0
                edit_unit = st.selectbox("Edit unit", UNIT_OPTIONS, index=unit_index)
                edit_add_exp = st.checkbox("Edit expiration date", value=bool(item.get("expiration_date")))
            edit_exp_date = None
            if edit_add_exp:
                default_date = date.fromisoformat(item["expiration_date"]) if item.get("expiration_date") else date.today()
                edit_exp_date = st.date_input("New expiration date", value=default_date)

            x, y, z = st.columns(3)
            with x:
                if st.button("Save changes"):
                    update_fridge_item(item["id"], edit_name, edit_quantity, edit_unit, edit_exp_date.isoformat() if edit_add_exp and edit_exp_date else None)
                    st.success("Ingredient updated.")
                    st.rerun()
            with y:
                if st.button("Delete selected ingredient"):
                    delete_fridge_item(item["id"])
                    st.success("Ingredient deleted.")
                    st.rerun()
            with z:
                if st.button("Delete all ingredients"):
                    delete_all_fridge_for_user(current_user["id"])
                    st.success("All ingredients deleted.")
                    st.rerun()

elif page == "Recommendations":
    themed_header("Recommendations", "Choose your meal settings and get useful ideas or simple online recipe links.", "linear-gradient(135deg, #fb923c 0%, #ea580c 100%)")
    if not current_user:
        st.warning("Create or select a user first.")
    else:
        filters = {}
        f1, f2 = st.columns(2)
        with f1:
            filters["meal_type"] = st.selectbox("Meal type", ["any", "breakfast", "lunch", "dinner", "snack"], format_func=lambda x: MEAL_TYPE_LABELS[x])
            filters["taste_type"] = st.selectbox("Taste", ["any", "savory", "sweet"], format_func=lambda x: TASTE_TYPE_LABELS[x])
            filters["diet_type"] = st.selectbox("Diet preference", ["any", "standard", "vegetarian", "high-protein", "light"], format_func=lambda x: DIET_TYPE_LABELS[x])
        with f2:
            filters["max_calories"] = st.number_input("Maximum calories per meal", min_value=100, max_value=2500, value=600, step=50)
            filters["max_prep_time"] = st.number_input("Maximum prep time (minutes)", min_value=5, max_value=180, value=20, step=5)
            filters["prefer_expiring"] = st.checkbox("Prioritize ingredients that expire soon", value=True)

        mode_label = st.selectbox("Recommendation mode", ["Only my ingredients", "I can go shopping"])
        mode = "only" if mode_label == "Only my ingredients" else "shopping"

        if st.button("Generate recommendations"):
            recommendations = recommend_meals(current_items, current_user, filters, mode=mode, top_n=8)
            if not recommendations:
                if mode == "only":
                    st.warning("No recipe ideas match these filters. Try relaxing filters or adding more ingredients.")
                else:
                    st.warning("No matching recommendations found. Try relaxing your filters.")
            else:
                if mode == "shopping":
                    missing_all = []
                    for rec in recommendations:
                        missing_all.extend(rec.get("missing_ingredients", []))
                    if missing_all:
                        shopping_list = sorted(set(missing_all))
                        st.info("Shopping list: " + ", ".join(shopping_list))
                for rec in recommendations:
                    recipe_card(rec)
