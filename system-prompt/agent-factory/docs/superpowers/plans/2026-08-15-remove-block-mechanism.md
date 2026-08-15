# Remove Block Mechanism Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完全删除 agent-factory 中 feature/issue 的 `block` 机制（schema / CLI / 文档 / 测试），保留 POC subagent 作为 designing 阶段的正常分支。

**Architecture:** 自底向上清理 — 先 schema → 再 CLI → 再 examples → 再 tests → 最后 PM 提示词 / subagent 文档 / README。每个独立单元独立 commit。

**Tech Stack:** Python 3 + pydantic + click + pytest

**Spec:** `docs/superpowers/specs/2026-08-15-remove-block-mechanism-design.md`

---

## Task 0: Pre-flight baseline verification

**Files:**
- Read: `agent_factory/schema/tests/`

- [ ] **Step 1: Run full test suite to confirm baseline green**

Run: `cd /Users/zhuowentao/Workspace/repos/JoeyAssistant/skill-repo/system-prompt/agent-factory && python3 -m pytest agent_factory/schema/tests/ -v 2>&1 | tail -30`

Expected: All tests pass. Record the final `passed` count for later comparison.

- [ ] **Step 2: Confirm no blocked YAML files in repo**

Run: `find . -name "BLOCKED.yaml" -o -name "BLOCKED.md" 2>/dev/null | grep -v ".git/"`

Expected: Empty output (no historical blocked data, per user confirmation).

- [ ] **Step 3: Record working dir state**

Run: `git status --short && git log -1 --oneline`

Expected: Working tree has only `agent_factory/doc/feature.md` (M) and the spec file (A). Record commit sha for later.

---

## Task 1: Schema — delete blocked.py module

**Files:**
- Delete: `agent_factory/schema/blocked.py`
- Modify: `agent_factory/schema/__init__.py:9,27,50-51`

- [ ] **Step 1: Update test_enums.py to expect 7 states (preparation for deletion)**

Modify `agent_factory/schema/tests/test_enums.py` line 23-24:

```python
def test_feature_status_lifecycle():
    """FeatureStatus 覆盖完整生命周期"""
    expected = {"draft", "designing", "approved", "implementing",
                "qa-reviewing", "done", "cancelled"}
    actual = {s.value for s in FeatureStatus}
    assert actual == expected
```

Run: `python3 -m pytest agent_factory/schema/tests/test_enums.py::test_feature_status_lifecycle -v`

Expected: FAIL with `AssertionError: assert {actual contains 'blocked'} == {expected without 'blocked'}`

- [ ] **Step 2: Delete `blocked.py` module**

Run: `git rm agent_factory/schema/blocked.py`

Expected: `rm 'agent_factory/schema/blocked.py'`

- [ ] **Step 3: Update `__init__.py` to remove BlockedRecord references**

Modify `agent_factory/schema/__init__.py`:

Delete line 9 (`- BlockedRecord：阻塞记录`)
Delete line 27 (`from agent_factory.schema.blocked import BlockedRecord`)
Delete line 50 (`    # Blocked`)
Delete line 51 (`    "BlockedRecord",`)

Final `__init__.py` should be:

```python
# agent_factory/schema/__init__.py
"""agent-factory PM 工作流 schema.

提供 5 个核心模型：
- Feature：feature 需求规格
- Issue：issue 报告
- FeatureIndex / FeatureIndexItem：feature 索引
- IssueIndex / IssueIndexItem：issue 索引
"""
from agent_factory.schema.enums import Priority
from agent_factory.schema.feature import AgentType, FeatureStatus
from agent_factory.schema.issue import IssueStatus
from agent_factory.schema.feature import Background, Feature, ModuleSpec, FeatureTestCase
from agent_factory.schema.issue import (
    BugfixResult,
    FeatureRequestResult,
    Issue,
    IssueResult,
)
from agent_factory.schema.index import (
    FeatureIndex,
    FeatureIndexItem,
    IssueIndex,
    IssueIndexItem,
)

__all__ = [
    # 枚举
    "AgentType",
    "FeatureStatus",
    "IssueStatus",
    "Priority",
    # Feature 系列
    "Feature",
    "Background",
    "ModuleSpec",
    "FeatureTestCase",
    # Issue
    "Issue",
    "BugfixResult",
    "FeatureRequestResult",
    "IssueResult",
    # Index 系列
    "FeatureIndex",
    "FeatureIndexItem",
    "IssueIndex",
    "IssueIndexItem",
]
```

