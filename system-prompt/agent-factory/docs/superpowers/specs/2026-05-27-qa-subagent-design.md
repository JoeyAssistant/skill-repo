# QA Subagent Design

## 概述

在 agent-factory 体系中新增 QA subagent，解决 developer 自审自验导致的功能质量问题。QA 作为独立的技术验收角色，在两个阶段介入：

1. **验收模式**：developer 完成后，QA 执行端到端验收，确保功能符合需求和设计
2. **诊断模式**：用户使用中发现问题，QA 进行根因分析和举一反三

## 问题与动机

当前流程 developer 完成开发后直接进入 `done` 状态，存在三类问题：

| 问题类型 | 根因 |
|----------|------|
| 功能不符合预期 | Developer 只看 DESIGN.md，不对照 REQUIREMENTS.md 的用户场景验收 |
| 集成/端到端问题 | Developer 的 IT 按模块编写，缺乏跨层级场景驱动验收 |
| 开发者自测不够 | 无独立角色审查，happy path 通过即完成 |
| 问题定位困难 | 日志可定位性从未被独立审视 |

核心矛盾：developer 既是运动员又是裁判——写代码、写测试、跑测试三重角色缺乏制衡。

## 架构变更

### 新增角色

```
User ←→ PM
          ├── designer (subagent)
          ├── developer (subagent)
          ├── QA (subagent)            ← 新增
          ├── poc (subagent)
          └── spec-compliance (subagent)
```

### 调度链路

**验收模式：**
```
PM → developer → PM → QA → PM → (如需修复) → developer → PM → QA 循环
```

**诊断模式：**
```
用户报告 → PM 创建 issue → PM → QA 诊断 → QA 更新 NOTES.md → PM → developer 修复
```

### Feature 生命周期更新

```
draft → designing → approved → implementing → qa-reviewing → done
```

新增 `qa-reviewing` 状态，表示 QA 正在验收。

| 状态 | 含义 | 触发时机 |
|------|------|----------|
| qa-reviewing | QA 正在验收 | Developer 返回 complete 后 PM 调度 QA |

`implementing` 不再直接流转到 `done`，而是先到 `qa-reviewing`。

## QA 核心职责

| 职责 | 说明 |
|------|------|
| E2E 场景验收 | 启动服务，基于 REQUIREMENTS.md 的 User Scenarios 执行端到端测试 |
| 设计合规检查 | 对照 DESIGN.md 验证实现（数据结构、API、CLI、UI） |
| 根因定位 | 发现问题时追踪日志和代码定位根因，不只报现象 |
| 日志可定位性审计 | 检查出问题时能否从日志直接看出原因，不满足则要求 developer 补充 |
| 举一反三 | 发现一个问题后，全局搜索同类模式，排查同类缺陷 |

## 验收的 4 个阶段

| 阶段 | 内容 |
|------|------|
| 1. 设计合规 | 对照 DESIGN.md 检查实现：数据结构字段、API 接口签名、CLI 命令参数、UI 元素 |
| 2. E2E 场景验收 | 启动服务，按 REQUIREMENTS.md 中每个 User Scenario 走完整链路 |
| 3. 日志审计 | 对验收中发现的每个问题，检查日志是否足以定位根因 |
| 4. 举一反三 | 对已确认的问题，全局搜索同类代码模式 |

## 两种工作模式

### 模式一：验收模式（Feature Acceptance）

Developer 返回 complete 后：

1. PM 更新状态为 `qa-reviewing`
2. PM 调度 QA subagent 验收
3. QA 执行 4 阶段验收
4. QA 返回结果：
   - **pass** → PM 更新 `done`
   - **fail** → PM 将 QA 报告转交 developer 修复，不创建 issue（简化流程）
5. Developer 修复完成 → PM 再次调 QA 复验
6. 最多循环 3 轮，超过仍不通过 PM 升级给用户决策

```
QA 验收 → fail → PM 收到 QA-REPORT.md
  → PM 调 developer 修复（附带 QA 的问题清单和根因分析）
  → developer 修复完成 → PM 调 QA 复验
  → 通过 → done
```

### 模式二：诊断模式（Issue Diagnosis）

用户使用中发现问题：

1. 用户报告问题 → PM 创建 issue
2. PM 调度 QA 诊断
3. QA 执行诊断：复现 → 定位根因 → 审计日志 → 举一反三 → 评估影响
4. QA 将诊断结论写入 `.issues/<NNN>/NOTES.md`
5. QA 返回结构化结果给 PM
6. PM 调度 developer 修复（带 NOTES.md 中的诊断结论）

```
用户报告 → PM 创建 issue → PM 调 QA 诊断
  → QA 诊断后将结论写入 NOTES.md
  → QA 返回结构化结果给 PM
  → PM 调 developer 修复（带诊断结论）
```

## QA 输入格式

### 验收模式

```
## Task
验收 feature #<NNN>: <title>

## Feature Directory
.features/<NNN>-<name>/

## Instructions
1. Read REQUIREMENTS.md (User Scenarios) and DESIGN.md
2. Verify design compliance (data schema, API, CLI, UI)
3. Start services and run E2E scenarios
4. For each issue found: diagnose root cause, check log auditability
5. For confirmed issues: search for similar patterns
6. Return structured result
```

### 诊断模式

