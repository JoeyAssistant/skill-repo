# worktree

feature 绑定的 git worktree 生命周期管理。

## 约定

- 一 feature ↔ 一分支 ↔ 一 worktree，同名同源
- 目录：`.worktrees/feat-<NNN>-<slug>`（入 .gitignore）
- 分支：`feature/<NNN>-<slug>`
- 绑定记录写在 FEATURE.yaml 的 `worktree` 字段（name/branch/path，相对路径），由 CLI 自动写入/清除
- 使用前以 `git worktree list` 为准校验记录是否仍然有效（记录是描述，git 登记是证据）

## 命令

- `worktree new <id> [--base <ref>]`：创建 worktree + 分支，写 FEATURE.yaml 记录。已绑定则报错。
- `worktree list [--format table|json]`：git 登记的 worktree 与 FEATURE.yaml 记录的对照（纯数据输出；孤儿/悬空判断留给 PM）
- `worktree remove <id> [--force]`：校验 feature=done → 移除 worktree → 删分支（-d）→ 清记录。非 done 拒绝（exit 3），确认要删用 --force（同时 git remove --force + branch -D）；分支已不存在时跳过删除（幂等）

## 退出码

0 成功 / 1 校验或 git 失败 / 2 资源不存在 / 3 状态违规 / 4 参数错误
