# OTA Issue Analyzer 工作流优化项

范围：`.features/*/workflow-issues/*.yaml`，不包含历史复盘。逐条保留原始记录，未去重。状态是记录中的原始状态，未逐条验证当前工作流是否已覆盖。

共 33 条：closed 9 条、open 24 条。

| Feature | 优化项 | 状态 | 原始记录 |
|---|---|---|---|
| 249 | agent-pm §3.4 缺 demo 工作区隔离规则，主工作区被污染、正式实现缺文件 | open | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/249-api-docs-sidebar-page/workflow-issues/001-demo-worktree-isolation.yaml) |
| 249 | agent-pm §3.3.2 规格粒度过粗，12 个接口压成一条，QA 返工两轮 | open | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/249-api-docs-sidebar-page/workflow-issues/002-spec-template-granularity.yaml) |
| 253 | PM 单轮输出过长，缺分步节奏，用户无法一次看完 | open | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/253-refactor-log-analysis-overview/workflow-issues/001-pm-chunked-discussion.yaml) |
| 253 | spec 未区分前后端边界，同一行为重复写成两条规格 | open | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/253-refactor-log-analysis-overview/workflow-issues/002-spec-layer-boundary.yaml) |
| 253 | 用户纠正后 PM 未即时提议 workflow issue，需用户追问才补 | closed | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/253-refactor-log-analysis-overview/workflow-issues/003-workflow-issue-trigger-not-fired.yaml) |
| 253 | PM 自造「项目组」术语，用户纠正为配置项目/项目别名 | closed | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/253-refactor-log-analysis-overview/workflow-issues/004-invented-terminology.yaml) |
| 253 | 长内容输出缺 HTML + 临时 server 承载，PM 仍用长文本刷屏 | open | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/253-refactor-log-analysis-overview/workflow-issues/005-long-output-html-temp-server.yaml) |
| 253 | worktree 隔离条款未覆盖设计预览产物，demo 混入源码目录 | open | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/253-refactor-log-analysis-overview/workflow-issues/006-design-preview-artifact-placement.yaml) |
| 255 | 需求讨论前无系统调研步骤，方案两次作废，评估返工 | open | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/255-classification-review-apply/workflow-issues/001-pm-system-survey-order.yaml) |
| 255 | spec 未经逐条确认即写入并进入 doc，流程漏检 | closed | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/255-classification-review-apply/workflow-issues/002-spec-alignment-before-doc.yaml) |
| 255 | spec 未回读已定决策与验证结论，已确认内容被当作新设计重提 | open | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/255-classification-review-apply/workflow-issues/003-spec-decision-loss.yaml) |
| 255 | 用户指出流程问题时未即时记录，第三次追问才补提案 | closed | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/255-classification-review-apply/workflow-issues/004-workflow-issue-recording-trigger.yaml) |
| 255 | QA 前端只验用例行为点，缺用户视角审视，本应隐藏的按钮可见仍判 PASS | open | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/255-classification-review-apply/workflow-issues/005-qa-frontend-user-perspective.yaml) |
| 255 | 决策变更只落 spec/doc，POC 原型与报告未同步，实现与设计稿脱节 | open | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/255-classification-review-apply/workflow-issues/006-poc-design-as-baseline.yaml) |
| 255 | §2 对话风格缺单轮输出量约束，讨论时一次性输出过多 | open | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/255-classification-review-apply/workflow-issues/007-pm-chunked-discussion.yaml) |
| 255 | §2 缺「新术语先确认」触发条件，命名反复返工 | closed | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/255-classification-review-apply/workflow-issues/008-terminology-alignment.yaml) |
| 255 | 终审缺明确的完成信号，用户追问期间 PM 已推进下一处 | open | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/255-classification-review-apply/workflow-issues/009-review-completion-signal.yaml) |
| 256 | 缺口出现后 PM 未在当轮记录确认，需用户三次追问才补，证据流失 | closed | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/256-product-user-manual/workflow-issues/001-defer-workflow-issue-recording.yaml) |
| 256 | design-reference 未定义内部资源目录契约，knowledge/ 用途无文档可查 | open | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/256-product-user-manual/workflow-issues/002-design-reference-resource-dir-contract.yaml) |
| 259 | 前期讨论/分析产物落在临时目录，未按 feature 归档，产物无法追溯复用 | open | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/259-robo-classification-table-init/workflow-issues/001-analysis-artifacts-archive.yaml) |
| 259 | 前端目标规格/效果 demo 做成独立 mock，未基于真实 worktree，无法所见即所得 | open | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/259-robo-classification-table-init/workflow-issues/002-frontend-demo-on-real-worktree.yaml) |
| 259 | 前端目标规格/效果 demo 被派给 developer，违反由 PM 亲自做的职责边界 | open | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/259-robo-classification-table-init/workflow-issues/003-frontend-demo-by-pm.yaml) |
| 259 | 前端效果 demo 被做成完整开发，跳过 spec/doc/approved 门禁 | open | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/259-robo-classification-table-init/workflow-issues/004-frontend-demo-not-dev.yaml) |
| 259 | spec 术语被简写/省略，导致概念歧义，需明确禁止缩写与省略 | closed | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/259-robo-classification-table-init/workflow-issues/005-spec-terminology-no-abbreviation.yaml) |
| 259 | service 契约按前端视图设计，展示规则漏进 service，职责边界混淆 | open | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/259-robo-classification-table-init/workflow-issues/006-service-first-boundary.yaml) |
| 259 | 提示词未约束单次工具调用体量，超长工具调用反复解析失败并打断流程 | open | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/259-robo-classification-table-init/workflow-issues/007-long-tool-call-parse-failure.yaml) |
| 260 | §3.3.5 doc 终审 · 修改点未标章节/行号致连续两轮纠偏 | open | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/260-dual-soc-master-only-analysis/workflow-issues/001-doc-review-locate-section.yaml) |
| 263 | QA 前端 E2E 只留文字观测点，无可查看截图/录屏，PM 需临时补拍 | open | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/263-prod-task-import-eval-case/workflow-issues/001-e2e-visual-evidence.yaml) |
| 265 | 术语新增/修改未在 doc 设计前对齐，终审才被推翻致返工 | closed | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/265-known-issue-form-field-adjustments/workflow-issues/001-term-alignment-before-doc-design.yaml) |
| 265 | E2E 观测点未核对现有设计，误判既有行为为缺陷致 QA 返工 | open | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/265-known-issue-form-field-adjustments/workflow-issues/002-e2e-observation-not-checked-against-design.yaml) |
| 265 | 前端方案选项只用文字描述，用户看不到效果，要求一律可视化呈现 | open | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/265-known-issue-form-field-adjustments/workflow-issues/003-frontend-option-must-be-visual.yaml) |
| 268 | 提示词 §5.4.3 与 §3.4.3 的 done 置位时序冲突，状态先于合入 | closed | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/268-partial-coverage-notice-conclusion-tail/workflow-issues/001-done-transition-order-conflict.yaml) |
| 268 | 提示词未禁止 subagent 间直接调度，QA 绕过 PM 驱动 developer 修复 | open | [查看](/home/wentao/work-dir/ota_issue_analyzer/.features/268-partial-coverage-notice-conclusion-tail/workflow-issues/002-qa-bypasses-pm-dispatch.yaml) |

