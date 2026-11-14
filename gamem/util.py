"""Shared helpers for scanners."""

from __future__ import annotations

import os
import re
import string
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional

IS_WINDOWS = sys.platform == "win32"

# Non-game titles shipped by Steam that should not appear in the library.
STEAM_TOOL_PATTERNS = (
    re.compile(p, re.IGNORECASE)
    for p in (
        r"steamworks common redistributables",
        r"proton \d",
        r"\bsdk\b",
        r"source sdk",
        r"valve test app",
        r"\btool\b",
    )
)
STEAM_TOOL_RES = list(STEAM_TOOL_PATTERNS)


def looks_like_tool(name: str) -> bool:
    return any(rx.search(name) for rx in STEAM_TOOL_RES)


def env_path(*parts: str, env: Optional[str] = None) -> Optional[Path]:
    """Resolve a path from an environment variable (e.g. PROGRAMFILES)."""
    if env:
        base = os.environ.get(env)
        if not base:
            return None
        return Path(base).joinpath(*parts)
    return None


def first_existing(candidates: Iterable[Path]) -> Optional[Path]:
    for c in candidates:
        try:
            if c and c.exists():
                return c
        except OSError:
            continue
    return None


def program_dirs() -> List[Path]:
    dirs = []
    for env in ("ProgramFiles", "ProgramFiles(x86)", "ProgramW6432"):
        v = os.environ.get(env)
        if v:
            p = Path(v)
            if p not in dirs:
                dirs.append(p)
    if not dirs and IS_WINDOWS:
        dirs = [Path(r"C:\Program Files"), Path(r"C:\Program Files (x86)")]
    return dirs


def drives() -> List[Path]:
    """All available drive roots on Windows (C:\, D:\ ...)."""
    if not IS_WINDOWS:
        return []
    roots = []
    for letter in string.ascii_uppercase:
        root = Path(f"{letter}:/")
        try:
            if root.exists():
                roots.append(root)
        except OSError:
            continue
    return roots


def find_main_exe(folder: Path, prefer_name: Optional[str] = None) -> Optional[Path]:
    """Heuristic: find the 'main' game executable inside an install folder.

    Prefers an exe matching `prefer_name`, then the largest exe at shallow
    depth (game executables are usually the biggest binaries).
    """
    best: Optional[Path] = None
    best_score = -1.0
    try:
        for path in folder.rglob("*.exe"):
            try:
                depth = len(path.relative_to(folder).parts)
                if depth > 3:
                    continue
                size = path.stat().st_size
            except OSError:
                continue
            score = size / (1 + depth)
            if prefer_name:
                stem = path.stem.lower()
                if stem == prefer_name.lower():
                    score += 1e12
                elif prefer_name.lower() in stem:
                    score += 1e9
            # Deprioritize obvious helpers
            low = path.name.lower()
            if any(x in low for x in ("unins", "crash", "report", "setup", "redist", "vcredist", "dxsetup", "unitycrash")):
                score -= 1e11
            if score > best_score:
                best_score = score
                best = path
    except OSError:
        return None
    return best


def folder_size(path: Path, limit_files: int = 200000) -> Optional[int]:
    total = 0
    count = 0
    try:
        for root, _dirs, files in os.walk(path):
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(root, f))
                except OSError:
                    continue
                count += 1
                if count > limit_files:
                    return total
        return total
    except OSError:
        return None


def parse_acf_date(unix_ts: Optional[str]) -> Optional[str]:
    import datetime

    try:
        ts = int(unix_ts)
        if ts <= 0:
            return None
        return datetime.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def iso_from_yyyymmdd(value: Optional[str]) -> Optional[str]:
    if not value or len(str(value)) < 8:
        return None
    v = str(value)
    return f"{v[0:4]}-{v[4:6]}-{v[6:8]}"


def powershell_json(command: str, timeout: int = 25):
    """Run a PowerShell command and parse JSON output. Windows only."""
    if not IS_WINDOWS:
        return None
    try:
        proc = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                command,
            ],
            capture_output=True,
            timeout=timeout,
            text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.SubprocessError):
        return None
    out = (proc.stdout or "").strip()
    if not out:
        return None
    import json

    try:
        return json.loads(out)
    except ValueError:
        return out


def norm_path(p: Optional[str]) -> str:
    if not p:
        return ""
    return os.path.normcase(os.path.normpath(str(p)))