- [ ] **Step 4: Run enums test to verify Step 1 fix was on the right path (still fails — next task fixes it)**

Run: `python3 -m pytest agent_factory/schema/tests/test_enums.py::test_feature_status_lifecycle -v`

Expected: FAIL with `ImportError: cannot import name 'BlockedRecord' from 'agent_factory.schema'` (because `__init__.py` no longer exports it, but `feature.py` still has BLOCKED enum).

Note: This is expected. The actual fix is in Task 2.

- [ ] **Step 5: Do NOT commit yet — proceed to Task 2**

---

## Task 2: Schema — remove BLOCKED from FeatureStatus

**Files:**
- Modify: `agent_factory/schema/feature.py:26`

- [ ] **Step 1: Remove BLOCKED enum value**

Modify `agent_factory/schema/feature.py`:

Delete line 26:
```python
    BLOCKED = "blocked",
```

Final `FeatureStatus` enum (lines 18-27) should be:

```python
class FeatureStatus(str, Enum):
    """Feature 生命周期状态."""
    DRAFT = "draft"
    DESIGNING = "designing"
    APPROVED = "approved"
    IMPLEMENTING = "implementing"
    QA_REVIEWING = "qa-reviewing"
    DONE = "done"
    CANCELLED = "cancelled"
```

- [ ] **Step 2: Run enums test to verify pass**

Run: `python3 -m pytest agent_factory/schema/tests/test_enums.py::test_feature_status_lifecycle -v`

Expected: PASS

- [ ] **Step 3: Run full schema test suite to check nothing else broke**

Run: `python3 -m pytest agent_factory/schema/tests/ -v 2>&1 | tail -40`

Expected: Many FAILs (CLI still references BLOCKED, tests reference blocked files). This is expected — Tasks 3-5 fix them.

- [ ] **Step 4: Commit schema changes**

```bash
git add agent_factory/schema/__init__.py agent_factory/schema/feature.py agent_factory/schema/blocked.py agent_factory/schema/tests/test_enums.py
git commit -m "$(cat <<'EOF'
refactor(schema): 删除 BlockedRecord + FeatureStatus.BLOCKED

block 机制从未被实际使用，清理 schema 层冗余。
- 删除 agent_factory/schema/blocked.py
- FeatureStatus 从 8 状态减为 7 状态
- 同步更新 test_enums.py 期望

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: CLI — delete feature block/unblock commands

**Files:**
- Modify: `agent_factory/cli/feature.py:17,26,364,366,368,449-514`

- [ ] **Step 1: Update test_cli_feature.py to remove block/unblock tests (preparation)**

Delete these 4 test functions from `agent_factory/schema/tests/test_cli_feature.py`:
- `test_feature_block_creates_blocked_yaml` (lines 505-525)
- `test_feature_block_already_blocked` (lines 528-535)
- `test_feature_unblock_removes_blocked_yaml_and_restores_status` (lines 538-552)
- `test_feature_unblock_not_blocked` (lines 555-561)

Also remove the blank line after the previous test function and the blank line before `test_feature_delete_requires_force` to keep formatting clean.

- [ ] **Step 2: Run test_cli_feature.py to verify it fails due to existing commands**

Run: `python3 -m pytest agent_factory/schema/tests/test_cli_feature.py -v 2>&1 | tail -20`

Expected: FAIL with `ImportError` or `AttributeError` referencing `BlockedRecord` (still imported in `feature.py`).

- [ ] **Step 3: Remove BLOCKED imports and command from feature.py**

Modify `agent_factory/cli/feature.py`:

**Line 17** — change:
```python
from agent_factory.schema import Feature, FeatureIndex, FeatureIndexItem, BlockedRecord
```
to:
```python
from agent_factory.schema import Feature, FeatureIndex, FeatureIndexItem
```

**Line 26** — change:
```python
    命令：new / set / show / list / transition / block / unblock / delete
