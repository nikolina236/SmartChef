from __future__ import annotations

from datetime import date
from typing import Any
from urllib.parse import quote_plus

from database import canonicalize_ingredient_name, display_name_for, normalize_text

# Curated, simple, practical recipes with real food photos.
TEMPLATES = [
    {
        "name": "Cheese Omelette",
        "meal_type": "breakfast",
        "taste_type": "savory",
        "diet_type": "high-protein",
        "required": ["eggs"],
        "optional": ["cheese", "onion", "bell pepper", "tomato", "butter"],
        "ingredient_lines": ["3 eggs", "40 g cheese", "1 tbsp butter", "pinch of salt"],
        "prep_time": 10,
        "calories": 360,
        "protein": 24,
        "instructions": "Beat the eggs. Melt butter in a pan, add any chopped onion or pepper if you have it, then pour in the eggs. Add cheese, fold the omelette and cook for 1–2 more minutes.",
        "image": "https://images.unsplash.com/photo-1510693206972-df098062cb71?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Eggs on Toast",
        "meal_type": "breakfast",
        "taste_type": "savory",
        "diet_type": "standard",
        "required": ["eggs", "bread"],
        "optional": ["butter", "avocado", "cheese", "tomato"],
        "ingredient_lines": ["2 eggs", "2 slices bread", "1 tsp butter"],
        "prep_time": 8,
        "calories": 320,
        "protein": 16,
        "instructions": "Toast the bread. Fry or scramble the eggs the way you like. Put the eggs on warm toast and add avocado, cheese or tomato if available.",
        "image": "https://images.unsplash.com/photo-1525351484163-7529414344d8?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Protein Yogurt Bowl",
        "meal_type": "breakfast",
        "taste_type": "sweet",
        "diet_type": "high-protein",
        "required": ["greek yogurt"],
        "optional": ["banana", "apple", "blueberries", "strawberries", "protein powder", "honey", "oats"],
        "ingredient_lines": ["200 g Greek yogurt", "1 banana", "20 g oats", "1 tsp honey"],
        "prep_time": 5,
        "calories": 350,
        "protein": 24,
        "instructions": "Put Greek yogurt in a bowl. Add sliced fruit, oats and a little honey. If you have protein powder, mix a small scoop into the yogurt first.",
        "image": "https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Chicken Rice Bowl",
        "meal_type": "lunch",
        "taste_type": "savory",
        "diet_type": "high-protein",
        "required": ["chicken breast", "rice"],
        "optional": ["bell pepper", "onion", "olive oil", "carrot", "broccoli"],
        "ingredient_lines": ["150 g chicken breast", "80 g rice", "1 tsp olive oil", "mixed vegetables"],
        "prep_time": 25,
        "calories": 560,
        "protein": 42,
        "instructions": "Cook the rice. Cut chicken into small pieces and season lightly. Sauté chicken in a pan with a little oil, add chopped vegetables if you have them, then serve over rice.",
        "image": "https://images.unsplash.com/photo-1512058564366-18510be2db19?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Tuna Pasta",
        "meal_type": "lunch",
        "taste_type": "savory",
        "diet_type": "high-protein",
        "required": ["tuna", "pasta"],
        "optional": ["onion", "tomato", "olive oil", "cheese"],
        "ingredient_lines": ["80 g pasta", "1 can tuna", "1 small tomato", "1 tsp olive oil"],
        "prep_time": 18,
        "calories": 520,
        "protein": 32,
        "instructions": "Boil the pasta. In a pan, warm tuna with a little oil and chopped tomato or onion if you have them. Mix with pasta and top with a little cheese.",
        "image": "https://images.unsplash.com/photo-1621996346565-e3dbc646d9a9?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Chicken Sandwich",
        "meal_type": "lunch",
        "taste_type": "savory",
        "diet_type": "standard",
        "required": ["bread"],
        "optional": ["chicken breast", "cheese", "lettuce", "tomato", "mayonnaise", "ketchup"],
        "ingredient_lines": ["2 slices bread", "100 g cooked chicken", "1 slice cheese", "lettuce and tomato"],
        "prep_time": 10,
        "calories": 430,
        "protein": 28,
        "instructions": "Toast the bread if you like. Layer the chicken, cheese, lettuce and tomato. Add a little mayo or ketchup and close the sandwich.",
        "image": "https://images.unsplash.com/photo-1553909489-cd47e0907980?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Loaded Baked Potato",
        "meal_type": "dinner",
        "taste_type": "savory",
        "diet_type": "standard",
        "required": ["potato"],
        "optional": ["cheese", "yogurt", "tuna", "butter", "onion"],
        "ingredient_lines": ["1 large potato", "30 g cheese", "1 tbsp yogurt or butter"],
        "prep_time": 30,
        "calories": 410,
        "protein": 14,
        "instructions": "Bake or boil the potato until soft. Cut it open and fill it with cheese, yogurt or tuna if you have it. Finish with chopped onion.",
        "image": "https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Tuna Salad",
        "meal_type": "dinner",
        "taste_type": "savory",
        "diet_type": "light",
        "required": ["tuna"],
        "optional": ["lettuce", "cucumber", "tomato", "olive oil", "onion"],
        "ingredient_lines": ["1 can tuna", "lettuce", "1 tomato", "1/2 cucumber", "1 tsp olive oil"],
        "prep_time": 10,
        "calories": 280,
        "protein": 27,
        "instructions": "Chop the vegetables. Drain the tuna and mix everything together. Add a little olive oil and salt if desired.",
        "image": "https://images.unsplash.com/photo-1546793665-c74683f339c1?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Chicken and Cheese Quick Plate",
        "meal_type": "dinner",
        "taste_type": "savory",
        "diet_type": "high-protein",
        "required": ["chicken"],
        "optional": ["cheese", "bread", "tomato", "cucumber"],
        "ingredient_lines": ["150 g chicken", "30 g cheese", "2 slices bread"],
        "prep_time": 12,
        "calories": 470,
        "protein": 38,
        "instructions": "Warm the chicken in a pan. Serve with sliced cheese and bread, plus any fresh vegetables you have. It is a fast high-protein plate.",
        "image": "https://images.unsplash.com/photo-1600891964092-4316c288032e?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Avocado Egg Bowl",
        "meal_type": "breakfast",
        "taste_type": "savory",
        "diet_type": "light",
        "required": ["avocado", "eggs"],
        "optional": ["bread", "tomato", "cheese"],
        "ingredient_lines": ["2 eggs", "1/2 avocado", "1 tomato"],
        "prep_time": 10,
        "calories": 340,
        "protein": 16,
        "instructions": "Boil or fry the eggs. Mash or slice the avocado, add chopped tomato, and serve everything together as a bowl or on toast.",
        "image": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Protein Shake",
        "meal_type": "snack",
        "taste_type": "sweet",
        "diet_type": "high-protein",
        "required": ["protein powder"],
        "optional": ["milk", "banana", "greek yogurt"],
        "ingredient_lines": ["1 scoop protein powder", "250 ml milk", "1 banana"],
        "prep_time": 3,
        "calories": 300,
        "protein": 30,
        "instructions": "Blend the protein powder with milk. Add banana and yogurt if you have them for a thicker shake.",
        "image": "https://images.unsplash.com/photo-1579722821273-0f6c2f11b2b4?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Butter Toast with Eggs",
        "meal_type": "breakfast",
        "taste_type": "savory",
        "diet_type": "standard",
        "required": ["bread", "butter"],
        "optional": ["eggs", "cheese"],
        "ingredient_lines": ["2 slices bread", "1 tsp butter", "2 eggs"],
        "prep_time": 8,
        "calories": 360,
        "protein": 14,
        "instructions": "Toast the bread and spread butter on it. Add fried or scrambled eggs and cheese if you want a richer breakfast.",
        "image": "https://upload.wikimedia.org/wikipedia/commons/7/70/Breakfast_in_Australia%3B_bacon_and_fried_eggs_on_toast.jpg",
    },
    {
        "name": "Rice and Egg Bowl",
        "meal_type": "lunch",
        "taste_type": "savory",
        "diet_type": "standard",
        "required": ["rice", "eggs"],
        "optional": ["butter", "onion", "bell pepper"],
        "ingredient_lines": ["80 g rice", "2 eggs", "1 tsp butter"],
        "prep_time": 15,
        "calories": 430,
        "protein": 18,
        "instructions": "Cook the rice. Scramble or fry the eggs, then serve them over warm rice. Add onion or pepper if you have them.",
        "image": "https://images.unsplash.com/photo-1515003197210-e0cd71810b5f?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Apple Oat Bowl",
        "meal_type": "breakfast",
        "taste_type": "sweet",
        "diet_type": "light",
        "required": ["oats"],
        "optional": ["apple", "honey", "milk", "yogurt"],
        "ingredient_lines": ["50 g oats", "1 apple", "1 tsp honey", "200 ml milk"],
        "prep_time": 8,
        "calories": 320,
        "protein": 10,
        "instructions": "Cook oats with milk or water. Add chopped apple and a little honey. Top with yogurt if you have it.",
        "image": "https://images.unsplash.com/photo-1517673400267-0251440c45dc?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Banana Honey Toast",
        "meal_type": "snack",
        "taste_type": "sweet",
        "diet_type": "standard",
        "required": ["bread", "banana"],
        "optional": ["honey", "peanut butter"],
        "ingredient_lines": ["2 slices bread", "1 banana", "1 tsp honey"],
        "prep_time": 6,
        "calories": 290,
        "protein": 7,
        "instructions": "Toast the bread. Add sliced banana on top and finish with a little honey or peanut butter.",
        "image": "https://images.unsplash.com/photo-1484723091739-30a097e8f929?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Fruit Yogurt Cup",
        "meal_type": "snack",
        "taste_type": "sweet",
        "diet_type": "light",
        "required": ["yogurt"],
        "optional": ["banana", "apple", "strawberries", "blueberries", "honey"],
        "ingredient_lines": ["200 ml yogurt", "1 fruit of choice", "1 tsp honey"],
        "prep_time": 4,
        "calories": 220,
        "protein": 8,
        "instructions": "Pour yogurt into a bowl or glass. Add chopped fruit and finish with a little honey if you want it sweeter.",
        "image": "https://images.unsplash.com/photo-1505252585461-04db1eb84625?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Tomato Cheese Toast",
        "meal_type": "breakfast",
        "taste_type": "savory",
        "diet_type": "standard",
        "required": ["bread", "tomato"],
        "optional": ["cheese", "butter"],
        "ingredient_lines": ["2 slices bread", "1 tomato", "30 g cheese"],
        "prep_time": 7,
        "calories": 300,
        "protein": 12,
        "instructions": "Toast the bread. Add tomato slices and cheese on top. Warm briefly so the cheese softens.",
        "image": "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Greek Style Salad",
        "meal_type": "dinner",
        "taste_type": "savory",
        "diet_type": "light",
        "required": ["tomato", "cucumber"],
        "optional": ["feta cheese", "olive oil", "onion", "lettuce"],
        "ingredient_lines": ["1 tomato", "1/2 cucumber", "40 g feta cheese", "1 tsp olive oil"],
        "prep_time": 8,
        "calories": 240,
        "protein": 9,
        "instructions": "Chop the vegetables, add feta cheese, drizzle with olive oil and mix gently.",
        "image": "https://images.unsplash.com/photo-1490645935967-10de6ba17061?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Cheesy Pasta",
        "meal_type": "lunch",
        "taste_type": "savory",
        "diet_type": "standard",
        "required": ["pasta"],
        "optional": ["cheese", "butter", "tomato"],
        "ingredient_lines": ["80 g pasta", "40 g cheese", "1 tsp butter"],
        "prep_time": 15,
        "calories": 480,
        "protein": 18,
        "instructions": "Boil pasta. Drain it, then mix with cheese and butter while hot. Add chopped tomato if you want freshness.",
        "image": "https://images.unsplash.com/photo-1563379091339-03246963d29d?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Banana Pancakes",
        "meal_type": "breakfast",
        "taste_type": "sweet",
        "diet_type": "standard",
        "required": ["banana", "eggs"],
        "optional": ["oats", "milk", "honey"],
        "ingredient_lines": ["1 banana", "2 eggs", "30 g oats"],
        "prep_time": 12,
        "calories": 340,
        "protein": 14,
        "instructions": "Mash the banana, mix it with eggs and oats, then cook small pancakes in a non-stick pan for 2–3 minutes per side.",
        "image": "https://images.unsplash.com/photo-1528207776546-365bb710ee93?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "French Toast",
        "meal_type": "breakfast",
        "taste_type": "sweet",
        "diet_type": "standard",
        "required": ["bread", "eggs"],
        "optional": ["milk", "banana", "honey", "apple"],
        "ingredient_lines": ["2 slices bread", "2 eggs", "50 ml milk", "1 tsp honey"],
        "prep_time": 10,
        "calories": 360,
        "protein": 15,
        "instructions": "Whisk the eggs with milk, dip the bread slices, then cook them in a pan until golden. Serve with fruit or honey.",
        "image": "https://images.unsplash.com/photo-1484723091739-30a097e8f929?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Overnight Oats",
        "meal_type": "breakfast",
        "taste_type": "sweet",
        "diet_type": "light",
        "required": ["oats"],
        "optional": ["milk", "yogurt", "banana", "apple", "honey"],
        "ingredient_lines": ["50 g oats", "150 ml milk", "2 tbsp yogurt", "fruit"],
        "prep_time": 5,
        "calories": 300,
        "protein": 11,
        "instructions": "Mix oats with milk and yogurt, leave them in the fridge, then top with fruit and honey before eating.",
        "image": "https://images.unsplash.com/photo-1517673400267-0251440c45dc?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Protein Oat Bowl",
        "meal_type": "breakfast",
        "taste_type": "sweet",
        "diet_type": "high-protein",
        "required": ["oats"],
        "optional": ["protein powder", "milk", "banana", "honey", "greek yogurt"],
        "ingredient_lines": ["50 g oats", "1 scoop protein powder", "200 ml milk"],
        "prep_time": 8,
        "calories": 380,
        "protein": 28,
        "instructions": "Cook the oats, stir in protein powder after cooking, then top with banana, yogurt or honey.",
        "image": "https://images.unsplash.com/photo-1517673400267-0251440c45dc?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Fruit Parfait",
        "meal_type": "snack",
        "taste_type": "sweet",
        "diet_type": "light",
        "required": ["yogurt"],
        "optional": ["banana", "apple", "strawberries", "blueberries", "oats", "honey"],
        "ingredient_lines": ["200 ml yogurt", "fruit", "20 g oats", "1 tsp honey"],
        "prep_time": 5,
        "calories": 240,
        "protein": 9,
        "instructions": "Layer yogurt, fruit and oats in a glass or bowl, then finish with a little honey.",
        "image": "https://images.unsplash.com/photo-1505252585461-04db1eb84625?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Chocolate Banana Protein Shake",
        "meal_type": "snack",
        "taste_type": "sweet",
        "diet_type": "high-protein",
        "required": ["protein powder"],
        "optional": ["milk", "banana", "greek yogurt"],
        "ingredient_lines": ["1 scoop protein powder", "250 ml milk", "1 banana"],
        "prep_time": 3,
        "calories": 320,
        "protein": 30,
        "instructions": "Blend protein powder with milk and banana. Add Greek yogurt if you want a creamier shake.",
        "image": "https://images.unsplash.com/photo-1579722821273-0f6c2f11b2b4?auto=format&fit=crop&w=900&q=80",
    },

]

