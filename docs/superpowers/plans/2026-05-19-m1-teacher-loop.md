# M1 教师闭环实施计划

> **给 agentic workers：** 必须使用子技能：`superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans`，按任务逐步执行本计划。步骤使用 checkbox（`- [ ]`）追踪。

**目标：** 以开源项目质量构建本地机器学习教学平台的第一条垂直闭环：本地 Compose stack、精美 Ant Design 应用外壳、教师型 Agent 流程、课程进度、作业、验收记录、Dashboard、CI 和丰富测试。

**架构：** M1 聚焦教学闭环，不实现完整实验执行。后端使用 FastAPI + PostgreSQL + SQLAlchemy/Alembic；前端使用 React + Vite + TypeScript + Ant Design。Agent 先用确定性的教学编排和 fake model provider 起步，先验证学习状态、API 契约和 UI，再在后续里程碑加入真实模型调用、Git 执行、Docker 实验和数据集下载。

**技术栈：** Python、FastAPI、SQLAlchemy、Alembic、PostgreSQL、pytest、ruff、React、Vite、TypeScript、Ant Design、Vitest、Playwright、GitHub Actions。

---

## 范围

本计划只实现 M1：

- `backend`、`frontend`、`postgres` 的本地 Docker Compose stack。
- 后端健康检查和数据库连接。
- SaaS-ready 的本地 tenant/workspace 上下文，固定为 `default`。
- 学习者画像、学习计划、模块、课程、作业、提交、验收、掌握度记录、学习事件和 Agent 观察。
- 教师型 Agent 接口：入学诊断、课程计划创建、课程开始、作业提交、评分和进度更新。
- 第一批精美 UI 页面：Dashboard、Chat、Learning Plan、Assignments、Settings。
- 覆盖 service 规则、API 路由、UI 状态和 M1 e2e smoke 的丰富测试。
- 开源项目文件：README、LICENSE、CONTRIBUTING、SECURITY、`.env.example`、`.editorconfig` 和 CI。

本计划暂不实现：

- 真实 Ollama 或在线模型调用。
- Git 凭据存储或 Git 项目导入。
- DockerRunner 实验。
- 数据集下载。
- Notebook 导出。

这些属于 M2/M3 计划。

## 文件结构

创建如下结构：

```text
.
├── .gitignore
├── .editorconfig
├── .env.example
├── CONTRIBUTING.md
├── LICENSE
├── docker-compose.yml
├── README.md
├── SECURITY.md
├── .github
│   └── workflows
│       └── ci.yml
├── backend
│   ├── alembic.ini
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── app
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── api
│   │   │   ├── __init__.py
│   │   │   ├── deps.py
│   │   │   └── routes
│   │   │       ├── __init__.py
│   │   │       ├── agent.py
│   │   │       ├── assignments.py
│   │   │       ├── health.py
│   │   │       └── learning.py
│   │   ├── core
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   └── tenant.py
│   │   ├── db
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   └── session.py
│   │   ├── models
│   │   │   ├── __init__.py
│   │   │   └── learning.py
│   │   ├── schemas
│   │   │   ├── __init__.py
│   │   │   └── learning.py
│   │   └── services
│   │       ├── __init__.py
│   │       ├── agent_service.py
│   │       ├── grading_service.py
│   │       └── learning_service.py
│   ├── migrations
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions
│   │       └── 0001_learning_loop.py
│   └── tests
│       ├── conftest.py
│       ├── test_agent_flow.py
│       └── test_learning_service.py
└── frontend
    ├── index.html
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    ├── e2e
    │   └── m1-teacher-loop.spec.ts
    ├── playwright.config.ts
    └── src
        ├── App.tsx
        ├── main.tsx
        ├── api
        │   └── client.ts
        ├── components
        │   ├── AppShell.tsx
        │   ├── StatusTag.tsx
        │   └── MetricCard.tsx
        ├── pages
        │   ├── AssignmentsPage.tsx
        │   ├── ChatPage.tsx
        │   ├── DashboardPage.tsx
        │   ├── LearningPlanPage.tsx
        │   └── SettingsPage.tsx
        ├── types
        │   └── learning.ts
        └── test
            ├── setup.ts
            └── dashboard.test.tsx
```

## 任务 1：项目脚手架

**文件：**
- 创建：`.gitignore`
- 创建：`.editorconfig`
- 创建：`.env.example`
- 创建：`README.md`
- 创建：`LICENSE`
- 创建：`CONTRIBUTING.md`
- 创建：`SECURITY.md`
- 创建：`docker-compose.yml`
- 创建：`backend/pyproject.toml`
- 创建：`backend/Dockerfile`
- 创建：`frontend/package.json`
- 创建：`frontend/tsconfig.json`
- 创建：`frontend/vite.config.ts`
- 创建：`frontend/playwright.config.ts`
- 创建：`frontend/index.html`
- 创建：`.github/workflows/ci.yml`

- [ ] **步骤 1：创建 `.gitignore`**

```gitignore
.DS_Store
.env
.env.*
!.env.example
__pycache__/
.pytest_cache/
.ruff_cache/
.venv/
dist/
node_modules/
coverage/
htmlcov/
artifacts/
datasets/
test-results/
playwright-report/
```

- [ ] **步骤 2：创建开源项目元数据**

`.editorconfig`:

```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
indent_style = space
indent_size = 2

[*.py]
indent_size = 4
```

`.env.example`:

```bash
APP_ENV=local
DEFAULT_TENANT_ID=default
DEFAULT_WORKSPACE_ID=default
DATABASE_URL=postgresql+psycopg://ai_dream:ai_dream@localhost:5432/ai_dream
```

`LICENSE`:

```text
MIT License

Copyright (c) 2026 AI Dream

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

`CONTRIBUTING.md`:

````markdown
# 贡献指南

## 开发流程

1. 创建聚焦的分支。
2. 实现前先新增或更新测试。
3. 运行后端和前端检查。
4. 每次变更只聚焦一个功能或修复。

## 后端检查

```bash
cd backend
ruff check .
pytest -v
````