```
to:
```python
    命令：new / set / show / list / transition / delete
```

**Lines 364, 366, 368** — modify `ALLOWED_TRANSITIONS`:

```python
ALLOWED_TRANSITIONS = {
    FeatureStatus.DRAFT: {FeatureStatus.DESIGNING, FeatureStatus.CANCELLED},
    FeatureStatus.DESIGNING: {FeatureStatus.APPROVED, FeatureStatus.CANCELLED},
    FeatureStatus.APPROVED: {FeatureStatus.IMPLEMENTING, FeatureStatus.CANCELLED},
    FeatureStatus.IMPLEMENTING: {FeatureStatus.QA_REVIEWING},
    FeatureStatus.QA_REVIEWING: {FeatureStatus.DONE, FeatureStatus.IMPLEMENTING},  # QA fail → implementing
    FeatureStatus.DONE: set(),
    FeatureStatus.CANCELLED: set(),
}
```

**Lines 449-514** — delete the entire `block` and `unblock` commands (66 lines including decorators).

- [ ] **Step 4: Run test_cli_feature.py to verify pass**

Run: `python3 -m pytest agent_factory/schema/tests/test_cli_feature.py -v 2>&1 | tail -20`

Expected: All tests pass.

- [ ] **Step 5: Commit**

```bash
git add agent_factory/cli/feature.py agent_factory/schema/tests/test_cli_feature.py
git commit -m "$(cat <<'EOF'
refactor(cli): 删除 feature block/unblock 命令

- 移除 BlockedRecord 导入
- FeatureStatus.BLOCKED 不再是有效转换目标
- 删除 4 个 block/unblock 测试
- 状态机从 5 状态减为 4 状态（无 blocked 分支）

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: CLI — delete issue block/unblock commands

**Files:**
- Modify: `agent_factory/cli/issue.py:16,376-437`

- [ ] **Step 1: Update test_cli_issue.py to remove block/unblock test (preparation)**

Delete `test_issue_block_unblock` (lines 160-175) from `agent_factory/schema/tests/test_cli_issue.py`. Also remove the surrounding blank lines if needed.

- [ ] **Step 2: Run test_cli_issue.py to verify it fails**

Run: `python3 -m pytest agent_factory/schema/tests/test_cli_issue.py -v 2>&1 | tail -20`

Expected: FAIL with `ImportError` referencing `BlockedRecord`.

- [ ] **Step 3: Remove BLOCKED import and commands from issue.py**

Modify `agent_factory/cli/issue.py`:

**Line 16** — change:
```python
from agent_factory.schema import BlockedRecord, Issue, IssueIndex, IssueIndexItem
```
to:
```python
from agent_factory.schema import Issue, IssueIndex, IssueIndexItem
```

**Lines 376-437** — delete the entire `block` and `unblock` commands (62 lines).

- [ ] **Step 4: Run test_cli_issue.py to verify pass**

Run: `python3 -m pytest agent_factory/schema/tests/test_cli_issue.py -v 2>&1 | tail -20`

Expected: All tests pass.

- [ ] **Step 5: Commit**

