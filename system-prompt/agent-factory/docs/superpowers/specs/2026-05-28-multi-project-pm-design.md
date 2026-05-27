# Multi-Project PM Design

## Goal

Extend agent-pm to manage multiple agent projects simultaneously, while maintaining full backward compatibility with single-project mode.

## Core Requirements

1. **Backward compatible**: Single-project mode behavior unchanged (detect `.features/` → single-project)
2. **Multi-project mode**: PM manages multiple agent projects, each with independent git repo
3. **Feature/Issue locations unchanged**: `.features/` and `.issues/` stay within each project directory
4. **Independent numbering**: Each project has its own 001-999 sequence
5. **Globally shared subagents**: Subagent definitions stored once in workspace `.claude/agents/`, not duplicated per project
6. **No deployment for now**: Deployment management deferred to future iteration

## Mode Detection

PM detects mode at startup:

```
Priority:
1. Current directory has .workspace/ → multi-project mode
2. Current directory has .features/ → single-project mode
3. Neither → prompt user to initialize (create workspace or features directory)
```

Single-project mode: all existing PM behavior preserved. Project's own `.claude/agents/` takes precedence.

## Workspace Structure

```
~/agent-workspace/          ← Claude Code runs here
├── .claude/
│   └── agents/
│       ├── designer.md
│       ├── developer.md
│       ├── qa.md
│       ├── poc.md
│       └── spec-compliance.md
├── .workspace/
│   └── projects.md         ← project registry
├── football-agent/         ← independent git repo
├── news-agent/             ← independent git repo
└── CLAUDE.md               ← agent-pm content (as system prompt)
```

## Project Registry (projects.md)

```markdown
# Projects

| ID | Name | Path | Status | Created | Last Active |
|----|------|------|--------|---------|-------------|
| football | football-agent | ./football-agent | active | 2026-05-28 | 2026-05-28 |
| news | news-agent | ./news-agent | active | 2026-05-27 | 2026-05-27 |
```

Fields:
- `ID`: short identifier, used to specify project in conversations (e.g., `@football feature #001`)
- `Path`: relative to workspace root
- `Status`: `active` (normal) / `archived` (skipped in巡检)

Operations:
- "Register new project" → PM adds entry to projects.md + initializes `.features/` `.issues/` in target dir
- "Register existing project" → PM adds entry pointing to existing directory
- "Archive project" → set status to archived, skip in daily巡检

Initialization: When registering a project, PM checks if target directory has `.features/` and `.issues/`, creates them if missing.

## Multi-Project PM Workflow

### Daily巡检 (Multi-Project)

PM scans all active projects and reports summary:

```
📊 项目状态总览

| 项目 | Draft | Designing | Approved | Implementing | QA-Reviewing | Blocked | Open Issues |
|------|-------|-----------|----------|--------------|--------------|---------|-------------|
| football | 1 | 0 | 2 | 0 | 1 | 0 | 3 |
| news | 0 | 1 | 0 | 0 | 0 | 1 | 0 |

待处理事项：
- football: 2 个 approved 待开发，1 个 qa-reviewing 待验收，3 个 open issue
- news: 1 个 designing 中，1 个 blocked 需处理
```

### Subagent Dispatch

When PM dispatches a subagent, the prompt includes the project's absolute path:

```
## Task
实现 feature #002: 收入统计功能

## Project
Name: football-agent
Root: ./football-agent

## Feature Directory
./football-agent/.features/002-income-stats/

## Instructions
...
```

### Background Dispatch (Non-Blocking)

PM dispatches subagents using `run_in_background: true` to avoid blocking the main conversation.

PM behavior:
- After dispatching, immediately returns to conversation, informs user "已调度 XXX 处理 feature #NNN"
- User can continue discussing requirements, submitting issues, etc.
- When subagent completes, PM receives notification, processes result and reports

PM maintains an in-memory dispatch table:

```
📋 进行中的任务：
- football / feature #002 → developer（后台运行中）
- news / feature #001 → designer（后台运行中）
```

