"""
OpenAI assistant for careful recipe proofreading.
"""

import json
import re
from typing import Any, Dict

from backend.config import settings


class RecipeAgent:
    def __init__(self):
        self.model = settings.openai_model
        self._client = None

    @property
    def client(self):
        if self._client is None:
            if not settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY is not configured")

            from openai import OpenAI

            self._client = OpenAI(api_key=settings.openai_api_key)

        return self._client

    def polish_recipe(self, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Proofread and lightly polish recipe text without changing the author's meaning.
        """
        prompt = f"""
Ты редактор семейной книги рецептов.

Твоя задача:
- исправить только орфографию, пунктуацию и явные грамматические ошибки;
- сделать описание более грамотным, красивым и естественным;
- сохранить смысл, стиль и все факты автора;
- не добавлять новые ингредиенты, шаги, советы, времена готовки или факты;
- не удалять важные детали автора;
- не менять категорию и страну;
- если английское название явно с ошибкой, аккуратно исправить перевод.

Верни только валидный JSON без markdown с такими полями:
{{
  "title": "исправленное русское название",
  "titleEn": "исправленное английское название",
  "description": "грамотное описание без новых фактов",
  "ingredients": ["исправленный ингредиент 1", "исправленный ингредиент 2"],
  "preparation": "исправленное приготовление без новых шагов"
}}

Исходный рецепт:
{json.dumps(recipe_data, ensure_ascii=False, indent=2)}
"""

        response = self.client.responses.create(
            model=self.model,
            input=prompt,
        )

        result = self._parse_json(response.output_text)

        return {
            **recipe_data,
            "title": result.get("title", recipe_data.get("title", "")),
            "titleEn": result.get("titleEn", recipe_data.get("titleEn", "")),
            "description": result.get("description", recipe_data.get("description", "")),
            "ingredients": result.get("ingredients", recipe_data.get("ingredients", [])),
            "preparation": result.get("preparation", recipe_data.get("preparation", "")),
        }

    def _parse_json(self, text: str) -> Dict[str, Any]:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                raise ValueError("AI response did not contain JSON")
            return json.loads(match.group())


recipe_agent = RecipeAgent()
