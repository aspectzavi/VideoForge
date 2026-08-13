"""
VideoForge Version Information

Single source of truth for application version metadata.
"""

from __future__ import annotations

from typing import Final

# =====================================================================
# Semantic Version
# =====================================================================

MAJOR: Final[int] = 0
MINOR: Final[int] = 1
PATCH: Final[int] = 0

# Optional pre-release tag:
# Examples:
#   None
#   "alpha"
#   "beta"
#   "rc1"

PRERELEASE: Final[str | None] = None

# Optional build metadata
# Example:
#   "20260727"

BUILD: Final[str | None] = None

# =====================================================================
# Application Metadata
# =====================================================================

APP_NAME: Final[str] = "VideoForge"

APP_AUTHOR: Final[str] = "Kevin Kamau"

APP_EMAIL: Final[str] = "envisio.io@gmail.com"

APP_DESCRIPTION: Final[str] = "AI-powered FFmpeg video processing toolkit."

# =====================================================================
# Version Strings
# =====================================================================

_VERSION = f"{MAJOR}.{MINOR}.{PATCH}"

if PRERELEASE:
    _VERSION += f"-{PRERELEASE}"

if BUILD:
    _VERSION += f"+{BUILD}"

__version__: Final[str] = _VERSION

VERSION: Final[str] = __version__

# =====================================================================
# Helpers
# =====================================================================


def version_tuple() -> tuple[int, int, int]:
    """
    Return the semantic version as a tuple.

    Example
    -------
    >>> version_tuple()
    (0, 1, 0)
    """
    return (
        MAJOR,
        MINOR,
        PATCH,
    )


def version_info() -> dict[str, str | int | None]:
    """
    Return structured version information.
    """
    return {
        "name": APP_NAME,
        "version": __version__,
        "major": MAJOR,
        "minor": MINOR,
        "patch": PATCH,
        "prerelease": PRERELEASE,
        "build": BUILD,
        "author": APP_AUTHOR,
        "email": APP_EMAIL,
        "description": APP_DESCRIPTION,
    }


def banner() -> str:
    """
    Return a CLI banner.
    """
    return f"""
====================================================
                    VideoForge
       AI-Powered FFmpeg Video Toolkit

Version : {__version__}
Author  : {APP_AUTHOR}
====================================================
""".strip()


# =====================================================================
# Public API
# =====================================================================

__all__ = [
    "__version__",
    "VERSION",
    "APP_NAME",
    "APP_AUTHOR",
    "APP_EMAIL",
    "APP_DESCRIPTION",
    "MAJOR",
    "MINOR",
    "PATCH",
    "PRERELEASE",
    "BUILD",
    "version_tuple",
    "version_info",
    "banner",
]
