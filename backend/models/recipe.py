from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Recipe(BaseModel):
    id: Optional[str] = None
    title: str
    titleEn: str
    category: str
    country_origin: str
    country_code: str
    description: str
    ingredients: List[str]
    preparation: str
    image: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "recipe_001",
                "title": "Борщ",
                "titleEn": "Borscht",
                "category": "Soup",
                "country_origin": "Ukraine",
                "country_code": "UA",
                "description": "Traditional Ukrainian soup",
                "ingredients": ["Beef", "Beets", "Cabbage"],
                "preparation": "1. Cook beef...",
                "image": "images/recipe_001.jpg",
                "created_at": "2026-04-17T12:00:00Z",
                "updated_at": "2026-04-17T12:00:00Z"
            }
        }

class RecipeCreate(BaseModel):
    title: str
    titleEn: str
    category: str
    country_origin: str
    country_code: str
    description: str
    ingredients: List[str]
    preparation: str

class RecipeUpdate(BaseModel):
    title: Optional[str] = None
    titleEn: Optional[str] = None
    category: Optional[str] = None
    country_origin: Optional[str] = None
    country_code: Optional[str] = None
    description: Optional[str] = None
    ingredients: Optional[List[str]] = None
    preparation: Optional[str] = None

class Country(BaseModel):
    name: str
    code: str
    flag: str

class RecipeDatabase(BaseModel):
    recipes: List[Recipe] = []
    categories: List[str] = [
        "Soup",
        "Salad",
        "Main Course",
        "Side Dish",
        "Appetizer",
        "Dessert",
        "Breakfast",
        "Beverage"
    ]
    countries: List[Country] = []
