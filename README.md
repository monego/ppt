# Primitive Package Tool

I got tired of checking and downloading programs that aren't packaged in distributions (yes, mostly Rust CLI tools) on GitHub, so I automated the process. This script checks for the latest releases in a repository, allows you to download a binary file and unpack it into `~/.local/bin`. 

## Usage

Rename `ppt.sh` to `ppt` and move it to a directory in your PATH.

`$ ppt owner repo # On GitHub`

e.g. `$ ppt astral-sh ruff` will install or update [ruff](https://github.com/astral-sh/ruff).

## Dependencies

`ppt` depends on `curl`, `jq` and `wget`.

## TODO

- Verify sha256sum when available
- Write a short help section
- POSIX compatibility
- Customize unpack path
