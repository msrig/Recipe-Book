from fastapi import APIRouter, HTTPException, status, File, UploadFile, Depends, Header, Body
from typing import List, Optional
from pathlib import Path
from datetime import datetime
import json
import uuid
import base64
import urllib.parse
import urllib.request

from backend.models.recipe import Recipe, RecipeCreate, RecipeUpdate, RecipeDatabase, Country
from backend.config import settings
from backend.routes.auth import UserRecord, ensure_admin_user, find_user_by_username, load_users, verify_token
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
            db = RecipeDatabase(**data)
            migrate_recipe_owners(db)
            return db
    return RecipeDatabase()

def save_recipes(db: RecipeDatabase):
    """Save recipes to JSON file"""
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    with open(settings.recipes_file, 'w', encoding='utf-8') as f:
        json.dump(db.model_dump(), f, ensure_ascii=False, indent=2)

def migrate_recipe_owners(db: RecipeDatabase):
    """Attach legacy recipes to the default admin account."""
    admin_user = ensure_admin_user()
    changed = False
    for recipe in db.recipes:
        if not recipe.owner_id:
            recipe.owner_id = admin_user.id
            recipe.owner_username = admin_user.username
            changed = True
        elif not recipe.owner_username:
            recipe.owner_username = admin_user.username
            changed = True

    if changed:
        save_recipes(db)

def require_recipe_owner(recipe: Recipe, user: UserRecord):
    if recipe.owner_id != user.id:
        raise HTTPException(status_code=403, detail="You can only change your own recipes")

def optimize_image(file: UploadFile, max_width: int = 800, max_height: int = 500) -> bytes:
    """Optimize uploaded image"""
    img = Image.open(file.file)
    return optimize_pil_image(img, max_width=max_width, max_height=max_height)

def optimize_image_bytes(raw_image: bytes, max_width: int = 800, max_height: int = 500) -> bytes:
    """Optimize raw image bytes."""
    img = Image.open(io.BytesIO(raw_image))
    return optimize_pil_image(img, max_width=max_width, max_height=max_height)

def optimize_pil_image(img: Image.Image, max_width: int = 800, max_height: int = 500) -> bytes:
    """Resize and compress PIL image to JPEG."""
    # Resize if needed
    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

    # Save as JPEG
    img_byte_arr = io.BytesIO()
    img.convert('RGB').save(img_byte_arr, format='JPEG', quality=85)
    img_byte_arr.seek(0)
    return img_byte_arr.getvalue()

def find_country_by_code(code: str) -> Optional[Country]:
    upper = (code or "").upper()
    return next((country for country in COUNTRIES if country.code == upper), None)

def unsplash_source_url(query: str, width: int = 1000, height: int = 700) -> str:
    safe_query = urllib.parse.quote_plus(query.strip())
    return f"https://source.unsplash.com/{width}x{height}/?{safe_query}"

def ai_preview_url(preview_filename: str) -> str:
    return f"/images/ai-previews/{preview_filename}"

def generate_ai_preview_image(query: str) -> Optional[dict]:
    """Generate a preview food image and save it under /images."""
    image_bytes = try_generate_image_with_openai(query)
    if image_bytes is None:
        return None

    image_data = optimize_image_bytes(image_bytes, max_width=1000, max_height=700)
    preview_dir = settings.images_dir / "ai-previews"
    preview_dir.mkdir(parents=True, exist_ok=True)

    preview_filename = f"{uuid.uuid4().hex}.jpg"
    preview_path = preview_dir / preview_filename
    with open(preview_path, "wb") as f:
        f.write(image_data)

    return {
        "preview_path": f"images/ai-previews/{preview_filename}",
        "preview_url": ai_preview_url(preview_filename),
    }

def try_generate_image_with_openai(query: str) -> Optional[bytes]:
    """Generate a food image with OpenAI; return raw bytes on success."""
    if not settings.openai_api_key:
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        response = client.images.generate(
            model="gpt-image-1",
            prompt=(
                "High-quality realistic food photography, plated dish, natural lighting, "
                f"editorial cooking magazine style. Dish: {query}"
            ),
            size="1024x1024",
        )

        b64 = response.data[0].b64_json if response.data else None
        if not b64:
            return None
        return base64.b64decode(b64)
    except Exception:
        return None

@router.get("/")
async def get_recipes(
    category: str = None,
    country: str = None,
    username: str = None,
    mine: bool = False,
):
    """Get all recipes with optional filters"""
    db = load_recipes()

    recipes = db.recipes

    if mine:
        raise HTTPException(status_code=401, detail="Use /api/recipes/mine/list for your recipes")

    if username:
        owner = find_user_by_username(load_users(), username)
        if not owner:
            raise HTTPException(status_code=404, detail="User not found")
        recipes = [r for r in recipes if r.owner_id == owner.id]

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

