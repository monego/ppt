from packaging import version
from pathlib import Path
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress
from rich.table import Table
import click
import json
import logging
import os
import requests
import shutil
import sys
import tarfile

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[RichHandler()])


@click.group()
def ppt():
    """Python program for downloading and managing binaries from GitHub."""
    pass


@click.command()
@click.argument('url')
@click.option('--install-path', default=Path('~/.local/bin/').expanduser(),
              help='Installation path')
def install(url: str, install_path: str):
    """Install a program (i.e. copy it to a directory in PATH)."""
    # <--- Download --->

    response = requests.get(url, stream=True)

    url_split = url.split('/')
    archive_filename = url_split[-1]
    owner = url_split[3]
    filename = url_split[4]
    version = url_split[7]
    repository = url.split('releases')

    logging.info(f"Dowloading {filename}...")

    archive_path = download_archive(response, archive_filename)

    logging.info("Download complete!")

    # <--- Copy --->

    logging.info(f"Extracting and copying f{filename}")
    scan_archive(archive_path, filename)
    logging.info("Extraction and copy done!")

    # <--- Save to JSON file --->

    save_to_json(filename, owner, version, repository[0], archive_filename, is_update=False)


@click.command()
@click.argument('program')
def uninstall(program):
    """Delete the executable from the location."""
    path = Path('~/.local/share/ppt/ppt.json').expanduser()

    if json_file_exists(path):
        with path.open('r') as f:
            packages = json.load(f)
            if program in packages:
                del packages[program]
                program_path = Path(f'~/.local/bin/{program}').expanduser()
                try:
                    program_path.unlink()
                except FileNotFoundError:
                    logging.warning(
                        'Could not find the executable. Not deleting anything.'
                    )
                with open(path, 'w') as file:
                    json.dump(packages, file, indent=4)
                sys.stdout.write('\n')
                click.echo(f'Uninstalled {program}.')
            else:
                logging.error(f'Could not find {program} installed.')
    else:
        logging.error('Could not find ppt.json')


@click.command()
@click.argument('program')
def update(program):
    """Update a given executable."""
    path = Path('~/.local/share/ppt/ppt.json').expanduser()

    if json_file_exists(path):
        with path.open('r') as f:
            packages = json.load(f)
        if program in packages:
            try:
                owner = packages[program]['owner']
                repo = packages[program]['repo']
                latest = fetch_latest_release(owner, repo)
                latest_version = version.parse(latest)
                current_version = version.parse(
                    packages[program]['version']
                )
                if latest_version > current_version:
                    logging.info(
                        f'Updating {program} from {current_version}'
                        f' to {latest_version}'
                    )
                    fname = packages[program]['filename']
                    url = f'https://github.com/{owner}/{repo}/releases/download/{latest_version}/{fname}'
                    response = requests.get(url, stream=True)
                    archive_path = download_archive(response, fname)
                    scan_archive(archive_path, repo)
                    packages[program]['version'] = str(latest_version)
                    with path.open('w') as f:
                        json.dump(packages, f, indent=4)
                    click.echo(f'Updated {program}')
                else:
                    click.echo(f'Latest version of {program} is'
                               f' {latest_version}, nothing to update.')
            except FileNotFoundError:
                logging.warning(
                    'Could not find the executable. Not deleting anything.'
                )
        else:
            logging.error(f'Could not find {program} installed.')
    else:
        logging.error('Could not find ppt.json')


@click.command()
def list():
    """List all 'installed' executables."""
    path = Path('~/.local/share/ppt/ppt.json').expanduser()
    if not path.exists():
        sys.stdout.write('')
    else:
        with path.open('r') as f:
            try:
                packages = json.load(f)
            except json.JSONDecodeError:
                logging.error('Error decoding ppt.json')
                return

            table = Table(title="Program list")
            table.add_column("Program", style='magenta')
            table.add_column("Version", style='green')

            for package in packages:
                name = package
                version = packages[package].get('version')
                table.add_row(name, version)

            console = Console()
            console.print(table)


def download_archive(response, filename: str):
    """Download the compressed archive to /tmp."""
    total_size = int(response.headers.get('content-length', 0))
    archive_path = '/tmp/' + filename

    with open(archive_path, 'wb') as f, Progress() as progress:
        task = progress.add_task("[cyan]Downloading...", total=total_size)
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            progress.update(task, advance=len(chunk))

    return archive_path


def fetch_latest_release(owner, repo):
    """Check for the latest release on GitHub."""
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    response = requests.get(url)
    response.raise_for_status()
    release_data = response.json()
    return release_data.get('tag_name')


def json_file_exists(path):
    """Check whether ppt.json exists."""
    if path.exists() and path.stat().st_size > 0:
        return True
    else:
        return False


def save_to_json(name, owner, version, url, fname, is_update=True):
    """Save executable information to the JSON file."""
    path = Path('~/.local/share/ppt/ppt.json').expanduser()

    if json_file_exists(path):
        with open(path, 'r') as f:
            packages = json.load(f)
    else:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)
        packages = {}

    if name in packages and not is_update:
        logging.warning(f"Package '{name}' already exists. Skipping.")
    else:
        with open(path, 'w') as f:
            packages[name] = {
                'owner': owner,
                'repo': name,
                'version': version,
                'url': url,
                'filename': fname,
            }
            json.dump(packages, f, indent=4)


def is_executable(path: str):
    """Check whether the file is executable."""
    return os.access(path, os.X_OK) and not os.path.isdir(path)


def scan_archive(path: str, bname: str):
    """Scan the compressed archive for binaries."""
    path = Path(path)

    if '.tar' in path.suffixes:
        if '.gz' in path.suffixes:
            with tarfile.open(path, 'r:gz') as tar:
                for member in tar.getmembers():
                    if member.isfile():
                        tar.extract(member, path='/tmp/tmp')
                        file_path = Path('/tmp/tmp') / member.name

                        if is_executable(file_path):
                            shutil.copy2(
                                file_path,
                                Path(f'~/.local/bin/{bname}').expanduser()
                            )


ppt.add_command(install)
ppt.add_command(uninstall)
ppt.add_command(update)
ppt.add_command(list)

if __name__ == '__main__':
    ppt()
