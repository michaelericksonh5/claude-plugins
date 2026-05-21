"""Shared Spine editor/runtime version policy for generated proof packages."""

from __future__ import annotations

DEFAULT_SPINE_EDITOR_VERSION = "4.3.04"
DEFAULT_SPINE_PLAYER_VERSION = "4.3.1"
SUPPORTED_SPINE_EDITOR_PREFIXES = ("4.2", "4.3")


def is_supported_editor_version(version: str) -> bool:
    return any(version.startswith(prefix) for prefix in SUPPORTED_SPINE_EDITOR_PREFIXES)
