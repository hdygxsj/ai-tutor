# M2.1 AI Tutor Chat Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect the Agent chat page to the configured tutor provider so users can send a message and receive a real tutor response while preserving the deterministic M1 learning loop.

**Architecture:** Add a small tutor chat provider layer behind `POST /api/agent/chat`. The provider reads the existing in-memory tutor settings, supports deterministic `fake`, Ollama `/api/chat`, and OpenAI-compatible `/chat/completions`, and returns clear errors when configuration or provider calls fail. The frontend replaces the Chat placeholder with a simple message thread and composer that calls the new endpoint.

**Tech Stack:** FastAPI, Pydantic, pytest, urllib from Python standard library, React, TypeScript, Ant Design, Vitest.

---

## Scope

Included:
- `POST /api/agent/chat` for one-turn and short-history tutor conversations.
- Provider abstraction for `fake`, `ollama`, and `openai_compatible`.
- Frontend Agent Chat UI with send/loading/error states.
- Tests for provider behavior, API contract, and UI flow.

Excluded:
- Real model use in intake, plan generation, grading, or dashboard.
- Streaming responses.
- Persistent chat history.
- Database storage for tutor settings or messages.

## File Structure

- Create: `backend/app/schemas/agent.py`
- Create: `backend/app/services/tutor_provider.py`
- Modify: `backend/app/api/routes/agent.py`
- Test: `backend/tests/test_tutor_chat.py`
- Modify: `frontend/src/types/learning.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/pages/ChatPage.tsx`
- Modify: `frontend/src/test/app-shell.test.tsx`
- Test: `frontend/src/test/chat.test.tsx`

## Task 1: Backend Tutor Chat API

**Files:**
- Create: `backend/app/schemas/agent.py`
- Create: `backend/app/services/tutor_provider.py`
- Modify: `backend/app/api/routes/agent.py`
- Test: `backend/tests/test_tutor_chat.py`

- [ ] **Step 1: Write failing backend tests**

Create `backend/tests/test_tutor_chat.py` covering:
- `POST /api/agent/chat` with default fake provider returns a deterministic tutor reply and does not create a learning plan.
- OpenAI-compatible provider calls a mock transport with `/chat/completions`, `Authorization: Bearer <key>`, model name, system prompt, and user message.
- Ollama provider calls a mock transport with `/api/chat`, model name, system prompt, and user message.
- Missing required provider settings returns HTTP 400 with a clear `detail`.
- Provider transport failure returns HTTP 502 with a clear `detail`.

Run: `cd backend && python3 -m pytest tests/test_tutor_chat.py -v`
Expected: FAIL because schemas/provider/chat route do not exist.

- [ ] **Step 2: Add chat schemas**

Create `backend/app/schemas/agent.py`:
- `ChatMessage`: role `system | user | assistant`, content.
- `TutorChatRequest`: message, history list default empty.
- `TutorChatResponse`: reply, provider.

Validate `message` is not blank.

- [ ] **Step 3: Add tutor provider service**

Create `backend/app/services/tutor_provider.py`:
- `TutorProviderError(message, status_code=400)`
- `HttpTutorTransport.post_json(url, payload, headers)` using `urllib.request`.
- `TutorProviderService(settings_service, transport)`
- `reply(request)` dispatches by saved provider.

Provider behavior:
- `fake`: return a deterministic Chinese tutor reply that references the user message.
- `ollama`: require `base_url` and `model_name`; POST `{base_url}/api/chat` with `model`, `messages`, `stream: false`; parse `message.content`.
- `openai_compatible`: require `base_url`, `model_name`, `api_key`; POST `{base_url}/chat/completions` with `model`, `messages`, `temperature: 0.2`; parse `choices[0].message.content`.
- Include a system prompt: "你是 AI Dream 的机器学习导师，用中文简洁回答，并给出下一步学习建议。"
- Raise 502 for transport/provider response parse failures.

- [ ] **Step 4: Register chat route**

Modify `backend/app/api/routes/agent.py`:
- Add `POST /chat` returning `TutorChatResponse`.
- Use `Annotated[..., Depends(...)]`.
- Convert `TutorProviderError` to `HTTPException`.
- Keep existing `/intake` behavior unchanged.

- [ ] **Step 5: Verify backend**

Run:
- `cd backend && python3 -m pytest tests/test_tutor_chat.py -v`
- `cd backend && python3 -m pytest -v`
- `cd backend && python3 -m ruff check app tests`
- `cd backend && python3 -m compileall app`

## Task 2: Frontend Agent Chat UI

**Files:**
- Modify: `frontend/src/types/learning.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/pages/ChatPage.tsx`
- Modify: `frontend/src/test/app-shell.test.tsx`
- Test: `frontend/src/test/chat.test.tsx`

- [ ] **Step 1: Write failing frontend tests**

Create `frontend/src/test/chat.test.tsx` covering:
- The chat page renders an initial tutor greeting and composer.
- Sending a message calls `sendTutorMessage` with message and history.
- The returned assistant reply appears in the thread.
- API failure shows a visible error and preserves the typed conversation.

Run: `cd frontend && npm test -- --run src/test/chat.test.tsx`
Expected: FAIL because Chat page and client method are not implemented.

- [ ] **Step 2: Add frontend types and client method**

Add:
- `ChatRole`
- `TutorChatMessage`
- `TutorChatRequest`
- `TutorChatResponse`
- `sendTutorMessage(payload)`

Route: `POST /agent/chat`.

- [ ] **Step 3: Replace Chat placeholder**

Implement a simple Ant Design UI:
- Header explaining M2.1 uses Settings provider.
- Message list with user and assistant bubbles.
- TextArea composer and "发送" button.
- Enter behavior can remain button-only for M2.1.
- Loading state while waiting.
- Error Alert when API fails.
- Preserve local in-memory history during page session.

- [ ] **Step 4: Verify frontend**

Run:
- `cd frontend && npm test -- --run src/test/chat.test.tsx`
- `cd frontend && npm test -- --run`
- `cd frontend && npm run typecheck`

## Task 3: Full Verification

- [ ] **Step 1: Run backend checks**

Run:
- `cd backend && python3 -m pytest -v`
- `cd backend && python3 -m ruff check app tests`
- `cd backend && python3 -m compileall app`

- [ ] **Step 2: Run frontend checks**

Run:
- `cd frontend && npm test -- --run`
- `cd frontend && npm run typecheck`

- [ ] **Step 3: Run config check**

Run:
- `docker compose config`

Manual smoke:
- Start backend/frontend.
- Open Agent 对话.
- Send a message with Fake provider.
- Configure Ollama/OpenAI-compatible in Settings and verify Chat reports either a provider reply or a clear configuration/transport error.