## 详细记录

### 249-api-docs-sidebar-page / 001-demo-worktree-isolation

- 状态：open；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/249-api-docs-sidebar-page/workflow-issues/001-demo-worktree-isolation.yaml)
- 问题：agent-pm §3.4 缺 demo 工作区隔离规则，主工作区被污染、正式实现缺文件
- 经过：阶段：需求（demo 验证）。feature 已创建（draft）后用户要求先做 demo 验证并指定「你来修改前端代码，不要调用 developer」。PM 直接在主仓 dev 工作区改前端，未创建 worktree 或临时分支；用户确认效果后才从 origin/dev 创建正式 worktree，demo 改动只能 stash；正式 worktree 缺少 demo 引用的未入库脚本 js/release_notes_demo.js，QA 发现页面 404。
- 原记录归因：没有这条规则。§3.4 只规定正式 feature 在 designing 阶段建 worktree，没有规定 feature 已创建但 worktree 未建时的 demo 必须使用独立工作区，也没有规定 demo 转正式实现时不能复用主工作区脏文件。
- 原记录建议：agent-pm §3.4 补充 demo 工作区约束：feature 内首次修改代码或文档前即创建 worktree，纯讨论不建； feature 已创建但需要先做 demo 验证时，在临时 worktree 或临时分支内完成，不碰主工作区； demo 转正式实现时，demo 产物必须能落到正式 worktree（不依赖未入库文件）。

### 249-api-docs-sidebar-page / 002-spec-template-granularity

- 状态：open；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/249-api-docs-sidebar-page/workflow-issues/002-spec-template-granularity.yaml)
- 问题：agent-pm §3.3.2 规格粒度过粗，12 个接口压成一条，QA 返工两轮
- 经过：阶段：spec 设计。PM 把 12 个接口的内容补齐写成一条「其余 12 个接口按同一模板补齐」；QA 第 1 轮按这条规格检查只列出 log_analysis / ops 的部分接口，未列 RMP，还误判「RMP 系列已扩充」；developer 第一轮只改 log_analysis / ops，RMP 3 个与 async-analyze 到第二轮 QA 仍 fail 才补齐。
- 原记录归因：有但没有触发条件。§3.3.2 写了「一条规格 = 一个功能点」，但没有把「模板类工作必须逐接口成条或落矩阵」写成可检查条件，PM 用一条汇总规格绕过了它。
- 原记录建议：agent-pm §3.3.2 把该原则改成可检查条件：模板类 / 列表类工作，一条规格只覆盖一个条目 （一个接口、一个字段、一个用例），或落成逐条目矩阵；「其余 N 个按模板补齐」「同类接口同上」 这类汇总写法一律不合格，写入前自检。

### 253-refactor-log-analysis-overview / 001-pm-chunked-discussion