## 前端检查

```bash
cd frontend
npm install
npm run typecheck
npm test
npm run e2e
```

## 提交风格

使用简短的祈使句提交信息，例如：

```text
feat: add teacher loop dashboard
test: cover assignment grading
```
```

`SECURITY.md`:

```markdown
# 安全

AI Dream 会在后续里程碑运行用户代码和 Agent 生成的代码。生成代码、Git 仓库、数据集和凭据都必须按不可信输入处理。

## 报告方式

目前请私下向项目维护者报告安全问题。

## 本地 Secret 规则

- 不要提交 `.env` 文件。
- 不要把 Git token 或模型 API key 粘贴进 prompt。
- 不要把 secrets 传入实验容器。
- Git 凭据在后续里程碑必须加密后再存储。
```

- [ ] **步骤 3：创建 `docker-compose.yml`**

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: ai_dream
      POSTGRES_PASSWORD: ai_dream
      POSTGRES_DB: ai_dream
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ai_dream -d ai_dream"]
      interval: 5s
      timeout: 5s
      retries: 10

  backend:
    build:
      context: ./backend
    environment:
      DATABASE_URL: postgresql+psycopg://ai_dream:ai_dream@postgres:5432/ai_dream
      APP_ENV: local
      DEFAULT_TENANT_ID: default
      DEFAULT_WORKSPACE_ID: default
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./backend:/app

  frontend:
    image: node:22-alpine
    working_dir: /app
    command: sh -c "npm install && npm run dev -- --host 0.0.0.0"
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
    depends_on:
      - backend

volumes:
  postgres_data:
```

- [ ] **步骤 4：创建 `backend/pyproject.toml`**

```toml
[project]
name = "ai-dream-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "alembic",
  "fastapi",
  "psycopg[binary]",
  "pydantic-settings",
  "sqlalchemy",
  "uvicorn[standard]",
]

[project.optional-dependencies]
dev = [
  "httpx",
  "pytest",
  "pytest-asyncio",
  "ruff",
]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]

[tool.ruff]
line-length = 100
target-version = "py311"
```

- [ ] **步骤 5：创建 `backend/Dockerfile`**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip
COPY pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir -e ".[dev]"

COPY . /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

- [ ] **步骤 6：创建前端 package 文件**

`frontend/package.json`:

```json
{
  "name": "ai-dream-frontend",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "test:watch": "vitest",
    "e2e": "playwright test"
  },
  "dependencies": {
    "@ant-design/icons": "latest",
    "@vitejs/plugin-react": "latest",
    "antd": "latest",
    "vite": "latest",
    "react": "latest",
    "react-dom": "latest",
    "recharts": "latest"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "latest",
    "@testing-library/react": "latest",
    "@testing-library/user-event": "latest",
    "@types/react": "latest",
    "@types/react-dom": "latest",
    "@playwright/test": "latest",
    "typescript": "latest",
    "vitest": "latest",
    "jsdom": "latest"
  }
}
```

`frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "useDefineForClassFields": true,
    "lib": ["DOM", "DOM.Iterable", "ES2022"],
    "allowJs": false,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "module": "ESNext",
    "moduleResolution": "Node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src"],
  "references": []
}
```

`frontend/vite.config.ts`:

```ts
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
  },
});
```

`frontend/playwright.config.ts`:

```ts
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  use: {
    baseURL: "http://localhost:5173",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
```

`frontend/index.html`:

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>AI Dream</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **步骤 7：创建 `README.md`**

````markdown
# AI Dream

本地机器学习教师 Agent 平台。

## M1 目标

M1 打通本地教学闭环：

- 入学诊断
- 课程计划
- 课程进度
- 作业提交
- 作业验收
- Dashboard 展示下一步学习建议

## 本地启动

```bash
docker compose up
````

Backend: http://localhost:8000

Frontend: http://localhost:5173

## 测试

```bash
cd backend && ruff check . && pytest -v
cd frontend && npm install && npm run typecheck && npm test
```
```

- [ ] **步骤 8：创建 GitHub Actions CI**

`.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: ai_dream
          POSTGRES_PASSWORD: ai_dream
          POSTGRES_DB: ai_dream
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U ai_dream -d ai_dream"
          --health-interval 5s
          --health-timeout 5s
          --health-retries 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install backend
        working-directory: backend
        run: pip install -e ".[dev]"
      - name: Lint backend
        working-directory: backend
        run: ruff check .
      - name: Test backend
        working-directory: backend
        run: pytest -v

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - name: Install frontend
        working-directory: frontend
        run: npm install
      - name: Typecheck frontend
        working-directory: frontend
        run: npm run typecheck
      - name: Test frontend
        working-directory: frontend
        run: npm test
      - name: Build frontend
        working-directory: frontend
        run: npm run build

  e2e-smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - name: Start stack
        run: docker compose up -d --build
      - name: Run migrations
        run: docker compose exec -T backend alembic upgrade head
      - name: Install frontend dependencies
        working-directory: frontend
        run: npm install
      - name: Install Playwright
        working-directory: frontend
        run: npx playwright install --with-deps chromium
      - name: Run M1 e2e smoke
        working-directory: frontend
        run: npm run e2e
```

- [ ] **步骤 9：运行脚手架检查**

运行：

```bash
docker compose config
```

预期：命令以 `0` 退出，并打印解析后的 compose 配置。

## 任务 2：后端应用、配置、数据库和租户上下文

**文件：**
- 创建：`backend/app/__init__.py`
- 创建：`backend/app/main.py`
- 创建：`backend/app/core/config.py`
- 创建：`backend/app/core/tenant.py`
- 创建：`backend/app/db/session.py`
- 创建：`backend/app/db/base.py`
- 创建：`backend/app/api/deps.py`
- 创建：`backend/app/api/routes/health.py`
- 创建：`backend/app/api/routes/__init__.py`
- 创建：`backend/app/api/__init__.py`
- 创建：`backend/tests/conftest.py`

- [ ] **步骤 1：创建后端 package 文件**

