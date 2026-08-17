# AGENTS.md

## Stack

- Python 3.11 (`requires-python = ">=3.11,<3.12"`)
- Flask 3.1.3 with app factory in `create_app(testing=False)` (`main.py`)
- SQLAlchemy + Flask-Migrate (Alembic) for ORM/migrations
- MySQL/MariaDB via `pymysql` in production; SQLite in-memory for tests
- Package manager: **PDM** (not pip). Venv at `.venv/`

## Commands

```bash
# Dev server
python main.py                    # runs on 0.0.0.0:5000

# Initialize DB (first time)
python iniciar_base_de_datos.py
python iniciar_base_de_datos.py --testing   # SQLite in-memory

# Create initial admin user
python crear_admin.py

# Migrations (Flask-Migrate)
flask db migrate -m "description"
flask db upgrade

# Tests
pytest                            # unittest-based, via pytest-flask

# Lint & format (via pre-commit hooks)
ruff check --fix .
ruff format .
pre-commit run --all-files
```

## Linting

Pre-commit runs `ruff` (lint + format), trailing-whitespace, end-of-file-fixer, check-yaml, check-added-large-files. No type checker configured.

## Project structure

- `main.py` — app factory, blueprint registration, template filters, DB connection check
- `config.py` — `Config` class, loads `.env`, MySQL URI from env vars
- `extensions.py` — shared `db` and `mail` instances
- `src/models/` — `Libro`, `Usuario`, `Prestamo`, `Reserva` (re-exported from `src/models/__init__.py`)
- `src/routes/` — Blueprints: `generales_bp` (/), `auth_bp` (/auth), `usuarios_bp` (/usuarios), `libros_bp` (/libros), `prestamos_bp` (/prestamos)
- `src/forms/forms.py` — WTForms
- `src/auth.py` — Flask-Login `load_user`
- `src/permissions.py` — role-based access
- `templates/` — Jinja2 templates (top-level)
- `static/` — CSS and JS (top-level)
- `migrations/` — Alembic migration scripts (tracked in git)
- `instance/` — local DB files (gitignored)

## Key gotchas

- **All code, comments, templates, and variable names are in Spanish.** Maintain this convention.
- `Config.SERVER_NAME` reads from env var, defaults to `None` (Flask auto-detects). Set in `.env` if needed.
- `strict_slashes = False` is set globally (`main.py:110`), so trailing slashes are flexible.
- Route files import `db` from `extensions` and models from specific submodules (e.g. `src.models.models_libro`). Do not import models from the `src.models` package re-export.
- `.env` contains credentials (DB, mail, admin). It is gitignored but exists in the working tree — never commit it.
- `db.engine.execute()` is deprecated in SQLAlchemy 2.x. Always use `db.engine.connect()` + `conn.execute(text(...))`.
- Tests use SQLite in-memory (`TestConfig`), production uses MySQL via `pymysql`.
