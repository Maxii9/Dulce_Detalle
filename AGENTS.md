# AGENTS.md

Django multi-tenant e-commerce app (sweet/accessory shops). Stack: Django 5.2, PostgreSQL, Tailwind CSS (CDN), Cloudinary, deployed on Render. UI text is in Spanish.

## Commands

The Django project lives in the `dulce_detalle/` subfolder; the repo root only holds git + config. **Run all `manage.py` commands from `dulce_detalle/`.**

```powershell
..\env\Scripts\python.exe manage.py runserver
..\env\Scripts\python.exe manage.py migrate
..\env\Scripts\python.exe manage.py test
..\env\Scripts\python.exe manage.py createsuperuser
```

venv is Windows-only at repo root `env/`. No lint/typecheck/CI/pytest config exists; `app/tests.py` is empty boilerplate. Match existing style.

## Setup quirks

- `settings.py` raises `ValueError` at import if `SECRET_KEY` is missing — it must live in `dulce_detalle/.env` (loaded via python-dotenv with an explicit path) or the environment. `.env` also drives `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_URL`, Cloudinary, email.
- DB defaults to PostgreSQL `postgres://postgres:admin@localhost:5432/TiendaBD`. Local dev needs a Postgres server running (or set `DATABASE_URL`).
- `requirements.txt` pins `Django==5.2`. The "Django 6.0.3" header in `settings.py` is stale — do not bump Django.
- Git branches: `main`, `develop`, `deploy-render`. Daily work goes on `develop`.
- One-off scripts at `dulce_detalle/` root (`setup_data.py`, `cargar_*.py`, `create_superuser.py`, `patch_views.py`, etc.) are dev utilities, not importable app code.

## Deployment (Render)

- `build.sh`: pip install → collectstatic → optional flush → migrate → idempotent superuser creation (never overwrites existing password).
- `Procfile`: gunicorn `dulce_detalle.wsgi`; `runtime.txt`: python-3.12.7.
- Django admin is intentionally renamed to `/gestion-privada/` — not `/admin/`.
- Custom error pages for 400/403/404/500 wired via `handlerXXX` in `dulce_detalle/urls.py`; `app/middleware.py` redirects CSRF failures instead of returning 403.

## Architecture

- `app/models.py` defines all models (Negocio, Producto, Venta, Pedido, Nota, Insumo, EventoAnalytics, Notificacion…).
- `app/services.py` is the data-access layer: views in `app/views.py` delegate CRUD/business logic there. Put DB logic in services, not views.
- Multi-tenancy: each `Negocio` belongs to a `User`; the active store is tracked in session key `negocio_slug`. Guarded views use the `@tienda_requerida` decorator and the `_contexto_base(request, slug)` helper.
- `app/context_processors.py` injects `carrito_count`, `current_view`, and `notificaciones*` into every template.

## Storage & templates

- Images go to Cloudinary only when `CLOUDINARY_*` vars are set; otherwise local `media/`. Use `{% load imagen_tags %}` + `{% cloudinary_thumb img 400 400 %}` for optimized URLs (no-ops on local files).
- No build step: Tailwind CSS, Alpine.js, and Chart.js load via CDN; the Tailwind theme is configured inline via `tailwind.config` in `base.html` and `tienda_publica/base_publica.html`.