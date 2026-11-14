"""Minimal parser for Valve KeyValues (VDF / ACF) text format.

Handles both the classic and modern syntax used by Steam files
(libraryfolders.vdf, appmanifest_*.acf, localconfig.vdf ...).
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

_TOKEN_RE = re.compile(
    r'"((?:[^"\\]|\\.)*)"|([{}])|([^\s{}"]+)',
    re.MULTILINE,
)

_UNESCAPE = {"\\n": "\n", "\\t": "\t", '\\\\"': '"', "\\\\": "\\"}


def _clean(value: str) -> str:
    for k, v in _UNESCAPE.items():
        value = value.replace(k, v)
    return value


def parse_vdf(text: str) -> Dict[str, Any]:
    """Parse VDF text into nested dicts. Duplicate keys are merged."""
    tokens = []
    for m in _TOKEN_RE.finditer(text):
        quoted, brace, bare = m.group(1), m.group(2), m.group(3)
        if quoted is not None:
            tokens.append(("str", _clean(quoted)))
        elif brace:
            tokens.append(("brace", brace))
        else:
            tokens.append(("str", bare))

    root: Dict[str, Any] = {}
    # Parallel stacks: current dict per level + the key awaiting a value.
    dicts = [root]
    pending: List[Optional[str]] = [None]
    i = 0
    n = len(tokens)
    while i < n:
        kind, value = tokens[i]
        if kind == "brace":
            if value == "{":
                key = pending[-1]
                if key is None:
                    raise ValueError("Unexpected '{' in VDF stream")
                child: Dict[str, Any] = {}
                existing = dicts[-1].get(key)
                if isinstance(existing, dict):
                    child = existing
                dicts[-1][key] = child
                pending[-1] = None  # key consumed by the block
                dicts.append(child)
                pending.append(None)
            else:  # '}'
                if len(dicts) == 1:
                    raise ValueError("Unbalanced '}' in VDF stream")
                dicts.pop()
                pending.pop()
            i += 1
        else:  # string token
            if pending[-1] is None:
                pending[-1] = value
            else:
                dicts[-1][pending[-1]] = value
                pending[-1] = None
            i += 1
    return root


def get_ci(d: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Case-insensitive dict get (Steam files are inconsistent with casing)."""
    if key in d:
        return d[key]
    low = key.lower()
    for k, v in d.items():
        if k.lower() == low:
            return v
    return default
