import click
import os

from os import path
from mayhemify.utils import bold, get_config_toml

@click.command()
def create_config():
    """Ensures a config file exists for mayhemify."""
    get_config_toml()

