# Prompt Optimization Design

**日期**: 2026-06-21
**作者**: 用户 + Claude（brainstorming 协作）
**状态**: Draft（待用户 review）

## 背景

agent-factory 工作流实际使用中暴露 4 个问题：

### 问题一：doc-changes 在 review 中很少看

designer 在设计阶段手动生成 `doc-changes/*.diff`（unified diff），但实际 review 时用户只看 DESIGN.md，developer 应用 diff 是冗余步骤（designer 已直接写 `doc/<module>/*.md`，diff 是二次表达）。手写 diff 还容易与实际文件不一致。

### 问题二：doc/frontend/ UI 预览基本用不上

http-web 形态下 designer 在 `doc/frontend/` 生成 HTML 预览（mock 数据 + playwright 验证）。实际使用中：UI 讨论通常在 developer 实现后看真实效果；HTML 预览维护成本高、易与实现脱节、mock 数据与真实数据差异大。

### 问题三：data-schema 还是会设计非必要字段

当前 don'ts 写的是 "避免过度设计，定义agent功能非必要的数据结构以及字段，**如不确定请于用户确认**"——负向约束 + escape hatch（"不确定"成了放过自己的理由）。LLM 倾向忽略负向约束。

### 问题四：经常出现代码没提交

当前规则是"一个 feature 对应一个 commit"，但 bug 修复（issue）明确写 "不要求自动提交，由 PM 决定提交策略"——这是漏洞。PM 调度 bug 修复和 QA 诊断后修复的指令完全没提 commit。输出格式中没有 commit 校验，developer 可能"忘了 commit"也能返回 complete。

## 目标

- **删除冗余机制**：doc-changes、doc/frontend/ 都删除
- **强化字段必要性**：用正向指令 + 消费方清单替代负向约束
- **强制 commit**：所有任务类型必 commit，输出契约强制 commit_sha
- **应用 prompt-engineering 原则**：Design with simplicity / Use Instructions over Constraints / Be specific / JSON Schema / CoT

## 决策汇总

| # | 决策点 | 结论 |
|---|--------|------|
| **A** | doc-changes | 完全删除机制；DESIGN.md `## Doc 变更清单` 保留为纯文本概要 |
| **B** | doc/frontend/ | 删除；UI 设计下沉到 DESIGN.md `## Frontend` 章节（页面清单 + 关键交互 + API 对应表） |
| **C** | data-schema 字段必要性 | 正向指令 + 消费方清单 + 判断表（2 行）；designer.md + spec-compliance.md 双层强制 |
| **D** | commit 强制 | 所有任务类型必 commit；输出 JSON 强制 commit_sha；移除 bug 修复例外；commit message 不带编号 |

## 详细设计

### 1. 删除 doc-changes 机制（Issue 1）

#### 删除位置

| 文件 | 位置 | 操作 |
|------|------|------|
| `designer.md` | Feature Management 目录结构中 `doc-changes/` 子目录 | 删除 |
| `designer.md` | 职责边界操作范围含 `doc-changes/*.diff` | 移除该项 |
| `designer.md` | 工作流 step "生成 diff" | 删除整步 |
| `designer.md` | `### diff 文件规范` 整章 | 删除 |
| `designer.md` | 输出 JSON 的 artifacts 含 `doc-changes/...` | 移除 |
| `agent-pm.md` | Feature 目录结构含 `doc-changes/` | 删除 |
| `agent-pm.md` | approved 状态触发条件 "diff 通过审阅" | 改为 "DESIGN.md review 通过" |
| `agent-pm.md` | 调度 designer 指令 step "Generate doc-changes" | 删除 |
| `agent-pm.md` | 调度 developer 指令 step "Apply doc-changes" | 删除 |
| `agent-pm.md` | PM Review 标准 "doc-changes 文件范围匹配" | 改为 "DESIGN.md Doc 变更清单 章节涉及的文件范围匹配" |
| `agent-pm.md` | PM Review 后 "展示 doc-changes/*.diff" | 改为 "展示 DESIGN.md 概要 + git diff 摘要" |
| `developer.md` | 开发前准备 step "Apply doc-changes" | 删除 |
| `developer.md` | 阅读列表含 doc-changes | 移除该项 |
| `developer.md` | "应用 doc 变更"步骤 | 删除整步 |

#### 保留内容

DESIGN.md 模板的 `## Doc 变更清单` 章节保留，改为纯文本概要：

```markdown
## Doc 变更清单
<!-- 列出受影响的 doc 文件及变更类型 -->
<!-- 示例：
- doc/financial/data-schema.md（新增 IncomeRecord dataclass）
- doc/financial/data-persistence.md（修改存储路径）
- doc/common/data-schema.md（无变更）
-->
```