- 状态：open；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/253-refactor-log-analysis-overview/workflow-issues/001-pm-chunked-discussion.yaml)
- 问题：PM 单轮输出过长，缺分步节奏，用户无法一次看完
- 经过：需求评审阶段，PM 评估后端接口时一次输出数据缺口表、接口契约、性能数据和口径风险，用户无法一次阅读，要求改为逐个讨论。
- 原记录归因：没有这条规则：§2 只限制每轮问题数量，未限制单轮输出长度，长表格与完整方案可一次性输出。

### 253-refactor-log-analysis-overview / 002-spec-layer-boundary

- 状态：open；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/253-refactor-log-analysis-overview/workflow-issues/002-spec-layer-boundary.yaml)
- 问题：spec 未区分前后端边界，同一行为重复写成两条规格
- 经过：阶段：spec 定稿。PM 先逐条向用户确认 17 条 frontend 规格，随后又把同一批页面行为用 数据口径写成 backend 规格；用户指出两边重复，并明确 frontend 只写用户操作逻辑、 backend 只写 API 功能提供逻辑。
- 原记录归因：有规则但没有触发条件：§3.3.2 有「一条规格 = 一个功能点」、设计原则有「唯一真源」， 但没有把「frontend 只写用户操作逻辑、backend 只写 API 功能逻辑」落成可执行的检查点， PM 因此把同一行为在两层各写一遍。

### 253-refactor-log-analysis-overview / 003-workflow-issue-trigger-not-fired

- 状态：closed；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/253-refactor-log-analysis-overview/workflow-issues/003-workflow-issue-trigger-not-fired.yaml)
- 问题：用户纠正后 PM 未即时提议 workflow issue，需用户追问才补
- 经过：阶段：spec 定稿。用户指出 frontend / backend spec 描述重复；PM 解释重复并继续讨论、 更新 spec，没有提议记录工作流缺口；直到用户追问「为什么没有触发工作流 issue 提议」， PM 才补写 002。
- 原记录归因：有规则但没有触发条件：§7.2 有「当下就落文件」，但没有把「用户纠正 PM 产出」定为 强制触发，也没有规定触发后暂停原讨论、先确认缺口；PM 把记录当成可以稍后补的动作。
- 原记录建议：agent-pm.md §7.2 判据段替换为触发信号清单（用户侧：提出质疑 / 指出错误；PM 侧：发现报错 / 发现工作流问题 / 出现返工），全文术语统一为「工作流优化项」。

### 253-refactor-log-analysis-overview / 004-invented-terminology

- 状态：closed；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/253-refactor-log-analysis-overview/workflow-issues/004-invented-terminology.yaml)
- 问题：PM 自造「项目组」术语，用户纠正为配置项目/项目别名
- 经过：阶段：module doc 设计。PM 为 log_analysis_stats README 拟新增术语「项目组」，指配置 项目及其别名对应的原始 project 值集合；用户指出没有这个概念，并明确 XYANGS 是项目、 XYANGS_IS4GR_sop 等是项目别名。
- 原记录归因：有但没有触发条件：§2 禁止自造名词，但未规定在 spec / doc 引入新术语前先查项目既有 术语并请用户确认；PM 把临时集合概念当成术语写入 README。
- 原记录建议：待巡检判定（同类第 2 次：255-008 + 本项，未达 3 次门槛）

### 253-refactor-log-analysis-overview / 005-long-output-html-temp-server

- 状态：open；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/253-refactor-log-analysis-overview/workflow-issues/005-long-output-html-temp-server.yaml)
- 问题：长内容输出缺 HTML + 临时 server 承载，PM 仍用长文本刷屏
- 经过：阶段：对话交互 / 汇报。 PM 在单轮需要输出大量内容时，直接以长文本回复；用户反馈“内容太多了”， 要求改为生成 HTML 并通过临时 server 打开查看，把详细内容移出对话。
- 原记录归因：§2 对话风格缺少“输出量阈值 + 载体切换”规则：当单轮内容超过对话可读范围时， PM 仍默认用 Markdown 长文回复，而不是生成 HTML 报告并启动临时 server 供用户查看。

### 253-refactor-log-analysis-overview / 006-design-preview-artifact-placement

- 状态：open；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/253-refactor-log-analysis-overview/workflow-issues/006-design-preview-artifact-placement.yaml)
- 问题：worktree 隔离条款未覆盖设计预览产物，demo 混入源码目录
- 经过：#253 设计阶段把「日志分析总览」Demo 写在主工作区 src/frontend/ 下： overview_demo.html + overview_demo_prod.js / .json（1.7MB × 2，prod 任务快照）， 通过 4000 端口 dev 前端 server 预览；#262 同样把 known_issue_demo.* 写在主工作区。 用户发现后质疑「为什么 demo 放在主工作区而不是 worktree，是不是工作流出问题」。
- 原记录归因：没有这条规则：worktree 隔离条款只约束交付物，未定义非交付的预览/临时产物放在哪里、 如何与源码目录隔离，以及何时清理。

