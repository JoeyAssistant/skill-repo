# Agent Factory - PM-Driven Agent System

PM 驱动的 AI Agent 开发体系。PM 作为用户主入口，管理 feature 和 issue，直接完成设计并调度 developer subagent 完成开发。

## 架构

### 单项目模式

```
User ←→ PM (agent-pm.md, system prompt)
            ├── developer (subagent, .claude/agents/developer.md)
            ├── qa (subagent, .claude/agents/qa.md)
            ├── poc (subagent, .claude/agents/poc.md)
            └── spec-compliance (subagent, .claude/agents/spec-compliance.md)

PM 在 designing 阶段直接修改 doc/，调度 spec-compliance 自检，向用户展示 git diff 终审。
```

### 多项目模式

```
User ←→ PM (agent-pm.md, system prompt)
            ├── .workspace/projects.md (项目注册表)
            ├── Project A (独立 git 仓) ──┐
            ├── Project B (独立 git 仓) ──┤── 共享 subagents
            └── ...                       │
            ├── developer (subagent) ──────┤
            ├── qa (subagent)              │
            ├── poc (subagent)             │
            └── spec-compliance (subagent) ┘
```

### 生产 ↔ 开发协作

生产环境和开发环境都以 PM 为 system prompt。生产环境 PM 仅在 `.issues/_incoming/` 下提交产物，开发环境 PM 拉取后按文件类型分流。

```
生产环境 (PM 入口)
  User 报告 → PM 调度 QA 诊断 (仅诊断，输出 JSON)
           → PM 在 .issues/_incoming/<timestamp>-<name>/ 下提交:
             ├─ bug             → ISSUE.yaml (含 QA Diagnosis) + snapshot/
             └─ feature-request → FEATURE.yaml (与用户讨论后) + snapshot/
           → git push
                ↓ git pull
开发环境 (PM 入口)
  PM 扫描 .issues/_incoming/:
    ├─ 含 ISSUE.yaml         → 登记 .issues/<NNN>-<name>/  → 标准 issue 修复流程
    └─ 含 FEATURE.yaml  → 登记 .features/<NNN>-<name>/ → 标准 feature 设计流程
```

## 安装

### 1. 设置 PM 为 system prompt

将 `agent-pm.md` 的内容作为项目的 system prompt 使用：
- 通过 Claude Code 的 `--system-prompt` 参数
- 或写入项目的 `CLAUDE.md`
- 或通过 Claude Code 的 append-system-prompt 机制

### 2. 安装 subagents

将四个 subagent 复制到项目的 `.claude/agents/` 目录：

```bash
mkdir -p <project-root>/.claude/agents
cp developer.md <project-root>/.claude/agents/developer.md
cp qa.md <project-root>/.claude/agents/qa.md
cp poc.md <project-root>/.claude/agents/poc.md
cp spec-compliance.md <project-root>/.claude/agents/spec-compliance.md

# Optional: copy design-reference.md to project root for PM's on-demand reference
cp design-reference.md <project-root>/design-reference.md
```

### 3. 初始化目录结构

在项目根目录创建 feature 和 issue 管理目录：

```bash
mkdir -p .features .issues
```

### 4. 多项目模式初始化（可选）

如需管理多个项目：

```bash
# 创建工作区目录
mkdir agent-workspace && cd agent-workspace

# 复制 PM 作为 system prompt
cp <agent-factory>/agent-pm.md CLAUDE.md

# 安装全局 subagents
mkdir -p .claude/agents
cp <agent-factory>/developer.md .claude/agents/
cp <agent-factory>/qa.md .claude/agents/
cp <agent-factory>/poc.md .claude/agents/
cp <agent-factory>/spec-compliance.md .claude/agents/

# 初始化 workspace
mkdir -p .workspace
cat > .workspace/projects.md << 'EOF'
# Projects

| ID | Name | Path | Status | Created | Last Active |
|----|------|------|--------|---------|-------------|
EOF

# 将项目放入工作区（或使用 symlink）
git clone <repo-url> ./project-a
```

