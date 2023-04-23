import click
import os
import pkgutil

from os import path

from mayhemify.utils import bold, get_repo_dir, is_snake_case, copy_template, \
    render_template

@click.command()
@click.argument('name')
def add_harness(name):
    """
    Script to add a test harness and integrate with the existing mayhem framework.
    Make sure to use "mayhemify init" before you add harnesses.

    NAME: Name of the test harness. should be all lowercase with underscores
          instead of spaces.
    """
    if not is_snake_case(name):
        click.echo(bold("Name must be in snake case"))
        return

    repo_dir, project_name = get_repo_dir()

    workflows_dir = path.join(repo_dir, ".github/workflows/")
    fuzz_dir = path.join(repo_dir, "fuzz/")
    fuzz_targets_dir = path.join(fuzz_dir, "fuzz_targets/")
    mayhemfiles_dir = path.join(fuzz_dir, "mayhemfiles/")

    click.echo(bold("Adding harness source file"))
    click.echo(f"Copying harness template to {fuzz_targets_dir}{name}.rs")
    copy_template(path.join(fuzz_targets_dir, f'{name}.rs'), "harness.rs")
    click.echo('')

    click.echo(bold("Adding bin build target to Cargo.toml"))
    click.echo(f"Appending cargo bin template to {fuzz_dir}Cargo.toml")
    copy_template(
        path.join(fuzz_dir, 'Cargo.toml'),
        'cargo_toml_bin_build',
        {'harness_name': name},
        'a'
    )
    click.echo('')

    click.echo(bold("Adding Mayhemfile"))
    click.echo(f"Copying Mayhemfile template to {mayhemfiles_dir}Mayhemfile_{name}")
    copy_template(
        path.join(mayhemfiles_dir, f"Mayhemfile_{name}"),
        "Mayhemfile",
        {'harness_name': name, 'project_name': project_name},
    )
    click.echo('')

    click.echo(bold("Adding entry to mayhem.yml"))
    contents = []
    with open(path.join(workflows_dir, "mayhem.yml"), 'r') as f:
        contents = f.readlines()

    search = "      # ------ end mcode-action steps\n"
    try:
        # search for second marker string
        idx = contents.index(search)
        click.echo(f"Inserting mayhem yml template into {workflows_dir}mayhem.yml")

        # insert yaml entry right before
        contents[idx:idx] = [
            line + '\n' for line
            in render_template("mayhem_yml_template", {'harness_name': name}).split("\n")
        ]
        with open(path.join(workflows_dir, "mayhem.yml"), 'w') as f:
            f.write(''.join(contents))
    except:
        click.echo('Unable to parse mayhem.yml file. You must add this manually.')
    click.echo('')


    click.echo(bold("Modifying Dockerfile"))
    click.echo(f"Appending dockerfile copy template to {fuzz_dir}Dockerfile")
    copy_template(
        path.join(fuzz_dir, 'Dockerfile'),
        'dockerfile_copy',
        {'harness_name': name, 'project_name': project_name},
        'a'
    )