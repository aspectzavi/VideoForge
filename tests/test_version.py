"""
Fast, pytest-based tests for engine/version.py.
"""

from __future__ import annotations

from videoforge.engine import version


def test_version_string_format() -> None:
    assert version.VERSION == f"{version.MAJOR}.{version.MINOR}.{version.PATCH}"
    assert version.__version__ == version.VERSION


def test_version_tuple() -> None:
    assert version.version_tuple() == (version.MAJOR, version.MINOR, version.PATCH)


def test_version_info_contains_expected_keys() -> None:
    info = version.version_info()

    assert info["name"] == version.APP_NAME
    assert info["version"] == version.__version__
    assert info["major"] == version.MAJOR
    assert info["minor"] == version.MINOR
    assert info["patch"] == version.PATCH


def test_banner_includes_version_and_app_name() -> None:
    banner = version.banner()

    assert version.APP_NAME in banner
    assert version.__version__ in banner
