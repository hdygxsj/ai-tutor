# AI Dream

AI Dream 是一个本地机器学习教师 Agent 平台。M1 阶段聚焦 FastAPI、PostgreSQL、React/Vite 和 Ant Design 组成的本地教师闭环。

## M1 目标

- 提供可本地启动的后端、数据库和前端开发环境。
- 建立教师循环所需的项目边界和工程检查。
- 为后续课程、作业、批改和反馈功能保留清晰的扩展入口。

## 本地启动

Compose 默认使用内置的本地开发环境变量，直接启动服务即可：

```sh
docker compose up
```

- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- PostgreSQL: localhost:5432

`.env.example` 用于本地非 Compose 运行时参考变量名称和默认值。

## M1 冒烟测试

```bash
docker compose up --build
docker compose exec backend alembic upgrade head
curl http://localhost:8000/api/health
cd frontend && npm run e2e
```

也可以打开 http://localhost:5173，在 Dashboard 点击“创建 M1 示例学习计划”，确认页面生成 M1 教师闭环学习计划和下一步建议。

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