```bash
git add agent_factory/cli/issue.py agent_factory/schema/tests/test_cli_issue.py
git commit -m "$(cat <<'EOF'
refactor(cli): 删除 issue block/unblock 命令

- 移除 BlockedRecord 导入
- 删除 1 个 block/unblock 测试
- issue 状态机保持 3 状态（原本就没 blocked）

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Delete blocked.yaml example

**Files:**
- Delete: `agent_factory/schema/examples/blocked.yaml`

- [ ] **Step 1: Delete the example file**

Run: `git rm agent_factory/schema/examples/blocked.yaml`

Expected: `rm 'agent_factory/schema/examples/blocked.yaml'`

- [ ] **Step 2: Verify examples/ now has 4 files**

Run: `ls agent_factory/schema/examples/`

Expected:
```
feature.yaml
feature_index.yaml
issue.yaml
issue_index.yaml
```

- [ ] **Step 3: Check if test_examples.py references blocked.yaml**

Run: `grep -n "blocked" agent_factory/schema/tests/test_examples.py`

Expected: Empty output (no test references).

- [ ] **Step 4: Commit**

```bash
git commit -m "$(cat <<'EOF'
refactor(schema): 删除 blocked.yaml 示例文件

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Test cleanup — remove test_blocked.py and update test_feature.py

**Files:**
- Delete: `agent_factory/schema/tests/test_blocked.py`
- Modify: `agent_factory/schema/tests/test_feature.py:148,157`

- [ ] **Step 1: Update test_feature.py to expect 7 states**

Modify `agent_factory/schema/tests/test_feature.py`:

**Line 148** — change:
```python
    """8 states: draft/designing/approved/implementing/qa-reviewing/done/blocked/cancelled."""
```
to:
```python
    """7 states: draft/designing/approved/implementing/qa-reviewing/done/cancelled."""
```

**Line 150** — change:
```python
    assert len(FeatureStatus) == 8
```
to:
```python
    assert len(FeatureStatus) == 7
```

**Line 157** — delete:
```python
    assert FeatureStatus.BLOCKED.value == "blocked"
```

- [ ] **Step 2: Run test_feature.py to verify pass**

Run: `python3 -m pytest agent_factory/schema/tests/test_feature.py -v 2>&1 | tail -20`

Expected: All tests pass.

- [ ] **Step 3: Delete test_blocked.py**

Run: `git rm agent_factory/schema/tests/test_blocked.py`

Expected: `rm 'agent_factory/schema/tests/test_blocked.py'`

- [ ] **Step 4: Run full test suite to confirm all green**

Run: `python3 -m pytest agent_factory/schema/tests/ -v 2>&1 | tail -10`

Expected: All tests pass. Compare count to Task 0 baseline — should be fewer tests (removed block-related).

- [ ] **Step 5: Commit**

```bash
git add agent_factory/schema/tests/test_blocked.py agent_factory/schema/tests/test_feature.py
git commit -m "$(cat <<'EOF'
refactor(tests): 删除 block 相关测试 + 修正状态计数

- 删除 test_blocked.py（整个 blocked schema 测试）
- test_feature.py: 状态数 8 → 7，删除 BLOCKED 断言

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Final schema/CLI test verification

**Files:**
- Read: `agent_factory/schema/tests/`

- [ ] **Step 1: Run full test suite**

Run: `python3 -m pytest agent_factory/schema/tests/ 2>&1 | tail -5`

Expected: All tests pass.

- [ ] **Step 2: Verify CLI help has no block/unblock commands**

Run: `cd agent_factory && python3 -m agent_factory.cli --help 2>&1; cd ..`

Expected: Output shows `feature` and `issue` as subcommands, but no `block` / `unblock`.

Run: `python3 -m agent_factory.cli --help 2>&1 | grep -i "block"`

Expected: Empty output.

- [ ] **Step 3: Verify imports are clean**

Run: `grep -rn "BlockedRecord\|FeatureStatus.BLOCKED" agent_factory/`

Expected: Empty output.

- [ ] **Step 4: No commit needed**

---

## Task 8: agent-pm.md — remove §Blocked 处理 section and pull blocked refs

**Files:**
- Modify: `agent-pm.md`

- [ ] **Step 1: Remove §BLOCKED.yaml 格式 subsection**

In `agent-pm.md`, locate line 348 (### BLOCKED.yaml 格式) and the surrounding content. Delete lines 342-346 (the `### BLOCKED.yaml 格式` heading + its 2-sentence description + `示例见...` link).

