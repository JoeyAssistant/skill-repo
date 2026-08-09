"""agent-factory CLI main entry."""
from __future__ import annotations

import click


@click.group()
def main() -> None:
    """agent-factory CLI - operate YAML workflow files."""


# Subcommand groups will be registered here as they are implemented:
# from agent_factory.cli import feature, issue, index
# main.add_command(feature.feature_group)
# main.add_command(issue.issue_group)
# main.add_command(index.index_group)


if __name__ == "__main__":
    main()
