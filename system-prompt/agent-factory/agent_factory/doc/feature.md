# feature
## schema
- id # feature编号
- title # feature标题，与目录一致
- desc # 需求描述
- agent_type
- background # 需求背景，为什么要做这个需求
    - pain_point # 解决什么痛点
    - benefit # 带来什么收益
- spec # 需求规格
    - model_a # 模块A
        - functions # 功能、修改点
            1. function_1 
            2. function_2
        - schema # data schema
        - interface # API CLI
- test_cases[]


## workflow
```mermaid
sequenceDiagram
    actor user
    user->>pm: 提一个需求 + desc
    participant feat as FEATURE.yaml
    participant code as codebase

    pm->>feat: create(id + title)
    pm->>user: 需求信息收集
    pm->>feat: background
    pm->>feat: set designing
    pm->>code: 了解文档 + 代码
    pm->>pm: load design-reference.md + agent-architecture.drawio
    pm->>pm: 分析与设计
    loop for each question
        pm->>+user: ask with prppose and discusses
        user->>-pm: desision
    end
    pm->>feat: write spec
    loop for test case
        pm->>+user: prppose test plan
        user->>-pm: ok
    end
    pm->>feat: write test_cases
    participant dev as developer
    pm->>+user: ask for review FEATURE.yaml
    user->>-pm: review ok

    pm->>code: write doc
    pm->>+user: ask for doc review
    user-->-pm: review ok
    pm->>feat: set approved

    pm->>feat: set implementing
    pm->>+dev: start coding(FEATURE.yaml + doc)
    dev->>code: test driven development
    dev->>-pm: done

    pm->>feat: qa-reviewing
    pm->>+qa: start acceptance test
    qa->>-pm: done
    pm->>feat: set done
```