Verify the ToC entry (line 23) is also removed:

Delete line 23: `  - [BLOCKED.yaml 格式](#blockedyaml-格式)`

- [ ] **Step 2: Remove §Blocked 处理 section entirely**

Delete lines 987-1033 (the entire `## Blocked 处理` section including `### Tech-Feasibility Blocked 处理流程` and `### 解除阻塞（一般阻塞）` subsections).

Also delete the ToC entry (line 49): `- [Blocked 处理](#blocked-处理)` and sub-entries (lines 50-53).

- [ ] **Step 3: Update lifecycle diagram to remove blocked**

In the `### 生命周期` subsection (around line 310-311), change:

```
`draft` → `designing` → `approved` → `implementing` → `qa-reviewing` → `done`
                 ↘ blocked ↗
```

to:

```
`draft` → `designing` → `approved` → `implementing` → `qa-reviewing` → `done`
```

- [ ] **Step 4: Remove blocked from lifecycle table**

Locate the lifecycle table (around line 320-329). Delete the row:

```
| **blocked** | **需要用户介入，等待外部输入** | PM 设计阶段或 developer 实现阶段受阻 |
```

- [ ] **Step 5: Update §任务调度 场景 8 (POC) header**

Locate `#### 场景 8: POC（技术可行性）` (around line 942). Change the text following:

Change `**调度时机**：PM 在 designing 阶段因 \`tech-feasibility\` blocked`

to: `**调度时机**：PM 在 designing 阶段判断需要技术可行性 / 选型验证`

Locate the `## Questions` optional chapter description (around line 947). Change:

`<PM 在 blocked_reason 中提出的技术问题清单>`

to:

`<PM 在 designing 时发现的技术问题清单>`

- [ ] **Step 6: Update §跨环境 Issue 处理 Step 2 markdown table**

Locate the inline table (around line 567-571). Change the row:

```
| 内容模糊 / 无法判断 | blocked | 标记为 `agent-factory issue block`，等用户澄清 |
```

to:

```
| 内容模糊 / 无法判断 | ask user | PM 在对话中直接询问用户 |
```

- [ ] **Step 7: Update §状态管理 table**

Locate the status files table (around line 1042-1056). Delete these 2 rows:

```
| `.features/<id>/BLOCKED.yaml` | feature 的阻塞详情（含 blocked 类型） |
```

and:

```
| `.issues/<id>/BLOCKED.yaml` | issue 的阻塞详情 |
```

Also update the `.features/<id>/POC-REPORT.md` row description to remove "tech-feasibility blocked". Change:

```
| `.features/<id>/POC-REPORT.md` | 技术可行性评估报告（tech-feasibility blocked 时生成） |
```

to:

```
| `.features/<id>/POC-REPORT.md` | 技术可行性评估报告（designing 阶段 PM 调度 POC 时生成） |
```

- [ ] **Step 8: Update §日常巡检 status report**

Locate the bullet list (around line 1067-1073). Delete:

```
   - blocked 项数（需用户处理）
```

- [ ] **Step 9: Final grep for blocked in agent-pm.md**

Run: `grep -n -i "block" agent-pm.md`

Expected: Empty output. If non-empty, fix remaining references.

- [ ] **Step 10: Commit**

