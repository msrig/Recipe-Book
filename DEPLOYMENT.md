# Deployment

This app can run as one FastAPI service. The backend serves the public recipe
site, the admin panel, API routes, CSS, JavaScript, and images.

## Required persistent storage

Recipes are stored in `backend/data/recipes.json`, and uploaded/generated images
are stored in `images/`. In production, mount persistent storage and point the
app to it with:

```env
DATA_DIR=/var/data/backend/data
IMAGES_DIR=/var/data/images
```

On first startup, the app copies the bundled recipes and images into those
folders if they are missing.

## Environment variables

Set these in the hosting dashboard. Do not commit them to Git.

```env
DEBUG=production
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5.2
ADMIN_USERNAME=...
ADMIN_PASSWORD=...
JWT_SECRET_KEY=...
```

Most hosts set `PORT` automatically. Locally, the Docker image defaults to
`8000`.

## Render

This repo includes `render.yaml`.

1. Create a new Render Blueprint from this GitHub repository.
2. Set the secret environment variables requested by Render.
3. Keep the persistent disk mounted at `/var/data`.
4. Open `/admin/` after deploy and log in with your configured admin user.

## Railway or Fly.io

Use the included `Dockerfile`, add a persistent volume, and set:

```env
DATA_DIR=/data/backend/data
IMAGES_DIR=/data/images
```

Mount the volume at `/data`.
