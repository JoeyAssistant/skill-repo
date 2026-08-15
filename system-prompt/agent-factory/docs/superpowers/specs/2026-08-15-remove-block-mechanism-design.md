# Remove Block Mechanism from Feature/Issue Management

**Date**: 2026-08-15
**Status**: Approved (待 spec review)
**Scope**: Pure cleanup of unused `block` mechanism

## Background

agent-factory 当前为 feature 和 issue 提供了 `block` / `unblock` 机制：

- **Feature 端**：完整的状态机节点（`FeatureStatus.BLOCKED`），`block` 命令改 status，`unblock` 必须显式 `--to` 恢复
- **Issue 端**：仅作为 `BLOCKED.yaml` 文件标记（status 保持 `in_progress` 不变）

**核心问题**：
- 机制从未被实际使用（dev/QA subagent 不返回 blocked，PM 不用 block 命令）
- 增加多文件维护成本（`index.yaml` + `BLOCKED.yaml`）+ 状态机分支复杂度
- 与 PM 主动对话的工作模式冲突（PM 倾向直接问用户，不需要"冻结状态"）

**已被用户部分实现**：
- `agent_factory/doc/feature.md` 已移除 `blocked` 状态，POC 改为 designing 阶段的正常 `alt` 分支

## Goals

1. 完全删除 `block` 相关的 schema / CLI / 文件 / 文档
2. 保留 POC subagent 能力和 designing 阶段调度 POC 的能力
3. 更新 PM 提示词：「卡住怎么办」改为 PM 直接在对话中问用户
4. 同步更新 subagent 定义（developer / poc）返回格式

## Non-Goals

- 不引入新的"等待输入"状态（特性是清理，不是替换）
- 不提供 migration 工具（假定历史项目无 blocked 残留）
- 不修改历史设计文档（`docs/2026-08-09-cli-command-set-*.md`）
- 不重构 feature/issue 状态机其他部分

## Design

### 1. Schema 删减

**删除整个文件**：
- `agent_factory/schema/blocked.py`（`BlockedRecord` 类）

**修改**：
- `agent_factory/schema/feature.py`：删除 `FeatureStatus.BLOCKED = "blocked"`
- `agent_factory/schema/__init__.py`：删除 `BlockedRecord` 导入和导出

**保留**：
- `FeatureStatus` 其他 7 个状态：`draft` / `designing` / `approved` / `implementing` / `qa-reviewing` / `done` / `cancelled`
- `IssueStatus` 维持 3 个状态：`open` / `in_progress` / `closed`（原本就没 blocked）

### 2. CLI 删减

**删除命令**：
- `agent-factory feature block <id> --reason --action`
- `agent-factory feature unblock <id> --to`
- `agent-factory issue block <id> --reason --action`
- `agent-factory issue unblock <id> --to`

**修改状态机**：
- `agent_factory/cli/feature.py`：
  - `ALLOWED_TRANSITIONS` 中删除 `FeatureStatus.BLOCKED` 作为目标 / 源
  - `DESIGNING` 仅允许 `→ APPROVED / CANCELLED`
  - `IMPLEMENTING` 仅允许 `→ QA_REVIEWING`
- 进出口提示文本中移除 `block / unblock`

### 3. 文档删减

**删除整个文件**：
- `agent_factory/schema/examples/blocked.yaml`

**修改**：
- `agent-pm.md`：
  - §生命周期 状态机图删除 `↘ blocked ↗`
  - §Lifecycle 表格删除 `blocked` 行
  - §任务调度 场景 8 修订：「tech-feasibility blocked」 → 「designing 阶段 PM 判断需要技术可行性」
  - §跨环境 Issue 处理 Step 2 表格：「block 标记」 → 「PM 在对话中询问用户」
  - §状态管理 表删除 `BLOCKED.yaml` 行
  - §日常巡检 状态汇报删除 `blocked 项数`
  - **整节删除** `## Blocked 处理`（含 `### Tech-Feasibility Blocked 处理流程` + `### 解除阻塞`）
- `developer.md`：
  - 删除 "On blocker" 步骤（场景 2 / 场景 5 / 场景 7）
  - 删除 `status: "blocked"` 返回值示例
  - 删除 `BLOCKED.md` 创建说明
- `poc.md`：
  - 删除 `status: "blocked"` 返回值示例
- `README.md`：
  - 目录树删除 `BLOCKED.yaml` 行
  - 状态机图删除 `blocked`

**保留**：
- `agent_factory/doc/feature.md`（用户已改）
- `agent_factory/doc/issue.md`（本就没 blocked）
- 历史文档 `docs/2026-08-09-cli-command-set-{design,plan}.md`

### 4. POC 流程改名

**调度机制变更**：
- **旧**：`feature block <id> --reason "tech-feasibility"` → 调度 POC → `feature unblock <id> --to designing`
- **新**：PM 在 designing 阶段判断需要技术可行性 → 直接用 Agent tool 调度 POC subagent → POC 返回 POC-REPORT.md → PM 把报告给用户 → 用户决策 → PM 继续 designing

**PM 提示词场景 8 修订**：

```
#### 场景 8: POC（技术可行性）

**调度时机**：PM 在 designing 阶段判断需要技术可行性 / 选型验证

**Feature Directory**: `<Root>/.features/<id>/`

**Instructions**:
1. 逐一分析每个技术问题
2. 通过 web search、文档查询等方式调研
3. 对高风险项编写 POC 验证代码并运行
4. 输出评估报告到 POC-REPORT.md
5. Return structured result
```