```bash
git add agent-pm.md
git commit -m "$(cat <<'EOF'
refactor(pm-prompt): 删除 §Blocked 处理整节 + 清理 blocked 引用

- 删除 §BLOCKED.yaml 格式 / §Blocked 处理（含 Tech-Feasibility 子节）
- 状态机图、状态表、状态管理表、巡检表去掉 blocked
- 场景 8 POC 调度改名为 'designing 阶段判断需要技术可行性'
- 跨环境 Issue '内容模糊' 兜底改为 PM 对话询问用户

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: developer.md — remove blocked return status

**Files:**
- Modify: `developer.md`

- [ ] **Step 1: Remove "On blocker" bullet points**

Locate and delete these 4 occurrences:
- Line 45 (`8. On blocker: update index.md status to "blocked", return blocked with reason` — note: typo "index.md" but should be cleaned)
- Line 104 (`8. On blocker: update index.md status to "blocked", return blocked with reason`)
- Line 72 (`11. On blocker: \`agent-factory issue block <NNN> --reason "..." --action "..."\`, return blocked with reason`)
- Line 122 (`11. On blocker: \`agent-factory issue block <id> --reason "..." --action "..."\`, return blocked with reason`)

**Recommended replacement** (uniform across all 4 occurrences):

Replace `On blocker: update index.md status to "blocked", return blocked with reason` with:

```
On fail: return fail with reason (status unchanged for review)
```

Replace `On blocker: agent-factory issue block <NNN> --reason "..." --action "...", return blocked with reason` with:

```
On fail: agent-factory issue set <NNN> scenario "failure reason", return fail with reason
```

- [ ] **Step 2: Remove blocked return status documentation**

Locate lines 321, 465-491 (the BLOCKED status documentation in 场景 5 and the return value section).

Delete line 321 (`- blocked（代码不完整）`).

For the return value section (around line 465-491), find:

```
"blocked_reason": null,  // ...
```

and the section after `### status: blocked` examples. Delete the entire "blocked" status block.

**Note**: The subagent result schema may keep `blocked_reason` as a field name (since renaming is out of scope), but the `status: "blocked"` enum value is removed and the example is updated.

- [ ] **Step 3: Update You don't talk to user section**

Lines 17-18:
```
- 你不与用户直接讨论（遇到问题返回 blocked 给 PM，由 PM 处理）
- 遇到无法独立解决的问题时，返回 blocked 状态给 PM
```

Change to:
```
- 你不与用户直接讨论（遇到问题返回 fail 给 PM，由 PM 处理）
- 遇到无法独立解决的问题时，返回 fail 状态 + reason 字段给 PM
```

- [ ] **Step 4: Update 文件 / 状态说明 if any**

Line 122 (场景 1 spec-compliance step 2):
```
2. **确认理解**：如果设计文档中存在模糊或矛盾之处，返回 blocked 给 PM，由 PM 协调解决
```

Change to:
```
2. **确认理解**：如果设计文档中存在模糊或矛盾之处，写入 violations 列表返回给 PM
```

- [ ] **Step 5: Final grep for blocked in developer.md**

Run: `grep -n -i "block" developer.md`

Expected: Empty output. If non-empty, fix remaining references.

- [ ] **Step 6: Commit**

```bash
git add developer.md
git commit -m "$(cat <<'EOF'
refactor(subagent): developer.md 移除 blocked 状态

- 删除 'On blocker' 步骤（4 处）
- subagent 返回状态改为 complete | fail 二元（移除 blocked）
- 'You don't talk to user' 部分同步更新

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 10: poc.md — remove blocked return status

**Files:**
- Modify: `poc.md`

- [ ] **Step 1: Update return status documentation**

Locate lines 150-164 (the structured result schema). Find the `status: "blocked"` example and replace with fail-returning guidance.

Specifically:
- Line 150 (`"blocked_reason": null`) → replace with `"reason": null` (or remove field)
- Line 158 (`"status": "blocked"`) → change to `"status": "fail"` (or remove blocked example)
- Line 164 (`"blocked_reason": "<阻塞原因及所需操作>"`) → replace with reason example

- [ ] **Step 2: Final grep for blocked in poc.md**

Run: `grep -n -i "block" poc.md`

Expected: Empty output. If non-empty, fix remaining references.

- [ ] **Step 3: Commit**

```bash
git add poc.md
git commit -m "$(cat <<'EOF'
refactor(subagent): poc.md 移除 blocked 状态

