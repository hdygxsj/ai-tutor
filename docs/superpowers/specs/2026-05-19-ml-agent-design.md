# 本地机器学习 Agent 设计文档

## 目标

构建一个本地部署的机器学习教学与实验平台。第一期要让用户可以在精美的 Web 界面里和 Agent 对话，按计划学习机器学习相关主题，设计实验，在 Docker 里运行实验，并查看实验结果和可视化图表。PyTorch 是第一期重点学习内容之一，但不是系统未来的全部边界。

这个项目同时要保留后续演进成 SaaS 的路径，但第一期不是 SaaS 产品。第一期定位为单用户本地产品，但不是粗糙 MVP。第一期就要做到界面精美、学习体验完整、实验闭环清晰，并且模块边界要按后续可产品化的方式设计。

## 第一期范围

第一期是增强版本地产品。

包含：

- Web 界面：聊天、学习计划、实验管理、实验详情、日志、产物和图表。
- 精美前端 UI：提供高质量应用布局、导航、表单、卡片、弹窗、状态提示、空状态、加载状态和错误状态，不只是裸页面或简单 MVP。
- FastAPI 后端：提供 Agent、学习、实验、产物和可视化 API。
- PostgreSQL：通过 Docker Compose 在本地启动，不使用 SQLite。
- Docker 实验执行：实验在隔离容器里运行，不直接在后端进程里运行。
- 模型提供方抽象：同时支持本地模型和在线模型 API。
- Ollama：支持调用本地模型。
- 在线模型 API：通过统一 provider 接口支持，第一期用环境变量配置。
- 内置机器学习实验模板库，第一期优先覆盖 PyTorch。
- Git 项目导入：用户可以在自己的 IDE 里写代码并推送到 Git，系统从 Git 拉取代码，在 Docker 中运行指定实验入口。
- Agent 初始化模板代码：Agent 可以根据学习目标或实验目标生成一份可运行的模板项目，初始化 Git 仓库或提交到已配置仓库，作为用户继续开发和实验的起点。
- 教师型 Agent：能够制定课程、管理学习进度、布置作业、验收作业、指出薄弱点，并根据学习表现调整后续学习计划。
- 公开数据集准备：Agent 可以根据课程或实验目标，从公开来源选择、下载、缓存、校验并登记数据集，供实验容器使用。
- 本地任务系统：Git 拉取、数据集下载、实验运行和 Notebook 导出都通过本地 Job 管理，支持状态、日志、取消和失败记录。
- 保存 checkpoint、模型文件、配置、指标、日志和生成文件。
- 可视化 loss、accuracy、learning rate、混淆矩阵、样本预测和实验对比。
- 支持把课程或实验导出成 Notebook。
- SaaS-ready 多租户边界：本地第一期默认使用 `default` tenant/workspace，但数据模型、请求上下文、任务上下文和 artifact 路径按多租户方式预留。
- 为后续 SaaS 保留接口：云端模型、云端 Runner、多用户数据归属、对象存储。
- 开源项目标准：第一期就包含 README、LICENSE、贡献指南、开发环境说明、测试说明、代码规范、CI 配置和安全说明。
- 丰富测试体系：后端单元测试、服务集成测试、前端组件测试、API 测试和端到端 e2e 测试都要进入第一期质量门禁。

第一期不包含：

- 用户账号、登录、计费、订阅和租户管理。
- 云端实验 Worker。
- Kubernetes、Firecracker、gVisor 等云端沙箱基础设施。
- 云端 SaaS 连接客户本地 Ollama 的 Connector。
- 完整在线 IDE。第一期只做代码浏览、实验入口配置和运行编排，不做浏览器内完整代码编辑器。
- 团队协作功能。

## 第一期内部里程碑

第一期范围较大，实施时必须拆成可验收的内部里程碑，避免一直堆功能但没有完整闭环。

### M1：本地基础和教师闭环

目标是先证明“Agent 像老师一样教我”的核心体验。

必须完成：

- Docker Compose 启动 frontend、backend、Postgres。
- 精美 UI 基础布局：Dashboard、Chat、Learning Plan、Assignments。
- 入学诊断、课程计划、lesson 状态、assignment 状态、mastery score。
- 一个最小课程，例如“PyTorch 张量和 autograd 入门”。
- 一个概念作业和一个代码作业。
- 作业提交、验收、反馈、进度更新。

验收标准：

- 用户能完成一次从入学诊断到作业通过的完整学习闭环。
- Dashboard 能展示当前课程、待办作业、掌握程度和下一步建议。

### M2：代码和实验闭环

目标是证明平台能生成代码、进入 Git、在 Docker 中运行，并用结果验收作业。

必须完成：

- Git 凭据和本地/公开仓库接入。
- Agent 初始化模板项目，生成变更预览，用户确认后创建 commit。
- DockerRunner 运行最小 PyTorch 实验。
- 结构化 metrics、logs、artifacts。
- 实验作业验收：确定性检查 + Agent 解释反馈。

验收标准：

- 用户可以让 Agent 初始化一个模板项目，运行实验，并看到指标图表和验收结果。

### M3：数据集、模板和可视化增强

目标是扩展到更真实的课程和实验。

必须完成：

- Dataset Service 支持公开小数据集下载、缓存、校验和只读挂载。
- 内置多个 PyTorch 模板。
- 实验对比、混淆矩阵、预测样本、checkpoint 管理。
- Notebook 导出。

验收标准：

- 用户可以学习一个使用公开数据集的完整课程，完成实验、查看可视化、导出 Notebook。

### M4：产品化打磨

目标是让第一期达到可长期使用的本地产品质量。

必须完成：

- UI 细节打磨：空状态、错误状态、loading、toast、确认弹窗、视觉统一。
- 数据管理页面：导出、清理学习记录、清理实验日志、清理代码摘要。
- 本地启动文档和端到端冒烟测试。
- 开源项目文档：README、CONTRIBUTING、LICENSE、SECURITY、开发指南和测试指南。
- CI 质量门禁：lint、type check、backend tests、frontend tests、e2e smoke test。

验收标准：

- 新用户按文档启动后，可以完成 M1 到 M3 的核心流程。

## 产品形态

应用包含四条主要用户流程。

### Agent 对话

用户在浏览器里和 Agent 对话。Agent 可以回答机器学习、深度学习、工程实践和实验设计问题，解释代码、追问背景、生成学习计划、建议实验，并帮助解读实验结果。

Agent 应该能感知系统里的可用工具和数据，包括学习计划、实验模板、历史实验、指标、日志和产物。

Agent 还应该能帮助用户创建代码起点：

