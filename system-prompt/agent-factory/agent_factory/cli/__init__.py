"""agent-factory CLI main entry."""
from __future__ import annotations

import click

from agent_factory.cli.feature import feature_group


@click.group()
def main() -> None:
    """agent-factory CLI - operate YAML workflow files."""


main.add_command(feature_group)


# Subcommand groups will be registered here as they are implemented:
# from agent_factory.cli import issue, index
# main.add_command(issue.issue_group)
# main.add_command(index.index_group)


if __name__ == "__main__":
    main()
