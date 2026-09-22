# NatID — National Identity Platform

A national identity platform that enforces field-level, scope-based disclosure of citizen data to approved organisations via OAuth 2.0.

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) — must be running
- Python 3.13
- A web browser

---

## How to Run

### 1. Create and activate the Python virtual environment

```bash
python3 -m venv venv
```

Activate it:

- **macOS / Linux:**
  ```bash
  source venv/bin/activate
  ```
- **Windows:**
  ```bash
  venv\Scripts\activate
  ```

Then install dependencies:

```bash
pip install -r requirements.txt
```

---

### 2. Start infrastructure (MySQL + Ory Hydra + MailHog)

```bash
docker-compose up -d
```

Wait about 15 seconds for Hydra to finish its database migrations.

### 3. Start the API backend

```bash
venv/bin/uvicorn main:app --reload --port 8000
```

The API is now running at **http://localhost:8000**
Interactive API docs: **http://localhost:8000/docs**

### 4. Run the frontend

```bash
cd frontend
npx serve . -p 5500
```

The frontend is now available at **http://localhost:5500**

### 5. Create the admin account (first time only)

In a separate terminal:

```bash
venv/bin/python -m scripts.seed_admin
```

---

## Default Admin Credentials

| Field | Value |
|---|---|
| Email | `admin@natid.gov` |
| Password | `Admin1234!` |
| Username | `admin` |

> Login at `frontend/admin/login.html`

---

## Services

| Service | URL | Purpose |
|---|---|---|
| API | http://localhost:8000 | FastAPI backend |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Hydra (public) | http://localhost:4444 | OAuth 2.0 token endpoint |
| Hydra (admin) | http://localhost:4445 | Client management |
| MailHog | http://localhost:8025 | Catch password-reset emails |

---

## Run Tests

```bash
venv/bin/pytest tests/ -v
```

52 tests — all should pass. No MySQL or Hydra instance required (tests use an in-memory SQLite database).

---

## Stop Everything

```bash
docker-compose down
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.13) |
| Database | MySQL 8.0 via SQLAlchemy 2.0 |
| OAuth 2.0 | Ory Hydra v2.2 |
| Frontend | HTML / CSS / JavaScript (Bootstrap) |
| Email (dev) | MailHog |
| Tests | pytest with SQLite in-memory DB |