- 根据学习目标选择合适模板，例如 PyTorch 线性回归、CNN、优化器对比或用户自定义实验骨架。
- 生成标准项目结构，包括训练脚本、配置文件、依赖文件、指标输出约定、README 和最小测试。
- 初始化 Git 仓库，或者把模板代码提交到用户已配置的远程仓库。
- 生成初始 commit，并记录 commit hash，后续实验从这个 commit 或用户后续 commit 运行。
- 在写入或推送代码前让用户确认目标仓库、分支、文件变更和 commit message。

Agent 还应该能帮助准备数据集：

- 根据课程或实验目标推荐合适的公开数据集。
- 解释数据集适合学习什么概念，例如分类、回归、过拟合、数据清洗、特征工程或模型评估。
- 在下载前展示数据集来源、大小、许可、引用信息和预计下载时间。
- 调用 Dataset Service 下载、缓存、校验并登记数据集。
- 生成使用该数据集的 dataloader、预处理代码和实验说明。
- 如果数据集太大、许可不合适或网络不可用，推荐轻量替代数据集或 synthetic dataset。

### 教师型 Agent

第一期 Agent 的核心体验不是普通聊天机器人，而是一个机器学习老师。它要能围绕用户目标持续教学、跟踪进度、验收作业，并推动用户真正学会。

教师型 Agent 能力：

- 入学诊断：询问用户背景、数学基础、Python 基础、机器学习经验、目标和可投入时间。
- 课程设计：生成分阶段课程，包括章节、学习目标、预计时间、前置知识、练习和实验。
- 课程进度管理：记录每节课状态，例如未开始、学习中、待提交作业、待验收、已掌握、需要复习。
- 讲解与追问：不只是给答案，还要通过提问检查理解，例如让用户解释 loss、梯度、过拟合等概念。
- 作业布置：每节课可以包含代码作业、概念问答、实验任务和结果分析任务。
- 作业验收：根据用户提交的答案、代码、Git commit、实验指标和日志进行检查。
- 反馈和评分：给出通过/未通过、评分、具体问题、修改建议和下一步复习材料。
- 个性化调整：根据作业表现、实验结果和用户反馈调整后续课程难度。
- 学习复盘：阶段性总结已经掌握的内容、薄弱点、推荐复习和下一阶段目标。

作业验收可以使用多种证据：

- 用户在聊天中提交的文字回答。
- 用户 Git 项目的代码 diff 或指定 commit。
- 实验运行结果，包括 metrics、logs、artifacts 和测试结果。
- Notebook 导出内容或用户补充说明。

第一期需要把教学状态持久化，避免每次对话都从零开始。

### Agent 内部设计

教师型 Agent 不是单个大 prompt，而是由 Agent Orchestrator 调用多个明确的能力模块完成教学闭环。

核心模块：

- `TutorAgent`：负责对话、讲解、追问、引导用户思考和总结。
- `CurriculumPlanner`：负责入学诊断、课程设计、章节拆分、先修关系和阶段目标。
- `ProgressManager`：负责课程状态、作业状态、掌握程度、复习计划和下一步推荐。
- `AssignmentDesigner`：负责生成概念题、代码题、实验题和验收标准。
- `CodeGenerator`：负责生成模板项目、训练脚本、配置、README、测试和指标输出约定。
- `ExperimentDesigner`：负责把学习目标转成可运行实验，包括变量、超参数、数据集、指标和预期观察点。
- `GradingAgent`：负责验收作业、阅读代码 diff、分析实验结果、给出评分和修改建议。
- `ReflectionAgent`：负责阶段复盘，识别薄弱点，并调整后续课程。

这些模块共享同一套持久化上下文：tenant/workspace、用户学习目标、课程计划、当前课程状态、历史对话、作业记录、Git commit、实验 run、数据集和 artifact。

### 课程状态管理

课程由 plan、module、lesson、assignment 四层组成。

课程计划状态：

- `draft`：Agent 已生成计划，但用户还未确认。
- `active`：用户确认后进入学习中。
- `paused`：用户暂停学习。
- `completed`：所有核心章节通过验收。
- `archived`：用户归档，不再继续。

课程章节状态：

- `not_started`：未开始。
- `in_progress`：正在学习。
- `assignment_ready`：课程讲解完成，等待做作业。
- `submitted`：用户已提交作业，等待验收。
- `needs_revision`：验收未通过，需要修改或复习。
- `mastered`：已掌握。
- `review_scheduled`：已掌握但安排了后续复习。

掌握程度建议使用 0 到 5 分：

- `0`：未接触。
- `1`：知道概念名，但不能解释。
- `2`：能复述概念，但不能独立应用。
- `3`：能在指导下完成练习。
- `4`：能独立完成标准任务。
- `5`：能解释原理、迁移到新问题，并能调试错误。

`ProgressManager` 每次对话或作业验收后都要更新：

- 当前 lesson 状态。
- 当前 assignment 状态。
- mastery score。
- 薄弱知识点。
- 下一步推荐：继续学习、复习、重做作业、运行实验或进入下一课。

### 课程准备流程

Agent 准备课程时不能只生成一段文字。每节课应包含结构化内容：

- 学习目标：用户学完后应该能做什么。
- 先修知识：需要先理解哪些概念。
- 核心讲解：概念、直觉、公式或代码。
- 检查问题：用来确认用户是否理解。
- 代码示例：最小可运行示例。
- 实验任务：需要运行的实验和观察指标。
- 作业：概念题、代码题或实验分析题。
- 验收标准：通过条件、评分规则和常见错误。
- 复习材料：如果未掌握，应该回看哪些内容。

课程生成流程：

```text
用户提出学习目标
  -> TutorAgent 做入学诊断
  -> CurriculumPlanner 生成课程计划 draft
  -> UI 展示课程大纲、预计时间、难度和作业形式
  -> 用户确认或修改
  -> ProgressManager 创建 active plan 和 lesson 状态
  -> TutorAgent 开始第一课
```

### 代码生成流程

Agent 生成代码时必须走可审查流程，避免直接写入用户仓库。

代码生成步骤：

1. `AssignmentDesigner` 或 `ExperimentDesigner` 生成代码需求。
2. `CodeGenerator` 选择模板或生成项目骨架。
3. 生成文件到临时 workspace。
4. 运行最小检查，例如语法检查、单元测试或 smoke test。
5. UI 展示变更预览：文件列表、关键代码片段、README、运行入口、依赖和 commit message。
6. 用户确认后，`Git Project Service` 初始化 Git 或写入目标分支。
7. 创建 commit 并记录 commit hash。
8. 如果用户选择远程仓库，使用 `Git Credential Service` 推送。

生成代码的最低要求：

- 有清晰 README，说明目标、运行方式、指标输出和作业要求。
- 有固定指标输出格式，便于平台读取，例如 `metrics.jsonl`。
- 有配置文件，例如 `config.yaml` 或命令行参数说明。
- 有最小 smoke test 或可快速运行的 debug mode。
- 不包含用户 secret、API key 或本机路径。

