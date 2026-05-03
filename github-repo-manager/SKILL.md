---
name: github-repo-manager
description: Use when managing multiple GitHub repositories across accounts - clone all repos, sync updates, check for new repos, explore repo structure, or configure GitHub account management
---

# GitHub Repo Manager

管理多个 GitHub 账户的仓库：克隆、同步、检查新仓库、探索仓库结构。配置保存在 `~/.repo-manager/config.yaml`。

## 触发条件

- 用户提到 GitHub 仓库管理、克隆、同步
- 用户想检查是否有新仓库
- 用户想查看/探索某个仓库
- 用户想添加新的 GitHub 账户
- 用户提到 `/github-repo-manager`

## 首次配置

如果 `~/.repo-manager/config.yaml` 不存在，向用户收集以下信息：

1. **基础目录** — 仓库本地存储路径（如 `~/Workspace/repos`）
2. **GitHub 账户** — 每个账户需要：
   - 账户名（GitHub 用户名或组织名）
   - 类型：`organization`（组织）或 `user`（个人）

### 配置文件格式

保存到 `~/.repo-manager/config.yaml`：

```yaml
# ~/.repo-manager/config.yaml
base_path: ~/Workspace/repos
accounts:
  - name: <ORG_NAME>
    type: organization
  - name: <USER_NAME>
    type: user
```

创建目录：
```bash
mkdir -p ~/.repo-manager
```

## 关键规则

### 必须使用 `gh` 命令
- 所有 GitHub 操作必须使用 `gh` CLI
- 禁止使用 curl 直接调用 GitHub API

### 路径约定
- 本地路径 = `<base_path>/<account_name>/<repo_name>`
- 远程 URL = `https://github.com/<account_name>/<repo_name>.git`

## 快速参考

| 操作 | 命令 |
|------|------|
| 列出远程仓库 | `gh repo list <account> --limit 100` |
| JSON 格式列出 | `gh repo list <account> --json name,description,isPrivate --jq '.[]'` |
| 克隆单个仓库 | `git clone https://github.com/<account>/<repo>.git <base>/<account>/<repo>` |
| 同步所有仓库 | `cd <account_dir> && for d in */; do [ -d "$d/.git" ] && git -C "$d" pull 2>/dev/null; done` |

## 工作流

### "检查新仓库"
1. 读取 `~/.repo-manager/config.yaml`
2. 对每个账户运行：`gh repo list <name> --limit 100 --json name --jq '.[].name'`
3. 与本地 `<base_path>/<account>/` 下的目录对比
4. 克隆缺失的仓库
5. 报告新增内容

### "同步所有仓库"
1. 读取配置文件
2. 对每个账户目录，遍历子目录执行 `git pull`
3. 报告同步状态

### "克隆所有仓库"
1. 读取配置文件
2. 对每个账户：`gh repo list <account> --limit 100`
3. 跳过已存在的目录，克隆新仓库
4. 报告完成数量

### "展示所有仓库"
1. 读取配置文件
2. 对每个账户：`gh repo list <account> --json name,description,isPrivate`
3. 格式化显示，标注可见性
4. 显示本地同步状态

### "探索仓库"
1. 读取配置，若本地不存在则先克隆
2. 读取 `CLAUDE.md`、`README.md`
3. 提供摘要：用途、技术栈、项目结构

### "添加账户"
1. 询问账户名、类型
2. 追加到 `~/.repo-manager/config.yaml`
3. 创建本地目录

### "重新配置"
1. 读取当前配置
2. 询问需要修改的内容
3. 更新配置文件

## 常见错误

- 使用 curl 代替 `gh` 调用 GitHub API
- 操作前未通过 `gh repo list` 获取最新仓库列表
- 克隆前未检查目录是否已存在
- 忘记读取配置文件就执行操作
