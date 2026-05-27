# Agent Factory - PM-Driven Agent System

PM 驱动的 AI Agent 开发体系。PM 作为用户主入口，管理 feature 和 issue，调度 designer 和 developer subagent 完成设计与开发。

## 架构

```
User ←→ PM (agent-pm.md, system prompt)
            ├── designer (subagent, .claude/agents/designer.md)
            ├── developer (subagent, .claude/agents/developer.md)
            ├── qa (subagent, .claude/agents/qa.md)
            ├── poc (subagent, .claude/agents/poc.md)
            └── spec-compliance (subagent, .claude/agents/spec-compliance.md)
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
cp designer.md <project-root>/.claude/agents/designer.md
cp developer.md <project-root>/.claude/agents/developer.md
cp qa.md <project-root>/.claude/agents/qa.md
cp poc.md <project-root>/.claude/agents/poc.md
cp spec-compliance.md <project-root>/.claude/agents/spec-compliance.md
```

### 3. 初始化目录结构

在项目根目录创建 feature 和 issue 管理目录：

```bash
mkdir -p .features .issues
```

## 使用

### 交互模式：讨论需求

```
用户: 我想做一个财务日报功能
PM:   [创建 feature #NNN，引导讨论背景、价值、范围]
用户: 确认范围
PM:   [整理 requirement brief，调度 designer]
用户: [review 设计]
PM:   [调度 developer]
```

### 交互模式：提交 Issue

```
用户: 登录页面点击提交就崩溃了
PM:   [创建 issue #NNN，确认复现步骤]
PM:   [triage: bug → 调度 developer 直接修复]
```

### Ralph-Loop 模式：批量处理

```bash
/ralph-loop "PM: 处理所有待办需求和issue" --completion-promise "PM_BATCH_COMPLETE" --max-iterations 20
```

PM 会自动：
1. 检查 open issue → triage
2. 检查 draft feature → 调度 designer
3. 检查 approved feature → 调度 developer
4. 检查 blocked item (tech-feasibility) → 调度 POC 分析
5. 检查 blocked item (其他) → 尝试继续
6. 全部处理完毕后输出 `<promise>PM_BATCH_COMPLETE</promise>`
5. 全部处理完毕后输出 `<promise>PM_BATCH_COMPLETE</promise>`

### 直接调用 subagent

用户也可以跳过 PM，直接调用 subagent：

```
用户: Use the designer agent to design feature #004
用户: Use the developer agent to implement feature #003
```

## 项目目录结构

```
project-root/
  .features/
    index.md
    <NNN>-<name>/
      DESIGN.md
      doc-changes/
        <filename>.diff
      BLOCKED.md          # blocked 时创建
      POC-REPORT.md       # 技术可行性评估报告（tech-feasibility blocked 时生成）
      QA-REPORT.md        # QA 验收报告（QA 验收后生成）
      poc/                # POC 验证代码（验证完成后保留）
  .issues/
    index.md
    <NNN>-<name>/
      NOTES.md
      BLOCKED.md          # blocked 时创建
  .claude/
    agents/
      designer.md
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

## 文件说明

| 文件 | 用途 |
|------|------|
| `agent-pm.md` | PM system prompt，用户主入口 |
| `designer.md` | Designer subagent 定义，负责设计文档输出 |
| `developer.md` | Developer subagent 定义，负责代码实现 |
| `qa.md` | QA subagent 定义，负责功能验收和问题诊断 |
| `poc.md` | POC subagent 定义，负责技术可行性分析和验证 |
| `spec-compliance.md` | 规范合规检查 subagent（designer 内部调用） |

## 生命周期

### Feature

`draft` → `designing` → `blocked` → `approved` → `implementing` → `blocked` → `qa-reviewing` → `done` → `cancelled`

### Issue

`open` → `triaging` → `closed`

Issue 类型为 `feature-request` 时，可转化为 feature 进入设计流程。
