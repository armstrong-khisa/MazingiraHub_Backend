# MazingiraHub Backend

Backend service for MazingiraHub, a platform intended to connect donors with organizations and make the progress of funded projects visible. The project is built with Flask, SQLAlchemy, Flask-Migrate, and JWT support.

> **Development status:** The core domain models, authentication, organization applications, donations, projects, payments, recurring donations, inventory, beneficiaries, and stories are implemented. The endpoint suite still needs automated integration coverage before production use.

## Contents

- [Implemented functionality](#implemented-functionality)
- [Planned domain](#planned-domain)
- [Technology](#technology)
- [Project structure](#project-structure)
- [Getting started](#getting-started)
- [Configuration](#configuration)
- [Running the application](#running-the-application)
- [Current API](#current-api)
- [Data model](#data-model)
- [Database migrations](#database-migrations)
- [Testing](#testing)
- [Deployment](#deployment)
- [Development notes](#development-notes)

## Implemented functionality

The current application provides:

- Flask application creation through `create_app()` in `app.py`.
- SQLite configuration using `sqlite:///mazingirahub.db`.
- SQLAlchemy database integration.
- Flask-Migrate integration for database migrations.
- JWT manager initialization.
- A `User` model with password hashing using Werkzeug.
- User roles with a default of `donor` and account status with a default of `active`.
- A root endpoint that can be used as a basic health check.
- JWT authentication endpoints under `/api/auth`.
- Organization application review endpoints and public organization reads.
- Donation creation and donor-scoped reads under `/api/donations`.
- Project, payment, recurring donation, inventory, beneficiary, and story endpoints under `/api`.

JWT protection is applied to authenticated operations. Role-specific authorization is currently implemented for organization application review.

## Planned domain

The ERD in [`docs/ERD AND DATABASE SCHEMA.jpeg`](docs/ERD%20AND%20DATABASE%20SCHEMA.jpeg) describes the target platform model:

- Users can act as donors, organization users, or administrators.
- A user may have a donor profile or an organization profile.
- Organizations are created through organization applications and require review/approval.
- Approved organizations can manage projects, donations, beneficiaries, inventory items, and stories.
- Donors can make one-time or recurring donations to organizations and optionally to projects.
- Payments record the provider payment ID, method, amount, currency, status, and payment date for donations.
- Stories can contain media and may be featured or published.
- Administrators review organization applications.

These are planned relationships from the ERD, not currently exposed API behavior.

## Technology

- Python 3.14
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- Flask-JWT-Extended
- SQLite for local development
- Gunicorn as the configured production WSGI server

Dependencies are declared in [`Pipfile`](Pipfile). Install dependencies in a virtual environment before importing or running the application.

## Project structure

```text
.
├── app.py                         # Flask application factory and root route
├── extensions.py                  # Shared SQLAlchemy, migration, and JWT extensions
├── controllers/                   # Planned HTTP route/controller modules
├── models/                        # ORM models; User is currently implemented
├── schemas/                       # Planned request/response schemas
├── docs/                          # Design documentation, including the ERD
├── tests/                         # Test package (tests are not implemented yet)
├── Pipfile                        # Python dependencies and interpreter version
└── render.yaml                    # Render deployment configuration
```

## Getting started

### Prerequisites

- Python 3.14
- `pipenv`
- Git

Create and activate the project environment:

```bash
pip install pipenv
pipenv install
pipenv shell
```

Alternatively, run commands without activating the shell:

```bash
pipenv install
pipenv run python app.py
```

Verify the installed packages before starting the service:

```bash
pipenv run python -c "import flask, flask_sqlalchemy, flask_migrate, flask_jwt_extended; print('Dependencies OK')"
```

## Configuration

The application currently sets these values directly in `app.py`:

| Setting | Current value | Purpose |
| --- | --- | --- |
| `SQLALCHEMY_DATABASE_URI` | `sqlite:///mazingirahub.db` | Local SQLite database |
| `SQLALCHEMY_TRACK_MODIFICATIONS` | `False` | Disables SQLAlchemy modification tracking |
| `JWT_SECRET_KEY` | `change-this-secret-key` | Signs JWTs when authentication is added |

The JWT key is a development placeholder. Before deploying or enabling authentication, replace it with a strong secret loaded from an environment variable. The application does not yet read configuration from environment variables.

## Running the application

Start the development server on port 5000:

```bash
pipenv run python app.py
```

The service is available at `http://127.0.0.1:5000`.

The development server runs with Flask debug mode enabled by the `__main__` block. Do not use this mode as the production server.

## Current API

### `GET /`

Returns a plain-text service greeting.

Example:

```bash
curl http://127.0.0.1:5000/
```

Response:

```text
Welcome to MazingiraHub Backend!
```

Authentication routes are available under `/api/auth`; domain routes are available under `/api` and organization application routes are available under `/organizations`.

## Data model

### Implemented: `users`

The `User` model in [`models/user.py`](models/user.py) currently contains:

| Column | Type | Details |
| --- | --- | --- |
| `id` | Integer | Primary key |
| `full_name` | String(150) | Required |
| `email` | String(150) | Required and unique |
| `password_hash` | String(255) | Required; stores a Werkzeug hash, not the raw password |
| `phone` | String(30) | Optional |
| `role` | String(20) | Required; defaults to `donor` |
| `status` | String(20) | Required; defaults to `active` |
| `created_at` | DateTime | Required; defaults to UTC creation time |
| `updated_at` | DateTime | Required; updates on model changes |

Use `set_password()` and `check_password()` rather than manipulating `password_hash` directly.

### Additional tables

The ERD identifies these additional tables for future implementation:

`donor_profiles`, `organization_profiles`, `organizations`, `organization_applications`, `projects`, `donations`, `payments`, `recurring_donations`, `inventory_items`, `beneficiaries`, `stories`, and `story_media`.

The implemented model files are registered through `models/__init__.py` and imported by the application factory for migration discovery. The ERD's `donor_profiles` and `organization_profiles` tables still need dedicated model, schema, controller, and migration files.

## Database migrations

Flask-Migrate is initialized and the repository includes migration scripts. Review generated migration files against the ERD before applying new changes:

```bash
pipenv run flask --app app db init
pipenv run flask --app app db migrate -m "describe schema change"
pipenv run flask --app app db upgrade
```

Review generated migration files before applying them. The SQLite database file is created relative to Flask's instance configuration when the application accesses the database.

## Testing

The `tests/` package currently contains no test cases. After installing dependencies, a basic smoke check can be run with:

```bash
pipenv run python -c "from app import app; response = app.test_client().get('/'); print(response.status_code, response.get_data(as_text=True))"
```

Expected output begins with:

```text
200 Welcome to MazingiraHub Backend!
```

As the API is implemented, add focused tests for authentication, role authorization, validation, database relationships, donations, and payment status handling.

## Deployment

[`render.yaml`](render.yaml) configures a Render web service named `mazingira-hub-backend`:

- Build: `pip install pipenv && pipenv install --deploy`
- Start: `pipenv run gunicorn app:app`
- Health check: `GET /`
- Runtime: Python
- Configured Python version: 3.14

Before deploying, verify that the production dependencies include Gunicorn. It is referenced by `render.yaml` but is not currently declared in `Pipfile`. Also provide a production `JWT_SECRET_KEY`, move the database configuration out of source code, and use a persistent/managed database for production data instead of local SQLite.

## Development notes

- Keep shared Flask extensions in `extensions.py` and initialize them through the application factory.
- Import each implemented model before generating migrations so SQLAlchemy can discover its metadata.
- Do not return or log raw passwords; only password hashes belong in persistence.
- Add blueprints in `create_app()` when controllers become available.
- Keep the ERD and this README synchronized as relationships and endpoint contracts are implemented.