### 255-classification-review-apply / 001-pm-system-survey-order

- 状态：open；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/255-classification-review-apply/workflow-issues/001-pm-system-survey-order.yaml)
- 问题：需求讨论前无系统调研步骤，方案两次作废，评估返工
- 经过：阶段：需求讨论（业务资产唯一真源）。PM 只核对分类表与问题库的存储 / 编辑代码，就以「平台内版本目录 + current 指针」为首选方案； 用户追问 release 流程后才核实到门禁跑 dev 实时数据、发布记录只含代码 commit、PAT 写权限未确认。方案被迫改为「资产在 dev + 路径式应用」 并追加门禁固定资产设计，前两轮评估作废。
- 原记录归因：有这条规则，但位置让人读不到：系统背景调研只写在 designing 阶段的工作流图，需求讨论阶段只剩「先查证，再提问」 与「先核实，再提案」两条通用原则，未定义核实的链路范围；PM 因此把「核实数据本体的读写」当成「核实系统」， 未沿生产 → 消费 → 发布 → 部署 → 门禁 → 权限追下去。
- 原记录建议：agent-pm §3.3 把系统调研前置到需求讨论阶段，并定义链路范围：给出方案前，先沿 「数据生产 → 消费 → 发布 → 部署 → 门禁 → 权限」逐段核实，每段给出证据（文件路径 + 分支 + 关键位置）； 任何一段未核实就给出选型方案，视为违规。核实动作写进需求讨论的工作流图，不留在 designing。

### 255-classification-review-apply / 002-spec-alignment-before-doc

- 状态：closed；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/255-classification-review-apply/workflow-issues/002-spec-alignment-before-doc.yaml)
- 问题：spec 未经逐条确认即写入并进入 doc，流程漏检
- 经过：阶段：spec 定稿。PM 只确认模块划分与 6 条功能点标题，就把完整的 project_mgr / backend / frontend / scheduled_task spec（9+7+8+2 条）写入 FEATURE.yaml 并开始 doc；用户发现 spec 未对齐，doc 暂停。
- 原记录归因：有规则但缺少检查点：spec 定稿只有描述性要求，没有「逐条确认后才能写入」的硬门禁； PM 把功能点标题确认当成 spec 定稿，先写入再进入 doc。
- 原记录建议：agent-pm.md §3.3 工作流图 spec design 改为逐 module 先展示确认再 write spec.<module>；§3.3.2 增加「硬门禁：逐条确认后才写入」。

### 255-classification-review-apply / 003-spec-decision-loss

- 状态：open；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/255-classification-review-apply/workflow-issues/003-spec-decision-loss.yaml)
- 问题：spec 未回读已定决策与验证结论，已确认内容被当作新设计重提
- 经过：阶段：feature spec 定稿。此前多轮讨论与验证已确认的结论（只做阶段一、去掉草稿、沿用顶部流程卡、不做专用回滚、 不改 repo_mgr 等），在写入 spec 时没有被带入；PM 在后续条目里重新提出这些已定内容，并要求用户再次确认。
- 原记录归因：有规则但位置与形态让人读不到：§3.3.2 只描述「与用户讨论定稿」，没有「写入前对照决策清单、验证结论与已有产物」 的强制动作；PM 按当轮对话组织 spec，跨轮确认的结论没有承载位置。
- 原记录建议：agent-pm §3.3.2 增加写入前检查点：写 spec 前，先回读本轮需求中已确认的决策、验证结论与已有原型， 逐条映射到 spec 条目；映射不上的列为待确认项，不得当作新设计重新提出。spec 中每条已定内容标注来源 （哪次讨论 / 哪个原型），未标注来源的新增条目一律先与用户确认。

### 255-classification-review-apply / 004-workflow-issue-recording-trigger

- 状态：closed；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/255-classification-review-apply/workflow-issues/004-workflow-issue-recording-trigger.yaml)
- 问题：用户指出流程问题时未即时记录，第三次追问才补提案
- 经过：阶段：feature spec 定稿。用户先后指出「spec 没对齐就写」「spec 丢了此前讨论内容」两次流程问题， PM 都把问题当作业务讨论输入处理，继续推进 spec 对齐；直到用户第三次追问才提出记录工作流缺口。
- 原记录归因：有规则但没有触发条件：§7.2 写「问题出现的当下就进 issue」，但未定义「用户指出流程问题」即触发记录； PM 把用户的流程纠正当作业务需求调整处理，未转为缺口记录。
- 原记录建议：agent-pm §7.2 把触发条件写死：用户直接指出流程问题（对齐缺失、内容丢失、步骤跳步、返工）时， 当轮必须先把缺口写成 workflow-issues 优化项文件并请用户确认，原讨论问题顺延到下一轮；「稍后补」不算记录。 并明确「一轮一问」下，缺口确认优先于继续讨论原问题。

### 255-classification-review-apply / 005-qa-frontend-user-perspective

