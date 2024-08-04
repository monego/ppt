# Primitive Package Tool

I got tired of checking and downloading programs that aren't packaged in distributions (yes, mostly Rust CLI tools) on GitHub, so I automated the process. This script checks for the latest releases in a repository, allows you to download a binary file and unpack it into `~/.local/bin`.

## Usage

`$ ppt install URL # GitHub URL`

e.g. `$ ppt https://github.com/astral-sh/ruff/releases/download/0.5.6/ruff-x86_64-unknown-linux-gnu.tar.gz` will install [ruff](https://github.com/astral-sh/ruff) (change the URL to pick the latest version).

After that, you can update the program by the repository name:

`$ ppt update ruff`

## Dependencies

`ppt` depends on Click, Packaging, Requests and Rich.
