import click
import os

from os import path

from mayhemify.utils import bold, get_repo_dir, copy_template, Language

@click.command()
@click.option('--language', '-l', type=click.Choice([l.value for l in Language]), default=Language.RUST.value)
def init(language):
    """
    Script to prepare an existing Rust project for fuzzing with Mayhem.
    Adds Mayhemfile, Dockerfile, and fuzz folder skeleton.
    """
    repo_dir, project_name = get_repo_dir()

    workflows_dir = path.join(repo_dir, ".github/workflows/")
    fuzz_dir = path.join(repo_dir, "fuzz/")
    fuzz_targets_dir = path.join(fuzz_dir, "fuzz_targets/")
    mayhemfiles_dir = path.join(fuzz_dir, "mayhemfiles/")

    click.echo(bold(
        f'Detecting Project Name to be {project_name}',
    ))

    click.echo('')
    if not click.confirm(click.style(
        "This command is potentially destructive and is only meant to be "\
        "used on a new repo. Do you wish to continue?",
        fg="white", bg="red", bold="true"
    )):
        return
    click.echo('')

    click.echo(bold('Initializing Mayhem GH Action'))
    click.echo(f"Creating folder {workflows_dir}")
    os.makedirs(workflows_dir, exist_ok=True)
    click.echo(f"Copying mayhem.yml to {workflows_dir}mayhem.yml")
    copy_template(path.join(workflows_dir, 'mayhem.yml'), "mayhem.yml")
    click.echo('')

    click.echo(bold('Initializing Fuzz Folder'))
    click.echo(f"Creating folder {fuzz_dir}")
    click.echo(f"Creating folder {fuzz_targets_dir}")
    os.makedirs(fuzz_targets_dir, exist_ok=True)

    if language == Language.RUST.value:
        click.echo(f"Copying Cargo.toml to {fuzz_dir}Cargo.toml")
        copy_template(
            path.join(fuzz_dir, 'Cargo.toml'), "Cargo.toml", {'project_name': project_name}
        )
    click.echo(f"Copying .gitignore to {fuzz_dir}.gitignore")
    copy_template(path.join(fuzz_dir, '.gitignore'), "gitignore")
    click.echo('')

    click.echo(bold('Initializing Mayhemfiles Folder'))
    click.echo(f"Creating folder {mayhemfiles_dir}")
    os.makedirs(mayhemfiles_dir, exist_ok=True)
    click.echo('')

    click.echo(bold('Initializing Dockerfile'))
    click.echo(f"Copying Dockerfile to {fuzz_dir}Dockerfile")
    copy_template(
        path.join(fuzz_dir, 'Dockerfile'), f"Dockerfile_{language}", {'project_name': project_name}
    )

    click.echo(bold('Overwriting vscode settings.'))
    click.echo(f"Copying settings.json to /root/.vscode-server/data/Machine/settings.json")
    copy_template(
        "/root/.vscode-server/data/Machine/settings.json",
        'settings.json', {'project_name': project_name}
    )