### 作业验收流程

作业可以是概念作业、代码作业、实验作业或混合作业。

验收输入：

- 文本回答。
- Git commit 或 diff。
- 实验 run。
- 指标、日志、artifact、checkpoint。
- Notebook 或报告。

验收步骤：

```text
User submits assignment
  -> Assignment Service records submission
  -> GradingAgent loads rubric and lesson context
  -> If code is required, Git Project Service fetches commit
  -> If execution is required, Experiment Service creates run
  -> DockerRunner runs tests or experiment
  -> Deterministic checks evaluate tests, metrics, required files, and artifacts
  -> GradingAgent reviews explanation quality, code reasoning, and learning evidence
  -> Assignment Review is saved
  -> ProgressManager updates lesson status and mastery score
  -> TutorAgent explains feedback and next action
```

验收结果需要包含：

- `status`：`passed`、`needs_revision`、`failed`、`blocked`。
- `score`：0 到 100。
- `rubric_results`：每条标准是否通过。
- `strengths`：做得好的地方。
- `issues`：具体问题。
- `required_changes`：必须修改的内容。
- `suggested_review`：建议复习内容。
- `next_action`：下一步继续、重做、复习或进入下一课。

如果作业未通过，Agent 不应该只给答案，而应该指出问题、给提示、建议复习材料，并让用户重新提交。

作业验收需要区分确定性检查和 LLM 评价：

- 确定性检查负责判断代码是否运行、测试是否通过、必需文件是否存在、指标是否达标、artifact 是否生成。
- LLM 评价负责判断用户解释是否清楚、代码思路是否合理、错误分析是否到位、是否真正理解概念。
- 最终评分需要保存两部分结果：`deterministic_results` 和 `llm_review`。
- 如果确定性检查失败，LLM 可以解释失败原因和建议，但不能把失败作业判为通过。
- 如果确定性检查通过但用户解释明显错误，作业可以是 `needs_revision`，要求用户补充理解说明。
- rubric 中必须明确哪些条件是 hard gate，哪些条件是教学反馈项。

### 实验验收规则

实验作业不能只看程序是否运行成功，还要看用户是否理解实验结果。

验收维度：

- 代码是否能在 Docker 中稳定运行。
- 是否记录了必要指标。
- 指标是否达到课程要求，例如 loss 下降、accuracy 超过阈值、过拟合现象可观察。
- 是否生成了必要 artifact，例如图表、checkpoint、预测样本或混淆矩阵。
- 用户是否能解释结果，尤其是失败、过拟合、欠拟合、学习率异常等情况。

Agent 可以要求用户补充解释。如果指标通过但解释错误，课程状态可以是 `needs_revision`，而不是 `mastered`。

### 学习计划

用户可以要求系统制定学习计划。系统会把学习计划保存成结构化的课程和里程碑。每节课可以包含讲解、练习、推荐实验，并支持导出 Notebook。

系统的学习主题要可扩展。PyTorch 是第一期重点内容之一，后续可以扩展到机器学习基础、深度学习、数据处理、模型评估、LLM 应用、MLOps、实验管理和部署等主题。

第一期重点覆盖实用 PyTorch 内容：

- tensor 和 autograd
- dataset 和 dataloader
- 用 `nn.Module` 定义模型
- 训练循环
- 优化器和学习率
- 验证集和过拟合
- CNN 基础
- 实验追踪和结果解读

课程对象需要包含：

- 课程目标
- 章节和知识点
- 前置知识
- 作业和验收标准
- 推荐实验
- 当前进度
- 掌握程度
- 复习计划
- 下一步建议

### 实验设计和运行

Agent 可以基于模板提出实验，也可以生成新的实验方案。用户先 review 参数，然后再运行。

第一期支持两种实验来源：

- 模板实验：系统内置实验模板，适合学习和快速验证概念。
- Git 项目实验：用户在自己的 IDE 中开发代码，推送到 Git 仓库后，在 Web UI 中配置仓库地址、分支、commit、运行入口、参数和 Docker 环境，由系统拉取代码并运行。
- Agent 初始化项目：用户告诉 Agent 学习或实验目标，Agent 生成模板代码并提交到 Git，然后系统基于该 commit 运行第一次实验。

推荐第一期优先采用 Git 项目实验，而不是完整在线 IDE。原因是用户已经有熟悉的 IDE、Git 工作流和代码管理方式；系统专注于 Agent 指导、实验编排、Docker 执行、结果记录和可视化。完整在线 IDE 会显著增加编辑器、文件同步、权限、终端、安全和协作复杂度，适合作为后续产品增强。

每次实验运行包含：

- 名称和描述
- 模板或生成代码引用
- Git 仓库、分支和 commit 信息，适用于 Git 项目实验
- 运行入口，例如 Python 脚本、模块命令或配置文件
- 超参数
- Docker 镜像或环境 preset
- 状态
- stdout 和 stderr 日志
- 指标
- 产物
- checkpoints
- Notebook 导出选项

实验通过 `DockerRunner` 运行。第一期不提供默认 subprocess 回退，因为目标本地机器已经安装 Docker。

Git 项目实验流程：

```text
用户在本地 IDE 写代码
  -> 用户提交并推送到 Git
  -> Web UI 选择仓库、分支、commit 和运行入口
  -> Backend 拉取代码到隔离工作目录
  -> DockerRunner 挂载只读代码目录和可写 artifact 目录
  -> 实验容器运行用户指定入口
  -> Backend 收集日志、指标和产物
  -> UI 展示结果和可视化
```

### 可视化展示

Web UI 展示实验进度和结果：

- 实时或刷新式日志
- loss、accuracy、learning rate 等标量图表
- 可用时展示混淆矩阵
- 可用时展示样本预测
- 产物和生成文件
- 多个实验 run 的对比视图

图表数据必须来自后端保存的结构化指标，而不是从日志文本里临时解析。

## 架构

高层架构：

```text
Web UI
  -> FastAPI Backend
    -> Agent Service
    -> Learning Plan Service
    -> Experiment Service
      -> DockerRunner
    -> Job Service
    -> Template Library
    -> Dataset Service
    -> Artifact Service
    -> Notebook Export Service
    -> ModelProvider
      -> OllamaProvider
      -> OnlineApiProvider
    -> PostgreSQL
```

本地启动方式：

```text
docker compose up
```

Compose 服务：

- `frontend`：浏览器 UI。
- `backend`：FastAPI API 服务。
- `postgres`：本地 PostgreSQL 数据库。
- `ollama`：可选服务。如果用户希望用 Compose 管理 Ollama，就启动它；否则后端连接宿主机已有的 Ollama。
- 实验容器：由后端通过 Docker 创建，只挂载受限的工作目录和产物目录。

