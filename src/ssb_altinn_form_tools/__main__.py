"""Command-line interface."""

import click


@click.command()
@click.version_option()
def main() -> None:
    """SSB Altinn Form Tools."""


if __name__ == "__main__":
    main(prog_name="ssb-altinn-form-tools")  # pragma: no cover