- 状态：open；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/255-classification-review-apply/workflow-issues/005-qa-frontend-user-perspective.yaml)
- 问题：QA 前端只验用例行为点，缺用户视角审视，本应隐藏的按钮可见仍判 PASS
- 经过：错误分类配置页默认态，「错误分类定义」卡片出现本应隐藏的「保存」「取消」按钮；QA 第 2 轮报告判 PASS，证据只列 DOM `hidden=true`，用户打开页面发现多余按钮。
- 原记录归因：没有这条规则——qa.md 未定义「以用户视角审视前端界面」的验收阶段，前端只在 E2E 用例覆盖到的行为点上被检查，页面默认态、空态、编辑态与多余入口都不在验收范围内。

### 255-classification-review-apply / 006-poc-design-as-baseline

- 状态：open；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/255-classification-review-apply/workflow-issues/006-poc-design-as-baseline.yaml)
- 问题：决策变更只落 spec/doc，POC 原型与报告未同步，实现与设计稿脱节
- 经过：POC 阶段产出前端原型与方案报告（含草稿、通知对象展示、模拟 PR 合入）；后续决策改为保存即提交、通知只在飞书、本需求仅编辑、角色收敛；spec 与 doc/ 随决策更新，POC 设计稿未更新；developer 按 doc/ 实现，QA 按 doc/ 验收；用户打开 demo 后发现实现与设计稿不一致。
- 原记录归因：没有这条规则——提示词未定义「POC 设计稿是设计基线，设计决策变更须回写设计稿，实现与验收须对齐设计稿」；doc/ 与设计稿两套产物并存，只有 doc/ 被流程约束。

### 255-classification-review-apply / 007-pm-chunked-discussion

- 状态：open；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/255-classification-review-apply/workflow-issues/007-pm-chunked-discussion.yaml)
- 问题：§2 对话风格缺单轮输出量约束，讨论时一次性输出过多
- 经过：需求讨论阶段，PM 在单轮内并列多个问题与大段方案对比，用户表示看不过来，要求减少单轮输出量。
- 原记录归因：有但没有触发条件：§2 只有「一轮一问」与「最小信息」，未定义单轮输出的长度上限或分段要求，PM 把「一轮一问」理解为只限问题个数、不限内容量。

### 255-classification-review-apply / 008-terminology-alignment

- 状态：closed；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/255-classification-review-apply/workflow-issues/008-terminology-alignment.yaml)
- 问题：§2 缺「新术语先确认」触发条件，命名反复返工
- 经过：spec 与 doc 讨论中，PM 自拟「业务资产」「CS」「唯一真源」「配置生效版本」「AppliedConfig」「submissions」等术语与命名并直接写入 spec/doc，用户逐次表示看不懂或要求改名；最终改为「错误分类定义 / 错误分类表」「唯一版本来源」、删除「配置生效版本」、实体改为 `EffectiveClassificationConfig`、接口改为 `submissions`、删除 `closed_reason`。
- 原记录归因：有但没有触发条件：§2 只禁止自造名词，未定义「引入新术语 / entity 名 / 接口名」即触发确认，PM 把命名当作实现细节直接写入。

### 255-classification-review-apply / 009-review-completion-signal

- 状态：open；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/255-classification-review-apply/workflow-issues/009-review-completion-signal.yaml)
- 问题：终审缺明确的完成信号，用户追问期间 PM 已推进下一处
- 经过：doc 终审停在 schema 修改点时，用户就 `content_hash` 的作用连续追问；PM 回答后直接应用改动并贴出下一个文件 `api.md` 的修改点，未等用户确认。用户指出尚未 OK，实际仍在讨论 schema。
- 原记录归因：有但没有触发条件：§3.3.5 要求「用户确认后再给下一处」，但没有定义确认信号（如显式的「OK / 通过 / 下一个」），PM 把追问与讨论当成默认通过。

### 256-product-user-manual / 001-defer-workflow-issue-recording

- 状态：closed；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/256-product-user-manual/workflow-issues/001-defer-workflow-issue-recording.yaml)
- 问题：缺口出现后 PM 未在当轮记录确认，需用户三次追问才补，证据流失
- 经过：阶段：需求讨论。PM 把 knowledge/ 误解为面向使用者的知识，用户指出「你的理解也不对」。PM 当轮只做口头承认， 继续追问手册受众，未提出缺口记录；用户追问「为什么会有这种问题？？？」后仍未提；直到用户第三次点名才补提案。 当时错误描述与用户原话都在上下文中，证据本可一次取全。
- 原记录归因：有但没有触发条件。§7.2 有时机要求、§7.3 有确认要求，但没有一条把「用户纠正 / 自察到缺口」定义为当轮触发条件， 也没有规定触发后原讨论问题顺延、缺口确认成为本轮唯一动作。PM 因此把记录当作可与讨论并行、稍后补的动作， 「一轮一问」被理解为「继续问原问题」。
- 原记录建议：agent-pm §7.2 写明触发与优先级：用户纠正 PM 的产出、或 PM 自察到流程缺口时，当轮立即把「阶段 + 现象 + 触发」 写成 workflow-issues 优化项文件并请用户确认；确认前不继续原讨论，缺口确认优先于其它问题。 并把「用户说『记一下』」与「用户直接指出流程问题」列为强制触发，不等用户重复追问。