## 组件边界

### Web UI

职责：

- 聊天界面。
- 应用级 UI shell：侧边栏、顶部栏、主内容区、状态提示区。
- 学习计划视图。
- 实验创建和 review。
- 实验状态页和详情页。
- 指标和产物可视化。
- 触发 Notebook 导出。
- 基于 Ant Design 的统一表单、按钮、卡片、表格、弹窗、Tabs、Message/Notification、加载状态、空状态和错误状态。

UI 不应该关心回答来自 Ollama 还是在线模型。UI 也不应该关心未来实验是在本地还是云端运行。UI 只和后端 API 通信。

第一期 UI 页面：

- Dashboard：展示学习进度、今日任务、待验收作业、最近实验、运行中任务、薄弱点和关键提醒。
- Chat：和 Agent 对话，支持展示学习建议、实验建议和结果解释。
- Learning Plan：查看学习路线、课程、章节、练习、掌握程度、复习计划和可导出的 Notebook。
- Assignments：查看作业列表、提交状态、验收结果、评分、反馈和重做建议。
- Templates：浏览内置机器学习实验模板，第一期重点是 PyTorch，查看目标、参数和预期结果。
- Projects：管理 Git 项目来源，包括仓库地址、分支、commit、运行入口和 Docker 环境配置。
- Experiments：实验列表、筛选、状态、创建入口和对比入口。
- Experiment Detail：展示配置、日志、指标图表、产物、checkpoint 和 Notebook 导出。
- Jobs：查看 Git 拉取、数据集下载、实验运行、Notebook 导出等后台任务状态、日志和错误。
- Settings：配置模型 provider、Ollama 地址、在线 API、Docker Runner、Git 凭据、数据管理和数据目录。

第一期 UI 风格：

- 第一视觉质量要接近正式产品，而不是内部工具或粗糙 MVP。
- 面向开发者和学习者，优先清晰、稳定、信息密度适中，同时要有现代感和精致感。
- 使用浅色主题作为默认主题，预留暗色主题能力。
- 使用 Ant Design 的专业组件能力，但要通过统一 spacing、色彩、字体层级、卡片层级、图标和空状态插画做出产品感。
- Dashboard、课程进度、作业验收和实验详情是第一期重点打磨页面。
- 实验状态要有明确颜色和文案，例如 running、succeeded、failed、cancelled。
- 学习状态也要有明确颜色和文案，例如 not started、in progress、submitted、needs revision、mastered。
- 图表和日志区域要适合长时间观察实验运行。
- 所有危险操作，例如取消实验、删除产物，需要二次确认。

### FastAPI 后端

职责：

- API 路由。
- 为未来 SaaS 预留认证边界。
- 构建请求上下文，第一期固定注入 `tenant_id=default` 和 `workspace_id=default`。
- 请求校验。
- Agent 编排。
- 实验生命周期管理。
- Docker Runner 调度。
- 数据持久化。
- 产物索引。

后端服务要保持模块化，保证未来做 SaaS 时不用重写核心学习和实验逻辑。

FastAPI 是第一期后端默认选择。多租户能力不依赖换框架，而依赖从第一期开始保留清晰的 tenant/workspace 边界。第一期不做登录和权限系统，但所有核心 service 方法、数据库记录、实验任务和 artifact 路径都应能接收 tenant/workspace 上下文。

### Model Provider

`ModelProvider` 用统一接口隐藏具体模型细节。

第一期 provider：

- `OllamaProvider`：调用本地 Ollama 服务。
- `OnlineApiProvider`：调用配置好的在线模型 API。

当前使用哪个 provider 由配置选择。未来 SaaS 版可以按 workspace 或 tenant 选择 provider。

provider 接口应支持：

- chat messages
- system prompt
- 如果实现成本合适，支持流式响应
- model name
- temperature 和基础生成参数
- provider-specific error normalization，即把不同 provider 的错误统一包装

### Agent Service

`Agent Service` 负责把模型能力、课程状态、实验工具、Git 工具和数据集工具编排成教师型 Agent。

职责：

- 加载当前 tenant/workspace 的学习上下文。
- 维护 Agent 可用工具列表，例如课程创建、作业创建、Git 初始化、实验运行、数据集准备和 Notebook 导出。
- 对高风险工具调用做审批，例如写入 Git、推送远程仓库、下载大数据集、运行实验、删除 artifact。
- 把 Agent 的重要动作写入 `agent_actions`，便于后续审计和调试。
- 在每次 Agent 回复后，判断是否需要更新课程进度、作业状态或 mastery record。
- 控制 prompt 上下文，不把 Git token、模型 API key 或其他 secret 放进模型上下文。

Agent 工具调用要遵循“先计划、再确认、再执行、再记录”的原则。尤其是代码生成、Git 写入、数据集下载和实验运行，不能只靠模型文本直接执行。

### Job Service

第一期需要本地任务系统。Git clone、数据集下载、Docker 实验、Notebook 导出都不应该阻塞普通 API 请求。

`Job Service` 职责：

- 创建本地后台任务。
- 持久化任务状态、进度、日志、错误和结果引用。
- 支持取消可取消任务，例如实验运行和数据集下载。
- 支持失败记录和手动重试。
- 把任务绑定到 tenant/workspace、触发用户、关联 project、experiment、dataset 或 artifact。
- 给 UI 提供任务列表、任务详情和日志查询 API。

建议任务状态：

- `pending`
- `running`
- `succeeded`
- `failed`
- `cancelled`

第一期可以用后端进程内 worker 或轻量本地 worker 实现，但接口要能迁移到 SaaS 的队列系统。SaaS 版可以替换成 Celery、RQ、Dramatiq、Kubernetes Jobs 或云任务队列。

长任务都要通过 `Job Service`：

- Git 项目拉取。
- Agent 初始化模板项目和 Git commit。
- 数据集下载和校验。
- Docker 实验运行。
- Notebook 导出。
- 大 artifact 清理。

### Agent 数据收集设计

教师型 Agent 需要持续收集学习证据，才能判断用户是否真的学会、下一步该教什么、作业是否通过。数据收集必须结构化、可解释、可审计，并且从第一期开始按 tenant/workspace 隔离。

Agent 需要收集的数据类型：