`backend/app/__init__.py`:

```python
```

`backend/app/api/__init__.py`:

```python
```

`backend/app/api/routes/__init__.py`:

```python
```

- [ ] **步骤 2：创建配置**

`backend/app/core/config.py`:

```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    database_url: str = "postgresql+psycopg://ai_dream:ai_dream@localhost:5432/ai_dream"
    default_tenant_id: str = "default"
    default_workspace_id: str = "default"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **步骤 3：创建租户上下文**

`backend/app/core/tenant.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class TenantContext:
    tenant_id: str
    workspace_id: str
```

- [ ] **步骤 4：创建数据库 session**

`backend/app/db/session.py`:

```python
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **步骤 5：创建 declarative base**

`backend/app/db/base.py`:

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

- [ ] **步骤 6：创建 API 依赖**

`backend/app/api/deps.py`:

```python
from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.tenant import TenantContext
from app.db.session import get_db


def get_tenant_context(settings: Settings = Depends(get_settings)) -> TenantContext:
    return TenantContext(
        tenant_id=settings.default_tenant_id,
        workspace_id=settings.default_workspace_id,
    )


def get_session(db: Session = Depends(get_db)) -> Generator[Session, None, None]:
    yield db
```

- [ ] **步骤 7：创建健康检查路由**

`backend/app/api/routes/health.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_session

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health(db: Session = Depends(get_session)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
```

- [ ] **步骤 8：创建 FastAPI 应用**

`backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router

app = FastAPI(title="AI Dream API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
```

- [ ] **步骤 9：创建 pytest 配置**

`backend/tests/conftest.py`:

```python
import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://ai_dream:ai_dream@localhost:5432/ai_dream",
)
```

- [ ] **步骤 10：验证后端导入**

运行：

```bash
cd backend && python -m compileall app
```

预期：命令以 `0` 退出。

## 任务 3：学习领域模型和数据库迁移

**文件：**
- 创建：`backend/app/models/__init__.py`
- 创建：`backend/app/models/learning.py`
- 创建：`backend/app/schemas/__init__.py`
- 创建：`backend/app/schemas/learning.py`
- 创建：`backend/alembic.ini`
- 创建：`backend/migrations/env.py`
- 创建：`backend/migrations/script.py.mako`
- 创建：`backend/migrations/versions/0001_learning_loop.py`
- 修改：`backend/app/db/base.py`

- [ ] **步骤 1：创建模型导出**

`backend/app/models/__init__.py`:

```python
from app.models.learning import (
    AgentObservation,
    Assignment,
    AssignmentReview,
    AssignmentSubmission,
    LearnerProfile,
    LearningEvent,
    LearningLesson,
    LearningModule,
    LearningPlan,
    LessonProgress,
    MasteryRecord,
)

__all__ = [
    "AgentObservation",
    "Assignment",
    "AssignmentReview",
    "AssignmentSubmission",
    "LearnerProfile",
    "LearningEvent",
    "LearningLesson",
    "LearningModule",
    "LearningPlan",
    "LessonProgress",
    "MasteryRecord",
]
```

- [ ] **步骤 2：创建学习模型**

`backend/app/models/learning.py`:

```python
from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def new_id() -> str:
    return str(uuid4())


class TenantMixin:
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class LearnerProfile(TenantMixin, TimestampMixin, Base):
    __tablename__ = "learner_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    display_name: Mapped[str] = mapped_column(String(120), default="本地学习者")
    goals: Mapped[list[str]] = mapped_column(JSON, default=list)
    background: Mapped[dict] = mapped_column(JSON, default=dict)
    preferences: Mapped[dict] = mapped_column(JSON, default=dict)


class LearningPlan(TenantMixin, TimestampMixin, Base):
    __tablename__ = "learning_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    title: Mapped[str] = mapped_column(String(200))
    goal: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    modules: Mapped[list["LearningModule"]] = relationship(back_populates="plan")


class LearningModule(TenantMixin, TimestampMixin, Base):
    __tablename__ = "learning_modules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    plan_id: Mapped[str] = mapped_column(ForeignKey("learning_plans.id"))
    title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer)
    plan: Mapped[LearningPlan] = relationship(back_populates="modules")
    lessons: Mapped[list["LearningLesson"]] = relationship(back_populates="module")


class LearningLesson(TenantMixin, TimestampMixin, Base):
    __tablename__ = "learning_lessons"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    module_id: Mapped[str] = mapped_column(ForeignKey("learning_modules.id"))
    title: Mapped[str] = mapped_column(String(200))
    objective: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer)
    module: Mapped[LearningModule] = relationship(back_populates="lessons")


class LessonProgress(TenantMixin, TimestampMixin, Base):
    __tablename__ = "lesson_progress"
    __table_args__ = (UniqueConstraint("tenant_id", "workspace_id", "lesson_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("learning_lessons.id"))
    status: Mapped[str] = mapped_column(String(32), default="not_started")
    mastery_score: Mapped[int] = mapped_column(Integer, default=0)
    next_action: Mapped[str] = mapped_column(String(200), default="开始学习")


class Assignment(TenantMixin, TimestampMixin, Base):
    __tablename__ = "assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("learning_lessons.id"))
    title: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(32))
    prompt: Mapped[str] = mapped_column(Text)
    rubric: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="assigned")


class AssignmentSubmission(TenantMixin, TimestampMixin, Base):
    __tablename__ = "assignment_submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    assignment_id: Mapped[str] = mapped_column(ForeignKey("assignments.id"))
    content: Mapped[str] = mapped_column(Text)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)


class AssignmentReview(TenantMixin, TimestampMixin, Base):
    __tablename__ = "assignment_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    submission_id: Mapped[str] = mapped_column(ForeignKey("assignment_submissions.id"))
    status: Mapped[str] = mapped_column(String(32))
    score: Mapped[int] = mapped_column(Integer)
    deterministic_results: Mapped[dict] = mapped_column(JSON, default=dict)
    llm_review: Mapped[dict] = mapped_column(JSON, default=dict)
    feedback: Mapped[str] = mapped_column(Text)


class MasteryRecord(TenantMixin, TimestampMixin, Base):
    __tablename__ = "mastery_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    knowledge_point: Mapped[str] = mapped_column(String(120))
    mastery_score: Mapped[int] = mapped_column(Integer)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)


class LearningEvent(TenantMixin, TimestampMixin, Base):
    __tablename__ = "learning_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    event_type: Mapped[str] = mapped_column(String(80))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)


class AgentObservation(TenantMixin, TimestampMixin, Base):
    __tablename__ = "agent_observations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    observation_type: Mapped[str] = mapped_column(String(80))
    summary: Mapped[str] = mapped_column(Text)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
```

