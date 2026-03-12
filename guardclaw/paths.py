from __future__ import annotations

from pathlib import Path


def resolve_runtime_root(root: Path) -> Path:
    hidden_root = root / ".openclaw"
    if hidden_root.exists() and hidden_root.is_dir():
        return hidden_root.resolve()
    return root.resolve()
