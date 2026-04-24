"""
OpenAI assistant for careful recipe proofreading.
"""

import json
import re
import base64
from typing import Any, Dict, List

from backend.config import settings


class RecipeAgent:
    def __init__(self):
        self.model = settings.openai_model
        self._client = None

    @property
    def client(self):
        if self._client is None:
            if not settings.openai_api_key:
                raise ValueError(
                    "OPENAI_API_KEY is not configured. "
                    "Add it to backend/.env (or project .env) and restart the backend."
                )

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

    def extract_recipe_from_photo(
        self,
        image_bytes: bytes,
        mime_type: str,
        categories: List[str],
        countries: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """
        Extract recipe fields from a handwritten photo.
        """
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        categories_text = ", ".join(categories)
        countries_text = ", ".join(f"{c['name']} ({c['code']})" for c in countries)

        prompt = f"""
Ты помощник для админки книги рецептов.
Нужно распознать рукописный рецепт с фотографии и вернуть структурированные данные.

Правила:
- Распознавай текст максимально точно, но исправляй явные орфографические ошибки.
- Не выдумывай ингредиенты и шаги. Если фрагмент не читается, оставь максимально вероятный вариант.
- category выбери строго из списка: {categories_text}
- country выбери строго из списка стран: {countries_text}
- titleEn переведи кратко и естественно на английский.
- description сделай кратким 1-2 предложения.
- image_query: короткий поисковый запрос на английском для фото готового блюда (2-8 слов), без брендов.

Верни только JSON без markdown:
{{
  "title": "Название на русском",
  "titleEn": "Title in English",
  "category": "одна из категорий",
  "country_origin": "название страны",
  "country_code": "код страны",
  "description": "краткое описание",
  "ingredients": ["ингредиент 1", "ингредиент 2"],
  "preparation": "шаги приготовления",
  "image_query": "english food photo query"
}}
"""

        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {
                            "type": "input_image",
                            "image_url": f"data:{mime_type};base64,{encoded}",
                        },
                    ],
                }
            ],
        )

        result = self._parse_json(response.output_text)
        return {
            "title": result.get("title", ""),
            "titleEn": result.get("titleEn", ""),
            "category": result.get("category", ""),
            "country_origin": result.get("country_origin", ""),
            "country_code": result.get("country_code", ""),
            "description": result.get("description", ""),
            "ingredients": result.get("ingredients", []),
            "preparation": result.get("preparation", ""),
            "image_query": result.get("image_query", ""),
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