- subagent 返回状态改为 complete | fail
- blocked_reason 字段改名为 reason（简洁命名）

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 11: README.md — remove blocked from directory tree and state machine

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Remove BLOCKED.yaml from directory tree**

Locate the project directory structure (around lines 175-202). Remove these 2 lines:

In `.features/<id>/` block:
```
      BLOCKED.yaml
```

In `.issues/<id>/` block:
```
    BLOCKED.yaml
```

- [ ] **Step 2: Update state machine section**

Locate the `### Feature` lifecycle (line 244-248):

```
`draft` → `designing` → `approved` → `implementing` → `qa-reviewing` → `done`

`blocked` 为可逆中间状态，`cancelled` 可从任何状态直接流转。
```

Change to:

```
`draft` → `designing` → `approved` → `implementing` → `qa-reviewing` → `done`

`cancelled` 可从任何状态直接流转。
```

- [ ] **Step 3: Remove BlockedRecord from schema table**

Locate the schema module table (around line 218-229). Delete the row:

```
| `agent_factory/schema/blocked.py` | BlockedRecord 模型 |
```

- [ ] **Step 4: Final grep for blocked in README.md**

Run: `grep -n -i "block" README.md`

Expected: Empty output. If non-empty, fix remaining references.

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "$(cat <<'EOF'
refactor(docs): README.md 移除 blocked 状态机

- 删除目录树中 BLOCKED.yaml 行
- 删除 BlockedRecord schema 表格行
- 状态机描述去 'blocked 为可逆中间状态'

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 12: Final verification — full sweep

**Files:**
- Read: entire repo

- [ ] **Step 1: Run full test suite**

Run: `python3 -m pytest agent_factory/schema/tests/ 2>&1 | tail -5`

Expected: All tests pass.

- [ ] **Step 2: Verify no blocked references in active code/docs**

Run:
```bash
grep -rn -i "block" agent_factory/ agent-pm.md developer.md poc.md README.md 2>&1
```

Expected: Empty output. (Historical docs in `docs/2026-08-09-*.md` are allowed to keep block mentions.)

- [ ] **Step 3: Verify CLI help**

Run: `python3 -m agent_factory.cli --help`

Expected: `feature` and `issue` subcommands visible, no block/unblock.

- [ ] **Step 4: Verify feature status enum**

Run: `python3 -c "from agent_factory.schema.feature import FeatureStatus; print(list(FeatureStatus))"`

Expected: `[<FeatureStatus.DRAFT: 'draft'>, <FeatureStatus.DESIGNING: 'designing'>, <FeatureStatus.APPROVED: 'approved'>, <FeatureStatus.IMPLEMENTING: 'implementing'>, <FeatureStatus.QA_REVIEWING: 'qa-reviewing'>, <FeatureStatus.DONE: 'done'>, <FeatureStatus.CANCELLED: 'cancelled'>]`

- [ ] **Step 5: Verify git log**

Run: `git log --oneline refactor/agent-arch-2026-06-21 ^53ca11a | head -20`

Expected: 8-10 commits about block removal, ending with README update.

- [ ] **Step 6: No commit needed**

---

## Summary

This plan:
- **12 tasks** organized in 4 phases: schema → CLI → examples → tests → docs
- **~10 commits** with clear, focused messages
- **TDD**: each task updates tests first (or prepares for deletion), then deletes code, then verifies
- **No-placeholder**: exact file paths, complete code blocks, exact commands
- **Verification**: final sweep confirms no blocked references in active code/docs