Conflict protection: Do not dispatch duplicate subagent for the same feature/issue (check if already running).

### Ralph-Loop (Multi-Project)

Each iteration scans all active projects:
1. Read `.features/index.md` and `.issues/index.md` per project
2. Select next todo by global priority (P1 > P2 > P3) and project order
3. Process one item, report progress

```
🔄 Ralph-Loop 迭代 #3
- football: 调度 developer 实现 feature #002
- news: 调度 designer 设计 feature #001
- 剩余: football 2个blocked, news 1个draft(待讨论)
```

Ralph-Loop also uses background dispatch where possible, processing completed tasks and dispatching new ones each iteration (parallelism across projects).

### User Project Specification

Users can specify or omit project in conversations:
- "football 的 feature #001 怎么样了" → PM locates football project
- "帮我建个新功能" → PM asks which project (if ambiguous in multi-project mode)
- Single-project mode: no project specification needed

## Subagent Definition Changes

Mechanical change only: path resolution from "current directory" to "resolve from PM-passed project root".

### Input Format Change

Each subagent prompt gets a new `## Project` section:

```
## Project
Name: <project-name>
Root: <project-root-path>
```

### Path Resolution Rule

- Single-project mode: `Root` is `.` (current directory), identical to existing behavior
- Multi-project mode: `Root` is relative or absolute path to the project
- All paths originally hardcoded to project root (`.features/`, `.issues/`, `doc/`, `agent/`, etc.) resolve based on `Root`

### Per-Subagent Impact

| Subagent | Change |
|----------|--------|
| designer.md | `.features/<NNN>/` → `{Root}/.features/<NNN>/`, `doc/` → `{Root}/doc/` |
| developer.md | All project-relative paths prefixed with `{Root}` |
| qa.md | All project-relative paths prefixed with `{Root}` |
| poc.md | All project-relative paths prefixed with `{Root}` |
| spec-compliance.md | No change (called by designer, operates on already-resolved paths) |

Workflow logic, output format, and responsibility boundaries remain unchanged.

## Feature = Commit

Developer subagent must commit code as part of the implementation workflow.

### Developer Flow (Updated)

```
1. Read DESIGN.md
2. Apply doc-changes/*.diff
3. Update index.md status to "implementing"
4. Implement all code per design
5. Run tests
6. git add + git commit (NEW)
7. On success: update index.md status to "qa-reviewing", return complete
8. On blocker: update index.md status to "blocked", return blocked
```

### Commit Message Convention

Multi-project mode:
```
feat(<project-id>): <feature title> (#<NNN>)

<DESIGN.md summary, 1-2 sentences>
```

Single-project mode:
```
feat: <feature title> (#<NNN>)

<DESIGN.md summary, 1-2 sentences>
```

QA fix:
```
fix(<project-id>): 修复 QA 发现的 <issue summary> (#<NNN>)

QA round N: <what was fixed>
```

### When NOT to Commit

- Bug fix via issue (PM decides commit strategy)
- Blocked (code incomplete)

## agent-pm.md Structure Changes

Existing content preserved, new sections added:

| Section | Change Type | Description |
|---------|-------------|-------------|
| 核心职责 | Minor | Add "多项目调度" |
| Agent参考架构 | Minor | Add workspace layer to diagram |
| 模式检测 | New | Detection logic |
| 多项目管理 | New | projects.md format, register/unregister, initialization |
| PM 工作模式 - 日常巡检（多项目） | New | Multi-project status report |
| PM 工作模式 - Ralph-Loop（多项目） | New | Cross-project loop logic |
| PM 工作模式 - 交互式讨论 | Minor | Add project specification |
| 任务调度 | Minor | Subagent prompt adds Project section, background dispatch |
| Feature Management | Unchanged | |
| Issue Management | Unchanged | |
| PM 初步 Review | Unchanged | |
| Blocked 处理 | Unchanged | |
| 状态管理 | Unchanged | |
| 日常巡检 | Refactored | Merged into PM 工作模式 |