### 256-product-user-manual / 002-design-reference-resource-dir-contract

- 状态：open；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/256-product-user-manual/workflow-issues/002-design-reference-resource-dir-contract.yaml)
- 问题：design-reference 未定义内部资源目录契约，knowledge/ 用途无文档可查
- 经过：需求讨论阶段，PM 要说明 knowledge/ 是什么，在设计规范与 doc 中找不到全量清单，按目录名推断为 「面向使用者的知识」并写入现状描述；用户纠正。核查确认：design-reference.md 全文无 knowledge 承载位置； 29 个文件仅 19 个有清单，rmp_log_analysis_mistakes.md / rmp_common_errors.md / rmp_benv_id_mapping.md 全文无任何文档引用。
- 原记录归因：没有这条规则。design-reference 只定义 src/modules、doc/modules、doc/backend 的目录与章节契约， 仓库根下共享资源目录（knowledge/）既不在 §3 目录树，也没有对应的文档章节契约；唯一提及是 §3.1 画图规则「非模块对象：系统内资源目录、外部服务等按其归属着色」，只管图怎么画， 不管内容写在哪、写什么。清单只能由个别模块自加，跨消费者资源无归属，缺失无人兜底。
- 原记录建议：为 LLM 知识库新增专属保存目录并纳入 design-reference 目录契约；承载形式（doc 承载目录 / 物理迁移）待定

### 259-robo-classification-table-init / 001-analysis-artifacts-archive

- 状态：open；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/259-robo-classification-table-init/workflow-issues/001-analysis-artifacts-archive.yaml)
- 问题：前期讨论/分析产物落在临时目录，未按 feature 归档，产物无法追溯复用
- 经过：需求收集与设计阶段，PM 为错误分类表拆分做了代码分析，生成复核 HTML、生成脚本与 base_rows.json，放在仓库根 .tmp_259_split/；用户指出这类 POC/前期讨论产物应放到 对应 feature 目录并正式归档，类似 POC 输出。
- 原记录归因：没有这条规则——提示词只约定了 subagent 的 POC 产物路径，未约定 PM 在前期 讨论/分析阶段自行生成的产物路径，PM 沿用临时目录习惯，产物无法随 feature 归档与复用。

### 259-robo-classification-table-init / 002-frontend-demo-on-real-worktree

- 状态：open；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/259-robo-classification-table-init/workflow-issues/002-frontend-demo-on-real-worktree.yaml)
- 问题：前端目标规格/效果 demo 做成独立 mock，未基于真实 worktree，无法所见即所得
- 经过：需求讨论阶段，PM 把「前端目标规格与效果 demo」做成了一个独立的 HTML mock 页面， 放在 feature 的 poc/frontend/ 下；没有改真实 worktree 的前端代码，也没有跑真实服务。 用户打开后指出这不是他要的，要求基于当前实际 worktree 的项目修改，看最终效果。
- 原记录归因：没有这条规则——提示词未规定前端目标规格/效果 demo 必须直接改真实 worktree 并运行真实 服务；PM 按「静态 mock」的旧习惯处理，demo 与最终实现脱节，用户无法判断最终效果。

### 259-robo-classification-table-init / 003-frontend-demo-by-pm

- 状态：open；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/259-robo-classification-table-init/workflow-issues/003-frontend-demo-by-pm.yaml)
- 问题：前端目标规格/效果 demo 被派给 developer，违反由 PM 亲自做的职责边界
- 经过：用户要求基于真实 worktree 做前端效果 demo；PM 按「只调度，不执行」把它派给 developer subagent。用户质问为什么派 developer，并明确之后前端的 demo 都要由 PM 亲自来。
- 原记录归因：没有这条规则——提示词没有定义「前端目标规格/效果 demo 由 PM 亲自做，不派 subagent」； PM 把规格/效果讨论误判为实现类工作，派给 developer，既超前于 approved 流程，也不是 用户要的产物。

### 259-robo-classification-table-init / 004-frontend-demo-not-dev

- 状态：open；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/259-robo-classification-table-init/workflow-issues/004-frontend-demo-not-dev.yaml)
- 问题：前端效果 demo 被做成完整开发，跳过 spec/doc/approved 门禁
- 经过：需求讨论阶段，用户要求基于真实 worktree 做前端目标规格/效果 demo 用于讨论；PM 为让 页面真实可读写，直接修改了后端模型、配置数据、测试与前端代码，并在独立端口启动服务， 未走 designing → spec → doc → 终审 → approved → implementing 流程。
- 原记录归因：没有这条规则——提示词没有定义「前端效果 demo 允许改动的边界」与「approved 前禁止 实现」，PM 把用户「基于真实 worktree」的要求扩大为完整开发，跳过了 spec/doc/approved 门禁。

### 259-robo-classification-table-init / 005-spec-terminology-no-abbreviation

