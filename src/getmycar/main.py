from __future__ import annotations

import click


@click.group()
@click.version_option()
def cli() -> None:
    """getmycar - Carsensor scraping CLI."""


if __name__ == "__main__":
    cli()
