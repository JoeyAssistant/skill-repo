"""agent-factory CLI main entry."""
from __future__ import annotations

import click

from agent_factory.cli.feature import feature_group
from agent_factory.cli.issue import issue_group
from agent_factory.cli.index import index_group


@click.group()
def main() -> None:
    """agent-factory CLI - operate YAML workflow files."""


main.add_command(feature_group)
main.add_command(issue_group)
main.add_command(index_group)


if __name__ == "__main__":
    main()