@router.get("/mine/list")
async def get_my_recipes(
    category: str = None,
    country: str = None,
    username: UserRecord = Depends(verify_token),
):
    """Get recipes owned by the logged-in user."""
    db = load_recipes()
    recipes = [r for r in db.recipes if r.owner_id == username.id]

    if category:
        recipes = [r for r in recipes if r.category.lower() == category.lower()]

    if country:
        recipes = [r for r in recipes if country.lower() in r.country_origin.lower()]

    return {"recipes": recipes, "total": len(recipes)}

@router.get("/users/{username}")
async def get_user_recipes(username: str):
    """Get public recipes for a user profile page."""
    owner = find_user_by_username(load_users(), username)
    if not owner:
        raise HTTPException(status_code=404, detail="User not found")

    db = load_recipes()
    recipes = [r for r in db.recipes if r.owner_id == owner.id]
    return {"user": {"username": owner.username, "display_name": owner.display_name}, "recipes": recipes, "total": len(recipes)}

@router.post("/ai/polish", response_model=RecipeCreate)
async def polish_recipe(
    recipe: RecipeCreate,
    username: UserRecord = Depends(verify_token)
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

@router.post("/ai/extract-from-photo")
async def extract_recipe_from_photo(
    file: UploadFile = File(...),
    username: UserRecord = Depends(verify_token)
):
    """Extract recipe draft fields from a handwritten photo."""
    try:
        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        mime_type = file.content_type or "image/jpeg"
        if not mime_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image files are supported")

        from backend.agents.recipe_agent import recipe_agent

        extracted = recipe_agent.extract_recipe_from_photo(
            image_bytes=image_bytes,
            mime_type=mime_type,
            categories=load_recipes().categories,
            countries=[{"name": c.name, "code": c.code} for c in COUNTRIES],
        )

        country = find_country_by_code(extracted.get("country_code", ""))
        if country and not extracted.get("country_origin"):
            extracted["country_origin"] = country.name
        elif country:
            extracted["country_origin"] = country.name
            extracted["country_code"] = country.code

        image_query = extracted.get("image_query", "").strip()
        if not image_query:
            image_query = f"{extracted.get('titleEn', '').strip()} plated food".strip()

        preview = generate_ai_preview_image(image_query)

        return {
            "recipe": {
                "title": extracted.get("title", ""),
                "titleEn": extracted.get("titleEn", ""),
                "category": extracted.get("category", ""),
                "country_origin": extracted.get("country_origin", ""),
                "country_code": extracted.get("country_code", ""),
                "description": extracted.get("description", ""),
                "ingredients": extracted.get("ingredients", []),
                "preparation": extracted.get("preparation", ""),
            },
            "image_query": image_query,
            "image_preview_url": preview["preview_url"] if preview else "",
            "image_preview_path": preview["preview_path"] if preview else "",
        }
    except HTTPException:
        raise
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
    username: UserRecord = Depends(verify_token)
):
    """Create a new recipe"""
    db = load_recipes()

    # Generate unique ID
    recipe_id = f"recipe_{uuid.uuid4().hex[:8]}"

    new_recipe = Recipe(
        id=recipe_id,
        owner_id=username.id,
        owner_username=username.username,
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
    username: UserRecord = Depends(verify_token)
):
    """Update an existing recipe"""
    db = load_recipes()

    recipe_index = next((i for i, r in enumerate(db.recipes) if r.id == recipe_id), None)
    if recipe_index is None:
        raise HTTPException(status_code=404, detail="Recipe not found")

    existing_recipe = db.recipes[recipe_index]
    require_recipe_owner(existing_recipe, username)

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
    username: UserRecord = Depends(verify_token)
):
    """Delete a recipe"""
    db = load_recipes()

    recipe_index = next((i for i, r in enumerate(db.recipes) if r.id == recipe_id), None)
    if recipe_index is None:
        raise HTTPException(status_code=404, detail="Recipe not found")

    require_recipe_owner(db.recipes[recipe_index], username)
    deleted = db.recipes.pop(recipe_index)
    save_recipes(db)

    return {"message": "Recipe deleted", "recipe_id": recipe_id}

@router.post("/{recipe_id}/image")
async def upload_recipe_image(
    recipe_id: str,
    file: UploadFile = File(...),
    username: UserRecord = Depends(verify_token)
):
    """Upload or replace recipe image"""
    db = load_recipes()

    recipe = next((r for r in db.recipes if r.id == recipe_id), None)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    require_recipe_owner(recipe, username)

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

    # Update recipe image path to the newly uploaded file.
    recipe.image = f"images/{recipe_id}.jpg"

    # Touch recipe timestamp to bust client image cache via updated_at.
    recipe.updated_at = datetime.now().isoformat()
    save_recipes(db)

    return {
        "message": "Image uploaded successfully",
        "recipe_id": recipe_id,
        "image_path": recipe.image,
        "updated_at": recipe.updated_at,
    }

