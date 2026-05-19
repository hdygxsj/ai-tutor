# 贡献指南

感谢你参与 AI Dream。请保持变更小而清晰，优先补充测试，并在提交前运行相关检查。

## 开发流程

1. 从最新主分支创建功能分支。
2. 在本地完成实现和测试。
3. 确认没有提交 `.env`、凭据、密钥、模型私有数据或本地运行产物。
4. 发起 PR，并说明变更目的、测试结果和已知风险。

## 后端检查

```sh
cd backend && ruff check . && pytest -v
```

## 前端检查

```sh
cd frontend && npm ci && npm run typecheck && npm test && npm run e2e
```

## 提交信息示例

- `feat: add teacher loop dashboard`
- `test: cover assignment grading`

请使用清晰的英文提交前缀和简短描述，让审阅者能快速理解变更意图。
