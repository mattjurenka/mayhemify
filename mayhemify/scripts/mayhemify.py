import click

from mayhemify.init import init
from mayhemify.add_harness import add_harness
from mayhemify.launch_dev_env import launch_dev_env

@click.group()
def cli():
    pass

cli.add_command(init)
cli.add_command(add_harness)
cli.add_command(launch_dev_env)