- 状态：closed；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/259-robo-classification-table-init/workflow-issues/005-spec-terminology-no-abbreviation.yaml)
- 问题：spec 术语被简写/省略，导致概念歧义，需明确禁止缩写与省略
- 经过：编写 project_mgr spec 时，把「分类表引用列表」简写成「引用列表」；用户无法判断 引用的是什么，追问「引用列表 -- 是什么的引用列表？」。同轮还把「effective 错误 分类表」简写成「有效表」，经用户指出后才改回完整名称。
- 原记录归因：没有这条规则——spec design 要求只约束功能点的完整性，未约束术语的完整表达； PM 沿用口语简写习惯，同一概念在不同位置出现不同叫法，产生歧义。

### 259-robo-classification-table-init / 006-service-first-boundary

- 状态：open；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/259-robo-classification-table-init/workflow-issues/006-service-first-boundary.yaml)
- 问题：service 契约按前端视图设计，展示规则漏进 service，职责边界混淆
- 经过：编写 backend spec 时，PM 把前端「全局表视图不展示项目专属错误分类表」的展示需求， 直接写成 service 的「错误分类表清单不返回项目专属错误分类表」规则。用户指出这是 为前端提供功能，不是从 service 出发；视图过滤应放在 frontend，service 应返回 完整的错误分类表清单。
- 原记录归因：没有这条规则——提示词没有规定 service / frontend 的职责边界，PM 从页面需求 反推 service 契约，把视图过滤、展示范围等前端逻辑写进 service 规则，导致 API 被单一前端视图绑定。

### 259-robo-classification-table-init / 007-long-tool-call-parse-failure

- 状态：open；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/259-robo-classification-table-init/workflow-issues/007-long-tool-call-parse-failure.yaml)
- 问题：提示词未约束单次工具调用体量，超长工具调用反复解析失败并打断流程
- 经过：设计阶段批量更新 doc 与 spec 期间，PM 把「多个文件的多处修改」合并进单个工具调用： 一条 Bash 命令内嵌多个 heredoc 写大段中文 YAML / Markdown，或一条命令里串联多次 文件写入与 git 操作。连续 3 次返回 “Your tool call was malformed and could not be parsed”，该批修改未落地，用户每次都要重发「继续」才能续上，同一批 doc 编辑被打断 3 次。
- 原记录归因：没有这条规则——提示词未定义单次工具调用的体量上限与形态要求（如「一次调用只做一处 文件修改」「大批量中文文本用 Write/Edit 而不用 heredoc 拼接」），PM 在需要改多处时 缺少可执行的拆分依据，自然倾向把多步合并成一次巨型调用。

### 260-dual-soc-master-only-analysis / 001-doc-review-locate-section

- 状态：open；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/260-dual-soc-master-only-analysis/workflow-issues/001-doc-review-locate-section.yaml)
- 问题：§3.3.5 doc 终审 · 修改点未标章节/行号致连续两轮纠偏
- 经过：阶段：feature #260 的 doc 终审。 PM 逐处提交 diff；第一处（log_filter/api.md 实现描述第 3 条）只写「对象：run_cla_filter 实现描述第 3 条」， 未给文件名内的章节路径，用户回复「- 修改内容： -- 没有给出具体章节，不行」。 PM 后续补充章节层级；在 ota_log_analyzer/api.md 的 is_dual_soc 约束一处，diff 只贴 docstring 两行、 未标出所属章节与行号，用户再次回复「没有给出具体章节，不行，提个工作流优化项」。
- 原记录归因：有规则但没有可执行的定位格式：§3.3.5 规定了「对象」要落到契约元素， 却未规定非接口元素（实现描述条目、docstring 参数说明）应写成「章节路径 + 行号范围」， 导致 PM 只写到条目名。

### 263-prod-task-import-eval-case / 001-e2e-visual-evidence

- 状态：open；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/263-prod-task-import-eval-case/workflow-issues/001-e2e-visual-evidence.yaml)
- 问题：QA 前端 E2E 只留文字观测点，无可查看截图/录屏，PM 需临时补拍
- 经过：feature 实现任务详情【导入用例集】。QA 验收 3 条 E2E 全部 PASS 并落盘 QA-REPORT.md，报告逐条列出观测点与实际值，但没有任何截图、录屏或 CDP 产物。用户验收后要求查看前端效果，PM 只能重新启动 dev 服务、用 CDP 打开页面补截 4 张图，才满足诉求。
- 原记录归因：有但位置或形态让人读不到：产物要求只存在于 PM 提示词 §1 的原则层，§5.4 QA 输入 prompt 与 §3.3.6 E2E 字段没有触发条件，QA 的验收基准仍是 FEATURE.yaml 的文字观测点与 doc 契约。

### 265-known-issue-form-field-adjustments / 001-term-alignment-before-doc-design

