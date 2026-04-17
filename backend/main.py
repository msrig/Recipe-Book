from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

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

# Mount static files
base_dir = Path(__file__).parent.parent
static_dir = base_dir / "admin"
if static_dir.exists():
    app.mount("/admin", StaticFiles(directory=str(static_dir), html=True), name="admin")

images_dir = base_dir / "images"
if images_dir.exists():
    app.mount("/images", StaticFiles(directory=str(images_dir)), name="images")

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
    if asset_name not in {"recipes-data", "search", "country-utils"}:
        return {"detail": "Asset not found"}

    asset = base_dir / f"{asset_name}.js"
    if asset.exists() and asset.is_file():
        return FileResponse(str(asset), media_type="application/javascript")
    return {"detail": "Asset not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