PM 启动时自动检测模式：
- 当前目录有 `.workspace/` → 多项目模式
- 当前目录有 `.features/` → 单项目模式

## 使用

### 交互模式：讨论需求

```
用户: 我想做一个财务日报功能
PM:   [创建 feature #NNN，引导讨论背景、价值、范围]
用户: 确认范围
PM:   [整理 FEATURE.yaml，自己写 doc/，调度 spec-compliance 自检]
用户: [review git diff]
PM:   [调度 developer]
```

### 交互模式：提交 Issue

```
用户: 登录页面点击提交就崩溃了
PM:   [创建 issue #NNN，确认复现步骤]
PM:   [triage: bug → 调度 QA 诊断 → 调度 developer 修复]
```

### 直接调用 subagent

用户也可以跳过 PM，直接调用 subagent：

```
用户: Use the developer agent to implement feature #003
```

## 项目目录结构

```
project-root/
  .features/
    index.yaml
    <id>/
      FEATURE.yaml
      BLOCKED.yaml
      POC-REPORT.md
      QA-REPORT.md
      poc/
  .issues/
    index.yaml
    <id>/
      ISSUE.yaml
      BLOCKED.yaml
  .claude/
    agents/
      developer.md
      qa.md
      poc.md
      spec-compliance.md
  agent/
  cli/
  doc/
  backend/
  frontend/
  script/
  test/
```

## 多项目工作区目录结构

```
agent-workspace/
├── .claude/
│   └── agents/
│       ├── developer.md
│       ├── qa.md
│       ├── poc.md
│       └── spec-compliance.md
├── .workspace/
│   └── projects.md
├── football-agent/         ← 独立 git 仓
│   ├── .features/
│   ├── .issues/
│   ├── agent/
│   ├── cli/
│   ├── doc/
│   └── ...
├── news-agent/             ← 独立 git 仓
│   ├── .features/
│   ├── .issues/
│   └── ...
└── CLAUDE.md               ← PM system prompt
```

## 文件说明

| 文件 | 用途 |
|------|------|
| `agent-pm.md` | PM system prompt，用户主入口（含设计阶段直接修改 doc/） |
| `design-reference.md` | PM 设计阶段按需参考手册 |
| `developer.md` | Developer subagent 定义，负责代码实现 |
| `qa.md` | QA subagent 定义，负责功能验收和问题诊断 |
| `poc.md` | POC subagent 定义，负责技术可行性分析和验证 |
| `spec-compliance.md` | 规范合规检查 subagent（PM 内部调用） |

## Schema 模块

PM 工作流 YAML 文件的 schema 定义在 `agent_factory/schema/` 目录：

| 文件 | 内容 |
|------|------|
| `agent_factory/schema/enums.py` | 6 个枚举（AgentType / Priority / FeatureStatus / 等） |
| `agent_factory/schema/feature.py` | Feature / Decision / Option 模型 |
| `agent_factory/schema/issue.py` | Issue 模型 |
| `agent_factory/schema/index.py` | FeatureIndex / IssueIndex 模型 |
| `agent_factory/schema/blocked.py` | BlockedRecord 模型 |
| `agent_factory/schema/validate.py` | YAML 校验 CLI |
| `agent_factory/schema/examples/` | 5 个示例 YAML 文件 |

校验单个文件：

```bash
python3 -m agent_factory.schema.validate path/to/file.yaml
```

校验整个项目：

```bash
python3 -m agent_factory.schema.validate .
```

## 生命周期

### Feature

`draft` → `designing` → `approved` → `implementing` → `qa-reviewing` → `done`

`blocked` 为可逆中间状态，`cancelled` 可从任何状态直接流转。

### Issue

`open → in_progress → closed`

Issue 类型为 `feature-request` 时，可转化为 feature 进入设计流程。
