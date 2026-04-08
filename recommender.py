
from datetime import date


def normalize_text(value):
    if value is None:
        return ""
    return str(value).strip().lower()


def unit_to_base(quantity, unit):
    quantity = float(quantity)
    unit = normalize_text(unit)

    if unit == "kg":
        return quantity * 1000, "g"
    if unit == "g":
        return quantity, "g"
    if unit == "l":
        return quantity * 1000, "ml"
    if unit == "ml":
        return quantity, "ml"
    if unit == "cup":
        return quantity * 240, "ml"
    if unit == "tbsp":
        return quantity * 15, "ml"
    if unit == "tsp":
        return quantity * 5, "ml"
    if unit == "piece":
        return quantity, "piece"

    return quantity, unit


def compatible_units(unit_a, unit_b):
    ua = unit_to_base(1, unit_a)[1]
    ub = unit_to_base(1, unit_b)[1]
    return ua == ub


def has_enough_amount(fridge_item, recipe_ingredient):
    fi_qty, fi_unit = unit_to_base(fridge_item["quantity"], fridge_item["unit"])
    ri_qty, ri_unit = unit_to_base(recipe_ingredient["quantity"], recipe_ingredient["unit"])

    if fi_unit != ri_unit:
        return False
    return fi_qty >= ri_qty


def days_until(expiration_date):
    if not expiration_date:
        return None
    return (date.fromisoformat(expiration_date) - date.today()).days


def recipe_matches_diet(recipe_diet, target_diet):
    recipe_diet = normalize_text(recipe_diet)
    target_diet = normalize_text(target_diet)

    if target_diet in ["", "any"]:
        return True
    if target_diet == "standard":
        return True
    if target_diet == "light":
        return recipe_diet in ["light", "vegetarian", "vegan", "standard"]
    if target_diet == "high-protein":
        return recipe_diet in ["high-protein", "standard"]
    return recipe_diet == target_diet