- [ ] **步骤 3：更新 `backend/app/db/base.py` 导入**

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.models import learning  # noqa: E402,F401
```

- [ ] **步骤 4：创建 Pydantic schemas**

`backend/app/schemas/__init__.py`:

```python
```

`backend/app/schemas/learning.py`:

```python
from pydantic import BaseModel, Field


class IntakeRequest(BaseModel):
    goal: str = Field(min_length=3)
    background: str = Field(default="")
    weekly_hours: int = Field(default=5, ge=1, le=80)


class LessonSummary(BaseModel):
    id: str
    title: str
    objective: str
    status: str
    mastery_score: int
    next_action: str


class LearningPlanSummary(BaseModel):
    id: str
    title: str
    goal: str
    status: str
    lessons: list[LessonSummary]


class AssignmentSummary(BaseModel):
    id: str
    lesson_id: str
    title: str
    kind: str
    prompt: str
    status: str


class AssignmentSubmissionRequest(BaseModel):
    content: str = Field(min_length=1)


class AssignmentReviewSummary(BaseModel):
    id: str
    status: str
    score: int
    feedback: str
```

- [ ] **步骤 5：创建 Alembic 文件**

`backend/alembic.ini`:

```ini
[alembic]
script_location = migrations
prepend_sys_path = .
sqlalchemy.url = postgresql+psycopg://ai_dream:ai_dream@localhost:5432/ai_dream

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
```

`backend/migrations/env.py`:

```python
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.db.base import Base

