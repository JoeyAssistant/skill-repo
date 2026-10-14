# feature
## schema
- id # feature编号
- title # feature标题，与目录一致
- desc # 需求描述
- background # 需求背景，为什么要做这个需求
    - pain_point # 解决什么痛点
    - benefit # 带来什么收益
- spec # 需求规格
    - module # 改动所在模块名，或 backend / frontend / skill / mcp
        - functions # 功能、修改点
            1. function_1 
            2. function_2
- e2e_test_cases # E2E 验收用例（可构造、可观测、可运行）
  1. test_case_1 # 端到端测试用例
    - name
    - precondition # 前置条件
    - inputs # 测试输入
    - steps # 测试步骤
    - observations
      - check  # 测试验证点
      - expect  # 预期结果

## state
  draft → designing → approved → implementing → qa-reviewing → done
  任意状态 → cancelled


## workflow
```mermaid
sequenceDiagram
    actor user
    user->>pm: 提一个需求 + desc
    participant feat as FEATURE.yaml
    participant wt as worktree(.worktrees/feat-NNN-slug)

    pm->>feat: create(id + title)
    pm->>user: 需求信息收集
    pm->>feat: background

    pm->>feat: set designing
    pm->>wt: worktree new（建目录+分支+写 feat 记录）
    pm->>wt: 了解文档 + 代码
    pm->>pm: 分析与设计
    alt 需要可行性验证
        pm->>+poc: 技术可行性或选型验证
        poc->>-pm: poc结果
    end

    Note over pm: question resolve start
    loop for each question
        pm->>+user: ask with propose and discusses
        user->>-pm: decision
    end
    Note over pm: question resolve end

    Note over pm: spec design start
    pm->>feat: write spec
    loop for each spec
        pm->>+user: ask and show for review
        user->>-pm: review ok
    end
    Note over pm: spec design end

    Note over pm: doc design start
    pm->>ref: read .claude/agents/{agent-architecture.drawio, design-reference.md}
    pm->>wt: write doc（写入 worktree 路径）

    Note over pm: 用户终审 start
    loop 逐处（按文件按修改点 N/M）
        pm->>+user: show diff + 修改原因（git -C worktree diff）
        user->>-pm: review ok
    end
    Note over pm: 用户终审 end
    Note over pm: doc design end

    Note over pm: E2E test design start
    loop for test case
        pm->>+user: propose test case design
        user->>-pm: ok
        pm->>feat: write e2e_test_cases
    end
    
    pm->>+user: ask for review e2e_test_cases in FEATURE.yaml
    user->>-pm: review ok
    Note over pm: E2E test design end

    pm->>feat: set approved
    participant dev as developer
    pm->>feat: set implementing
    pm->>wt: rebase origin/main（冲突→PM 当场解）
    pm-->>+dev: start coding(Root=worktree) background subagent
    dev->>wt: test driven development
    dev-->>-pm: complete + suggested_status

    pm->>pm: git show <sha> --stat 验证
    pm->>feat: qa-reviewing
    pm->>+qa: start acceptance test（E2E 前取 e2e.lock）
    qa->>-pm: done（释放锁）

    pm->>+user: 合入方式：merge 还是 PR
    user->>-pm: 选择
    alt merge
        pm->>wt: rebase origin/main（冲突→PM 当场解）
        pm->>pm: 主仓 merge --no-ff
        pm->>feat: set done
    else PR
        pm->>wt: rebase origin/main（冲突→PM 当场解）
        pm->>pm: push 分支 + 建 PR（带描述）
        Note over pm: 停在 qa-reviewing，等人工合入（打回则 set implementing → 修 → qa-reviewing → push 更新 PR）
        user->>pm: PR 已合入
        pm->>pm: 主仓 fetch + merge --ff-only origin/main
        pm->>feat: set done
    end
    pm->>pm: worktree remove（清目录+删分支+清记录）
```