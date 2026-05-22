# AI Dream

AI Dream 是一个本地机器学习教师 Agent 平台。M1 阶段聚焦 FastAPI、PostgreSQL、React/Vite 和 Ant Design 组成的本地教师闭环。

## M1 目标

- 提供可本地启动的后端、数据库和前端开发环境。
- 建立教师循环所需的项目边界和工程检查。
- 为后续课程、作业、批改和反馈功能保留清晰的扩展入口。

## 本地开发（推荐）

日常开发只通过 Docker 启动 PostgreSQL，前后端在宿主机运行。

**1. 启动数据库**

```sh
docker compose up -d
```

数据持久化在项目根目录的 `postgres-data/`。连接信息：

- Host: `localhost:5432`
- 用户 / 库 / 密码: `ai_dream`

**2. 启动后端**

```sh
cd backend
# 可选：复制根目录 .env.example 为 backend/.env
uvicorn app.main:app --reload --port 8000
```

应用启动时会自动执行 `alembic upgrade head`。默认 `DATABASE_URL` 为 `postgresql+psycopg://ai_dream:ai_dream@localhost:5432/ai_dream`。

**3. 启动前端**

```sh
cd frontend
npm ci
npm run dev
```

- Backend: http://localhost:8000
- Frontend: http://localhost:5173

`.env.example` 列出本地开发常用变量；前端 API 地址默认 `http://localhost:8000/api`。

## Docker 全栈（CI / 联调）

需要把前后端也放进容器时，使用 `full` profile：

```sh
docker compose --profile full up --build
```

## M1 冒烟测试

本地前后端 + Docker 数据库：

```bash
docker compose up -d
curl http://localhost:8000/api/health
cd frontend && npm run e2e
```

全 Docker 栈：

```bash
docker compose --profile full up --build
curl http://localhost:8000/api/health
cd frontend && npm run e2e
```

也可以打开 http://localhost:5173，在 Dashboard 点击「创建 M1 示例学习计划」，确认页面生成 M1 教师闭环学习计划和下一步建议。

## 测试与检查

后端：

```sh
cd backend
ruff check .
pytest -v
```

前端：

```sh
cd frontend
npm ci
npm run typecheck
npm test
npm run e2e
```