config = context.config
config.set_main_option("sqlalchemy.url", get_settings().database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=get_settings().database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

`backend/migrations/script.py.mako`:

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

- [ ] **步骤 6：生成迁移**

运行：

```bash
cd backend && alembic revision --autogenerate -m "learning loop"
```

预期：Alembic 在 `backend/migrations/versions` 下创建迁移文件。

如果生成的文件名不是 `0001_learning_loop.py`，将其重命名，同时保留生成的迁移操作。

- [ ] **步骤 7：运行迁移**

运行：

```bash
docker compose up -d postgres
cd backend && alembic upgrade head
```

预期：命令以 `0` 退出。

## 任务 4：学习服务和验收服务

**文件：**
- 创建：`backend/app/services/learning_service.py`
- 创建：`backend/app/services/grading_service.py`
- 测试：`backend/tests/test_learning_service.py`

- [ ] **步骤 1：编写失败的 service 测试**

`backend/tests/test_learning_service.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.tenant import TenantContext
from app.db.base import Base
from app.services.learning_service import LearningService


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_create_default_plan_builds_first_lesson_and_assignment() -> None:
    db = make_session()
    tenant = TenantContext(tenant_id="default", workspace_id="default")

    service = LearningService(db)
    plan = service.create_default_plan(
        tenant=tenant,
        goal="我想学习机器学习并理解 PyTorch autograd",
        background="会 Python，机器学习基础薄弱",
        weekly_hours=6,
    )

    assert plan.status == "active"
    assert plan.modules[0].lessons[0].title == "张量和 autograd 入门"

    dashboard = service.get_dashboard(tenant)
    assert dashboard["next_action"] == "开始第一课：张量和 autograd 入门"
    assert dashboard["assigned_count"] == 1
```

- [ ] **步骤 2：运行测试，确认它失败**

运行：

```bash
cd backend && pytest tests/test_learning_service.py -v
```

预期：失败，因为 `LearningService` 还不存在。

- [ ] **步骤 3：实现 `LearningService`**

`backend/app/services/learning_service.py`:

```python
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.tenant import TenantContext
from app.models.learning import (
    Assignment,
    LearnerProfile,
    LearningEvent,
    LearningLesson,
    LearningModule,
    LearningPlan,
    LessonProgress,
)


class LearningService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_default_plan(
        self,
        tenant: TenantContext,
        goal: str,
        background: str,
        weekly_hours: int,
    ) -> LearningPlan:
        profile = LearnerProfile(
            tenant_id=tenant.tenant_id,
            workspace_id=tenant.workspace_id,
            goals=[goal],
            background={"summary": background, "weekly_hours": weekly_hours},
            preferences={"language": "zh-CN"},
        )
        plan = LearningPlan(
            tenant_id=tenant.tenant_id,
            workspace_id=tenant.workspace_id,
            title="机器学习教师计划",
            goal=goal,
            status="active",
        )
        module = LearningModule(
            tenant_id=tenant.tenant_id,
            workspace_id=tenant.workspace_id,
            plan=plan,
            title="PyTorch 基础",
            summary="从张量、autograd 和训练循环开始建立深度学习实践基础。",
            position=1,
        )
        lesson = LearningLesson(
            tenant_id=tenant.tenant_id,
            workspace_id=tenant.workspace_id,
            module=module,
            title="张量和 autograd 入门",
            objective="理解 tensor、requires_grad、loss.backward() 的作用。",
            content="本课通过最小线性函数例子解释 PyTorch 自动求导。",
            position=1,
        )
        self.db.add_all([profile, plan])
        self.db.flush()
        progress = LessonProgress(
            tenant_id=tenant.tenant_id,
            workspace_id=tenant.workspace_id,
            lesson_id=lesson.id,
            status="assignment_ready",
            mastery_score=1,
            next_action="完成 autograd 概念作业",
        )
        assignment = Assignment(
            tenant_id=tenant.tenant_id,
            workspace_id=tenant.workspace_id,
            lesson_id=lesson.id,
            title="解释 autograd 的作用",
            kind="concept",
            prompt="用自己的话解释 requires_grad=True 和 loss.backward() 分别做了什么。",
            rubric={
                "hard_gates": ["mentions_requires_grad", "mentions_backward"],
                "feedback_items": ["uses_own_words", "mentions_gradient"],
            },
            status="assigned",
        )
        event = LearningEvent(
            tenant_id=tenant.tenant_id,
            workspace_id=tenant.workspace_id,
            event_type="plan_created",
            payload={"goal": goal, "weekly_hours": weekly_hours},
        )
        self.db.add_all([progress, assignment, event])
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def get_active_plan(self, tenant: TenantContext) -> LearningPlan | None:
        stmt = (
            select(LearningPlan)
            .where(LearningPlan.tenant_id == tenant.tenant_id)
            .where(LearningPlan.workspace_id == tenant.workspace_id)
            .where(LearningPlan.status == "active")
        )
        return self.db.scalar(stmt)

    def get_dashboard(self, tenant: TenantContext) -> dict:
        assigned_count = self.db.scalar(
            select(Assignment)
            .where(Assignment.tenant_id == tenant.tenant_id)
            .where(Assignment.workspace_id == tenant.workspace_id)
            .where(Assignment.status == "assigned")
            .limit(1)
        )
        plan = self.get_active_plan(tenant)
        return {
            "active_plan_title": plan.title if plan else "",
            "next_action": "开始第一课：张量和 autograd 入门" if plan else "创建学习计划",
            "assigned_count": 1 if assigned_count else 0,
            "mastery_average": 1 if plan else 0,
        }
```

- [ ] **步骤 4：实现验收服务**

`backend/app/services/grading_service.py`:

```python
from sqlalchemy.orm import Session

from app.core.tenant import TenantContext
from app.models.learning import (
    AgentObservation,
    Assignment,
    AssignmentReview,
    AssignmentSubmission,
    LearningEvent,
    MasteryRecord,
)


class GradingService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def submit_and_grade(
        self,
        tenant: TenantContext,
        assignment: Assignment,
        content: str,
    ) -> AssignmentReview:
        submission = AssignmentSubmission(
            tenant_id=tenant.tenant_id,
            workspace_id=tenant.workspace_id,
            assignment_id=assignment.id,
            content=content,
            evidence={"source": "chat"},
        )
        normalized = content.lower()
        mentions_requires_grad = "requires_grad" in normalized
        mentions_backward = "backward" in normalized
        passed = mentions_requires_grad and mentions_backward
        deterministic_results = {
            "mentions_requires_grad": mentions_requires_grad,
            "mentions_backward": mentions_backward,
        }
        llm_review = {
            "summary": "回答覆盖了 autograd 的核心触发条件。" if passed else "回答缺少关键概念。",
            "needs_followup": not passed,
        }
        review = AssignmentReview(
            tenant_id=tenant.tenant_id,
            workspace_id=tenant.workspace_id,
            submission_id=submission.id,
            status="passed" if passed else "needs_revision",
            score=90 if passed else 45,
            deterministic_results=deterministic_results,
            llm_review=llm_review,
            feedback=(
                "通过。你已经说明 requires_grad 和 backward 的核心作用。"
                if passed
                else "需要修改。回答必须说明 requires_grad=True 会追踪计算，loss.backward() 会反向传播梯度。"
            ),
        )
        assignment.status = "completed" if passed else "needs_revision"
        mastery = MasteryRecord(
            tenant_id=tenant.tenant_id,
            workspace_id=tenant.workspace_id,
            knowledge_point="autograd",
            mastery_score=3 if passed else 1,
            evidence={"assignment_id": assignment.id, "review_status": review.status},
        )
        observation = AgentObservation(
            tenant_id=tenant.tenant_id,
            workspace_id=tenant.workspace_id,
            observation_type="assignment_review",
            summary="用户已初步理解 autograd。" if passed else "用户需要复习 autograd 基础。",
            evidence={"assignment_id": assignment.id},
        )
        event = LearningEvent(
            tenant_id=tenant.tenant_id,
            workspace_id=tenant.workspace_id,
            event_type="assignment_reviewed",
            payload={"assignment_id": assignment.id, "status": review.status},
        )
        self.db.add_all([submission, review, mastery, observation, event])
        self.db.commit()
        self.db.refresh(review)
        return review
```

- [ ] **步骤 5：运行 service 测试**

运行：

```bash
cd backend && pytest tests/test_learning_service.py -v
```

预期：通过。

## 任务 5：Agent 和学习 API 路由

**文件：**
- 创建：`backend/app/services/agent_service.py`
- 创建：`backend/app/api/routes/agent.py`
- 创建：`backend/app/api/routes/learning.py`
- 创建：`backend/app/api/routes/assignments.py`
- 修改：`backend/app/main.py`
- 测试：`backend/tests/test_agent_flow.py`

- [ ] **步骤 1：编写失败的 API 流程测试**

`backend/tests/test_agent_flow.py`:

```python
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.deps import get_session
from app.db.base import Base
from app.main import app


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_teacher_loop_creates_plan_and_returns_dashboard() -> None:
    db = make_session()

    def override_session():
        yield db

    app.dependency_overrides[get_session] = override_session
    client = TestClient(app)

    response = client.post(
        "/api/agent/intake",
        json={
            "goal": "我想学机器学习并能独立跑 PyTorch 实验",
            "background": "会 Python",
            "weekly_hours": 5,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "机器学习教师计划"
    assert data["lessons"][0]["status"] == "assignment_ready"

    dashboard = client.get("/api/learning/dashboard")
    assert dashboard.status_code == 200
    assert dashboard.json()["assigned_count"] == 1

    app.dependency_overrides.clear()
```

- [ ] **步骤 2：运行 API 测试，确认它失败**

运行：

```bash
cd backend && pytest tests/test_agent_flow.py -v
```

预期：失败，因为路由还不存在。

- [ ] **步骤 3：实现 Agent service**

`backend/app/services/agent_service.py`:

```python
from sqlalchemy.orm import Session

from app.core.tenant import TenantContext
from app.schemas.learning import IntakeRequest, LearningPlanSummary, LessonSummary
from app.services.learning_service import LearningService


class AgentService:
    def __init__(self, db: Session) -> None:
        self.learning_service = LearningService(db)

    def run_intake(self, tenant: TenantContext, request: IntakeRequest) -> LearningPlanSummary:
        plan = self.learning_service.create_default_plan(
            tenant=tenant,
            goal=request.goal,
            background=request.background,
            weekly_hours=request.weekly_hours,
        )
        lessons = []
        for module in plan.modules:
            for lesson in module.lessons:
                lessons.append(
                    LessonSummary(
                        id=lesson.id,
                        title=lesson.title,
                        objective=lesson.objective,
                        status="assignment_ready",
                        mastery_score=1,
                        next_action="完成 autograd 概念作业",
                    )
                )
        return LearningPlanSummary(
            id=plan.id,
            title=plan.title,
            goal=plan.goal,
            status=plan.status,
            lessons=lessons,
        )
```

- [ ] **步骤 4：实现路由**

`backend/app/api/routes/agent.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_session, get_tenant_context
from app.core.tenant import TenantContext
from app.schemas.learning import IntakeRequest, LearningPlanSummary
from app.services.agent_service import AgentService

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/intake", response_model=LearningPlanSummary)
def intake(
    request: IntakeRequest,
    db: Session = Depends(get_session),
    tenant: TenantContext = Depends(get_tenant_context),
) -> LearningPlanSummary:
    return AgentService(db).run_intake(tenant, request)
```

`backend/app/api/routes/learning.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_session, get_tenant_context
from app.core.tenant import TenantContext
from app.services.learning_service import LearningService

router = APIRouter(prefix="/learning", tags=["learning"])


@router.get("/dashboard")
def dashboard(
    db: Session = Depends(get_session),
    tenant: TenantContext = Depends(get_tenant_context),
) -> dict:
    return LearningService(db).get_dashboard(tenant)
```

`backend/app/api/routes/assignments.py`:

```python
from fastapi import APIRouter

router = APIRouter(prefix="/assignments", tags=["assignments"])
```

- [ ] **步骤 5：注册路由**

修改 `backend/app/main.py`：

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.agent import router as agent_router
from app.api.routes.assignments import router as assignments_router
from app.api.routes.health import router as health_router
from app.api.routes.learning import router as learning_router

app = FastAPI(title="AI Dream API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(agent_router, prefix="/api")
app.include_router(learning_router, prefix="/api")
app.include_router(assignments_router, prefix="/api")
```

- [ ] **步骤 6：运行 API 测试**

运行：

```bash
cd backend && pytest tests/test_agent_flow.py -v
```

预期：通过。

## 任务 6：前端应用外壳和 API Client

**文件：**
- 创建：`frontend/src/main.tsx`
- 创建：`frontend/src/App.tsx`
- 创建：`frontend/src/api/client.ts`
- 创建：`frontend/src/types/learning.ts`
- 创建：`frontend/src/components/AppShell.tsx`
- 创建：`frontend/src/components/MetricCard.tsx`
- 创建：`frontend/src/components/StatusTag.tsx`
- 创建：`frontend/src/test/setup.ts`

- [ ] **步骤 1：创建前端类型**

`frontend/src/types/learning.ts`:

```ts
export interface LessonSummary {
  id: string;
  title: string;
  objective: string;
  status: "not_started" | "in_progress" | "assignment_ready" | "submitted" | "needs_revision" | "mastered" | "review_scheduled";
  mastery_score: number;
  next_action: string;
}

export interface LearningPlanSummary {
  id: string;
  title: string;
  goal: string;
  status: string;
  lessons: LessonSummary[];
}

export interface DashboardSummary {
  active_plan_title: string;
  next_action: string;
  assigned_count: number;
  mastery_average: number;
}
```

- [ ] **步骤 2：创建 API client**

`frontend/src/api/client.ts`:

```ts
import type { DashboardSummary, LearningPlanSummary } from "../types/learning";

const API_BASE = "http://localhost:8000/api";

export async function startIntake(payload: {
  goal: string;
  background: string;
  weekly_hours: number;
}): Promise<LearningPlanSummary> {
  const response = await fetch(`${API_BASE}/agent/intake`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("创建学习计划失败");
  }
  return response.json();
}

export async function fetchDashboard(): Promise<DashboardSummary> {
  const response = await fetch(`${API_BASE}/learning/dashboard`);
  if (!response.ok) {
    throw new Error("加载 Dashboard 失败");
  }
  return response.json();
}
```

- [ ] **步骤 3：创建可复用 UI 组件**

`frontend/src/components/MetricCard.tsx`:

```tsx
import { Card, Statistic } from "antd";
import type { ReactNode } from "react";

interface MetricCardProps {
  title: string;
  value: string | number;
  suffix?: ReactNode;
}

export function MetricCard({ title, value, suffix }: MetricCardProps) {
  return (
    <Card bordered={false} style={{ boxShadow: "0 8px 24px rgba(15, 23, 42, 0.06)" }}>
      <Statistic title={title} value={value} suffix={suffix} />
    </Card>
  );
}
```

`frontend/src/components/StatusTag.tsx`:

```tsx
import { Tag } from "antd";

const statusConfig: Record<string, { color: string; label: string }> = {
  assignment_ready: { color: "processing", label: "待完成作业" },
  mastered: { color: "success", label: "已掌握" },
  needs_revision: { color: "warning", label: "需要修改" },
  not_started: { color: "default", label: "未开始" },
};

export function StatusTag({ status }: { status: string }) {
  const config = statusConfig[status] ?? { color: "default", label: status };
  return <Tag color={config.color}>{config.label}</Tag>;
}
```

- [ ] **步骤 4：创建应用外壳**

`frontend/src/components/AppShell.tsx`:

```tsx
import {
  BookOutlined,
  CheckSquareOutlined,
  DashboardOutlined,
  MessageOutlined,
  SettingOutlined,
} from "@ant-design/icons";
import { Layout, Menu, Typography } from "antd";
import type { ReactNode } from "react";

const { Header, Sider, Content } = Layout;

interface AppShellProps {
  activeKey: string;
  children: ReactNode;
  onNavigate: (key: string) => void;
}

export function AppShell({ activeKey, children, onNavigate }: AppShellProps) {
  return (
    <Layout style={{ minHeight: "100vh", background: "#f5f7fb" }}>
      <Sider width={248} style={{ background: "#111827" }}>
        <div style={{ padding: 24 }}>
          <Typography.Title level={4} style={{ color: "white", margin: 0 }}>
            AI Dream
          </Typography.Title>
          <Typography.Text style={{ color: "#9ca3af" }}>机器学习教师 Agent</Typography.Text>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[activeKey]}
          onClick={(item) => onNavigate(item.key)}
          items={[
            { key: "dashboard", icon: <DashboardOutlined />, label: "Dashboard" },
            { key: "chat", icon: <MessageOutlined />, label: "Agent 对话" },
            { key: "learning", icon: <BookOutlined />, label: "学习计划" },
            { key: "assignments", icon: <CheckSquareOutlined />, label: "作业验收" },
            { key: "settings", icon: <SettingOutlined />, label: "设置" },
          ]}
        />
      </Sider>
      <Layout>
        <Header style={{ background: "white", borderBottom: "1px solid #eef2f7" }}>
          <Typography.Text strong>本地默认租户：default / default</Typography.Text>
        </Header>
        <Content style={{ padding: 32 }}>{children}</Content>
      </Layout>
    </Layout>
  );
}
```

- [ ] **步骤 5：创建应用入口**

`frontend/src/main.tsx`:

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import "antd/dist/reset.css";
import App from "./App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

`frontend/src/test/setup.ts`:

```ts
import "@testing-library/jest-dom/vitest";
```

## 任务 7：前端 M1 页面

**文件：**
- 创建：`frontend/src/pages/DashboardPage.tsx`
- 创建：`frontend/src/pages/ChatPage.tsx`
- 创建：`frontend/src/pages/LearningPlanPage.tsx`
- 创建：`frontend/src/pages/AssignmentsPage.tsx`
- 创建：`frontend/src/pages/SettingsPage.tsx`
- 修改：`frontend/src/App.tsx`
- 测试：`frontend/src/test/dashboard.test.tsx`

- [ ] **步骤 1：创建 Dashboard 页面**

`frontend/src/pages/DashboardPage.tsx`:

```tsx
import { Alert, Button, Card, Col, Row, Space, Typography } from "antd";
import { useEffect, useState } from "react";
import { fetchDashboard, startIntake } from "../api/client";
import { MetricCard } from "../components/MetricCard";
import type { DashboardSummary } from "../types/learning";

export function DashboardPage() {
  const [dashboard, setDashboard] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(false);

  async function loadDashboard() {
    try {
      setDashboard(await fetchDashboard());
    } catch {
      setDashboard(null);
    }
  }

  async function createPlan() {
    setLoading(true);
    await startIntake({
      goal: "我想系统学习机器学习，并从 PyTorch 的 tensor 和 autograd 开始。",
      background: "会 Python，但机器学习基础薄弱。",
      weekly_hours: 6,
    });
    await loadDashboard();
    setLoading(false);
  }

  useEffect(() => {
    void loadDashboard();
  }, []);

  return (
    <Space direction="vertical" size={24} style={{ width: "100%" }}>
      <div>
        <Typography.Title level={2} style={{ marginBottom: 4 }}>
          今日学习面板
        </Typography.Title>
        <Typography.Text type="secondary">
          你的教师 Agent 会跟踪课程、作业和掌握程度，并给出下一步建议。
        </Typography.Text>
      </div>

      <Row gutter={16}>
        <Col span={8}>
          <MetricCard title="待完成作业" value={dashboard?.assigned_count ?? 0} />
        </Col>
        <Col span={8}>
          <MetricCard title="平均掌握度" value={dashboard?.mastery_average ?? 0} suffix="/ 5" />
        </Col>
        <Col span={8}>
          <MetricCard title="当前课程" value={dashboard?.active_plan_title || "未创建"} />
        </Col>
      </Row>

      <Card bordered={false}>
        <Alert
          type="info"
          showIcon
          message="下一步建议"
          description={dashboard?.next_action || "先创建一个学习计划。"}
        />
        <Button type="primary" loading={loading} onClick={createPlan} style={{ marginTop: 16 }}>
          创建 M1 示例学习计划
        </Button>
      </Card>
    </Space>
  );
}
```

- [ ] **步骤 2：创建带精美空状态的辅助页面**

`frontend/src/pages/ChatPage.tsx`:

```tsx
import { Card, Empty, Typography } from "antd";

export function ChatPage() {
  return (
    <Card bordered={false}>
      <Typography.Title level={3}>Agent 对话</Typography.Title>
      <Empty description="M1 先打通入学诊断和课程闭环，完整聊天流在后续任务中增强。" />
    </Card>
  );
}
```

`frontend/src/pages/LearningPlanPage.tsx`:

```tsx
import { Card, Empty, Typography } from "antd";

export function LearningPlanPage() {
  return (
    <Card bordered={false}>
      <Typography.Title level={3}>学习计划</Typography.Title>
      <Empty description="创建学习计划后，这里展示课程、章节、掌握程度和复习建议。" />
    </Card>
  );
}
```

`frontend/src/pages/AssignmentsPage.tsx`:

```tsx
import { Card, Empty, Typography } from "antd";

export function AssignmentsPage() {
  return (
    <Card bordered={false}>
      <Typography.Title level={3}>作业验收</Typography.Title>
      <Empty description="这里会展示作业提交、验收结果、评分和重做建议。" />
    </Card>
  );
}
```

`frontend/src/pages/SettingsPage.tsx`:

```tsx
import { Card, Descriptions, Typography } from "antd";

export function SettingsPage() {
  return (
    <Card bordered={false}>
      <Typography.Title level={3}>设置</Typography.Title>
      <Descriptions bordered column={1}>
        <Descriptions.Item label="Tenant">default</Descriptions.Item>
        <Descriptions.Item label="Workspace">default</Descriptions.Item>
        <Descriptions.Item label="数据管理">M4 增强为可清理和导出本地数据</Descriptions.Item>
      </Descriptions>
    </Card>
  );
}
```

- [ ] **步骤 3：串联应用导航**

`frontend/src/App.tsx`:

```tsx
import { useState } from "react";
import { AppShell } from "./components/AppShell";
import { AssignmentsPage } from "./pages/AssignmentsPage";
import { ChatPage } from "./pages/ChatPage";
import { DashboardPage } from "./pages/DashboardPage";
import { LearningPlanPage } from "./pages/LearningPlanPage";
import { SettingsPage } from "./pages/SettingsPage";

export default function App() {
  const [activeKey, setActiveKey] = useState("dashboard");

  const pages: Record<string, JSX.Element> = {
    dashboard: <DashboardPage />,
    chat: <ChatPage />,
    learning: <LearningPlanPage />,
    assignments: <AssignmentsPage />,
    settings: <SettingsPage />,
  };

  return (
    <AppShell activeKey={activeKey} onNavigate={setActiveKey}>
      {pages[activeKey] ?? pages.dashboard}
    </AppShell>
  );
}
```

- [ ] **步骤 4：添加 dashboard 测试**

`frontend/src/test/dashboard.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { DashboardPage } from "../pages/DashboardPage";

vi.mock("../api/client", () => ({
  fetchDashboard: async () => ({
    active_plan_title: "机器学习教师计划",
    next_action: "开始第一课：张量和 autograd 入门",
    assigned_count: 1,
    mastery_average: 1,
  }),
  startIntake: async () => ({
    id: "plan-1",
    title: "机器学习教师计划",
    goal: "学习机器学习",
    status: "active",
    lessons: [],
  }),
}));

describe("DashboardPage", () => {
  it("renders teacher loop metrics", async () => {
    render(<DashboardPage />);
    expect(await screen.findByText("今日学习面板")).toBeInTheDocument();
    expect(await screen.findByText("开始第一课：张量和 autograd 入门")).toBeInTheDocument();
  });
});
```

- [ ] **步骤 5：运行前端测试**

运行：

```bash
cd frontend && npm install && npm test
```

预期：通过。

## 任务 8：M1 端到端冒烟检查

**文件：**
- 创建：`frontend/e2e/m1-teacher-loop.spec.ts`
- 修改：`README.md`

- [ ] **步骤 1：创建 Playwright M1 e2e 测试**

`frontend/e2e/m1-teacher-loop.spec.ts`:

```ts
import { expect, test } from "@playwright/test";

test("M1 teacher loop creates a learning plan from dashboard", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("今日学习面板")).toBeVisible();
  await expect(page.getByText("机器学习教师 Agent")).toBeVisible();

  await page.getByRole("button", { name: "创建 M1 示例学习计划" }).click();

  await expect(page.getByText("开始第一课：张量和 autograd 入门")).toBeVisible();
  await expect(page.getByText("机器学习教师计划")).toBeVisible();
});
```

- [ ] **步骤 2：运行完整 stack**

运行：

```bash
docker compose up --build
```

预期：

- Postgres health check 通过。
- Backend 在 `http://localhost:8000` 启动。
- Frontend 在 `http://localhost:5173` 启动。

