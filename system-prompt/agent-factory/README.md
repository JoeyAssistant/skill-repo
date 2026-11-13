# Agent Factory - PM-Driven Agent System

PM 驱动的 AI Agent 开发体系。PM 作为用户主入口，管理 feature 和 issue，直接完成需求设计与前端实现；developer 负责 backend、业务模块及其他非前端代码，QA 对完整交付做独立验收。

## 架构

### 单项目模式

```
User ←→ PM (agent-pm.md, system prompt)
            ├── developer (subagent, .claude/agents/developer.md)       # 非前端实现与修复
            ├── qa (subagent, .claude/agents/qa.md)                      # feature 验收
            ├── qa-diagnosis (subagent, .claude/agents/qa-diagnosis.md)  # issue 定位分析
            └── poc (subagent, .claude/agents/poc.md)

PM 在 feature worktree 中展示真实前端，与用户逐步确认页面和交互，所见即所得；在 designing 阶段修改 doc/ 并自检，向用户展示 git diff 审核。
implementing 阶段先由 developer 完成非前端任务，再由 PM 完成前端与接口联动；全部完成并有提交证据后进入 QA。仅前端需求由 PM 完成，仅非前端需求由 developer 完成。
```

### 多项目模式

```
User ←→ PM (agent-pm.md, system prompt)
            ├── .workspace/projects.md (项目注册表)
            ├── Project A (独立 git 仓) ──┐
            ├── Project B (独立 git 仓) ──┤── 共享 subagents
            └── ...                       │
            ├── developer (subagent)     ──┤
            ├── qa (subagent)               │
            ├── qa-diagnosis (subagent)     │
            └── poc (subagent)              ┘
```

## 安装

一键部署到目标项目（自动完成 subagents 复制、设计参考资产、`.features/` `.issues/` 初始化、git init）：

```bash
script/init-project.sh <target-project-dir> [--prod <prod-root>] [--base-branch <ref>]
```

- `--prod <path>`：生成 `topology: split` 配置
- `--base-branch <ref>`：写入默认基线分支（如 `origin/dev`），顶层 feature 直接采用，不再询问

`agent-factory.yaml` **仅在缺失时生成，已存在则跳过**——重跑部署不会覆盖手写配置（`base_branch`、`prod.log`、`prod.data` 等）。检测到 `--prod` / `--base-branch` 与现有配置不一致时会告警，提示手工编辑。

### 1. 设置 PM 为 system prompt

将 `agent-pm.md` 的内容作为项目的 system prompt 使用：
- 通过 Claude Code 的 `--system-prompt` 参数
- 或写入项目的 `CLAUDE.md`
- 或通过 Claude Code 的 append-system-prompt 机制

### 2. 安装 subagents 与设计资产

将 subagents 与 PM 设计参考资产复制到项目的 `.claude/agents/` 目录（agent-factory 资产落点，不进项目根）：

```bash
mkdir -p <project-root>/.claude/agents
cp developer.md qa.md qa-diagnosis.md poc.md design-reference.md agent-architecture.drawio browser-reference.md <project-root>/.claude/agents/
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
cp <agent-factory>/qa-diagnosis.md .claude/agents/
cp <agent-factory>/poc.md .claude/agents/

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

## 零足迹部署（协作项目）

团队协作仓不能出现 agent-factory 痕迹时的部署方式。

### 1. 安装资产与本地排除

subagents 与配置统一放在 `.claude/agents/`（agent-factory 资产落点）：

```bash
mkdir -p <project>/.claude/agents
cp developer.md qa.md qa-diagnosis.md poc.md design-reference.md agent-architecture.drawio browser-reference.md <project>/.claude/agents/
```

状态目录与（如被跟踪的）`.claude/` 加入本地排除——**不写 .gitignore**（.gitignore 本身进仓，暴露痕迹）：

```bash
printf '.features/\n.issues/\n.claude/\n' >> <project>/.git/info/exclude
```

### 2. 环境配置

创建 `<project>/.claude/agents/agent-factory.yaml`：

```yaml
topology: split                  # 可选：dev 与 prod 分离；缺省 unified
prod:
  root: /abs/path/to/prod-deploy
