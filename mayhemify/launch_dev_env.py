import click
import requests
import os
import time
import subprocess
import pkgutil

import hashlib
import giturlparse

from mayhemify.utils import bold, get_config_toml

from paramiko import SSHClient, AutoAddPolicy, RSAKey
from paramiko.ssh_exception import NoValidConnectionsError
from contextlib import contextmanager

def get_vultr_headers():
    vultr_pat = get_config_toml()['vultr_api_key']
    if vultr_pat == "":
        click.echo("Please set your Vultr Personal Access Token in ~/.config/mayhemify/config.toml")
        raise SystemExit
    return {
        "Authorization": "Bearer " + vultr_pat,
        "Content-Type": "application/json",
    }

def get_ssh_hash(pubkey):
    sha = hashlib.sha256()
    sha.update(pubkey.encode('utf-8'))
    return sha.hexdigest()[0:8]

def get_or_create_local_ssh_key():
    if not os.path.exists(os.path.expanduser("~/.ssh/mayhemify.pub")):
        click.echo("You don't have an SSH key. Generating one...")
        os.system("ssh-keygen -t rsa -b 4096 -f ~/.ssh/mayhemify -N \"\"")
    with open(os.path.expanduser("~/.ssh/mayhemify.pub")) as f:
        return f.read()

def delete_key(key):
    delete_key_url = "https://api.vultr.com/v2/ssh-keys/" + key
    delete_response = requests.delete(delete_key_url, headers=get_vultr_headers())
    delete_response.raise_for_status()
        

def get_or_create_ssh_key():
    pubkey = get_or_create_local_ssh_key()
    hash = get_ssh_hash(pubkey)

    list_keys_url = "https://api.vultr.com/v2/ssh-keys"
    list_response = requests.get(list_keys_url, headers=get_vultr_headers())
    list_response.raise_for_status()
    list_json = list_response.json()

    # if there is a valid key uploaded then return
    if list_json['meta']['total'] > 0:
        ssh_key = list_json['ssh_keys'][0]
        if ssh_key['name'] == "mayhemify-" + hash:
            click.echo("Authenticating with Vultr key " + ssh_key['name'] + "...")
            return ssh_key['id']
        else:
            click.echo("Vultr key invalid, deleting all uploaded keys...")
            for key in list_json['ssh_keys']:
                delete_key(key['id'])

    # otherwise delete all keys and create a new one
    click.echo("Uploading SSH key to Vultr...")

    new_response = requests.post(new_key_url, headers=get_vultr_headers(), json={
        "name": "mayhemify-" + hash,
        "ssh_key": pubkey,
    })
    new_response.raise_for_status()
    return new_response.json()['ssh_key']['id']

def get_instance_ip(instance_id):
    ping_interval = 5
    s_elapsed = 0
    while True:
        if s_elapsed > 180:
            click.echo("Instance took too long to start.")
            return None
        get_instance_url = "https://api.vultr.com/v2/instances/" + instance_id
        get_response = requests.get(get_instance_url, headers=get_vultr_headers())
        get_response.raise_for_status()
        ip = get_response.json()['instance']['main_ip']
        if ip != "0.0.0.0":
            return ip
        else:
            time.sleep(ping_interval)
        s_elapsed += ping_interval

def add_host_to_ssh_config(ip, hostname):
    # delete any existing host and all following lines
    with open(os.path.expanduser("~/.ssh/config"), "r") as f:
        lines = f.readlines()
    with open(os.path.expanduser("~/.ssh/config"), "w") as f:
        on_host = False
        for line in lines:
            if line.startswith("Host " + hostname):
                on_host = True
                break
            elif line == "\n":
                on_host = False
                continue

            if not on_host:
                f.write(line)

    with open(os.path.expanduser("~/.ssh/config"), "a") as f:
        f.write("\n")
        f.write("Host " + hostname + "\n")
        f.write("    HostName " + ip + "\n")
        f.write("    User root\n")
        f.write("    IdentityFile ~/.ssh/mayhemify\n")
        f.write("    StrictHostKeyChecking no\n")