@router.post("/{recipe_id}/image/from-query")
async def upload_recipe_image_from_query(
    recipe_id: str,
    query: str = Body(..., embed=True),
    username: UserRecord = Depends(verify_token)
):
    """Download a suggested food photo and assign it to recipe."""
    db = load_recipes()
    recipe = next((r for r in db.recipes if r.id == recipe_id), None)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    require_recipe_owner(recipe, username)

    normalized_query = (query or "").strip()
    if not normalized_query:
        raise HTTPException(status_code=400, detail="Image query is required")

    image_url = unsplash_source_url(normalized_query)

    downloaded = try_generate_image_with_openai(normalized_query)
    source_kind = "openai"

    if downloaded is None:
        source_kind = "unsplash"
        req = urllib.request.Request(
            image_url,
            headers={"User-Agent": "RecipeBookAdmin/1.0"},
        )

        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                downloaded = response.read()
        except Exception as e:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to fetch image from OpenAI and Unsplash: {str(e)}"
            )

    try:
        image_data = optimize_image_bytes(downloaded)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid downloaded image: {str(e)}")

    settings.images_dir.mkdir(parents=True, exist_ok=True)
    image_path = settings.images_dir / f"{recipe_id}.jpg"
    with open(image_path, "wb") as f:
        f.write(image_data)

    recipe.image = f"images/{recipe_id}.jpg"
    recipe.updated_at = datetime.now().isoformat()
    save_recipes(db)

    return {
        "message": "Suggested image uploaded successfully",
        "recipe_id": recipe_id,
        "image_path": recipe.image,
        "updated_at": recipe.updated_at,
        "source_url": image_url if source_kind == "unsplash" else None,
        "source_kind": source_kind,
    }

@router.post("/{recipe_id}/image/from-preview")
async def upload_recipe_image_from_preview(
    recipe_id: str,
    preview_path: str = Body(..., embed=True),
    username: UserRecord = Depends(verify_token)
):
    """Assign a previously generated AI preview image to recipe."""
    db = load_recipes()
    recipe = next((r for r in db.recipes if r.id == recipe_id), None)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    require_recipe_owner(recipe, username)

    normalized_preview_path = (preview_path or "").strip().replace("\\", "/")
    expected_prefix = "images/ai-previews/"
    if not normalized_preview_path.startswith(expected_prefix):
        raise HTTPException(status_code=400, detail="Invalid preview image path")

    preview_filename = Path(normalized_preview_path).name
    source_path = settings.images_dir / "ai-previews" / preview_filename
    if not source_path.exists() or not source_path.is_file():
        raise HTTPException(status_code=404, detail="Preview image not found")

    try:
        with open(source_path, "rb") as f:
            image_data = optimize_image_bytes(f.read())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid preview image: {str(e)}")

    settings.images_dir.mkdir(parents=True, exist_ok=True)
    image_path = settings.images_dir / f"{recipe_id}.jpg"
    with open(image_path, "wb") as f:
        f.write(image_data)

    recipe.image = f"images/{recipe_id}.jpg"
    recipe.updated_at = datetime.now().isoformat()
    save_recipes(db)

    return {
        "message": "Preview image uploaded successfully",
        "recipe_id": recipe_id,
        "image_path": recipe.image,
        "updated_at": recipe.updated_at,
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
    username: UserRecord = Depends(verify_token)
):
    """Add a new category"""
    db = load_recipes()

    if category in db.categories:
        raise HTTPException(status_code=400, detail="Category already exists")

    db.categories.append(category)
    save_recipes(db)

    return {"message": "Category added", "category": category}

@router.delete("/categories/{category}")
async def delete_category(
    category: str,
    username: UserRecord = Depends(verify_token)
):
    """Delete an unused category"""
    db = load_recipes()

    existing_category = next((cat for cat in db.categories if cat.lower() == category.lower()), None)
    if not existing_category:
        raise HTTPException(status_code=404, detail="Category not found")

    used_by = [recipe.title for recipe in db.recipes if recipe.category.lower() == existing_category.lower()]
    if used_by:
        raise HTTPException(
            status_code=400,
            detail=f"Category is used by {len(used_by)} recipe(s): {', '.join(used_by[:3])}"
        )

    db.categories = [cat for cat in db.categories if cat.lower() != existing_category.lower()]
    save_recipes(db)

    return {"message": "Category deleted", "category": existing_category}