**对比修改前**：去掉 `## Questions: <PM 在 blocked_reason 中提出的技术问题清单>`，改为 `## Questions: <PM 在 designing 时发现的技术问题清单>`（如果保留此字段）。

### 5. 测试删减

**删除整个文件**：
- `agent_factory/schema/tests/test_blocked.py`

**删除测试函数**：
- `test_cli_feature.py`：`test_feature_block_creates_blocked_yaml` / `test_feature_block_already_blocked` / `test_feature_unblock_removes_blocked_yaml_and_restores_status` / `test_feature_unblock_not_blocked`
- `test_cli_issue.py`：`test_issue_block_unblock`

**修改测试**：
- `test_feature.py`：状态计数 `8 states` → `7 states`；删除 `FeatureStatus.BLOCKED` 断言
- `test_enums.py`：状态集合删除 `"blocked"`

**验证**：
- 跑 `pytest agent_factory/schema/tests/` 全部通过
- 跑 `agent-factory --help` / `feature --help` / `issue --help` 命令清单无 block 相关条目

### 6. 「卡住怎么办」新流程

**旧**：PM 触发 `block` 命令 → 状态冻结 → 等用户 → `unblock` 恢复

**新**：PM 在对话中直接问用户（**通过 prompt-engineering，不再依赖状态机**）

边界场景处理：

| 场景 | 旧行为 | 新行为 |
|------|--------|--------|
| PM 在 designing 阶段遇到技术不确定 | `feature block --reason tech-feasibility` + 调度 POC | 直接调度 POC，或直接在对话中问用户（PM 自主判断） |
| Developer 在 implementing 阶段遇到障碍 | `issue block --reason` + PM 处理 | Developer 返回 `fail` 状态 + 结构化 `reason` 字段，PM 在对话中问用户 |
| QA 发现需求不清晰 | `issue block --reason clarification-needed` | QA 报告写 `reason` 字段，PM 读报告在对话中问用户 |
| 跨环境 Issue 内容模糊 | `issue block` 等用户澄清 | PM 直接在对话中询问用户 |

**关键约束**：
- PM 主导对话节奏，不需要"状态冻结"作为信号
- Subagent 返回 `complete | fail` 二元状态（**移除 `blocked` 状态**），失败时附 `reason` 字段供 PM 决策
- 「卡住」对 PM 而言 = 「在对话中等待用户回复」，不是「状态机节点」

## Impact Analysis

### 删除清单

| 类别 | 路径 |
|------|------|
| Schema | `agent_factory/schema/blocked.py` |
| Schema | `agent_factory/schema/feature.py` 的 `BLOCKED` 枚举 |
| Schema | `agent_factory/schema/__init__.py` 的 `BlockedRecord` 引用 |
| CLI | `agent_factory/cli/feature.py` 的 `block` / `unblock` 命令 + 状态机 |
| CLI | `agent_factory/cli/issue.py` 的 `block` / `unblock` 命令 |
| Example | `agent_factory/schema/examples/blocked.yaml` |
| Test | `agent_factory/schema/tests/test_blocked.py` |
| Test | `test_cli_feature.py` 中 4 个 block/unblock 测试 |
| Test | `test_cli_issue.py` 中 1 个 block/unblock 测试 |
| Test | `test_feature.py` / `test_enums.py` 的 blocked 断言 |
| Docs | `agent-pm.md` §Blocked 处理 整节 |
| Docs | `agent-pm.md` 状态机图、状态表、状态管理表、巡检表中的 blocked |
| Docs | `developer.md` / `poc.md` 的 blocked 返回值 |
| Docs | `README.md` 目录树 + 状态机图 |

### 保留清单

- `poc.md` subagent 整体定义
- `developer.md` 整体定义（只删 block 相关）
- `agent_factory/doc/feature.md`（用户已改）
- `agent_factory/doc/issue.md`（本就干净）
- 历史文档 `docs/2026-08-09-cli-command-set-*.md`
- 4 个 PMC 状态机节点（draft/designing/approved/implementing/qa-reviewing/done/cancelled）

### 风险与缓解

| 风险 | 概率 | 缓解 |
|------|------|------|
| 历史项目有 `BLOCKED.yaml` / `status=blocked` 残留 | 低（用户确认未用过） | 实施前先 grep 整个仓库确认无残留数据 |
| 删除后 subagent 文档与 PM 提示词不一致 | 中 | 同步删除 developer.md / poc.md 的 blocked 引用 |
| 状态机变更破坏示例 YAML | 低 | `examples/blocked.yaml` 一并删除 |
| 跨环境 Issue 「内容模糊」处理失去支撑 | 中 | 新流程依赖 PM 主动询问用户——在 PM 提示词中显式说明 |

## Success Criteria

1. `grep -rn -i "block" agent_factory/` 在 schema/CLI/example/test 路径下无残留（除历史设计文档外）
2. `agent-factory --help` / `feature --help` / `issue --help` 无 block / unblock 命令
3. `pytest agent_factory/schema/tests/` 全部通过
4. `agent-pm.md` 不含 §Blocked 处理章节
5. `developer.md` / `poc.md` 不含 `status: blocked` 返回值描述
6. `feature.md` / `issue.md` 状态机仅含允许的状态
7. `README.md` 状态机图与实际一致

## Implementation Plan

下一步走 `superpowers:writing-plans` 流程，输出详细实施计划。
