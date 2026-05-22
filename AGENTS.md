# AI Dream — Agent 指南

本文档供 Cursor / 编码 Agent 使用，说明本地环境约定与常见故障排查。用户向 README 看齐即可；Agent 改代码或排错时应优先遵守下文。

## 架构约定

- **只在主仓库 `AI_Dream/` 根目录开发**，不要使用 `.worktrees/`（已废弃；历史分支内容已并入 `master`）。
- **Docker Compose 默认只启动 PostgreSQL**（`docker compose up -d`）。`backend` / `frontend` 在 `full` profile 下，仅 CI 或全栈联调时使用。
- **日常开发**：数据库在容器里，**后端与前端在宿主机**运行（PyCharm、`uvicorn`、`npm run dev`）。
- **数据持久化**：Postgres 数据目录为项目根目录 `postgres-data/`（bind mount，已在 `.gitignore`）。
- **业务数据与设置**均写入 PostgreSQL（含 `workspace_settings` 表中的导师/运行时配置）。不要用内存单例持久化新设置。

## 本地启动清单（三项缺一不可）

| 服务 | 命令 | 地址 |
|------|------|------|
| PostgreSQL | `docker compose up -d` | `localhost:5432`，库/用户/密码均为 `ai_dream` |
| 后端 | `cd backend && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000` | http://localhost:8000 |
| 前端 | `cd frontend && npm run dev` | http://localhost:5173 |

环境变量见根目录 `.env.example`。后端默认 `DATABASE_URL=postgresql+psycopg://ai_dream:ai_dream@localhost:5432/ai_dream`。前端默认通过 Vite 代理访问 `/api` → `127.0.0.1:8000`（避免 `localhost` 与 `127.0.0.1` 的 CORS 问题）；CORS 亦允许 `http://localhost:5173` 与 `http://127.0.0.1:5173`。

后端 **启动时** 会执行 `alembic upgrade head`（`app/main.py` lifespan；`APP_ENV=test` 时跳过）。一般无需手动迁移，除非排查库表问题。

## PostgreSQL

- 客户端必须连接数据库 **`ai_dream`**、schema **`public`**，不要连默认库 `postgres`。
- 迁移版本应到 `0003_workspace_settings`；可用：
  ```sh
  docker compose exec postgres psql -U ai_dream -d ai_dream -c "\dt"
  ```
- 表存在但**无业务行**是正常的，需通过 API/页面创建学习计划或保存设置后才有数据。

## Docker Compose profiles

```sh
# 仅数据库（默认）
docker compose up -d

# 全栈（backend + frontend + postgres）
docker compose --profile full up --build
```

若用户曾用旧 compose 起过前后端容器，改 profile 后**不会自动删除**旧容器。仅需数据库时：

```sh
docker compose --profile full stop backend frontend
docker compose --profile full rm -f backend frontend
```

## 常见报错

### 前端：「无法连接到学习服务，请确认后端已启动。」

- **原因**：`http://localhost:8000` 无响应（后端未启动或启动失败），或前端用 `127.0.0.1:5173` 直连 `localhost:8000` 被 CORS 拦截（浏览器里 fetch 失败，表现与后端未启动相同）。
- **检查**：`curl http://127.0.0.1:8000/api/health` 应返回 `{"status":"ok"}`；改代码后需**重启前端** `npm run dev` 以加载 Vite 代理。
- **处理**：在 `backend/` 下启动 `uvicorn`；前端用 `http://localhost:5173` 或 `http://127.0.0.1:5173` 均可（推荐默认 `/api` 代理，勿在 `frontend/.env` 写死跨域的 `VITE_API_BASE_URL` 除非有意直连）。

### 前端：localhost:5173 打不开

- **原因**：停掉 Docker 前端容器后，宿主机未执行 `npm run dev`。
- **处理**：`cd frontend && npm run dev`。

### 对话：「Tutor provider request failed.」/「导师服务请求失败」

- **常见原因 1**：Settings 里选了 `openai_compatible` 或 `ollama`，但外网/本地 LLM 不可达。
- **常见原因 2（macOS + 代理）**：HTTPS 解密代理导致 Python `SSL: CERTIFICATE_VERIFY_FAILED`。在 `backend/.env` 设 `TUTOR_SSL_VERIFY=false` 后重启后端（仅本地调试），或关闭代理的 HTTPS 拦截。
- **DeepSeek**：`base_url` 填 `https://api.deepseek.com` 即可（后端会自动请求 `/v1/chat/completions`）；模型名常用 `deepseek-chat` 或 `deepseek-reasoner`，需有效 API Key。
- **快速验证**：`curl http://localhost:8000/api/settings/tutor`；临时改用 `fake` provider 可不调用外部 API。
- **检查**：`curl -X POST http://localhost:8000/api/agent/chat -H 'Content-Type: application/json' -d '{"message":"你好"}'`

### 后端：`ImportError` / `partially initialized module`（models 循环导入）

- **原因**：`app.models.settings` 与 `app.models.learning` 不可互相导入 mixin。
- **约定**：共享字段放 `app/models/mixins.py`；`settings.py` 只从 `mixins` 引用，不要从 `learning` 引用。

### PG 客户端里「一张表都没有」

- 几乎总是连错库（用了 `postgres`）或看错 schema。按上文连接 `ai_dream` / `public`。
- 若确实未迁移：`cd backend && alembic upgrade head`。

## 开发与测试

- 后端：`cd backend && ruff check . && pytest -v`（测试用 SQLite 内存库，不依赖 Docker Postgres）。
- 前端：`cd frontend && npm run typecheck && npm test`。
- E2E：需 `docker compose up -d` + 本地或 profile 内的 backend/frontend，见 README。

## 改代码时注意

- 新增 SQLAlchemy 模型：在 `app/db/base.py` 注册 import，并添加 Alembic 迁移；避免 `learning` ↔ `settings` 循环导入。
- 持久化用户/工作区配置：使用 `WorkspaceSettingsStore` + `workspace_settings` 表，不要新增进程内全局单例存储。
- 不要擅自 `docker compose up` 拉起 `full` profile，除非用户明确要求容器化前后端或跑 E2E 全栈。
