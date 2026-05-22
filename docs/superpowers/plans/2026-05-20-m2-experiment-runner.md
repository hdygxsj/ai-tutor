# M2.2 Experiment Runner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first experiment execution loop: users can run a deterministic minimal ML experiment, then inspect metrics, logs, and artifacts in the UI.

**Architecture:** Add a backend experiment runner service behind `/api/experiments/minimal`. The service creates a per-run artifact directory, writes a generated Python experiment script, executes it through an injectable process runner, reads structured outputs, and returns a typed result. The frontend adds an Experiments page that triggers the run and displays metrics/logs/artifact paths. This keeps the same runner boundary that a Docker process runner can replace in the next slice without changing the API or UI.

**Tech Stack:** FastAPI, Pydantic, pytest, Python subprocess/pathlib/json, React, TypeScript, Ant Design, Vitest.

---

## Scope

Included:
- `POST /api/experiments/minimal` synchronous run endpoint.
- Deterministic minimal gradient-descent experiment script generated per run.
- Structured metrics, logs, and artifact path response.
- Frontend "实验运行" page with run button and result display.
- Tests for successful run, artifact parsing, runner failure, and UI behavior.

Excluded:
- Docker image execution and container isolation.
- Git template project generation.
- Persistent database records for experiment runs.
- Dataset downloads and notebook export.

## File Structure

- Create: `backend/app/schemas/experiments.py`
- Create: `backend/app/services/experiment_runner.py`
- Create: `backend/app/api/routes/experiments.py`
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_experiments.py`
- Modify: `frontend/src/types/learning.ts`
- Modify: `frontend/src/api/client.ts`
- Create: `frontend/src/pages/ExperimentsPage.tsx`
- Modify: `frontend/src/components/AppShell.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/test/app-shell.test.tsx`
- Test: `frontend/src/test/experiments.test.tsx`

## Task 1: Backend Experiment Runner

**Files:**
- Create: `backend/app/schemas/experiments.py`
- Create: `backend/app/services/experiment_runner.py`
- Create: `backend/app/api/routes/experiments.py`
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_experiments.py`

- [ ] **Step 1: Write failing backend tests**

Create `backend/tests/test_experiments.py` covering:
- `POST /api/experiments/minimal` returns `status: "passed"`, a `run_id`, metrics containing `initial_loss`, `final_loss`, `improvement`, logs, and artifacts containing `metrics.json` and `log.txt`.
- The service writes artifacts under the configured artifact root.
- If the process runner exits non-zero, the API returns HTTP 502 with a clear `detail`.
- If metrics output is malformed, the API returns HTTP 502 instead of a 500.

Run: `cd backend && python3 -m pytest tests/test_experiments.py -v`
Expected: FAIL because route/service do not exist.

- [ ] **Step 2: Add schemas**

Create:
- `ExperimentArtifact`: name, path, content_type.
- `ExperimentRunResponse`: run_id, status, metrics, logs, artifacts.

Use only JSON-serializable values.

- [ ] **Step 3: Add runner service**

Create `ExperimentRunnerService`:
- Constructor accepts `artifact_root: Path` and injectable `process_runner`.
- Creates `artifact_root/experiments/<run_id>/`.
- Writes `experiment.py`.
- Runs the script with current Python executable.
- Script writes `metrics.json` and `log.txt`.
- Reads metrics/logs and returns `ExperimentRunResponse`.

Create errors:
- `ExperimentRunnerError(message, status_code=502)`.

Keep the generated experiment deterministic: simple scalar gradient descent with pure Python math so local tests do not need PyTorch installed. Name/logs should explain it is the M2.2 minimal runner and the next slice can swap in Docker/PyTorch execution.

- [ ] **Step 4: Add API route**

Create `APIRouter(prefix="/experiments", tags=["experiments"])`:
- `POST /minimal`

Register in `backend/app/main.py` with `/api`.

Add `artifact_root: str = "artifacts"` to settings.

- [ ] **Step 5: Verify backend**

Run:
- `cd backend && python3 -m pytest tests/test_experiments.py -v`
- `cd backend && python3 -m pytest -v`
- `cd backend && python3 -m ruff check app tests`
- `cd backend && python3 -m compileall app`

## Task 2: Frontend Experiments Page

**Files:**
- Modify: `frontend/src/types/learning.ts`
- Modify: `frontend/src/api/client.ts`
- Create: `frontend/src/pages/ExperimentsPage.tsx`
- Modify: `frontend/src/components/AppShell.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/test/app-shell.test.tsx`
- Test: `frontend/src/test/experiments.test.tsx`

- [ ] **Step 1: Write failing frontend tests**

Create `frontend/src/test/experiments.test.tsx` covering:
- Page renders "实验运行" and explains M2.2 minimal runner.
- Clicking "运行最小实验" calls `runMinimalExperiment`.
- Returned metrics/logs/artifacts render.
- API failure shows visible error.

Run: `cd frontend && npm test -- --run src/test/experiments.test.tsx`
Expected: FAIL because page/client/menu do not exist.

- [ ] **Step 2: Add frontend types and API method**

Add:
- `ExperimentArtifact`
- `ExperimentRunResult`
- `runMinimalExperiment()`

Route: `POST /experiments/minimal`.

- [ ] **Step 3: Add Experiments page and menu item**

Add menu key `experiments` with label "实验运行".

UI:
- Run button: "运行最小实验".
- Loading state.
- Metrics cards/table for loss and improvement.
- Logs block.
- Artifact list.
- Error Alert.

- [ ] **Step 4: Verify frontend**

Run:
- `cd frontend && npm test -- --run src/test/experiments.test.tsx`
- `cd frontend && npm test -- --run`
- `cd frontend && npm run typecheck`

## Task 3: Full Verification

Run:
- `cd backend && python3 -m pytest -v`
- `cd backend && python3 -m ruff check app tests`
- `cd backend && python3 -m compileall app`
- `cd frontend && npm test -- --run`
- `cd frontend && npm run typecheck`
- `docker compose config`

Manual smoke:
- Start frontend/backend.
- Open "实验运行".
- Click "运行最小实验".
- Confirm metrics/logs/artifacts render.
