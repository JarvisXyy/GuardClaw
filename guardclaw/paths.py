from __future__ import annotations

from pathlib import Path


def resolve_runtime_root(root: Path) -> Path:
    """
    Resolve OpenClaw runtime root with compatibility for different layouts.

    Supported priority:
    1) <root>/.openclaw          (nested layout)
    2) <root>/../.openclaw       (sibling layout)
    3) <root> (if itself is .openclaw)
    4) <root>                    (fallback)
    """
    root = root.resolve()

    nested_hidden = root / ".openclaw"
    sibling_hidden = root.parent / ".openclaw"

    if nested_hidden.exists() and nested_hidden.is_dir():
        return nested_hidden

    if sibling_hidden.exists() and sibling_hidden.is_dir():
        return sibling_hidden

    if root.name == ".openclaw" and root.is_dir():
        return root

    return root
