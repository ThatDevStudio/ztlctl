"""Allow running ztlctl as a module: python -m ztlctl."""

from ztlctl.cli import cli

if __name__ == "__main__":
    cli()
