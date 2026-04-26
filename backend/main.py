from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import shutil

from backend.routes import auth, recipes
from backend.config import settings

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="API for managing recipe book with AI assistance",
    version="1.0.0"
)

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(recipes.router)

base_dir = Path(__file__).parent.parent

def copy_missing_files(source_dir: Path, target_dir: Path):
    if not source_dir.exists():
        return

    for source_path in source_dir.rglob("*"):
        if not source_path.is_file():
            continue

        relative_path = source_path.relative_to(source_dir)
        target_path = target_dir / relative_path
        if target_path.exists():
            continue

        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)

@app.on_event("startup")
async def prepare_storage():
    """Seed mounted storage with bundled recipes and images on first deploy."""
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.images_dir.mkdir(parents=True, exist_ok=True)

    bundled_recipes = base_dir / "backend" / "data" / "recipes.json"
    if bundled_recipes.exists() and not settings.recipes_file.exists():
        shutil.copy2(bundled_recipes, settings.recipes_file)

    bundled_images = base_dir / "images"
    if bundled_images.resolve() != settings.images_dir.resolve():
        copy_missing_files(bundled_images, settings.images_dir)

# Mount static files
static_dir = base_dir / "admin"
if static_dir.exists():
    app.mount("/admin", StaticFiles(directory=str(static_dir), html=True), name="admin")

images_dir = settings.images_dir
images_dir.mkdir(parents=True, exist_ok=True)
if images_dir.exists():
    app.mount("/images", StaticFiles(directory=str(images_dir)), name="images")

css_dir = base_dir / "css"
if css_dir.exists():
    app.mount("/css", StaticFiles(directory=str(css_dir)), name="css")

@app.get("/")
async def root():
    index_file = base_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Recipe Book API", "docs": "/docs", "admin": "/admin"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/{page_name}.html")
async def static_html_page(page_name: str):
    page = base_dir / f"{page_name}.html"
    if page.exists() and page.is_file():
        return FileResponse(str(page))
    return {"detail": "Page not found"}

@app.get("/{asset_name}.js")
async def static_js_asset(asset_name: str):
    if asset_name not in {"recipes-data", "search", "country-utils", "i18n"}:
        return {"detail": "Asset not found"}

    asset = base_dir / f"{asset_name}.js"
    if asset.exists() and asset.is_file():
        return FileResponse(str(asset), media_type="application/javascript")
    return {"detail": "Asset not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
