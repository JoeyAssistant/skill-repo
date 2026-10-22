"""agent-factory CLI main entry."""
from __future__ import annotations

import click

from agent_factory.cli.feature import feature_group
from agent_factory.cli.issue import issue_group
from agent_factory.cli.index import index_group
from agent_factory.cli.lock import lock_group
from agent_factory.cli.worktree import worktree_group


@click.group()
def main() -> None:
    """agent-factory CLI - operate YAML workflow files (.features/ .issues/).

    命令组：feature / issue / index / worktree / lock
    使用前先看各组 help：agent-factory feature --help
    """


main.add_command(feature_group)
main.add_command(issue_group)
main.add_command(index_group)
main.add_command(worktree_group)
main.add_command(lock_group)

# click 框架层参数解析错误（UsageError 家族：缺必填参数 / 类型错 / 未知选项）默认
# exit 2，与命令层「2 资源不存在」撞车；统一映射为 4「参数错误」，让各组 help 宣称的
# 退出码体系（0/1/2/3/4）在框架层同样成立。
click.UsageError.exit_code = 4


if __name__ == "__main__":
    main()
