from fastapi import APIRouter, HTTPException, status, File, UploadFile, Depends, Header, Body
from typing import List
from pathlib import Path
from datetime import datetime
import json
import uuid

from backend.models.recipe import Recipe, RecipeCreate, RecipeUpdate, RecipeDatabase, Country
from backend.config import settings
from backend.routes.auth import verify_token
from PIL import Image
import io

router = APIRouter(prefix="/api/recipes", tags=["recipes"])

COUNTRY_CODES = [
    ("Ukraine", "UA"), ("Russia", "RU"), ("USA", "US"), ("Italy", "IT"),
    ("France", "FR"), ("Japan", "JP"), ("China", "CN"), ("Mexico", "MX"),
    ("India", "IN"), ("Thailand", "TH"), ("Germany", "DE"), ("Spain", "ES"),
    ("Greece", "GR"), ("Poland", "PL"), ("Hungary", "HU"), ("Czechia", "CZ"),
    ("South Korea", "KR"), ("North Korea", "KP"), ("Vietnam", "VN"),
    ("Turkey", "TR"), ("Georgia", "GE"), ("Armenia", "AM"), ("Azerbaijan", "AZ"),
    ("Uzbekistan", "UZ"), ("Kazakhstan", "KZ"), ("Israel", "IL"),
    ("Morocco", "MA"), ("Egypt", "EG"), ("Brazil", "BR"), ("Argentina", "AR"),
    ("Peru", "PE"), ("Canada", "CA"), ("United Kingdom", "GB"),
    ("Ireland", "IE"), ("Sweden", "SE"), ("Norway", "NO"), ("Denmark", "DK"),
    ("Netherlands", "NL"), ("Belgium", "BE"), ("Switzerland", "CH"),
    ("Austria", "AT"), ("Romania", "RO"), ("Bulgaria", "BG"), ("Serbia", "RS"),
    ("Croatia", "HR"), ("Australia", "AU"), ("New Zealand", "NZ"),
]

def flag_from_country_code(code: str) -> str:
    """Convert ISO 3166-1 alpha-2 country code to emoji flag."""
    if not code or len(code) != 2:
        return "🌍"
    return "".join(chr(127397 + ord(char)) for char in code.upper())

COUNTRIES = [
    Country(name=name, code=code, flag=flag_from_country_code(code))
    for name, code in COUNTRY_CODES
]

def load_recipes() -> RecipeDatabase:
    """Load recipes from JSON file"""
    if settings.recipes_file.exists():
        with open(settings.recipes_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return RecipeDatabase(**data)
    return RecipeDatabase()

def save_recipes(db: RecipeDatabase):
    """Save recipes to JSON file"""
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    with open(settings.recipes_file, 'w', encoding='utf-8') as f:
        json.dump(db.model_dump(), f, ensure_ascii=False, indent=2)

def optimize_image(file: UploadFile, max_width: int = 800, max_height: int = 500) -> bytes:
    """Optimize uploaded image"""
    img = Image.open(file.file)

    # Resize if needed
    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

    # Save as JPEG
    img_byte_arr = io.BytesIO()
    img.convert('RGB').save(img_byte_arr, format='JPEG', quality=85)
    img_byte_arr.seek(0)
    return img_byte_arr.getvalue()

@router.get("/")
async def get_recipes(category: str = None, country: str = None):
    """Get all recipes with optional filters"""
    db = load_recipes()

    recipes = db.recipes

    # Filter by category
    if category:
        recipes = [r for r in recipes if r.category.lower() == category.lower()]

    # Filter by country
    if country:
        recipes = [r for r in recipes if country.lower() in r.country_origin.lower()]

    return {
        "recipes": recipes,
        "total": len(recipes)
    }

@router.post("/ai/polish", response_model=RecipeCreate)
async def polish_recipe(
    recipe: RecipeCreate,
    username: str = Depends(verify_token)
):
    """Proofread recipe text with OpenAI before saving it"""
    try:
        from backend.agents.recipe_agent import recipe_agent

        polished = recipe_agent.polish_recipe(recipe.model_dump())
        return RecipeCreate(**polished)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI processing failed: {str(e)}")

@router.get("/{recipe_id}")
async def get_recipe(recipe_id: str):
    """Get a single recipe"""
    db = load_recipes()

    recipe = next((r for r in db.recipes if r.id == recipe_id), None)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    return recipe

@router.post("/", response_model=Recipe)
async def create_recipe(
    recipe: RecipeCreate,
    username: str = Depends(verify_token)
):
    """Create a new recipe"""
    db = load_recipes()

    # Generate unique ID
    recipe_id = f"recipe_{uuid.uuid4().hex[:8]}"

    new_recipe = Recipe(
        id=recipe_id,
        **recipe.model_dump(),
        image=f"images/{recipe_id}.jpg",
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )

    db.recipes.append(new_recipe)
    save_recipes(db)

    return new_recipe

@router.put("/{recipe_id}", response_model=Recipe)
async def update_recipe(
    recipe_id: str,
    recipe: RecipeUpdate,
    username: str = Depends(verify_token)
):
    """Update an existing recipe"""
    db = load_recipes()

    recipe_index = next((i for i, r in enumerate(db.recipes) if r.id == recipe_id), None)
    if recipe_index is None:
        raise HTTPException(status_code=404, detail="Recipe not found")

    existing_recipe = db.recipes[recipe_index]

    # Update only provided fields
    update_data = recipe.model_dump(exclude_unset=True)
    updated_recipe = existing_recipe.model_copy(update={
        **update_data,
        "updated_at": datetime.now().isoformat()
    })

    db.recipes[recipe_index] = updated_recipe
    save_recipes(db)

    return updated_recipe

@router.delete("/{recipe_id}")
async def delete_recipe(
    recipe_id: str,
    username: str = Depends(verify_token)
):
    """Delete a recipe"""
    db = load_recipes()

    recipe_index = next((i for i, r in enumerate(db.recipes) if r.id == recipe_id), None)
    if recipe_index is None:
        raise HTTPException(status_code=404, detail="Recipe not found")

    deleted = db.recipes.pop(recipe_index)
    save_recipes(db)

    return {"message": "Recipe deleted", "recipe_id": recipe_id}

@router.post("/{recipe_id}/image")
async def upload_recipe_image(
    recipe_id: str,
    file: UploadFile = File(...),
    username: str = Depends(verify_token)
):
    """Upload or replace recipe image"""
    db = load_recipes()

    recipe = next((r for r in db.recipes if r.id == recipe_id), None)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Optimize image
    try:
        image_data = optimize_image(file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")

    # Save image
    settings.images_dir.mkdir(parents=True, exist_ok=True)
    image_path = settings.images_dir / f"{recipe_id}.jpg"

    with open(image_path, 'wb') as f:
        f.write(image_data)

    return {
        "message": "Image uploaded successfully",
        "recipe_id": recipe_id,
        "image_path": f"images/{recipe_id}.jpg"
    }

@router.get("/categories/list")
async def get_categories():
    """Get all available categories"""
    db = load_recipes()
    return {
        "categories": db.categories
    }

@router.get("/countries/list")
async def get_countries():
    """Get all available countries"""
    return {
        "countries": COUNTRIES
    }

@router.post("/categories/")
async def add_category(
    category: str = Body(..., embed=True),
    username: str = Depends(verify_token)
):
    """Add a new category"""
    db = load_recipes()

    if category in db.categories:
        raise HTTPException(status_code=400, detail="Category already exists")

    db.categories.append(category)
    save_recipes(db)

    return {"message": "Category added", "category": category}
