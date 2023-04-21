import click
import os
import re
import pkgutil
import toml

from jinja2 import Environment, BaseLoader
from os import path
from git import Repo

def bold(s):
    return click.style(s, bold="true")

def get_repo_dir():
    repo = Repo(os.getcwd(), search_parent_directories=True)
    assert not repo.bare

    repo_dir = repo.working_dir
    project_name = path.basename(repo_dir)
    return (repo_dir, project_name)

def is_snake_case(s):
    return re.search("^[a-z0-9]+(?:_[a-z0-9]+)*$", s) != None

def copy_template(target_path, template_name, render_dict={}, flags='w'):
    with open(target_path, flags) as f:
        f.write(render_template(template_name, render_dict))

def render_template(template_name, render_dict={}):
    template_str = pkgutil.get_data(
        'mayhemify', f'templates/{template_name}'
    ).decode('utf-8')
    jinja_template = Environment(loader=BaseLoader()).from_string(template_str)
    return jinja_template.render(**render_dict)

def get_config_toml():
    # check if config.toml exists in ~/.config/mayhemify/
    config_path = os.path.expanduser("~/.config/mayhemify/config.toml")
    if not os.path.exists(config_path):
        click.echo("You don't have a config.toml file. Creating one...")
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        copy_template(config_path, "config.toml")

    # read config.toml
    with open(config_path) as f:
        return toml.loads(f.read())