- 学习目标数据：用户目标、当前水平、时间投入、偏好学习方式、希望掌握的主题。
- 交互数据：用户问题、Agent 回答、追问结果、用户自评、困惑点和反馈。
- 课程进度数据：当前 plan/module/lesson/assignment 状态、开始时间、完成时间、复习时间。
- 作业数据：作业题目、rubric、提交内容、提交 commit、提交 run、验收结果、评分和修改历史。
- 代码数据：Git 仓库、分支、commit hash、diff 摘要、运行入口、测试结果和静态检查结果。
- 实验数据：run 配置、超参数、数据集版本、metrics、logs、artifacts、checkpoint 和失败原因。
- 掌握度数据：知识点 mastery score、薄弱点、常见错误、复习计划和阶段复盘。
- 系统动作数据：Agent 调用了哪些工具、何时调用、用户是否确认、结果是否成功。

数据收集原则：

- 只收集教学和实验闭环需要的数据，不做无目的采集。
- secret 不进入 Agent 上下文，包括 Git token、SSH key、模型 API key、数据库密码。
- 对代码内容使用“按需读取”：默认收集 commit hash、文件列表、diff 摘要和测试结果；只有在作业验收或用户要求解释代码时，才读取相关文件片段。
- 对实验日志做分层保存：完整日志作为 artifact，Agent 默认读取摘要、错误片段和关键指标。
- 每条收集的数据都要绑定 tenant/workspace。
- SaaS 版需要给用户提供数据导出、删除和保留策略；本地版先保留数据模型和接口边界。

Agent 数据进入上下文前需要做整理：

- `LearningContextBuilder`：整理用户目标、当前课程、进度、薄弱点和下一步任务。
- `SubmissionContextBuilder`：整理作业提交、rubric、代码 diff、测试结果和实验 run。
- `ExperimentContextBuilder`：整理指标趋势、失败原因、关键日志和 artifact 摘要。
- `CodeContextBuilder`：按文件范围读取代码片段，并避免把凭据、`.env`、密钥文件放入模型上下文。
- `DatasetContextBuilder`：整理数据集来源、版本、许可、大小和使用方式。

建议新增数据采集表：

- `learner_profiles`：用户学习画像，第一期本地对应 `default` 用户。
- `learning_events`：记录学习行为事件，例如开始课程、完成章节、提交作业、复习完成。
- `agent_observations`：Agent 从对话、作业、代码和实验中总结出的观察，例如“对梯度概念不稳定”。
- `knowledge_points`：知识点定义，例如 autograd、dataloader、overfitting。
- `knowledge_point_mastery`：用户对每个知识点的掌握程度和证据来源。
- `agent_context_snapshots`：关键 Agent 回复或验收前使用的上下文摘要，便于调试和复盘。

数据采集触发点：

- 入学诊断完成后，创建或更新 `learner_profiles`。
- 用户学习一节课时，记录 `learning_events`。
- 用户提交作业时，记录 submission 和相关 Git/experiment 证据。
- 实验 run 完成时，记录指标摘要、失败原因和 artifact 索引。
- Agent 验收作业后，写入 `assignment_reviews`、`agent_observations` 和 `knowledge_point_mastery`。
- Agent 阶段复盘后，更新复习计划和下一阶段目标。

这些数据不是为了替代用户判断，而是为了让 Agent 的教学建议有依据。UI 应该能展示关键依据，例如“为什么 Agent 认为我需要复习过拟合”。

### 数据管理和隐私

第一期是本地产品，但仍然需要提供清晰的数据管理能力，避免后续 SaaS 再补隐私边界。

Settings 中需要有数据管理页面：

- 查看本地存储概览：课程数据、对话、作业、实验、artifact、dataset、代码摘要和日志占用空间。
- 导出学习数据：导出课程计划、作业记录、掌握度、实验摘要和 Agent observations。
- 清理对话历史。
- 清理学习画像和 mastery records。
- 清理代码摘要和 agent context snapshots。
- 清理实验日志和 artifact。
- 清理 dataset 缓存。
- 重置本地 `default` tenant/workspace。

数据保留原则：

- 学习记录默认长期保留，除非用户手动清理。
- 原始实验日志可以配置保留周期。
- artifact 可以按实验或时间清理。
- agent context snapshots 默认只保存摘要，不保存 secret 和完整私有代码。
- 删除操作需要二次确认，并记录 `agent_actions` 或系统审计记录。

### Experiment Service

职责：

- 创建实验记录。
- 校验实验 spec。
- 把模板或生成代码落到实验工作目录。
- 通过 `DockerRunner` 启动运行。
- 跟踪状态流转。
- 接收指标、日志和产物。
- 在支持时取消正在运行的实验。

实验状态机由 Experiment Service 管理。

建议状态：

- `draft`
- `queued`
- `running`
- `succeeded`
- `failed`
- `cancelled`

### DockerRunner

第一期使用 Docker 执行实验。

职责：

- 创建隔离的 run 目录。
- 构建或选择 PyTorch 运行时镜像。
- 只挂载 run 输入目录和 artifact 输出目录。
- 只传入最小环境变量白名单。
- 设置超时时间。
- 捕获 stdout 和 stderr。
- 把日志流式传回后端，或者由后端轮询。
- 收集退出码。
- 标记运行状态。

安全和可靠性约束：

- 不要把整个项目目录以可写方式挂载进实验容器。
- 不要把宿主机 secrets 传入实验容器。
- 生成实验默认禁用网络，除非模板明确需要下载数据集。
- 内置模板优先使用预下载或缓存的数据集。
- 在可行时限制 CPU、内存和磁盘。
- 每个 run 使用唯一目录。
- 实验容器默认使用非 root 用户运行。
- 代码目录只读挂载，artifact 目录单独可写挂载。
- 禁止把 Docker socket 挂载进实验容器。
- 尽量使用只读 root filesystem；需要写入的临时目录显式挂载。
- 默认禁用 privileged 模式。
- 默认禁用容器网络；需要下载数据集时通过 Dataset Service 预先下载，而不是让实验容器随意联网。
- 如果模板必须联网，需要在模板 metadata 中声明网络需求，并在 UI 中提示用户确认。
- 限制 CPU、内存、进程数、运行时长和可写磁盘空间。
- 固定基础镜像来源，优先使用平台维护的 PyTorch runtime image。
- 依赖安装优先发生在构建阶段或受控环境中，避免实验运行时随意执行不可信安装脚本。
- 捕获并保存容器退出码、超时原因、资源限制错误和最后关键日志。

### Git Project Service

第一期支持用户通过 Git 项目接入自己的代码。

职责：

- 保存项目来源配置，包括仓库地址、默认分支、Git 凭据引用、默认运行入口和默认 Docker 环境。
- 按用户选择的分支或 commit 拉取代码到隔离目录。
- 记录每次实验使用的 commit hash，保证结果可复现。
- 把代码目录以只读方式挂载给实验容器。
- 把运行输出、指标和产物写入当前 run 的 artifact 目录。
- 支持 Agent 初始化模板项目：生成代码到临时工作区，初始化 Git，创建初始 commit，并可选推送到用户配置的远程仓库。
- 在 Agent 写入 Git 前生成变更预览，包括文件列表、关键 README、运行入口和 commit message，等待用户确认。