- 状态：closed；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/265-known-issue-form-field-adjustments/workflow-issues/001-term-alignment-before-doc-design.yaml)
- 问题：术语新增/修改未在 doc 设计前对齐，终审才被推翻致返工
- 经过：阶段：feature #265 doc 终审。PM 在 README 术语表新增「版本排序键」， 并在 api.md 与 store.py docstring 中引用。用户先问「版本排序键 这个是啥？」， PM 解释后用户说「我不认同这个命名」，最终要求「删除这个概念吧」。 用户随后指出：术语或概念是模块功能的核心组成单元，新增或修改应该在 doc 设计之前就对好。
- 原记录归因：有但没有触发条件：§3.3.4 有逐 doc 对齐的要求，但没有术语/概念的提前 对齐节点。术语是模块功能的核心组成单元，却在 doc 撰写时才被引入， 只能等终审才被用户看到。
- 原记录建议：agent-pm.md §1 工作原则新增「概念清晰，术语先行」；§2 术语条禁止自造、简写、缩写或省略；§3.3.2 增加「术语完整且已对齐」；§3.3 / §3.3.4 将 doc 设计改为按维度及 README 优先的文件顺序逐文件修改并逐处审核确认。

### 265-known-issue-form-field-adjustments / 002-e2e-observation-not-checked-against-design

- 状态：open；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/265-known-issue-form-field-adjustments/workflow-issues/002-e2e-observation-not-checked-against-design.yaml)
- 问题：E2E 观测点未核对现有设计，误判既有行为为缺陷致 QA 返工
- 经过：阶段：feature #265 E2E 用例设计。PM 写观测点「保存成功后列表出现待提交行， 模块列显示「其他」」。QA 执行第 1 轮返回 fail（QA-001），指出列表按设计只 展示当前生效问题库，待提交内容在「提交变更」确认框中核对。PM 复核代码与 截图后确认是 E2E 期望写错，修正用例后第 2 轮通过。
- 原记录归因：有但没有触发条件：§3.3.6 要求观测点可判定，但没有要求写期望前先核对 现有设计/实现，既有行为被误当成本次缺陷，导致 QA 空跑一轮。

### 265-known-issue-form-field-adjustments / 003-frontend-option-must-be-visual

- 状态：open；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/265-known-issue-form-field-adjustments/workflow-issues/003-frontend-option-must-be-visual.yaml)
- 问题：前端方案选项只用文字描述，用户看不到效果，要求一律可视化呈现
- 经过：阶段：已知问题登记页需求讨论。PM 就「列表预览呈现方式」给出三个纯文字选项—— 「1. 就地预览：列表直接呈现草稿后的结果…… 2. 分组预览：…… 3. 弹窗预览：……」， 没有任何可看的界面效果。用户纠正：以后问前端使用哪个方案，一律禁止使用文字， 一定要让他看到，所见即所得。
- 原记录归因：没有这条规则——提示词只有「决策一律文本编号」的统一要求，没有「前端方案必须给出 可看的界面效果、禁止只用文字描述」的例外与做法；两者冲突时按文字选项执行，用户 无法判断最终效果。

### 268-partial-coverage-notice-conclusion-tail / 001-done-transition-order-conflict

- 状态：closed；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/268-partial-coverage-notice-conclusion-tail/workflow-issues/001-done-transition-order-conflict.yaml)
- 问题：提示词 §5.4.3 与 §3.4.3 的 done 置位时序冲突，状态先于合入
- 经过：阶段：feature #268 QA 验收通过后。PM 依据 §5.4.3 执行 `feature transition 268 --to done`，随后才询问合入方式并创建 PR #1422993。此时 PR 尚未合入，feature 状态已为 done；而 §3.4.3「顺序约定」写的是「合入动作 → set done → worktree remove」。CLI 的 done 状态无出边，无法回退到 qa-reviewing。
- 原记录归因：「有但位置或形态让人读不到」——两节各自给出 done 置位规则，§5.4.3 在 subagent 章节、§3.4.3 在 worktree 章节；PM 按章节顺序先执行了 §5.4.3，未读到后文更具体的顺序约定，两条规则没有交叉引用或单一真源。
- 原记录建议：agent-pm.md §5.4.3 的 pass 分支改为引用 §3.4.3 合入方式：「按 §3.4.3 合入方式完成合入、feature transition <id> --to done 与 worktree remove」。

### 268-partial-coverage-notice-conclusion-tail / 002-qa-bypasses-pm-dispatch

- 状态：open；[原始记录](/home/wentao/work-dir/ota_issue_analyzer/.features/268-partial-coverage-notice-conclusion-tail/workflow-issues/002-qa-bypasses-pm-dispatch.yaml)
- 问题：提示词未禁止 subagent 间直接调度，QA 绕过 PM 驱动 developer 修复
- 经过：阶段：feature #268 QA 验收进行中。QA 在 QA-REPORT.md 中发现 minor 文档缺口 QA-001；随后 developer 代理在未经过 PM 调度的情况下收到修复指令，产出 commit 77252323（补 schema.md 注释）。PM 侧未执行 `feature transition --to implementing`，也未重新调度 developer。
- 原记录归因：「没有这条规则」——提示词只规定 PM 是状态与字段的唯一写入者，未规定 subagent 之间不得直接发起调度或修复请求；QA 侧缺少「发现问题只返回报告、不得驱动 developer」的约束，形成绕过通道。