- [ ] **步骤 3：应用迁移**

运行：

```bash
docker compose exec backend alembic upgrade head
```

预期：迁移命令以 `0` 退出。

- [ ] **步骤 4：验证 API 健康检查**

运行：

```bash
curl http://localhost:8000/api/health
```

预期：

```json
{"status":"ok"}
```

- [ ] **步骤 5：验证入学诊断 API**

运行：

```bash
curl -X POST http://localhost:8000/api/agent/intake \
  -H "Content-Type: application/json" \
  -d '{"goal":"我想学习机器学习","background":"会 Python","weekly_hours":5}'
```

预期：JSON response 包含 `"title":"机器学习教师计划"`，并且至少有一个 lesson。

- [ ] **步骤 6：手动验证前端**

打开：

```text
http://localhost:5173
```

预期：

- Sidebar 正常渲染。
- Dashboard 渲染精美卡片。
- 点击“创建 M1 示例学习计划”后 Dashboard 状态更新。
- Learning Plan、Assignments、Chat、Settings 页面不出现空白屏。

- [ ] **步骤 7：运行 Playwright e2e 冒烟测试**

运行：

```bash
cd frontend && npm run e2e
```

预期：通过，并显示 `M1 teacher loop creates a learning plan from dashboard`。

- [ ] **步骤 8：更新 README 冒烟测试章节**

添加到 `README.md`：

````markdown
## M1 冒烟测试

```bash
docker compose up --build
docker compose exec backend alembic upgrade head
curl http://localhost:8000/api/health
cd frontend && npm run e2e
```

然后打开 http://localhost:5173，并从 Dashboard 创建 M1 示例学习计划。
````

## 自查清单

- [ ] M1 对应设计文档中的第一个内部里程碑。
- [ ] 后端依赖和数据库记录都包含默认 tenant/workspace。
- [ ] 教师闭环保留 learning plan、lesson progress、assignment、review、mastery、events 和 observations。
- [ ] 确定性评分字段和 LLM-style review 字段是分离的。
- [ ] 前端使用 Ant Design，并且有精美应用外壳，不是裸页面。
- [ ] M2/M3 关注点没有在 M1 中实现，但保留了扩展点。
- [ ] 后端测试和前端测试都有明确命令。
- [ ] 完整 stack 冒烟测试有明确命令。