第一期本地版支持本地可访问的 Git 仓库路径、公开远程仓库和带凭据的私有仓库。私有仓库认证必须通过显式配置，不要默认读取或传递宿主机 SSH key、Git credential helper 或 token。

Agent 初始化项目的安全边界：

- 默认创建新分支或新仓库，不直接覆盖用户已有代码。
- 对已有仓库写入时，必须要求用户选择目标分支并确认变更。
- 生成代码后先运行模板级静态检查或最小 smoke test，再建议提交。
- 推送远程仓库需要使用用户配置的 Git 凭据，并记录审计信息。
- 如果用户只想本地学习，可以只初始化本地 Git 仓库，不推送远程。

### Git Credential Service

通过 Git 接入用户代码时，系统需要管理 Git 账号和凭据。第一期本地版也要按 SaaS-ready 的方式设计，只是凭据存储可以先使用本地加密存储或环境变量。

支持的凭据类型：

- HTTPS personal access token，例如 GitHub、GitLab、Gitee token。
- SSH deploy key，用于只读拉取指定仓库。
- 本地仓库路径，不需要远程凭据。

第一期推荐优先支持 HTTPS token 和本地路径仓库。SSH deploy key 可以作为增强项，但接口要预留。

安全要求：

- 凭据只用于拉取代码，不传入实验容器。
- 凭据只保存在后端受控存储中，数据库里不能明文保存 token 或私钥。
- 本地版使用应用级密钥加密凭据；密钥来源需要显式配置，优先顺序是系统 Keychain、环境变量、用户输入 passphrase。
- 如果没有可用加密密钥，不允许保存 Git token，只允许使用本地路径仓库或公开仓库。
- 加密密钥不能写入 Git 仓库，不能进入 Docker 实验容器，不能进入模型上下文。
- 支持凭据轮换：用户更新 token 后，新拉取使用新凭据，历史 run 只保留凭据引用和审计信息。
- 删除凭据时删除加密 secret，并阻止引用该凭据的项目继续拉取私有仓库，直到用户重新配置。
- SaaS 版需要接入 KMS、Vault 或云厂商 Secret Manager。
- UI 创建凭据后不回显完整 token，只显示名称、平台、权限说明和最后使用时间。
- 支持删除、禁用和轮换凭据。
- 拉取代码时使用最小权限凭据，优先只读权限。
- 记录凭据使用审计信息，包括 tenant/workspace、project、时间和结果，但不要记录 secret 内容。

Git 凭据数据模型需要和 tenant/workspace 绑定。第一期本地固定使用 `default`，后续 SaaS 切换到真实 tenant/workspace。

建议表：

- `git_credentials`：保存凭据元数据、加密后的 secret 引用、类型、状态和最后使用时间。
- `projects`：引用 `git_credentials`，保存仓库地址、默认分支和运行配置。
- `project_revisions`：记录每次拉取到的 commit hash、分支、拉取时间和来源项目。

### Dataset Service

第一期支持从公开来源准备数据集，服务于课程、作业和实验。

职责：

- 维护数据集目录和元数据，包括名称、来源 URL、版本、许可、大小、校验值、下载时间、缓存路径和适用任务。
- 根据模板或 Agent 请求下载公开数据集。
- 下载完成后做 checksum 校验，避免损坏数据被实验使用。
- 把数据集缓存到 tenant/workspace 隔离路径，例如 `datasets/default/default/<dataset_name>/<version>/...`。
- 为实验容器提供只读 dataset mount。
- 记录每个实验 run 使用的数据集版本，保证实验可复现。
- 支持删除缓存和重新下载。

第一期优先支持：

- synthetic datasets：无需下载，用于快速教学和测试。
- torchvision datasets：MNIST、Fashion-MNIST、CIFAR-10 等。
- scikit-learn toy datasets：iris、wine、breast cancer、diabetes 等。
- 通过 URL 配置的小型公开 CSV 数据集。

安全、许可和可靠性要求：

- 下载前必须记录公开来源和许可信息；许可不清楚的数据集不能默认推荐给 SaaS 用户。
- 默认限制单个数据集大小，避免误下载超大数据。
- 下载数据集需要显式开启网络；实验运行阶段默认使用已缓存数据。
- 数据集只读挂载给实验容器。
- 不把用户 Git 凭据、模型 API key 或其他 secrets 传给数据集下载和实验容器。
- SaaS 版需要把数据集缓存迁移到对象存储，并按 tenant/workspace 隔离。

### Code Interaction Strategy

第一期采用“用户 IDE + Git + Web 编排”的方式。

推荐工作流：

```text
用户在 Cursor / PyCharm / VS Code 写代码
  -> git commit / push
  -> Web UI 选择项目、分支、commit 和运行入口
  -> Agent 帮助检查实验配置并解释结果
  -> DockerRunner 执行实验
```

Agent 初始化项目工作流：

```text
用户提出学习或实验目标
  -> Agent 选择或生成项目模板
  -> Web UI 展示文件变更、运行入口和 commit message
  -> 用户确认创建本地仓库或推送远程仓库
  -> Git Project Service 初始化代码并创建 commit
  -> Experiment Service 基于该 commit 创建首次实验 run
  -> DockerRunner 执行实验
```

这个方案的优点：

- 用户继续使用熟悉的 IDE，不需要在浏览器里重建完整开发环境。
- Git commit 天然提供实验可复现性。
- 本地版和 SaaS 版都可以沿用同一套项目来源模型。
- 系统聚焦在 Agent、实验执行、记录、可视化和教学，而不是先做复杂在线 IDE。

完整在线 IDE 作为后续增强考虑。只有当产品需要浏览器内编辑、云端工作区、协作开发或教学课堂场景时，再引入 Monaco Editor、Web terminal、文件同步和权限模型。

### Template Library

第一期内置机器学习实验模板，优先覆盖 PyTorch：

- 线性回归
- logistic regression 或二分类
- 基于表格数据或 toy data 的 MLP
- 基于 MNIST 或 Fashion-MNIST 的 CNN
- 过拟合演示
- 学习率对比
- 优化器对比
- 正则化对比

每个模板需要定义：

- 标题和描述
- 学习目标
- 可配置参数
- 生成的代码文件
- 预期指标
- 预期产物
- 可视化提示

### Artifact Service

Artifacts 是实验生成的文件。

示例：

- checkpoints
- best model files
- config snapshots
- metrics files
- prediction samples
- confusion matrix data
- generated images
- exported notebooks

第一期可以把 artifact 文件存到本地文件系统，把元数据存到 PostgreSQL。路径设计要兼容后续迁移到对象存储。