def score_recipe(recipe, recipe_details, fridge_items, user_profile, planner_input):
    total = 0
    details = {}

    meal_type = normalize_text(planner_input.get("meal_type", ""))
    taste_type = normalize_text(planner_input.get("taste_type", ""))
    target_diet = normalize_text(planner_input.get("diet_type", ""))
    max_calories = int(planner_input.get("max_calories", 9999))
    max_prep_time = int(planner_input.get("max_prep_time", 999))
    prefer_expiring = bool(planner_input.get("prefer_expiring", True))

    disliked = {normalize_text(x) for x in user_profile.get("disliked_ingredients", [])}
    allergies = {normalize_text(x) for x in user_profile.get("allergies", [])}
    user_diet = normalize_text(user_profile.get("diet_type", "standard"))
    favorite_ids = set()

    ingredients = recipe_details["ingredients"]
    available = []
    missing = []
    expiring_used = []

    fridge_lookup = {}
    for item in fridge_items:
        name = normalize_text(item["name"])
        fridge_lookup.setdefault(name, []).append(item)
        if item.get("is_favorite"):
            favorite_ids.add(name)

    for ing in ingredients:
        ing_name = normalize_text(ing["ingredient_name"])
        candidates = fridge_lookup.get(ing_name, [])

        found = None
        for candidate in candidates:
            if compatible_units(candidate["unit"], ing["unit"]) and has_enough_amount(candidate, ing):
                found = candidate
                break

        if found:
            available.append(ing["ingredient_name"])
            due = days_until(found["expiration_date"])
            if due is not None and due <= 2:
                expiring_used.append(ing["ingredient_name"])
        else:
            missing.append(ing["ingredient_name"])

    # hard blocks
    blocked_ingredients = [x["ingredient_name"] for x in ingredients if normalize_text(x["ingredient_name"]) in allergies]
    if blocked_ingredients:
        details["allergy_block"] = -100
        return -100, details, available, missing, expiring_used, blocked_ingredients

    # ingredient coverage
    if len(missing) == 0:
        coverage_score = 40
    elif len(missing) <= 2:
        coverage_score = 22
    else:
        coverage_score = max(-10, 18 - len(missing) * 8)

    # planner alignment
    meal_type_score = 20 if normalize_text(recipe["meal_type"]) == meal_type else -8
    if taste_type == "any":
        taste_score = 8
    else:
        taste_score = 12 if normalize_text(recipe["taste_type"]) == taste_type else -6

    # diet alignment
    diet_score = 16 if recipe_matches_diet(recipe["diet_type"], target_diet) and recipe_matches_diet(recipe["diet_type"], user_diet) else -18

    # calories and time
    if recipe["calories"] <= max_calories:
        calorie_score = 18
    elif recipe["calories"] <= max_calories + 100:
        calorie_score = 6
    else:
        calorie_score = -18

    if recipe["prep_time"] <= max_prep_time:
        time_score = 12
    elif recipe["prep_time"] <= max_prep_time + 10:
        time_score = 3
    else:
        time_score = -10

    # dislikes penalty
    disliked_used = [x["ingredient_name"] for x in ingredients if normalize_text(x["ingredient_name"]) in disliked]
    dislike_penalty = -15 * len(disliked_used)

    # expiring bonus
    expiring_score = 5 * len(expiring_used) if prefer_expiring else 0

    # favorite fridge ingredients bonus
    favorite_score = 3 * sum(1 for x in available if normalize_text(x) in favorite_ids)

    # meal goal bias
    goal = normalize_text(user_profile.get("goal", "maintenance"))
    if goal == "weight-loss":
        goal_score = 8 if recipe["calories"] <= max_calories and recipe["protein"] >= 15 else 0
    elif goal == "muscle-gain":
        goal_score = 8 if recipe["protein"] >= 25 else 0
    else:
        goal_score = 4

    details["coverage"] = coverage_score
    details["meal_type"] = meal_type_score
    details["taste_type"] = taste_score
    details["diet"] = diet_score
    details["calories"] = calorie_score
    details["prep_time"] = time_score
    details["dislikes"] = dislike_penalty
    details["expiring_bonus"] = expiring_score
    details["favorite_ingredients"] = favorite_score
    details["goal_bonus"] = goal_score

    total = (
        coverage_score + meal_type_score + taste_score + diet_score +
        calorie_score + time_score + dislike_penalty + expiring_score +
        favorite_score + goal_score
    )
    return total, details, available, missing, expiring_used, []


def build_explanation(recipe, available, missing, expiring_used):
    parts = []

    if not missing:
        parts.append("You already have all required ingredients.")
    elif len(missing) <= 2:
        parts.append("You are missing only a small number of ingredients.")
    else:
        parts.append("This recipe partially matches your current fridge.")

    parts.append(f"It fits the {recipe['meal_type']} category and takes about {recipe['prep_time']} minutes.")

    if expiring_used:
        parts.append("It also helps you use ingredients that expire soon.")

    return " ".join(parts)


def recommend_meals(fridge_items, user_profile, planner_input, recipes, top_n=3):
    if not fridge_items or not recipes:
        return []

    from database import get_recipe_details  # local import to avoid circular import

    scored = []
    for recipe in recipes:
        details = get_recipe_details(recipe["id"])
        score, breakdown, available, missing, expiring_used, blocked = score_recipe(
            recipe,
            details,
            fridge_items,
            user_profile,
            planner_input,
        )

        if blocked:
            continue

        explanation = build_explanation(recipe, available, missing, expiring_used)

        scored.append({
            "score": score,
            "recipe": recipe,
            "details": breakdown,
            "available_ingredients": available,
            "missing_ingredients": missing,
            "expiring_used": expiring_used,
            "explanation": explanation,
        })

    if not scored:
        return []

    scored.sort(key=lambda x: x["score"], reverse=True)
    best_score = scored[0]["score"] if scored else 1
    best_score = best_score if best_score > 0 else 1

    final = []
    for item in scored[:top_n]:
        match_percent = max(1, min(100, round((max(item["score"], 0) / best_score) * 100)))
        item["match_percent"] = match_percent
        final.append(item)

    return final
