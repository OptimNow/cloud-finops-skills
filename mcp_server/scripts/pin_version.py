#!/usr/bin/env python3
"""Set the package version in ``pyproject.toml`` to the one in ``plugin.json``.

The hosted connector answers ``initialize`` with the installed package's
version, and pip reads that from ``pyproject.toml``. ``plugin.json`` is the
version holder a release bumps; ``pyproject.toml`` is bumped beside it by hand
and nothing fails a release when it is forgotten, because the release workflow
rewrites the field itself before it builds the wheel. The image for the hosted
connector is built from the checkout, not from that wheel, so the Dockerfile
runs this script before ``pip install``: the image then announces the version
of ``plugin.json`` whoever builds it, the release workflow or ``fly deploy``
from a laptop.

Usage::

    python scripts/pin_version.py                     # rewrite pyproject.toml
    python scripts/pin_version.py --verify-installed  # after pip install

``--verify-installed`` changes nothing: it exits 1 unless the installed
``cloud-finops-mcp`` reports the version in ``plugin.json``.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as installed_version
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_JSON = REPO_ROOT / "plugins" / "cloud-finops" / ".claude-plugin" / "plugin.json"
PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"
PACKAGE = "cloud-finops-mcp"

# The first `version = "..."` at the start of a line is the one in [project]:
# the table opens the file's metadata and no table before it carries the key.
VERSION_LINE = re.compile(rb'^version = "[^"\r\n]*"', flags=re.M)
SEMVER = re.compile(r"\d+\.\d+\.\d+")


class PinError(Exception):
    """The version could not be read or written."""


def release_version(plugin_json: Path = PLUGIN_JSON) -> str:
    """The version in plugin.json, refused unless it is three-part semver."""
    try:
        version = str(json.loads(plugin_json.read_text(encoding="utf-8"))["version"])
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise PinError(f"cannot read a version from {plugin_json}: {exc}") from exc
    if not SEMVER.fullmatch(version):
        raise PinError(f"{plugin_json} carries version {version!r}, expected X.Y.Z")
    return version


def pin(pyproject: Path = PYPROJECT, plugin_json: Path = PLUGIN_JSON) -> str:
    """Write plugin.json's version into pyproject.toml and return it.

    Bytes in, bytes out: line endings and everything but the one field stay
    as they were. A file already on that version is not rewritten.
    """
    version = release_version(plugin_json)
    try:
        original = pyproject.read_bytes()
    except OSError as exc:
        raise PinError(f"cannot read {pyproject}: {exc}") from exc
    pinned, count = VERSION_LINE.subn(f'version = "{version}"'.encode(), original, count=1)
    if count != 1:
        raise PinError(f'{pyproject} has no `version = "..."` line to pin')
    if pinned != original:
        pyproject.write_bytes(pinned)
    return version


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--verify-installed",
        action="store_true",
        help=f"check the installed {PACKAGE} against plugin.json instead of writing",
    )
    args = parser.parse_args(argv)
    try:
        if args.verify_installed:
            expected = release_version()
            try:
                installed = installed_version(PACKAGE)
            except PackageNotFoundError:
                print(f"[pin_version] {PACKAGE} is not installed", file=sys.stderr)
                return 1
            if installed != expected:
                print(
                    f"[pin_version] installed {PACKAGE} is {installed}, "
                    f"plugin.json says {expected}",
                    file=sys.stderr,
                )
                return 1
            print(f"[pin_version] installed {PACKAGE} is {installed}, as plugin.json says")
            return 0
        version = pin()
    except PinError as exc:
        print(f"[pin_version] {exc}", file=sys.stderr)
        return 1
    print(f"[pin_version] pyproject.toml version is {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
