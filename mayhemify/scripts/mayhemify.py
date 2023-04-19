import click

from mayhemify.init import init
from mayhemify.add_harness import add_harness

@click.group()
def cli():
    pass

cli.add_command(init)
cli.add_command(add_harness)