MEAL_SEARCH_URLS = {
    "breakfast": "https://www.bbcgoodfood.com/search?q=easy+breakfast",
    "lunch": "https://www.bbcgoodfood.com/search?q=easy+lunch",
    "dinner": "https://www.bbcgoodfood.com/search?q=easy+dinner",
    "snack": "https://www.bbcgoodfood.com/search?q=easy+snack",
    "any": "https://www.bbcgoodfood.com/search?q=easy+recipe",
}


def days_until(expiration_date: str | None):
    if not expiration_date:
        return None
    try:
        return (date.fromisoformat(expiration_date) - date.today()).days
    except Exception:
        return None


def active_items(fridge_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [x for x in fridge_items if days_until(x.get("expiration_date")) is None or days_until(x.get("expiration_date")) >= 0]


def fridge_name_set(fridge_items: list[dict[str, Any]]) -> set[str]:
    names = set()
    for item in active_items(fridge_items):
        canonical = item.get("canonical_name") or canonicalize_ingredient_name(item.get("name", ""))
        if canonical:
            names.add(canonical)
    return names


def _diet_ok(recipe_diet: str, wanted: str) -> bool:
    recipe_diet = normalize_text(recipe_diet)
    wanted = normalize_text(wanted)
    if wanted in {"", "any", "standard"}:
        return True
    if wanted == "high-protein":
        return recipe_diet in {"high-protein", "standard"}
    if wanted == "vegetarian":
        return recipe_diet in {"vegetarian", "light"}
    if wanted == "light":
        return recipe_diet in {"light", "vegetarian", "standard"}
    return recipe_diet == wanted


def _strict_filter_ok(template: dict[str, Any], filters: dict[str, Any], profile: dict[str, Any]) -> bool:
    wanted_meal = normalize_text(filters.get("meal_type", "any"))
    wanted_taste = normalize_text(filters.get("taste_type", "any"))
    wanted_diet = normalize_text(filters.get("diet_type", "any"))
    profile_diet = normalize_text(profile.get("diet_type", "standard"))

    if wanted_meal not in {"", "any"} and normalize_text(template.get("meal_type")) != wanted_meal:
        return False
    if wanted_taste not in {"", "any"} and normalize_text(template.get("taste_type")) != wanted_taste:
        return False

    diet_target = wanted_diet if wanted_diet not in {"", "any"} else profile_diet
    if not _diet_ok(template.get("diet_type", "standard"), diet_target):
        return False

    max_cal = filters.get("max_calories")
    if max_cal and template.get("calories") and template["calories"] > max_cal:
        return False
    max_prep = filters.get("max_prep_time")
    if max_prep and template.get("prep_time") and template["prep_time"] > max_prep:
        return False
    return True


def _soft_penalties(template: dict[str, Any], filters: dict[str, Any], profile: dict[str, Any]) -> int:
    penalty = 0
    wanted_meal = normalize_text(filters.get("meal_type", "any"))
    wanted_taste = normalize_text(filters.get("taste_type", "any"))
    wanted_diet = normalize_text(filters.get("diet_type", "any"))
    profile_diet = normalize_text(profile.get("diet_type", "standard"))

    if wanted_meal not in {"", "any"} and normalize_text(template.get("meal_type")) != wanted_meal:
        penalty += 8
    if wanted_taste not in {"", "any"} and normalize_text(template.get("taste_type")) != wanted_taste:
        penalty += 20
    diet_target = wanted_diet if wanted_diet not in {"", "any"} else profile_diet
    if not _diet_ok(template.get("diet_type", "standard"), diet_target):
        penalty += 10

    max_cal = filters.get("max_calories")
    if max_cal and template.get("calories"):
        over = template["calories"] - max_cal
        if over > 0:
            penalty += min(20, int(over / 40))
    max_prep = filters.get("max_prep_time")
    if max_prep and template.get("prep_time"):
        over = template["prep_time"] - max_prep
        if over > 0:
            penalty += min(12, int(over / 5))
    return penalty


def _template_result(template: dict[str, Any], fridge_set: set[str], filters: dict[str, Any], profile: dict[str, Any], fridge_items: list[dict[str, Any]]):
    required = template.get("required", [])
    optional = template.get("optional", [])
    missing = [display_name_for(x) for x in required if x not in fridge_set]
    available = [display_name_for(x) for x in required if x in fridge_set]
    optional_available = [display_name_for(x) for x in optional if x in fridge_set]
    available_all = available + optional_available

    if not available_all and missing:
        return None

    score = len(available) * 35 + len(optional_available) * 10 - len(missing) * 14
    score -= _soft_penalties(template, filters, profile)

    used_expiring = []
    if filters.get("prefer_expiring"):
        expiring = set()
        for item in fridge_items:
            due = days_until(item.get("expiration_date"))
            if due is not None and 0 <= due <= 3:
                expiring.add(item.get("canonical_name") or canonicalize_ingredient_name(item.get("name", "")))
        used_expiring = [display_name_for(x) for x in required + optional if x in expiring and x in fridge_set]
        score += len(used_expiring) * 6

    explanation_parts = []
    if missing:
        explanation_parts.append(f"You already have {len(available_all)} useful ingredient(s) for this recipe.")
        explanation_parts.append(f"Missing: {', '.join(missing)}.")
    else:
        explanation_parts.append("You can make this from your current ingredients.")
    if used_expiring:
        explanation_parts.append("It also helps use ingredients that expire soon.")

    return {
        "name": template["name"],
        "meal_type": template["meal_type"],
        "taste_type": template["taste_type"],
        "diet_type": template["diet_type"],
        "prep_time": template["prep_time"],
        "calories": template["calories"],
        "protein": template["protein"],
        "image_url": template.get("image"),
        "ingredient_lines": template.get("ingredient_lines", []),
        "instructions": template.get("instructions"),
        "available_ingredients": available_all,
        "missing_ingredients": missing,
        "explanation": " ".join(explanation_parts),
        "match_percent": max(35, min(100, 65 + len(available) * 10 + len(optional_available) * 4 - len(missing) * 8 - _soft_penalties(template, filters, profile))),
        "source": "smart",
        "source_url": None,
        "shopping_required": bool(missing),
        "score": score,
    }


def _simple_search_result(fridge_set: set[str], filters: dict[str, Any]) -> dict[str, Any]:
    names = [display_name_for(x) for x in list(fridge_set)[:8]]
    meal_type = normalize_text(filters.get("meal_type", "any"))
    taste_type = normalize_text(filters.get("taste_type", "any"))

    base = MEAL_SEARCH_URLS.get(meal_type, MEAL_SEARCH_URLS["any"])
    taste_prefix = ""
    if taste_type == "sweet":
        taste_prefix = "sweet+"
    elif taste_type == "savory":
        taste_prefix = "savory+"

    query = "+".join([quote_plus(n) for n in names[:4]])
    search_url = f"{base}&q={taste_prefix}{query}" if "?" in base else f"{base}?q={taste_prefix}{query}"

    return {
        "name": "More easy recipe ideas",
        "meal_type": meal_type or "any",
        "taste_type": taste_type or "any",
        "diet_type": normalize_text(filters.get("diet_type", "any")),
        "prep_time": None,
        "calories": None,
        "protein": None,
        "image_url": "https://images.unsplash.com/photo-1490645935967-10de6ba17061?auto=format&fit=crop&w=900&q=80",
        "ingredient_lines": names,
        "instructions": "Open the recipe source link for extra ideas. If you choose shopping mode, first buy the missing basics shown in the Smart Chef suggestions above, then use this link for more inspiration.",
        "available_ingredients": names,
        "missing_ingredients": [],
        "explanation": "Extra online ideas based on what you already have.",
        "match_percent": 60,
        "source": "online",
        "source_url": search_url,
        "shopping_required": False,
        "score": 10,
    }


def recommend_meals(fridge_items: list[dict[str, Any]], profile: dict[str, Any], filters: dict[str, Any], mode: str = "only", top_n: int = 8):
    usable = active_items(fridge_items)
    fridge_set = fridge_name_set(usable)
    if not fridge_set:
        return []

    results = []
    for template in TEMPLATES:
        if not _strict_filter_ok(template, filters, profile):
            continue
        result = _template_result(template, fridge_set, filters, profile, usable)
        if not result:
            continue
        if mode == "only" and result["missing_ingredients"]:
            continue
        results.append(result)

    if not results:
        relaxed_filters = dict(filters)
        relaxed_filters["meal_type"] = "any"
        relaxed_filters["max_calories"] = None
        relaxed_filters["max_prep_time"] = None
        for template in TEMPLATES:
            if not _strict_filter_ok(template, relaxed_filters, profile):
                continue
            result = _template_result(template, fridge_set, relaxed_filters, profile, usable)
            if not result:
                continue
            if mode == "only" and result["missing_ingredients"]:
                continue
            results.append(result)

    if not results and mode == "only":
        names = [display_name_for(x) for x in list(fridge_set)[:6]]
        taste = normalize_text(filters.get("taste_type", "any"))
        if taste == "sweet":
            fallback_name = "Quick sweet bowl"
            fallback_text = "Make a simple sweet bowl or toast from the ingredients you already have. Start with yogurt, oats, fruit or honey if available."
        else:
            fallback_name = "Quick savory plate"
            fallback_text = "Make a simple savory plate, toast, bowl or salad from the ingredients you already have. Start with a protein ingredient, then add bread, rice, pasta or vegetables."
        results.append({
            "name": fallback_name,
            "meal_type": normalize_text(filters.get("meal_type", "any")),
            "taste_type": taste or "any",
            "diet_type": normalize_text(filters.get("diet_type", "any")),
            "prep_time": 10,
            "calories": None,
            "protein": None,
            "image_url": "https://images.unsplash.com/photo-1490645935967-10de6ba17061?auto=format&fit=crop&w=900&q=80",
            "ingredient_lines": names,
            "instructions": fallback_text,
            "available_ingredients": names,
            "missing_ingredients": [],
            "explanation": "A simple fallback idea made from your current ingredients.",
            "match_percent": 55,
            "source": "smart",
            "source_url": None,
            "shopping_required": False,
            "score": 1,
        })

    results.sort(key=lambda x: (x.get("shopping_required", False), -(x.get("score") or 0), -(x.get("match_percent") or 0)))

    deduped = []
    seen = set()
    for item in results:
        key = normalize_text(item["name"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
        if len(deduped) >= max(3, top_n - 1):
            break

    deduped.append(_simple_search_result(fridge_set, filters))
    return deduped[:top_n]
