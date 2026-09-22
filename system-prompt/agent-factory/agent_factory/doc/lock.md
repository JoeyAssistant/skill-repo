# lock

跨实例互斥锁（当前用于 E2E 验收串行）。

## 机制

- 锁位置：`$(git rev-parse --git-common-dir)/locks/<name>.lock/`——所有 worktree 共享同一 git common dir，此路径是跨实例唯一全局点
- 锁形态：目录（mkdir 原子获取）+ 内嵌 `holder.yaml {holder, pid, since}`
- stale 检测：acquire 失败时按 holder 的 pid 做 `kill -0` 存活检查；进程已死 → 自动清理旧锁并重取成功；holder 文件缺失/损坏 → 视为无效锁自动清理
- 等待策略：拿不到锁即失败退出（exit 1）并输出当前 holder 信息，不自动轮询——由用户决定何时重试

## 命令

- `lock acquire <name> --holder <text> [--pid <pid>] [--force]`：获取锁。`--pid` 传调用方实例 pid（如 shell 里用 `$PPID`），用于 stale 检测。被活锁占用 exit 1。`--force` 人工确认对方已死后强取。
- `lock release <name>`：释放锁（幂等，无锁 exit 0）。
- `lock status <name>`：查看 free / held（holder、pid、存活检测、since）。

## 典型用法（E2E 验收）

```bash
agent-factory lock acquire e2e --holder "feature/002-xxx" --pid $PPID || exit 1
# ... 跑 E2E ...
agent-factory lock release e2e   # 含 fail 路径，必须释放
```

## 退出码

0 成功 / 1 锁被活占用或校验失败 / 2 非 git 仓库 / 4 参数错误
