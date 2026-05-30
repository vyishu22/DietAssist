# DietAssist — Project Overview and Technical README

## Project summary
DietAssist is a lightweight nutrition coaching application providing patient-facing diet recommendations and a caretaker dashboard. The backend is a Flask-based API that generates personalized recommendations (via an OpenRouter-backed recommender service) and stores data in MongoDB. The frontend is a minimal static app (HTML/JS/CSS) that consumes the API.

## Repository layout (high-level)
- `backend/` — Flask app and services
  - `app/routes/` — API routes (`auth.py`, `patient.py`, `caretaker.py`, `recommendations.py`, `feedback.py`)
  - `app/models/` — data models
  - `app/services/` — recommendation integrations (e.g., `gemini_recommender.py`)
  - `utils/` — auth helpers and recommendation utilities
  - `run.py` — application entry
  - `requirements.txt` — Python dependencies
- `frontend/` — static site (HTML, JS, CSS)
- `k8s/` — Kubernetes manifests for deployment
- `tests/` and `backend/tests/` — automated tests (unit/e2e)

## Key features
- Authentication endpoints for caretakers and patients
- Personalized diet recommendations from `gemini_recommender` service
- Caretaker dashboard web UI
- Feedback collection endpoints
- Kubernetes deployment manifests

## Prerequisites
- Python 3.10+ (recommended)
- pip
- MongoDB (local or cloud-based)
- Redis (optional, for caching)

## Local development — backend
1. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r backend/requirements.txt
```

3. Configure environment variables (example):
- `MONGO_URI` — MongoDB connection string
- `FLASK_ENV=development`
- `SECRET_KEY` — Flask secret
- `GEMINI_API_KEY` — API key for recommender (if used)
- `OPENROUTER_API_KEY` — API key for OpenRouter (preferred)
- `OPENROUTER_MODEL` — optional model name for OpenRouter (defaults to `gpt-4o-mini`)
- `GEMINI_API_KEY` — API key for recommender (legacy/fallback, if used)

4. Run the backend locally:

```powershell
python backend/run.py
```

## Frontend
- The frontend is static and served from `frontend/index.html` and `frontend/pages/*.html`.
- To test locally, open the HTML files in a browser or serve them via a simple static server.

## API overview (examples)
The backend routes are grouped by responsibility. Confirm exact paths in `backend/app/routes/*.py`.
- `POST /auth/register` — register user
- `POST /auth/login` — authenticate
- `GET /recommendations?patient_id=...` — fetch recommendations
- `POST /feedback` — submit feedback
- `GET /patient/:id` — patient info
- `GET/POST /caretaker/*` — caretaker actions

(See `backend/app/routes` for full route signatures.)

## Tests
- Python tests live under `backend/tests/`. Run them with `pytest` from repository root:

```powershell
pytest -q
```

- Frontend UI tests are in `frontend/tests/` and use Playwright.

## Caching & performance
- Tests include caching-related checks (`test_caching.py`). The system uses Redis (or in-memory cache) as configured in application settings.

## Deployment
- Local development: run backend and MongoDB/Redis manually (see Local development section).
- Kubernetes manifests in `k8s/` for production deployment (includes `backend-deployment.yaml`, `mongo-pvc.yaml`, etc.).
- Secrets should be provided via secure stores (Kubernetes Secrets, environment variables, or a secrets manager).

## Security & privacy notes
- Medical or dietary guidance must be reviewed by qualified clinicians before production use (see `SECURITY_MEDICAL_REVIEW.md`).
- Sensitive configuration (API keys, DB URIs) must never be checked into source control.

## Developer notes
- Recommendation logic lives entirely in `backend/app/services/gemini_recommender.py`; the previous utility file has been removed and all output comes from OpenRouter.
- Auth helpers are in `backend/app/utils/auth_utils.py`.
- To add endpoints, follow existing patterns in `app/routes` and register Blueprints in `run.py`.

## Troubleshooting
- If Mongo connection fails: verify `MONGO_URI` and that the Mongo service is running.
- For missing dependencies: recreate the virtual environment and reinstall `requirements.txt`.

## Contributing
- Fork the repo, create a feature branch, add tests, and open a PR with a clear description.

## Contact / Maintainers
- See repository `README.md` for maintainer/contact details or open an issue in the project tracker.

---

This file was generated as a single consolidated technical README summarizing the codebase, setup, API, tests, and deployment notes. Adjust any section-specific details by inspecting the corresponding files under `backend/` and `k8s/`.