base_branch: origin/dev          # 可选：顶层 feature 的默认基线分支
```

一体项目无需此文件（默认 unified）；如需固定基线分支，可只写 `base_branch`。

### 3. 启动

`claude` 可替换为自己的包装命令/别名；split 时 `--add-dir` 授权读取 prod：

```bash
pm() {
  local prod_root=$(grep -E '^\s*root:' .claude/agents/agent-factory.yaml 2>/dev/null | head -1 | awk '{print $2}')
  claude \
    --append-system-prompt "$(cat .claude/agents/agent-pm.md)" \
    ${prod_root:+--add-dir "$prod_root"}
}
```

### 4. prod 只读硬兜底（建议）

用户级 `~/.claude/settings.json` 添加（路径限定，不影响其他项目）：

```json
{
  "permissions": {
    "deny": ["Edit(/abs/path/to/prod/**)", "Write(/abs/path/to/prod/**)"]
  }
}
```

> agent-factory 资产（prompt + subagents + CLI）可在任意 Claude Code 会话中使用，驱动方式不限。

## 使用

### 交互模式：讨论需求

```
用户: 我想做一个财务日报功能
PM:   [先阅读相关文档，再创建 feature #NNN，引导讨论背景、价值、范围]
PM:   [涉及前端时，在 feature worktree 的真实项目前端展示可操作效果，逐步确认]
用户: 确认范围
PM:   [整理 FEATURE.yaml，自己写 doc/ 并自检]
用户: [review git diff]
PM:   [调度 developer 完成本需求涉及的非前端任务]
PM:   [非前端完成后，完成前端与真实接口联动、测试、自检并提交]
PM:   [全部实现完成且有提交证据后，调度 QA 独立验收]
```

### 交互模式：提交 Issue

```
用户: 登录页面点击提交就崩溃了
PM:   [创建 issue #NNN，确认复现步骤]
PM:   [审核: bug → 调度 qa-diagnosis 定位 → 分析完成后转 feature]
```

### 直接调用 subagent

用户也可以跳过 PM，直接调用 subagent：

```
用户: Use the developer agent to implement the backend of feature #003
```

## 项目目录结构

```
project-root/
  .features/
    index.yaml
    <id>/
      FEATURE.yaml
      POC-REPORT.md
      QA-REPORT.md
      poc/
      workflow-issues/        ← 工作流优化项，一项一文件（字段复用 ISSUE.yaml）
        <NNN>-<slug>.yaml
  .issues/
    index.yaml
    <id>/
      ISSUE.yaml
  .claude/
    agents/
      developer.md
      qa.md
      qa-diagnosis.md
      poc.md
  src/
    modules/
      <module_name>/
    backend/
      app.py
      common/
      <service_name>/
    frontend/
    skill/
    mcp/
  doc/
    modules/
      <module_name>/
    backend/
      README.md
      <service_name>/
  test/
    unit/
      <module_name>/
  script/
```

## 多项目工作区目录结构

```
agent-workspace/
├── .claude/
│   └── agents/
│       ├── developer.md
│       ├── qa.md
│       ├── qa-diagnosis.md
│       └── poc.md
├── .workspace/
│   └── projects.md
├── football-agent/         ← 独立 git 仓
│   ├── .features/
│   ├── .issues/
│   ├── src/
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
| `agent-pm.md` | PM system prompt，用户主入口，负责需求设计、前端实现与工作流调度 |
| `design-reference.md` | PM 设计阶段按需参考手册 |
| `browser-reference.md` | 浏览器通道操作手册，所有 agent 共用（检测通道 → 建立通道 → 证据） |
| `developer.md` | Developer subagent 定义，负责非前端代码实现与修复 |
| `qa.md` | QA subagent 定义，独立验收 PM 与 developer 的完整交付 |
| `qa-diagnosis.md` | Issue 定位分析 subagent 定义 |
| `poc.md` | POC subagent 定义，负责技术可行性分析和验证 |

## Schema 模块

PM 工作流 YAML 文件的 schema 定义在 `agent_factory/schema/` 目录：

| 文件 | 内容 |
|------|------|
| `agent_factory/schema/enums.py` | 枚举（Priority / FeatureStatus / 等） |
| `agent_factory/schema/feature.py` | Feature / Decision / Option 模型 |
| `agent_factory/schema/issue.py` | Issue 模型 |
| `agent_factory/schema/index.py` | FeatureIndex / IssueIndex 模型 |
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

`cancelled` 可从任何状态直接流转。

### Issue

`open → in_progress → closed`

Issue 类型为 `feature-request` 时，可转化为 feature 进入设计流程。
