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
PUBLIC_BASE_URL=https://your-domain.example
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=...
SMTP_PASSWORD=...
SMTP_FROM_EMAIL=recipes@example.com
SMTP_USE_TLS=true
PASSWORD_RESET_EXPIRE_MINUTES=60
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

## DigitalOcean Droplet

The repo includes `docker-compose.yml` for a single app container. It binds the
app to `127.0.0.1:8000`, so put Nginx/Caddy in front of it for the public
subdomain and HTTPS. For Nginx, set `client_max_body_size 20M;` in the `server`
block so recipe images can be uploaded.

1. Copy `.env.production.example` to `.env.production`.
2. Fill in secrets and set `PUBLIC_BASE_URL` to the real subdomain.
3. Start the app:

```bash
docker-compose up -d --build
```

4. Point the reverse proxy to `http://127.0.0.1:8000`.

Persistent recipe data and uploaded images live in the Docker volume
`recipe-book-data`.
