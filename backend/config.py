from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

class Settings(BaseSettings):
    app_name: str = "Recipe Book Admin API"
    debug: bool = True

    # API Keys
    claude_api_key: str = ""

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

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
