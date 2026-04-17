"""
Claude AI Agent for recipe formatting and enhancement
"""

from anthropic import Anthropic
from backend.config import settings
from typing import Dict, Any

class RecipeAgent:
    def __init__(self):
        self.client = Anthropic(api_key=settings.claude_api_key)
        self.model = "claude-3-5-sonnet-20241022"

    def format_recipe(self, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format raw recipe data using Claude AI

        Takes user input and returns professionally formatted recipe
        """

        prompt = f"""
You are a professional chef and food writer. Format this recipe data into a professional, well-structured recipe.

Input Data:
- Title: {recipe_data.get('title', 'Untitled Recipe')}
- English Title: {recipe_data.get('titleEn', '')}
- Category: {recipe_data.get('category', 'Main Course')}
- Country: {recipe_data.get('country_origin', 'Unknown')}
- Description: {recipe_data.get('description', 'A delicious recipe')}
- Raw Ingredients: {recipe_data.get('raw_ingredients', '')}
- Raw Instructions: {recipe_data.get('raw_instructions', '')}

Please provide the response in JSON format with these exact fields:
{{
    "title": "Professional recipe title in Russian",
    "titleEn": "Professional English title",
    "description": "Professional description (1-2 sentences)",
    "ingredients": ["ingredient 1", "ingredient 2", ...],
    "preparation": "Detailed step-by-step instructions",
    "cooking_time": "Estimated cooking time",
    "servings": "Number of servings",
    "difficulty": "Easy/Medium/Hard",
    "tips": "Professional cooking tips"
}}

Ensure the recipe is well-formatted, clear, and appetizing. Make ingredients specific with quantities.
"""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # Extract the JSON response
        response_text = message.content[0].text

        # Try to parse JSON
        import json
        import re

        # Find JSON in response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
                return result
            except json.JSONDecodeError:
                pass

        # If JSON parsing fails, return structured response
        return {
            "title": recipe_data.get('title', 'Recipe'),
            "titleEn": recipe_data.get('titleEn', 'Recipe'),
            "description": recipe_data.get('description', 'A delicious recipe'),
            "ingredients": recipe_data.get('raw_ingredients', '').split('\n'),
            "preparation": recipe_data.get('raw_instructions', 'Follow the instructions'),
            "cooking_time": "Variable",
            "servings": "4-6",
            "difficulty": "Medium",
            "tips": "Cook with love!"
        }

    def suggest_improvements(self, recipe_text: str) -> str:
        """Get AI suggestions for recipe improvements"""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": f"""
As a professional chef, review this recipe and suggest improvements:

{recipe_text}

Provide constructive feedback on:
1. Ingredient quantities and measurements
2. Cooking techniques
3. Timing and temperature
4. Flavor balance
5. Presentation tips
"""
                }
            ]
        )

        return message.content[0].text

# Global agent instance
recipe_agent = RecipeAgent()