```
## Task
诊断 issue #<NNN>: <title>

## Issue Directory
.issues/<NNN>-<name>/

## Instructions
1. Read NOTES.md for issue description and reproduction steps
2. Reproduce the issue
3. Diagnose root cause (logs, code, data flow)
4. Audit log auditability for this issue
5. Search for similar patterns
6. Write diagnosis to NOTES.md
7. Return diagnosis report
```

## QA 输出格式

### 验收通过

```json
{
  "status": "pass",
  "feature_number": "<NNN>",
  "scenarios_tested": 5,
  "scenarios_passed": 5,
  "issues_found": [],
  "log_auditability": "pass",
  "summary": "<验收结论>"
}
```

### 验收不通过

```json
{
  "status": "fail",
  "feature_number": "<NNN>",
  "scenarios_tested": 5,
  "scenarios_passed": 3,
  "issues_found": [
    {
      "id": "QA-001",
      "severity": "critical | major | minor",
      "category": "functional | integration | design-mismatch | log-gap",
      "scenario": "<哪个场景发现的>",
      "symptom": "<现象>",
      "root_cause": "<根因>",
      "fix_suggestion": "<修复建议>",
      "log_auditability": "sufficient | insufficient",
      "log_improvement": "<日志改进建议，如需>",
      "similar_patterns": ["<文件:行号>"]
    }
  ],
  "summary": "<验收结论>"
}
```

### 诊断报告

```json
{
  "status": "diagnosed",
  "issue_number": "<NNN>",
  "root_cause": "<根因描述>",
  "reproduction_confirmed": true,
  "fix_suggestion": "<最小修复范围>",
  "log_auditability": "sufficient | insufficient",
  "log_improvement": "<日志改进建议>",
  "similar_patterns": [
    {"location": "<文件:行号>", "description": "<同类问题描述>"}
  ],
  "impact_assessment": "<影响范围>",
  "summary": "<诊断结论>"
}
```

## QA-REPORT.md 模板

QA 验收后生成在 feature 目录下：

```markdown
# QA Report: <feature-name>

## Result: PASS | FAIL
## Round: <验收轮次>
## Date: <YYYY-MM-DD>

## Scenario Results
| # | Scenario | Result | Notes |
|---|----------|--------|-------|
| 1 | <场景名> | PASS | ... |

## Design Compliance
| Item | Result | Notes |
|------|--------|-------|
| Data Schema | PASS | ... |
| API | PASS | ... |
| CLI | PASS | ... |

## Issues Found
### QA-001: <title>
- **Severity**: critical | major | minor
- **Category**: functional | integration | design-mismatch | log-gap
- **Root Cause**: ...
- **Fix Suggestion**: ...
- **Log Auditability**: sufficient | insufficient
- **Log Improvement**: ...
- **Similar Patterns**: ...

## Log Auditability
- Overall: sufficient | insufficient
- Details: ...

## Similar Patterns
- ...
```

## NOTES.md 模板更新（含 QA 诊断章节）

```markdown
# <Title>

## Description
<!-- 问题描述 -->

## Steps to Reproduce（bug 适用）
1. ...

## QA Diagnosis
- **Root Cause**: ...
- **Fix Suggestion**: ...
- **Log Auditability**: ...
- **Similar Patterns**: ...

## Impact
<!-- 影响范围 -->

## Resolution
<!-- 解决方式 -->
```

## 对现有角色的影响

### PM（agent-pm.md）变更

1. **生命周期**：新增 `qa-reviewing` 状态
2. **调度逻辑**：
   - Developer 返回 complete → 更新 `qa-reviewing` → 调度 QA
   - QA 返回 pass → 更新 `done`
   - QA 返回 fail → 调度 developer 修复 → 再调 QA 复验（最多 3 轮）
3. **Issue 处理**：bug issue 先调 QA 诊断，再调 developer 修复
4. **日常巡检**：增加 `qa-reviewing` 状态汇报

### Developer（developer.md）变更

1. **Bug 修复输入**：增加 QA 诊断报告引用
2. **Feature 修复输入**：增加 QA-REPORT.md 中 issues 列表引用
3. **最小变更**，不改变 developer 的核心工作方式

### Designer（designer.md）

无变更。

### Spec-compliance（spec-compliance.md）

无变更。

## 文件变更清单

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `qa.md` | 新增 | QA subagent 定义 |
| `agent-pm.md` | 修改 | 生命周期、调度逻辑、Issue 流程 |
| `developer.md` | 修改 | 输入格式增加 QA 报告引用 |
| `README.md` | 修改 | 架构图、目录结构、文件说明 |

## 修复循环控制

QA 验收失败 → developer 修复 → QA 复验，最多 **3 轮**。

超过 3 轮仍不通过，PM 将问题升级给用户决策（可能需要重新设计或调整需求范围）。

## 目录结构更新

```
.features/
  <NNN>-<name>/
    REQUIREMENTS.md
    DESIGN.md
    doc-changes/
      <filename>.diff
    QA-REPORT.md           ← 新增（QA 验收后生成）
    BLOCKED.md
    POC-REPORT.md
.issues/
  <NNN>-<name>/
    NOTES.md               ← 模板增加 QA Diagnosis 章节
    BLOCKED.md
.claude/
  agents/
    designer.md
    developer.md
    qa.md                  ← 新增
    poc.md
    spec-compliance.md
```
