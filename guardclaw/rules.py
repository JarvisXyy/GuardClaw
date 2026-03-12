from __future__ import annotations

from pathlib import Path

SYSTEM_RULE_DIR = Path("openclaw_system_rules/guardclaw-unified-rules")
SYSTEM_RULE_FILE = "SKILL.md"


def install_system_skill(root: Path, skill_source: Path) -> Path:
    if not skill_source.exists():
        raise FileNotFoundError(f"Skill file not found: {skill_source}")

    target_dir = root / SYSTEM_RULE_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / SYSTEM_RULE_FILE
    target_file.write_text(skill_source.read_text(encoding="utf-8"), encoding="utf-8")
    return target_file


def inject_workspace_rules(root: Path, skill_content: str) -> list[Path]:
    workspace_root = _resolve_workspace_root(root)
    changed: list[Path] = []

    if workspace_root is None:
        return changed

    targets = _collect_rule_targets(workspace_root)
    for target in targets:
        original = target.read_text(encoding="utf-8") if target.exists() else ""
        if skill_content in original:
            continue

        merged = f"{skill_content.strip()}\n\n{original.lstrip()}"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(merged, encoding="utf-8")
        changed.append(target)

    return changed


def _collect_rule_targets(workspace_root: Path) -> list[Path]:
    nested = sorted(workspace_root.glob("workspace-*"))
    if nested:
        targets: list[Path] = []
        for ws in nested:
            candidates = [ws / "AGENT_RULES.md", ws / "SOUL.md"]
            target = next((p for p in candidates if p.exists()), candidates[0])
            targets.append(target)
        return targets

    # 单工作区：workspace 下直接放 SOUL.md/AGENT_RULES.md
    direct_candidates = [workspace_root / "AGENT_RULES.md", workspace_root / "SOUL.md"]
    target = next((p for p in direct_candidates if p.exists()), workspace_root / "SOUL.md")
    return [target]


def _resolve_workspace_root(root: Path) -> Path | None:
    preferred = root / "workspace"
    legacy = root / "workspaces"
    if preferred.exists():
        return preferred
    if legacy.exists():
        return legacy
    return None
