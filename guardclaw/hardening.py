from __future__ import annotations

import json
import os
import stat
from pathlib import Path

from .backup import create_snapshot
from .rules import inject_workspace_rules, install_system_skill

LOCAL_BIND_VALUES = {"loopback", "127.0.0.1", "localhost", "local"}


class HardeningResult:
    def __init__(self) -> None:
        self.snapshot: str | None = None
        self.changed_files: list[Path] = []
        self.messages: list[str] = []


def run_hardening(
    root: Path,
    skill_source: Path | None,
    enforce_gateway_local: bool = False,
    allow_external_gateway: bool = False,
    lock_level: str = "soft",
) -> HardeningResult:
    result = HardeningResult()
    workspace_root = _resolve_workspace_root(root)

    targets = [
        root / "openclaw.json",
        root / ".env",
        root / "credentials",
    ]
    if workspace_root:
        targets.append(workspace_root)
    snap = create_snapshot(root, targets)
    result.snapshot = snap.name

    result.changed_files.extend(
        _handle_gateway(
            root,
            result.messages,
            enforce_gateway_local=enforce_gateway_local,
            allow_external_gateway=allow_external_gateway,
        )
    )
    result.changed_files.extend(_lock_permissions(root, result.messages))

    if skill_source:
        system_rule_path = install_system_skill(root, skill_source)
        result.changed_files.append(system_rule_path)
        skill_content = skill_source.read_text(encoding="utf-8")
        injected = inject_workspace_rules(root, skill_content)
        result.changed_files.extend(injected)
        result.messages.append(f"已向 {len(injected)} 个 workspace 注入 GuardClaw 系统规则。")

    result.changed_files.extend(_apply_lock_level(root, result.messages, lock_level))
    return result


def unlock_permissions(root: Path) -> list[Path]:
    changed: list[Path] = []
    if os.name == "nt":
        return changed

    for target in [root / "openclaw.json", root / ".env"]:
        if not target.exists():
            continue
        mode = stat.S_IMODE(target.stat().st_mode)
        os.chmod(target, mode | stat.S_IWUSR)
        changed.append(target)

    return changed


def _resolve_workspace_root(root: Path) -> Path | None:
    preferred = root / "workspace"
    legacy = root / "workspaces"
    if preferred.exists():
        return preferred
    if legacy.exists():
        return legacy
    return None


def _handle_gateway(
    root: Path,
    messages: list[str],
    enforce_gateway_local: bool,
    allow_external_gateway: bool,
) -> list[Path]:
    config = root / "openclaw.json"
    if not config.exists():
        messages.append("未找到 openclaw.json，已跳过 gateway 处理。")
        return []

    data = json.loads(config.read_text(encoding="utf-8"))
    gateway = data.get("gateway", {}) if isinstance(data.get("gateway", {}), dict) else {}

    mode = str(gateway.get("mode", "")).strip().lower()
    bind = str(gateway.get("bind", "")).strip().lower()
    host = str(gateway.get("host", "")).strip().lower()

    has_mode_bind_schema = "mode" in gateway or "bind" in gateway
    local_mode = mode == "local" and bind in LOCAL_BIND_VALUES
    local_host = host in {"127.0.0.1", "localhost"}

    if local_mode or local_host:
        messages.append("gateway 已是本地绑定，跳过重写。")
        return []

    if allow_external_gateway and not enforce_gateway_local:
        messages.append("检测到外网监听，但按用户策略允许外网访问，未修改 gateway。")
        return []

    if not enforce_gateway_local:
        messages.append("检测到非本地 gateway，默认不自动修改。若要强制本地化，请使用 --enforce-gateway-local。")
        return []

    if has_mode_bind_schema:
        gateway["mode"] = "local"
        gateway["bind"] = "loopback"
        # mode/bind schema 下不要写 host，避免 Unrecognized key: host
        if "host" in gateway:
            gateway.pop("host", None)
        data["gateway"] = gateway
        _write_json(config, data)
        messages.append("已按 mode/bind schema 将 gateway 强制设置为 local + loopback。")
        return [config]

    gateway["host"] = "127.0.0.1"
    data["gateway"] = gateway
    _write_json(config, data)
    messages.append("已按 host schema 将 gateway.host 强制设置为 127.0.0.1。")
    return [config]


def _write_json(path: Path, payload: dict) -> None:
    if os.name != "nt" and path.exists():
        mode = stat.S_IMODE(path.stat().st_mode)
        os.chmod(path, mode | stat.S_IWUSR)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _lock_permissions(root: Path, messages: list[str]) -> list[Path]:
    changed: list[Path] = []
    if os.name == "nt":
        messages.append("当前版本暂未实现 Windows ACL 自动加固。")
        return changed

    for f in [root / "openclaw.json", root / ".env"]:
        if f.exists():
            os.chmod(f, 0o600)
            changed.append(f)

    cred = root / "credentials"
    if cred.exists():
        os.chmod(cred, 0o700)
        changed.append(cred)
        for sub in cred.rglob("*"):
            if sub.is_dir():
                os.chmod(sub, 0o700)
            else:
                os.chmod(sub, 0o600)
            changed.append(sub)

    messages.append("已完成核心配置与 credentials 权限加固。")
    return changed


def _apply_lock_level(root: Path, messages: list[str], lock_level: str) -> list[Path]:
    if lock_level not in {"off", "soft", "strict"}:
        raise ValueError("lock_level must be one of: off, soft, strict")

    if lock_level == "off":
        messages.append("权限锁策略: off（不额外加锁）。")
        return []

    if lock_level == "soft":
        messages.append("权限锁策略: soft（保留 owner 写权限，便于后续维护）。")
        return []

    changed: list[Path] = []
    if os.name == "nt":
        messages.append("当前版本在 Windows 上跳过 strict 只读锁定。")
        return changed

    for target in [root / "openclaw.json", root / ".env"]:
        if target.exists():
            mode = stat.S_IMODE(target.stat().st_mode)
            readonly_mode = mode & ~stat.S_IWUSR
            os.chmod(target, readonly_mode)
            changed.append(target)

    messages.append("权限锁策略: strict（已移除 owner 写权限）。")
    return changed