不生成 diff 文件，仅文本列出。

#### 理由

**Design with simplicity / YAGNI**：doc-changes 是 designer 已直接写 `doc/<module>/*.md` 后的冗余二次表达；review 时 `git diff` 比手写 diff 更准确；developer 跳过 apply 步骤减少出错面。

---

### 2. 删除 doc/frontend/ 机制（Issue 2）

#### 删除位置

| 文件 | 位置 | 操作 |
|------|------|------|
| `designer.md` | 设计文档输出规范含 `doc/frontend/` | 删除该行 |
| `designer.md` | `## Web UI 设计` 整章（含"设计先行，所见即所得"） | 删除 |
| `designer.md` | artifact 矩阵 `doc/frontend/` 行 | 删除 |
| `designer.md` | http-web 目录结构示例含 `doc/frontend/` | 删除 |
| `developer.md` | 阅读列表含 `doc/frontend/` | 移除该项 |
| `qa.md` | UI 元素验收行（原指向 `doc/frontend/`） | 改为指向 DESIGN.md `## Frontend` 章节 |
| `spec-compliance.md` | F 检查组（原检查 `doc/frontend/` 目录文件） | 改为检查 DESIGN.md `## Frontend` 章节 |
| `spec-compliance.md` | 启用矩阵 F 行 | 保留，但说明改指 DESIGN.md |
| `spec-compliance.md` | 输出 JSON 示例含 `doc/frontend/` | 改为 `DESIGN.md (Frontend section)` |

#### 保留 + 增强：DESIGN.md `## Frontend` 章节

从单行注释扩展为明确三段结构：

```markdown
## Frontend（仅 http-web）

### 页面清单
<!-- 列出所有页面：路径、文件名、用途 -->

### 关键交互
<!-- 每个页面的关键用户操作流程 -->

### API 对应
| 页面 | 调用的 backend API |
|------|-------------------|
| <page> | <API list> |
```

#### 对存量项目

现有 `doc/frontend/` 文件不强制迁移，作为孤儿文档保留；新 feature 按新模式产出。如用户希望清理，开单独的 migration feature。

#### 理由

**Design with simplicity**：HTML 预览维护成本高、易与实现脱节；markdown 描述足够支撑讨论和实现。

---

### 3. data-schema 字段必要性原则（Issue 3）

#### 双层强制

- **designer.md**：写正向指令 + 消费方清单要求 + 判断表（设计时自应用）
- **spec-compliance.md**：新增 S 组检查项兜底（review 时验证 designer 是否在 DESIGN.md 列出消费方）

#### designer.md `## Data Schema` 重写

替换原 `## Data Schema` 整章为：

```markdown
## Data Schema

设计文档 `{Root}/doc/<module>/data-schema.md`（按 module 拆分，跨 module 共享部分写在 `{Root}/doc/common/data-schema.md`）

### 文件内容

- 结合业务场景、功能，使用合理数据类型，定义简洁、清晰的数据结构
- 每个数据结构使用 `python dataclass` 定义，class 与每个 field 配文字描述

### 字段必要性原则（核心）

每个字段必须能回答"谁在什么时候读取这个字段？"。设计 dataclass 前先做两件事：

1. **列出消费方清单**：该数据结构被哪些场景使用？
   - CLI 命令 / API 端点 / UI 元素 / 日志读取 / 持久化反序列化
2. **逐字段归因**：每个字段属于哪个消费方？没有明确消费方的不写入 schema

**判断标准（写入字段前自查）**：

| 场景 | 处理 |
|------|------|
| 字段有明确消费方（CLI/API/UI/日志读取它） | 保留 |
| 字段"将来可能用到"或"看起来应该有" | 不保留（YAGNI） |

**dos**

- 字段值存在有限集合时，优先使用枚举（Python `enum`）而非字符串常量或整数魔法值
- 数据结构命名清晰、合理，保证一致性
- 文档仅承载数据结构定义，不体现业务使用代码或持久化等其他内容

### 关键原则

- **每个 module 的 `data-schema.md` 作为该 module 数据结构的唯一真值，必须保证跨文档一致性**
- **跨 module 共享数据结构以 `{Root}/doc/common/data-schema.md` 为唯一真值**
- 任何 data-schema 修改需先与用户讨论
```

#### DESIGN.md 模板调整

各 Module 设计章节的「数据结构」部分追加要求：

```markdown
### <Module-A>
#### 数据结构
<!-- 引用 doc/<module-A>/data-schema.md，列关键 entity -->
<!-- 每个 dataclass 附消费方清单（被哪些 CLI/API/UI/日志使用） -->
```

#### spec-compliance.md 新增检查项

在 S 组（data-schema）内追加：

