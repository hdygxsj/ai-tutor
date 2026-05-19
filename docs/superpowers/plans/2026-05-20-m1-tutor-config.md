# M1.1 AI Tutor Configuration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a visible Settings workflow for configuring the AI tutor provider without changing the deterministic M1 teacher loop.

**Architecture:** Store tutor provider settings in an in-process settings service for M1.1, expose small FastAPI endpoints under `/api/settings/tutor`, and render a Settings form that can load, save, and test the configuration. API keys are accepted but never returned by read endpoints.

**Tech Stack:** FastAPI, Pydantic, pytest, React, TypeScript, Ant Design, Vitest.

---

## File Structure

- Create: `backend/app/schemas/settings.py`
- Create: `backend/app/services/tutor_settings_service.py`
- Create: `backend/app/api/routes/settings.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_tutor_settings.py`
- Modify: `frontend/src/types/learning.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/pages/SettingsPage.tsx`
- Test: `frontend/src/test/settings.test.tsx`

## Task 1: Backend Tutor Settings API

**Files:**
- Create: `backend/app/schemas/settings.py`
- Create: `backend/app/services/tutor_settings_service.py`
- Create: `backend/app/api/routes/settings.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_tutor_settings.py`

- [ ] **Step 1: Write failing API tests**

Create `backend/tests/test_tutor_settings.py` with tests for:
- `GET /api/settings/tutor` returns the default fake provider and does not include an API key.
- `PUT /api/settings/tutor` saves an OpenAI-compatible config and returns masked key metadata.
- `POST /api/settings/tutor/test` returns success for `fake`, validates Ollama `base_url`, and validates required OpenAI-compatible fields.

Run: `cd backend && python3 -m pytest tests/test_tutor_settings.py -v`
Expected: FAIL because the route does not exist.

- [ ] **Step 2: Implement schemas and service**

Create Pydantic schemas:
- `TutorProvider = Literal["fake", "ollama", "openai_compatible"]`
- `TutorSettingsUpdate`: provider, base_url, model_name, api_key
- `TutorSettingsResponse`: provider, base_url, model_name, has_api_key
- `TutorConnectionTestResponse`: ok, message

Create an in-memory `TutorSettingsService` with default provider `fake`. Store the API key internally but never expose it.

- [ ] **Step 3: Implement API route**

Create `APIRouter(prefix="/settings/tutor", tags=["settings"])`:
- `GET ""`
- `PUT ""`
- `POST "/test"`

Register it in `backend/app/main.py` with `/api` prefix.

- [ ] **Step 4: Verify backend**

Run:
- `cd backend && python3 -m pytest -v`
- `cd backend && python3 -m ruff check app tests`
- `cd backend && python3 -m compileall app`

## Task 2: Settings UI Tutor Configuration

**Files:**
- Modify: `frontend/src/types/learning.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/pages/SettingsPage.tsx`
- Test: `frontend/src/test/settings.test.tsx`

- [ ] **Step 1: Write failing UI tests**

Create `frontend/src/test/settings.test.tsx` with tests for:
- Loading existing tutor settings.
- Saving provider/base URL/model/API key.
- Testing connection and showing the result.

Run: `cd frontend && npm test -- --run src/test/settings.test.tsx`
Expected: FAIL because the client methods and form do not exist.

- [ ] **Step 2: Add frontend types and API methods**

Add:
- `TutorProvider`
- `TutorSettings`
- `TutorSettingsUpdate`
- `TutorConnectionTestResult`

Add client methods:
- `fetchTutorSettings()`
- `saveTutorSettings(payload)`
- `testTutorSettings(payload)`

- [ ] **Step 3: Replace Settings placeholder with form**

Render an Ant Design card with:
- Provider select.
- Base URL input.
- Model name input.
- API key password input.
- Save button.
- Test connection button.
- Status alerts for load/save/test errors and success.

- [ ] **Step 4: Verify frontend**

Run:
- `cd frontend && npm test -- --run`
- `cd frontend && npm run typecheck`

## Task 3: Smoke Verification

- [ ] **Step 1: Verify Compose config**

Run: `docker compose config`

- [ ] **Step 2: Run full checks**

Run:
- backend pytest, ruff, compileall
- frontend tests and typecheck

Manual UI check:
- Open `http://localhost:5173`
- Go to Settings
- Configure Fake provider
- Test connection
- Save config