@contextmanager
def get_connection(ip, ping_interval=10, timeout=300):
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy)
    ssh.load_host_keys(os.path.expanduser("~/.ssh/known_hosts"))
    mykey = RSAKey.from_private_key_file(os.path.expanduser("~/.ssh/mayhemify"))

    s_elapsed = 0
    while True:
        if s_elapsed < timeout:
            try:
                ssh.connect(ip, username="root", pkey=mykey)
                break
            except:
                time.sleep(ping_interval)
            s_elapsed += ping_interval
        else:
            raise Exception(f"Unable to connect to SSH after {timeout} seconds.")

    ssh.save_host_keys(os.path.expanduser("~/.ssh/known_hosts"))
    try:
        yield ssh
    finally:
        ssh.close()


def run_command(command, droplet_ip):
    with get_connection(droplet_ip) as ssh:
        click.echo(bold(
            "Running command: `" + command + "` on the dev environment..."
        ))
        stdin, stdout, stderr = ssh.exec_command(command)
        stdout.channel.set_combine_stderr(True)
        while not stdout.channel.exit_status_ready():
            time.sleep(0.1)
            buffer = stdout.channel.recv(1024)
            while buffer:
                click.echo(buffer.decode("utf-8"), nl=False)
                buffer = stdout.channel.recv(1024)
        return stdout.channel.recv_exit_status()

def append_repo(droplet_ip):
    with get_connection(droplet_ip) as ssh:
        click.echo(bold("Appending repos to sources.list..."))
        sftp = ssh.open_sftp()
        file = sftp.open("/etc/apt/sources.list", "a")

        file.write(pkgutil.get_data('mayhemify', "templates/repo_sources").decode("utf-8"))
        file.flush()

        sftp.close()


@click.command()
@click.argument('repo')
def launch_dev_env(repo):
    """
    Launches a mayhem development environment for the current project.
    """

    git_url = giturlparse.parse(repo)
    try:
        git_url.owner
        git_url.name
    except:
        click.echo("Invalid repo argument. Please use an https or ssh URL.")
        return

    list_instances_url = "https://api.vultr.com/v2/instances"
    list_response = requests.get(list_instances_url, headers=get_vultr_headers())
    list_response.raise_for_status()
    list_json = list_response.json()

    if list_json['meta']['total'] > 0:
        click.echo("You already have a mayhem development environment running.")
        if click.confirm("Do you want to delete it?"):
            instance_id = list_json['instances'][0]['id']
            delete_instance_url = "https://api.vultr.com/v2/instances/" + str(instance_id)
            delete_response = requests.delete(delete_instance_url, headers=get_vultr_headers())
            delete_response.raise_for_status()
        else:
            return

    label = f"mayhemify-{git_url.owner}-{git_url.name}"

    click.echo("Creating new Debian instance...")
    create_instance_url = "https://api.vultr.com/v2/instances"
    create_response = requests.post(create_instance_url, headers=get_vultr_headers(), json={
        "region": "lax",
        "label": label,
        "plan": "vc2-4c-8gb",
        "os_id": 477, # Debian 11
        "sshkey_id": [get_or_create_ssh_key()],
        "backups": "disabled",
    })
    create_response.raise_for_status()
    create_json = create_response.json()
    instance_id = create_json['instance']['id']

    instance_ip = get_instance_ip(instance_id)
    if instance_ip is None:
        return

    click.echo(f"Adding host to {'~/.ssh/config'}...")
    add_host_to_ssh_config(instance_ip, label)
    click.echo("Server is booting, connecting to SSH, could take a few minutes...")


    run_command(f"""
        apt-get update -y &&
        DEBIAN_FRONTEND=noninteractive apt-get -o Dpkg::Options::=--force-confold -o Dpkg::Options::=--force-confdef -y --allow-downgrades --allow-remove-essential --allow-change-held-packages dist-upgrade &&
        apt-get install -y cmake build-essential git &&
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y &&
        source "$HOME/.cargo/env" &&
        rustup install nightly &&
        rustup default nightly &&
        cargo install cargo-fuzz &&
        git clone {repo}
    """, instance_ip)

    # workflow permission -> read and write

    click.echo(bold(f"Dev environment is ready!"))
    click.echo(f"Connect with vscode or use `ssh {host}` to connect.")
