# Issue
## schema
- id # issue编号
- title # issue标题，与目录一致
- desc # 问题描述
- scenario # 场景
- impact # 问题影响
- root_cause # 问题根因
- fix_plan # 修改方案
- result # issue处理结果
    - bugfix
        - fix_desc # 修改内容
        - verification # 验证结果
    - feature_request # 转需求
        - feature_id # 需求编号

## workflow
```mermaid
sequenceDiagram
    actor user
    
    user->>pm: 提一个issue + desc
    pm->>ISSUE.yaml: create(id + title + desc)
    pm->>user: 信息收集 + 疑问确认
    user->>pm: 
    pm->>ISSUE.yaml: scenario + impact
    pm->>+qa: 开始问题定位
    qa->>ISSUE.yaml: root_cause + fix_plan
    qa->>-pm:
    pm->>+user: review 确认
    user->>-pm: ok
    alt is bugfix
    participant dev as developer
        pm->>+dev: fix this bug
        dev->>dev: bugfix
        dev->>ISSUE.yaml: fix_desc
        dev->>-pm:
        pm->>pm: 验收
        pm->>ISSUE.yaml: verification + close
    else is feature
        pm->>REQUIREMENT.yaml: create(root_cause fix_plan)
        pm->>ISSUE.yaml: feature_id + close
    end
```