| # | 检查 | 通过标准 |
|---|------|----------|
| S8 | 字段消费方标注 | DESIGN.md 中每个 dataclass 是否附消费方清单 |
| S9 | 字段必要性自检 | data-schema.md 中无"将来可能"/"看起来应该有"类描述（spec-compliance 通过字段描述启发式判断，发现疑似项列入 violation 待 designer 复核） |

#### 理由

- **Use Instructions over Constraints**：把 "避免过度设计" 负向约束改为 "每个字段必须能回答消费方" 正向指令
- **CoT**：强制 designer 设计前先列消费方清单，再逐字段归因
- **Be specific**：判断表给出具体反例（"将来可能"/"看起来应该有"），消除"必要"的模糊性
- 移除原 "如不确定请于用户确认" escape hatch

---

### 4. commit 强制（Issue 4）

#### 修改位置

| 文件 | 位置 | 操作 |
|------|------|------|
| `developer.md` | `## Git 提交规范` 整章 | 重写：移除 bug 修复例外，明确所有任务类型必 commit |
| `developer.md` | 输出格式 JSON | 新增 `commit_sha` 必填字段 |
| `developer.md` | `## 输入格式` 下 Bug 直接修复任务 / QA 修复任务 | 新增 commit step（原本只有常规开发任务有） |
| `agent-pm.md` | 调度 developer Bug 修复指令 | 新增 commit step |
| `agent-pm.md` | 调度 developer QA 修复指令 | 新增 commit step |
| `agent-pm.md` | 调度 developer QA 诊断后修复指令 | 新增 commit step |

#### developer.md `## Git 提交规范` 重写

```markdown
## Git 提交规范

### 提交时机

代码修改完成后必须立即 commit，然后才返回 complete。

### 提交规则（无一例外）

所有代码修改完成后必须 commit：
- Feature 实现完成 → 1 个 commit
- QA 修复完成 → 1 个 commit
- Bug 修复（issue）完成 → 1 个 commit

### 唯一不 commit 的情况

- blocked（代码不完整）

### Commit 前自检

返回 complete 前，developer 必须执行 `git log -1 --oneline` 确认最新 commit 是本次任务的。若工作区仍有未提交的代码改动，禁止返回 complete。

### Commit Message 格式

Feature 实现（多项目模式）：
\`\`\`
feat(<project-id>): <描述修改内容>

<DESIGN.md 概要，1-2 句>
\`\`\`

Feature 实现（单项目模式）：
\`\`\`
feat: <描述修改内容>

<DESIGN.md 概要，1-2 句>
\`\`\`

QA 修复：
\`\`\`
fix(<project-id>): 修复 QA 发现的 <问题描述>

QA round N: <修复内容>
\`\`\`

Bug 修复（issue，多项目模式）：
\`\`\`
fix(<project-id>): <问题描述>

<修复概要>
\`\`\`

Bug 修复（issue，单项目模式）：
\`\`\`
fix: <问题描述>

<修复概要>
\`\`\`

Migration feature：
\`\`\`
refactor(migrate): migrate <module> to new architecture

<迁移概要>
\`\`\`
```

#### developer.md 输出格式新增 commit_sha

```json
{
  "status": "complete",
  "feature_number": "<NNN>",
  "commit_sha": "<commit hash>",
  "artifacts": ["<list of created/modified files>"],
  "summary": "<简要描述实现了什么>",
  "blocked_reason": null
}
```

**约束说明**：`commit_sha` 必填，缺失视为未完成。blocked 状态下 `commit_sha` 为 null。

#### agent-pm.md Bug 修复指令新增 step

调度 developer Bug 直接修复的指令（原 steps 1-7）改为：

```
## Instructions
1. Update issue status to "triaging" in <Root>/.issues/index.md
2. Reproduce and diagnose the bug
3. Apply minimal fix
4. Add regression test
5. Run full test suite
6. Git commit (one issue = one commit, message: fix(<project>): <问题描述> 或单项目 fix: <问题描述>)
7. On success: update issue status to "closed", return complete with commit_sha
8. On blocker: update issue status to "blocked", return blocked with reason
```

#### agent-pm.md QA 诊断后修复指令新增 step

调度 developer QA 诊断后修复的指令（原 steps 1-7）改为：

```
## Instructions
1. Update issue status to "triaging" in <Root>/.issues/index.md
2. Read QA Diagnosis in NOTES.md
3. Apply fix based on QA's root cause analysis and suggestion
4. Add regression test
5. Run full test suite
6. Git commit (one issue = one commit, message: fix(<project>): <问题描述> 或单项目 fix: <问题描述>)
7. On success: update issue status to "closed", return complete with commit_sha
8. On blocker: update issue status to "blocked", return blocked with reason
```

#### agent-pm.md QA 修复指令新增 step

