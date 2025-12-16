# HemoVita — Copilot / AI contributor brief

This file provides focused, actionable notes to help an AI coding assistant be immediately productive in the HemoVita repo.

1) Big-picture architecture
- Backend: FastAPI app at `backend/app/main.py`. Core domain logic lives in `backend/app/engine/` (notably `core.py`) and uses structured CSVs in `backend/data/`.
- Frontend: Next.js app under `frontend/` (React + Tailwind). Server-side auth and Prisma integration live in `frontend/lib/` and `frontend/prisma/`.
- Data: `backend/data/` contains `foods_usda.csv`, `micronutrient_cutoffs_structured.csv`, and `network_relationships.csv` (used to build the nutrient graph).

2) Key integration points & flows
- API: Frontend -> Backend POST `/api/report` (see `backend/app/main.py`). The backend expects a `ReportRequest` (see `backend/app/schema.py`) with `labs: {marker: number}` and `patient` info.
- Classification & rules: `backend/app/engine/core.py` defines `MARKER_MAP`, the `REF` cutoffs, `classify_panel`, `classify_value`, and the nutrient network logic. Change thresholds here or in `micronutrient_cutoffs_structured.csv`.
- Food suggestions: `engine` reads `foods_usda.csv` and provides `suggest_foods` / `load_food_data` helpers used by the API.
- Auth & DB: Next Auth + Prisma in `frontend/` — Prisma schema: `frontend/prisma/schema.prisma`. Run `npx prisma generate` / `prisma db push` when you change models.

3) Developer workflows (commands & examples)
- Start frontend dev server (Next.js):
  - cd frontend && npm install && npm run dev  # serves the UI on localhost:3000
- Start backend (FastAPI) (example):
  - python -m pip install -r requirements.txt  # repo may not have a global requirements file; install FastAPI, uvicorn, pandas, networkx, xgboost as needed
  - uvicorn backend.app.main:app --reload --port 8000
- Prisma DB: (from `frontend/`)
  - npm run prisma:generate
  - npm run prisma:push  # requires DATABASE_URL in env
- Lint: `cd frontend && npm run lint`

4) Project-specific conventions & gotchas
- Marker naming must match `MARKER_MAP` keys in `backend/app/engine/core.py`. Common keys: `Hemoglobin`, `MCV`, `ferritin`, `vitamin_B12`, `folate_plasma`, `vitamin_D`, `magnesium`, `zinc`, `calcium`, `vitamin_C`, etc. Units are handled by `MARKER_MAP['unit']` — be careful when adding new markers.
- Classification outputs are strings: `low`, `high`, `normal`, `unknown`. Many downstream functions expect those exact labels.
- Nutrient network (optional) uses `networkx`. If not installed, the graph-based explainers gracefully fall back to static rules.
- Data files are authoritative: update `micronutrient_cutoffs_structured.csv` to change clinical cutoffs rather than hard-coding values in `core.py`.

5) Small examples
- Minimal API request shape (JSON):
  {
    "labs": { "Hemoglobin": 12.1, "ferritin": 18.0, "vitamin_B12": 250 },
    "patient": { "age": 35, "sex": "female", "country": "US" }
  }

6) Where to look for features/tasks
- Add/modify marker logic: `backend/app/engine/core.py` and `backend/data/micronutrient_cutoffs_structured.csv`.
- Add frontend UI pages/components: `frontend/app/` and `frontend/components/` (profile, labs upload, nutrient-graph).
- Auth & user model: `frontend/lib/auth.ts`, `frontend/prisma/schema.prisma`, and `frontend/lib/prisma.ts`.

If anything above is unclear or you want me to expand a particular section (example requests, tests, or a short runbook for local dev), tell me which part to expand and I will iterate.