### Notebook Export Service

Notebook 导出应支持：

- 从学习计划章节生成 lesson notebook
- 从实验 run 生成 experiment notebook
- Markdown 讲解单元格
- 数据加载、模型定义、训练、评估和可视化代码单元格
- 在可行时引用输出结果

导出的 `.ipynb` 应该适合用户继续手动学习，而不是简单把内部代码 dump 出来。

## 数据模型

第一期本地就使用 PostgreSQL。

核心表：

- `conversations`
- `messages`
- `learner_profiles`
- `learning_events`
- `learning_plans`
- `learning_modules`
- `learning_lessons`
- `lesson_progress`
- `knowledge_points`
- `knowledge_point_mastery`
- `assignments`
- `assignment_rubrics`
- `assignment_submissions`
- `assignment_reviews`
- `mastery_records`
- `agent_actions`
- `agent_observations`
- `agent_context_snapshots`
- `jobs`
- `git_credentials`
- `projects`
- `project_revisions`
- `datasets`
- `dataset_versions`
- `dataset_usages`
- `experiment_templates`
- `experiments`
- `experiment_runs`
- `experiment_metrics`
- `experiment_artifacts`
- `notebook_exports`

第一期采用 SaaS-ready 的多租户数据模型，但本地运行时固定使用默认租户：

- `tenant_id`：第一期固定为 `default`。
- `workspace_id`：第一期固定为 `default`。
- 所有 conversation、learning plan、experiment、run、metric、artifact、notebook export 都要归属到 tenant/workspace。
- 所有后端查询默认带 tenant/workspace 过滤，即使第一期只有 `default`。
- 后台实验任务需要携带 tenant/workspace 上下文，避免未来迁移到云端 worker 时丢失归属。
- artifact 本地路径要包含 tenant/workspace，例如 `artifacts/default/default/runs/<run_id>/...`。
- 创建时间和更新时间。
- 长任务状态字段。

第一期不实现完整多租户鉴权。

## 数据流

### 对话流程

```text
User message
  -> Web UI
  -> Backend chat endpoint
  -> Agent Service loads relevant context
  -> ModelProvider
  -> Agent response
  -> Message persisted
  -> UI displays response
```

### 教学和作业验收流程

```text
User starts learning goal
  -> Agent runs intake diagnosis
  -> Learner profile and learning events are updated
  -> Learning Plan Service creates course plan
  -> User studies lesson and completes assignment
  -> User submits answer, Git commit, experiment run, or notebook
  -> Agent reviews submission against rubric
  -> Assignment Review is persisted
  -> Progress, observations, and mastery records are updated
  -> Agent recommends next lesson, revision, or review
```

### Agent 数据收集流程

```text
User interacts with Agent or submits work
  -> Agent Service records learning event
  -> Context builders summarize conversation, code, experiment, and dataset evidence
  -> Agent uses summarized context without secrets
  -> Agent produces feedback, action, or review
  -> Observations and mastery updates are persisted
  -> UI can show the evidence behind progress decisions
```

### 实验运行流程

```text
User approves experiment
  -> Backend creates experiment run
  -> Experiment Service materializes workspace
  -> DockerRunner starts container
  -> Container writes metrics and artifacts
  -> Backend captures logs and status
  -> Metrics and artifacts persisted
  -> UI visualizes results
```

### Git 项目实验流程

```text
User pushes code to Git
  -> Web UI selects project, branch, commit, entrypoint, and params
  -> Git Project Service fetches code into isolated workspace
  -> Experiment Service creates run with commit hash
  -> DockerRunner runs selected entrypoint
  -> Metrics and artifacts persisted
  -> UI visualizes results
```

### 数据集准备流程

```text
Agent or user requests dataset for lesson/experiment
  -> Dataset Service checks metadata and cache
  -> UI shows source, license, size, and download plan
  -> User confirms download when network is needed
  -> Dataset Service downloads and verifies checksum
  -> Dataset metadata and version are persisted
  -> Experiment run mounts dataset read-only
```

### Notebook 导出流程

```text
User requests export
  -> Backend loads lesson or run context
  -> Notebook Export Service generates .ipynb
  -> Artifact metadata saved
  -> UI exposes download/open action
```

## 错误处理

模型错误：

- 把 provider 错误转成用户能看懂的信息。
- 在后端日志里保留 provider-specific 细节。
- 如果 Ollama 未运行或 API key 缺失，展示可操作的设置提示。

实验错误：

- 捕获 stdout、stderr、退出码和超时原因。
- 把 run 标记为 failed，并保存清楚的失败原因。
- 如果已经生成了部分指标和产物，需要保留。
- 支持基于同一配置重新运行。

Docker 错误：

- 检测 Docker 不可用、镜像缺失、构建失败、超时和资源不足。
- 展示设置指引，而不是直接暴露原始堆栈。

Notebook 导出错误：

- 导出失败不能破坏实验记录。
- 保留足够上下文，方便重试。

## 测试策略

测试是第一期的核心交付，不是最后补充。所有核心服务必须有单元测试，关键用户路径必须有 API/集成测试和 e2e 测试。

后端测试：

- 使用 fake provider 测试模型 provider 接口
- 学习计划、课程进度、作业提交、作业验收和 mastery record 测试
- 确定性验收和 LLM 评价分离测试
- Agent 数据收集、上下文摘要、secret 过滤和观察记录测试
- Job Service 状态流转、取消、失败记录和日志查询测试
- Git 项目导入和 commit 记录测试
- Git 凭据加密存储、禁用、删除和不回显测试
- 数据集下载、缓存、checksum 校验、只读挂载和元数据记录测试
- 实验状态机测试
- 模板校验测试
- artifact 元数据测试
- Notebook 导出测试
- API 路由测试

后端测试要求：

- 单元测试覆盖 service 层核心规则，例如课程状态、作业状态、确定性验收、mastery 更新、tenant/workspace 过滤。
- API 测试覆盖主要接口，例如入学诊断、课程创建、Dashboard、作业提交、作业验收。
- 数据库测试覆盖迁移、唯一约束、tenant/workspace 过滤和状态流转。
- 安全测试覆盖 secret 过滤、Git 凭据不回显、实验容器不接收 secret。

Runner 测试：

- DockerRunner 命令构造
- 工作目录隔离
- Docker 沙箱约束测试，包括非 root、只读代码挂载、禁用 Docker socket、资源限制和网络策略
- 超时处理
- 日志捕获
- 从小型 synthetic experiment 接收指标

前端测试：

- 聊天渲染
- Dashboard、学习进度和作业验收状态渲染
- 实验列表和详情页
- 使用 mock 指标数据渲染图表
- 错误状态渲染

前端测试要求：

