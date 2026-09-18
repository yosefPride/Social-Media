# Social Media API

A REST API built with FastAPI, from the "Mastering REST APIs with FastAPI" Udemy course. Supports user registration with email confirmation, JWT authentication, posts with comments and likes, image uploads, and AI-generated post images.

## Features

- **Auth** — register/login with JWT access tokens; email confirmation required before login
- **Posts** — create posts, list with sorting (`new` / `old` / `most_likes`), comment, like
- **AI images** — optionally generate an image for a post via DeepAI, emailed to the user when ready
- **File uploads** — upload files to Backblaze B2
- **Logging** — structured JSON logging with request correlation IDs, optional Logtail shipping

## Tech stack

FastAPI · SQLAlchemy Core + `databases` (async) · Pydantic Settings · JWT (`python-jose`) · Mailgun (email) · Backblaze B2 (file storage) · DeepAI (image generation)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `ENV_STATE` | `dev`, `test`, or `prod` — selects which config/env-prefix is loaded |
| `DATABASE_URL` | SQLAlchemy database URL |
| `DB_FORCE_ROLL_BACK` | Roll back all DB writes after each request (useful for tests) |
| `JWT_SECRET` | Secret used to sign access/confirmation tokens |
| `LOGTAIL_API_KEY` | *(optional)* Ships logs to Logtail if set |
| `MAILGUN_DOMAIN` / `MAILGUN_API_KEY` | Used to send registration confirmation and image-ready emails |
| `B2_KEY_ID` / `B2_APPLICATION_KEY` / `B2_BUCKET_NAME` | Backblaze B2 credentials for file uploads |
| `DEEPAI_API_KEY` | DeepAI API key used for post image generation |

Each variable is prefixed per environment, e.g. `DEV_JWT_SECRET`, `TEST_JWT_SECRET`, `PROD_JWT_SECRET`.

## Running

```bash
uvicorn app.main:app --reload
```

API docs are then available at `http://localhost:8000/docs`.

## Testing

```bash
pytest
```

## Linting

```bash
ruff check .
black --check .
isort --check .
```

## API overview

| Method | Path | Description |
|---|---|---|
| `POST` | `/register` | Register a new user; sends a confirmation email |
| `GET` | `/confirm/{token}` | Confirm a user's email |
| `POST` | `/login` | Log in and receive a JWT access token |
| `POST` | `/posts` | Create a post; pass `?prompt=...` to generate an AI image for it |
| `GET` | `/posts` | List posts, with `?sorting=new\|old\|most_likes` |
| `GET` | `/posts/{post_id}` | Get a post with its comments |
| `POST` | `/comments` | Comment on a post |
| `GET` | `/posts/{post_id}/comments` | List comments on a post |
| `POST` | `/likes` | Like a post |
| `POST` | `/upload` | Upload a file to B2 |
