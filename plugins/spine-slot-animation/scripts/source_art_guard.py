#!/usr/bin/env python3
"""Shared write guard for protected H5G source-art roots."""

from __future__ import annotations

import os
from pathlib import Path

PROHIBITED_WRITE_ROOTS = (
    Path(r"G:\artSource"),
    Path(r"\\high5.local\Games\artSource"),
)
PROHIBITED_ROOT_MARKERS = {"perforce", "p4", ".p4"}


def _normalized_text(path: Path) -> str:
    return os.path.normcase(os.path.abspath(str(path))).rstrip("\\/")


def _normalized_candidates(path: Path) -> set[str]:
    candidates = {_normalized_text(path)}
    try:
        candidates.add(os.path.normcase(str(path.resolve(strict=False))).rstrip("\\/"))
    except OSError:
        pass
    parent = path if path.is_dir() else path.parent
    try:
        candidates.add(os.path.normcase(str(parent.resolve(strict=True) / path.name)).rstrip("\\/"))
    except OSError:
        pass
    return candidates


def path_is_under(path: Path, root: Path) -> bool:
    root_candidates = _normalized_candidates(root)
    path_candidates = _normalized_candidates(path)
    for path_text in path_candidates:
        for root_text in root_candidates:
            if path_text == root_text or path_text.startswith(root_text + os.sep):
                return True
    return False


def write_guard_error(path: Path, label: str = "path") -> str | None:
    for root in PROHIBITED_WRITE_ROOTS:
        if path_is_under(path, root):
            return f"{label} is under prohibited source-art root: {root}"
    for part in path.parts:
        marker = part.casefold()
        if marker in PROHIBITED_ROOT_MARKERS or marker.startswith("p4_"):
            return f"{label} is under prohibited write root marker: {part}"
    return None


def ensure_safe_write_path(path: Path, label: str = "path") -> Path:
    error = write_guard_error(path, label)
    if error:
        raise ValueError(error)
    return path