- 组件测试覆盖 Dashboard、Learning Plan、Assignments、Jobs、Settings 数据管理。
- 页面测试覆盖 loading、empty、error、success 状态。
- 表单测试覆盖入学诊断、作业提交、凭据创建、数据集下载确认。
- UI 状态测试覆盖学习状态和实验状态颜色与文案。

端到端冒烟测试：

- 启动本地 Compose stack
- 从模板创建一个简单实验
- 在 Docker 中运行实验
- 验证指标、日志、产物和图表可见
- 导出 Notebook

e2e 测试要求：

- 第一条 e2e 路径必须覆盖 M1 教师闭环：启动应用、创建学习计划、提交作业、看到验收结果和 Dashboard 更新。
- 第二条 e2e 路径覆盖 M2 代码实验闭环：Agent 初始化项目、创建 commit、运行实验、看到指标图。
- 第三条 e2e 路径覆盖 M3 数据集闭环：确认下载公开数据集、运行使用该数据集的实验、查看数据集版本记录。
- e2e 使用 Playwright，CI 中可以先跑 M1 smoke，完整 e2e 可作为 nightly 或手动触发。

## 开源项目标准

项目从第一期开始按开源项目维护。

必须包含：

- `README.md`：项目目标、截图或 UI 说明、功能列表、快速启动、配置、测试、常见问题。
- `LICENSE`：默认使用 MIT，除非后续决定采用其他许可证。
- `CONTRIBUTING.md`：开发流程、分支策略、提交规范、测试要求。
- `SECURITY.md`：安全边界、漏洞报告方式、secret 管理、实验沙箱说明。
- `.env.example`：列出本地开发所需环境变量，不包含真实 secret。
- `.editorconfig`：统一基础编辑器格式。
- 后端 lint/type/test 命令。
- 前端 lint/type/test 命令。
- CI 配置：至少运行 backend tests、frontend tests、build 和 e2e smoke。

代码质量要求：

- 后端使用 `ruff` 做 lint/format。
- 前端使用 TypeScript strict mode。
- 每个新增 service 必须配套单元测试。
- 每个关键 API 必须配套 API 测试。
- 每个关键页面必须配套组件或页面测试。
- 任何涉及 secret、Git、Docker、数据集下载的能力必须有安全测试。

## SaaS 演进路径

第一期需要保留这些扩展点：

- 把本地固定 `default` tenant/workspace 替换成真实 users、tenants 和 workspaces。
- 把 PostgreSQL 从本地 Compose 迁移到托管 Postgres。
- 把 artifact 文件系统存储迁移到 S3-compatible 对象存储。
- 把 dataset 缓存迁移到 S3-compatible 对象存储，并按 tenant/workspace 隔离。
- 在相同 runner 接口后面添加 `CloudContainerRunner`。
- 把本地 `Job Service` 迁移到云端任务队列和 worker 服务。
- 围绕模型调用和实验运行添加计费和用量统计。
- 为不可信客户代码添加更严格的沙箱。
- 只有当未来客户明确需要云端 UI 调用客户本地模型时，再添加本地 Connector。

未来 SaaS 架构：

```text
SaaS Web UI
  -> Cloud API
    -> Agent Service
    -> Managed Postgres
    -> Object Storage
    -> Queue
    -> CloudContainerRunner / GPU Workers
    -> Cloud Model APIs or Self-hosted Inference
```

## 实施顺序

1. 搭建本地 Compose stack：frontend、backend、Postgres。
2. 添加后端项目结构、数据库迁移和健康检查。
3. 实现模型 provider 抽象，包括 fake provider、Ollama provider、online API provider。
4. 实现聊天持久化和基础 Agent prompt。
5. 实现教师型 Agent 基础能力：入学诊断、课程计划、课程进度、作业模型、验收记录和 mastery record。
6. 实现 Agent 数据收集和上下文构建，包括 learner profile、learning events、observations、secret 过滤和上下文摘要。
7. 实现本地 Job Service，包括状态、日志、取消、失败记录和重试入口。
8. 实现 Git 凭据数据模型和本地加密存储。
9. 实现项目数据模型、Git 项目导入和 commit 记录。
10. 实现 Agent 初始化模板项目能力，包括生成代码、变更预览、初始化 Git、创建初始 commit。
11. 实现实验数据模型和模板库。
12. 实现 Dataset Service，包括公开数据集元数据、下载、缓存、校验和只读挂载。
13. 用一个最小 synthetic PyTorch 实现实验打通 DockerRunner。
14. 添加 Git 项目实验运行：从指定 commit 拉取代码并执行入口。
15. 添加确定性作业验收，包括测试、指标、必需文件和 artifact hard gates。
16. 添加指标和 artifact 接收。
17. 构建高质量 Web UI 页面：Dashboard、聊天、学习计划、作业验收、项目管理、Git 凭据管理、数据集管理、Jobs、实验列表、run 详情和图表。
18. 添加 UI 组件体系和应用布局，包括 sidebar、topbar、cards、forms、tables、dialogs、toast、empty states、loading states 和 error states。
19. 添加 Settings 数据管理页面。
20. 添加内置 PyTorch 模板。
21. 添加 checkpoint 和模型 artifact 支持。
22. 添加混淆矩阵、样本预测和实验对比。
23. 添加 Notebook 导出。
24. 添加端到端冒烟测试和本地启动文档。

## 默认技术选型

第一版实施计划使用这些默认选型：

- 前端框架：React + Vite + TypeScript。
- UI 方案：Ant Design，用于快速搭建稳定、一致、适合后台系统和实验管理场景的组件体系；第一期要求精美 UI，需要额外设计统一视觉规范、页面层级、图标、空状态和关键页面细节。
- 后端框架：FastAPI + Python。
- 数据库层：SQLAlchemy + Alembic migrations。
- 图表库：Recharts，用于第一期的标量图和对比图。
- e2e 测试：Playwright。
- CI：GitHub Actions。
- 在线模型 provider：先实现一个 OpenAI-compatible provider，通过 base URL、API key 和 model name 配置。
- 数据集策略：优先使用 generated toy datasets 和小型公开数据集；MNIST、Fashion-MNIST、CIFAR-10 等通过 Dataset Service 下载到 tenant/workspace 隔离缓存，实验容器只读挂载；只有用户确认或模板明确开启网络时才允许下载。
- 代码交互策略：第一期使用用户本地 IDE + Git 项目导入 + Web 实验编排，不做完整在线 IDE。
- Git 支持：第一期支持本地路径仓库、公开远程仓库和 HTTPS token 私有仓库；SSH deploy key 接口预留。
- Git 凭据存储：本地版使用应用级密钥加密保存，SaaS 版迁移到 KMS、Vault 或云 Secret Manager。