调度 developer QA 修复的指令（feature 验收失败后）原本无 commit step，新增为：

```
## Instructions
1. Read QA-REPORT.md
2. Fix each issue listed in QA report
3. Add regression tests for each fix
4. Run full test suite
5. Git commit (one QA round = one commit, message: fix(<project>): 修复 QA 发现的 <问题描述>)
6. On success: update index.md status to "qa-reviewing", return complete with commit_sha
7. On blocker: update index.md status to "blocked", return blocked with reason
```

#### developer.md 输入格式新增 commit step

developer.md `## 输入格式` 下三个任务模板的 Instructions 列表统一加 commit step（原本只有常规开发任务有）：

- **Bug 直接修复任务**：step 5 后加 `Git commit (one issue = one commit, message: fix(<project>): <问题描述> 或单项目 fix: <问题描述>)`，原 step 5/6 顺延为 6/7，return complete 加 commit_sha
- **QA 修复任务**：step 4 后加 `Git commit (one QA round = one commit, message: fix(<project>): 修复 QA 发现的 <问题描述>)`，原 step 5/6 顺延为 6/7，return complete 加 commit_sha
- **常规开发任务**：原 step 6 commit 保留，commit message 去掉 `(#<NNN>)`；return complete 加 commit_sha

#### 理由

- **Be specific**：移除 "Bug 修复不要求自动提交，由 PM 决定" 的模糊例外，明确所有任务类型必 commit
- **JSON Schema**：输出契约层强制 commit_sha，PM 可凭此字段判断是否真 commit
- **CoT**：commit 前自检 `git log -1` 形成 self-verification 闭环

---

## 跨文件一致性

### PM 收到 complete 响应时

PM 调度 developer 后处理 complete 响应时，信任 `commit_sha` 字段。若 complete 响应缺失 `commit_sha`，PM 应记录异常并要求 developer 补提交（此为兜底，不作为常规路径）。

### PM Review 标准更新

PM 初步 Review 标准（`agent-pm.md` `## PM 初步 Review` 章节）中"完整性"项的"doc 变更清单"措辞改为"DESIGN.md Doc 变更清单 章节涉及的文件范围匹配需求范围"。

### QA-REPORT 模板

`qa.md` QA-REPORT.md 模板的 Design Compliance 表无需结构变化（原本就是 per-Agent-Type 表），但检查时对 data-schema 的判断标准应参考 designer.md 新的字段必要性原则。

---

## 影响范围

### 需要修改的文件

| 文件 | 修改内容 |
|------|----------|
| `agent-pm.md` | 删除 doc-changes 相关（目录、approved 触发、调度指令、Review 标准）；删除调度指令中 Apply doc-changes step；3 个 developer 调度指令新增/加强 commit step |
| `designer.md` | 删除 doc-changes 机制；删除 Web UI 设计章节；Data Schema 章节重写（正向指令+判断表）；DESIGN.md 模板调整（Doc 变更清单改文本概要、Frontend 扩展三段、各 Module 数据结构加消费方要求） |
| `developer.md` | 删除 doc-changes 相关；Git 提交规范重写；输出 JSON 新增 commit_sha；Bug/QA 修复任务 input format 加 commit step |
| `qa.md` | UI 元素验收改指 DESIGN.md Frontend 章节 |
| `spec-compliance.md` | F 检查组改指 DESIGN.md；S 组新增 S8/S9 检查项 |

### 不修改

| 文件 | 原因 |
|------|------|
| `poc.md` | 与本次优化无关 |
| `README.md` | 安装/使用说明兼容，可后续单独更新 |
| `agent架构.drawio` | 架构图无需调整 |
| `.features/index.md` 模板 | 无结构变化 |
| `REQUIREMENTS.md` 模板 | 无字段变化 |

### 对存量项目的影响

- 现有 `.features/<NNN>/doc-changes/` 目录：作为历史归档保留，新 feature 不再生成
- 现有 `doc/frontend/` 文件：作为孤儿文档保留，新 feature 按新模式产出
- 现有 DESIGN.md 模板未涉及消费方清单的：spec-compliance 在新 feature 设计时强制执行；存量已 done 的 feature 不补标

## 开放问题（YAGNI）

- **PM 是否主动验证 commit_sha**：当前设计 PM 信任 developer 输出，不主动 `git log` 校验。若实践中发现 developer 仍漏 commit，再加 PM 校验层
- **commit 粒度**：strict "one feature = one commit"，不允许中间 commit。若实践中大 feature 工作树过满（>500 行未提交），再考虑放宽为"按 module 子提交"
- **存量 doc/frontend/ 迁移**：当前保留为孤儿。若用户希望清理，开单独的 migration feature

## 后续

转入 `writing-plans` skill，制定详细实施计划，分阶段落地以上修改。
