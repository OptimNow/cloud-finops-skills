"""scripts/pin_version.py makes the hosted image announce plugin.json's version.

``serverInfo.version`` is the installed package's version, which pip reads from
``pyproject.toml``. The release workflow rewrites that field before building the
wheel, but the hosted connector's image is built from the checkout, so the
Dockerfile runs this script first. These tests pin that it changes that one field
and nothing else, and that it refuses rather than guesses.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "pin_version.py"

PYPROJECT = (
    "[build-system]\n"
    'requires = ["hatchling>=1.27,<2"]\n'
    "\n"
    "[project]\n"
    'name = "cloud-finops-mcp"\n'
    'version = "1.0.0"\n'
    'requires-python = ">=3.10"\n'
    "\n"
    "[tool.example]\n"
    'version = "9.9.9"\n'
)


@pytest.fixture()
def pinner():
    spec = importlib.util.spec_from_file_location("pin_version_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def files(tmp_path):
    """A pyproject.toml on 1.0.0 beside a plugin.json on 1.1.0."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_bytes(PYPROJECT.encode("utf-8"))
    plugin_json = tmp_path / "plugin.json"
    plugin_json.write_text(json.dumps({"name": "cloud-finops", "version": "1.1.0"}), "utf-8")
    return pyproject, plugin_json


def test_a_forgotten_bump_is_pinned_to_plugin_json(pinner, files):
    pyproject, plugin_json = files

    assert pinner.pin(pyproject, plugin_json) == "1.1.0"

    assert pyproject.read_bytes().decode("utf-8") == PYPROJECT.replace(
        'version = "1.0.0"', 'version = "1.1.0"'
    )


def test_only_the_project_version_moves(pinner, files):
    """A `version` key in a later table is somebody else's."""
    pyproject, plugin_json = files

    pinner.pin(pyproject, plugin_json)

    assert 'version = "9.9.9"' in pyproject.read_text("utf-8")


def test_windows_line_endings_survive(pinner, files):
    pyproject, plugin_json = files
    pyproject.write_bytes(PYPROJECT.replace("\n", "\r\n").encode("utf-8"))

    pinner.pin(pyproject, plugin_json)

    data = pyproject.read_bytes()
    assert b'version = "1.1.0"\r\n' in data
    assert data.count(b"\r\n") == PYPROJECT.count("\n")


def test_a_file_already_on_the_version_is_left_alone(pinner, files):
    pyproject, plugin_json = files
    plugin_json.write_text(json.dumps({"version": "1.0.0"}), "utf-8")
    before = pyproject.stat().st_mtime_ns

    assert pinner.pin(pyproject, plugin_json) == "1.0.0"

    assert pyproject.stat().st_mtime_ns == before
    assert pyproject.read_bytes() == PYPROJECT.encode("utf-8")


def test_no_version_line_is_an_error_not_a_silent_pass(pinner, files):
    pyproject, plugin_json = files
    pyproject.write_text('[project]\nname = "cloud-finops-mcp"\ndynamic = ["version"]\n', "utf-8")

    with pytest.raises(pinner.PinError, match="no `version"):
        pinner.pin(pyproject, plugin_json)


@pytest.mark.parametrize("content", ['{"version": "1.1"}', '{"name": "x"}', "[]", "not json"])
def test_a_plugin_json_without_a_semver_version_is_refused(pinner, files, content):
    pyproject, plugin_json = files
    plugin_json.write_text(content, "utf-8")

    with pytest.raises(pinner.PinError):
        pinner.pin(pyproject, plugin_json)

    assert pyproject.read_bytes() == PYPROJECT.encode("utf-8")


def test_the_repository_files_are_where_the_script_looks(pinner):
    """The Dockerfile calls the script with no argument, so its defaults must resolve."""
    if not pinner.PLUGIN_JSON.is_file():
        pytest.skip("plugin.json is not part of this checkout (sdist)")
    assert pinner.PYPROJECT.is_file()
    assert pinner.VERSION_LINE.search(pinner.PYPROJECT.read_bytes())
    assert pinner.SEMVER.fullmatch(pinner.release_version())
