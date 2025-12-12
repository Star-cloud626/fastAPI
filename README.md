# Xovate Data Validation Challenge

Dockerized FastAPI + React solution for validating CSV uploads. The API ingests a CSV, checks the required fields, and returns structured errors that the frontend renders.

## Running with Docker (recommended)

Prerequisites: Docker & Docker Compose.

```bash
docker-compose up --build
```

Services:

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`

## Frontend ↔ Backend wiring (architectural note)

The React app reads `VITE_API_BASE_URL` at build time. Defaults to `http://localhost:8000` for local dev; in Docker Compose the variable is set to `http://backend:8000` so the frontend container talks to the backend by service name. This keeps the client configuration explicit, avoids proxy complexity, and is easy to override for other environments.

## Backend rules (FastAPI + Pandas)

- Required columns: `id`, `email`, `age`. Missing columns return a single global error (`row_index`/`id` are null) and skip further checks.
- Volume check: must have **more than 10 data rows**. Failing returns one global error and stops.
- Email completeness: each empty/blank email produces an error with `row_index` (1-based, header is row 0) and `id`.
- Age validity:
  - Invalid format if non-integer text (e.g., `30yrs`, `unknown`, blank).
  - Out of range if integer not in `18–100`.
  - Each issue yields an error with `row_index` and `id`.
- Multiple errors per row are returned separately. A `pass` status means `errors` is empty.

### API

`POST /validate` (multipart/form-data, field: `file`) → JSON

```json
{
  "status": "fail",
  "errors": [
    {
      "row_index": 3,
      "id": 3,
      "column": "email",
      "error_message": "Email is required."
    }
  ]
}
```

## Local development (optional)

Backend:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
VITE_API_BASE_URL=http://localhost:8000 npm run dev -- --host --port 3000
```

## Sample data

`data/test_data_clean.csv` (15 valid rows) and `data/test_data_dirty.csv` (multiple validation issues) are provided for quick testing.

