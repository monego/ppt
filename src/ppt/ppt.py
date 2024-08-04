from pathlib import Path
import click
import logging
import os
import requests
import shutil
import sys
import tarfile

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


@click.group()
def ppt():
    """Python program for downloading and managing binaries from GitHub."""
    pass


@click.command()
@click.argument('url')
@click.option('--install-path', default=os.path.expanduser('~/.local/bin/'),
              help='Installation path')
def install(url: str, install_path: str):
    """Install a program (i.e. copy it to a directory in PATH)."""
    # <--- Download --->

    response = requests.get(url, stream=True)

    url_split = url.split('/')
    archive_filename = url_split[-1]
    filename = url_split[4]

    logging.info(f"Dowloading {filename}...")

    archive_path = download_archive(response, archive_filename)

    sys.stdout.write('\n')
    logging.info("Download complete!")

    # <--- Copy --->

    logging.info(f"Extracting and copying f{filename}")
    scan_archive(archive_path, filename)
    logging.info("Extraction and copy done!")


@click.command()
@click.argument('program')
def uninstall(program):
    """Delete the executable from the location."""
    click.echo(f'Deleted {program}')


@click.command()
@click.argument('program')
def update(program):
    """Update a given executable."""
    click.echo('Updated program')


@click.command()
def list():
    """List all 'installed' executables."""
    pass


def download_archive(response, filename: str):
    """Download the compressed archive to /tmp."""
    total_size = int(response.headers.get('content-length', 0))
    archive_path = '/tmp/' + filename

    downloaded_size = 0

    with open(archive_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            downloaded_size += len(chunk)
            percent_complete = (downloaded_size / total_size) * 100
            sys.stdout.write(f'\rDownload progress: {percent_complete:.2f}%')
            sys.stdout.flush()

    return archive_path


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
                        file_path = os.path.join('/tmp/tmp', member.name)

                        if is_executable(file_path):
                            shutil.copy2(
                                file_path,
                                f'{os.getenv("HOME")}/.local/bin/{bname}'
                            )


ppt.add_command(install)
ppt.add_command(uninstall)
ppt.add_command(update)
ppt.add_command(list)

if __name__ == '__main__':
    ppt()
