import click
import os
import pkgutil

from os import path

from git import Repo

from jinja2 import Environment, BaseLoader

@click.command()
def cli():
    """
    Script to prepare an existing Rust project for fuzzing with Mayhem.
    Adds Mayhemfile, Dockerfile, and fuzz folder skeleton.
    """

    repo = Repo(os.getcwd(), search_parent_directories=True)
    assert not repo.bare

    repo_dir = repo.working_dir
    project_name = path.basename(repo_dir)

    workflows_dir = path.join(repo_dir, ".github/workflows/")
    fuzz_dir = path.join(repo_dir, "fuzz")
    fuzz_targets_dir = path.join(fuzz_dir, "fuzz_targets")
    mayhemfiles_dir = path.join(fuzz_dir, "mayhemfiles")

    click.echo(f'Detecting Project Name to be {project_name}')

    if not click.confirm(click.style(
        "This command is potentially destructive and is only meant to be "\
        "used on a new repo. Do you wish to continue?",
        fg="white", bg="red", bold="true"
    )):
        return

    click.echo('Initializing Mayhem GH Action')
    os.makedirs(workflows_dir, exist_ok=True)
    with open(path.join(workflows_dir, 'mayhem.yml'), 'w') as f:
        yml_template_str = pkgutil.get_data(
            'mayhemify', 'templates/mayhem.yml'
        ).decode('utf-8')
        rtemplate = Environment(loader=BaseLoader()).from_string(yml_template_str)
        f.write(rtemplate.render(**{}))

    click.echo('Initializing Fuzz Folder')
    os.makedirs(fuzz_targets_dir, exist_ok=True)
    with open(path.join(fuzz_dir, 'Cargo.toml'), 'w') as f:
        cargo_template_str = pkgutil.get_data(
            'mayhemify', 'templates/Cargo.toml'
        ).decode('utf-8')
        rtemplate = Environment(loader=BaseLoader()).from_string(cargo_template_str)
        f.write(rtemplate.render(project_name=project_name))
    with open(path.join(fuzz_dir, '.gitignore'), 'wb') as f:
        f.write(pkgutil.get_data('mayhemify', 'templates/gitignore'))

    click.echo('Initializing Mayhemfiles Folder')
    os.makedirs(mayhemfiles_dir, exist_ok=True)

    click.echo('Initializing Dockerfile')
    with open(path.join(fuzz_dir, 'Dockerfile'), 'w') as f:
        docker_template_str = pkgutil.get_data(
            'mayhemify', 'templates/Dockerfile'
        ).decode('utf-8')
        rtemplate = Environment(loader=BaseLoader()).from_string(docker_template_str)
        f.write(rtemplate.render(project_name=project_name))
