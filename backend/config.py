from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from functools import lru_cache
from pathlib import Path
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            Path(__file__).parent / ".env",        # backend/.env
            Path(__file__).parent.parent / ".env", # project root .env
        ),
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Recipe Book Admin API"
    debug: bool = True
    port: int = 8000

    # API Keys
    openai_api_key: str = ""
    openai_model: str = "gpt-5.2"

    # JWT Settings
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24 hours

    # File paths
    base_dir: Path = Path(__file__).parent.parent
    data_dir: Path = base_dir / "backend" / "data"
    images_dir: Path = base_dir / "images"
    recipes_file: Path = data_dir / "recipes.json"
    users_file: Path = data_dir / "users.json"

    # Admin credentials
    admin_username: str = "admin"
    admin_password: str = "admin123"  # Change this!

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, str) and value.lower() in {"release", "prod", "production"}:
            return False
        return value

    @field_validator("openai_api_key", mode="before")
    @classmethod
    def resolve_openai_key(cls, value):
        # Keep explicit OPENAI_API_KEY as the source of truth.
        if value:
            return value

        env_value = os.getenv("OPENAI_API_KEY")
        if env_value:
            return env_value

        return ""

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
