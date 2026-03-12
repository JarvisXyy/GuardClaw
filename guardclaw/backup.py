from __future__ import annotations

import json
import os
import shutil
import stat
from datetime import datetime
from pathlib import Path


def snapshot_id() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def create_snapshot(root: Path, targets: list[Path]) -> Path:
    backup_root = root / ".guardclaw" / "backups"
    snap = backup_root / snapshot_id()
    snap.mkdir(parents=True, exist_ok=False)

    manifest: dict[str, str] = {}
    for path in targets:
        if not path.exists():
            continue
        rel = path.relative_to(root)
        dst = snap / rel
        dst.parent.mkdir(parents=True, exist_ok=True)

        if path.is_dir():
            shutil.copytree(path, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(path, dst)
        manifest[str(rel)] = str(dst.relative_to(snap))

    (snap / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return snap


def rollback_latest(root: Path, snapshot: str | None = None) -> Path:
    backup_root = root / ".guardclaw" / "backups"
    if not backup_root.exists():
        raise FileNotFoundError("No backup snapshots found.")

    snap = backup_root / snapshot if snapshot else sorted(backup_root.iterdir())[-1]
    if not snap.exists() or not snap.is_dir():
        raise FileNotFoundError(f"Snapshot not found: {snapshot}")

    manifest_path = snap / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Invalid snapshot: {snap.name}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for rel in manifest.keys():
        src = snap / rel
        dst = root / rel
        if src.is_dir():
            if dst.exists() and dst.is_file():
                dst.unlink()
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            _ensure_writable(dst)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    return snap


def _ensure_writable(path: Path) -> None:
    if not path.exists():
        return
    mode = stat.S_IMODE(path.stat().st_mode)
    os.chmod(path, mode | stat.S_IWUSR)
