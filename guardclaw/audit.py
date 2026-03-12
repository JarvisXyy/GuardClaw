from __future__ import annotations

import json
import os
import re
import stat
from pathlib import Path

from .models import AuditReport, Finding

SENSITIVE_PATTERNS: dict[str, str] = {
    r"\bos\.system\s*\(": "检测到 os.system 命令执行行为",
    r"\bsubprocess\.(run|Popen|call)\s*\(": "检测到 subprocess 命令执行行为",
    r"\beval\s*\(": "检测到 eval 动态执行",
    r"\bexec\s*\(": "检测到 exec 动态执行",
    r"\brequests\.post\s*\(": "检测到 requests.post 外发请求",
    r"\bcurl\s+https?://": "检测到 curl 网络请求",
    r"\bwget\s+https?://": "检测到 wget 网络请求",
    r"/etc/hosts|C:\\\\Windows\\\\System32\\\\drivers\\\\etc\\\\hosts": "检测到 hosts 文件修改风险",
    r"systemctl\s+(enable|start)|sc\s+create": "检测到服务安装/启动行为",
    r"(Invoke-WebRequest|Start-BitsTransfer)": "检测到静默下载行为",
}

EXTERNAL_IP_POST_PATTERN = re.compile(r"requests\.post\s*\(\s*['\"]http://(?!localhost|127\.0\.0\.1)([^'\"]+)['\"]")
LOCAL_BIND_VALUES = {"loopback", "127.0.0.1", "localhost", "local"}


def run_audit(
    runtime_root: Path,
    display_root: Path | None = None,
    allow_external_gateway: bool = False,
) -> AuditReport:
    findings: list[Finding] = []
    findings.extend(_audit_gateway(runtime_root, allow_external_gateway))
    findings.extend(_audit_permissions(runtime_root))
    findings.extend(_audit_skills(runtime_root))
    findings.extend(_audit_workspace_isolation(runtime_root))
    root_for_report = display_root.resolve() if display_root else runtime_root.resolve()
    return AuditReport.new(str(root_for_report), findings)


def _audit_gateway(runtime_root: Path, allow_external_gateway: bool) -> list[Finding]:
    findings: list[Finding] = []
    config = runtime_root / "openclaw.json"
    if not config.exists():
        findings.append(Finding("网关暴露检测", "中", "未找到 openclaw.json，无法校验 gateway 配置。"))
        return findings

    try:
        payload = json.loads(config.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        findings.append(Finding("网关暴露检测", "高", f"openclaw.json 不是合法 JSON：{exc}"))
        return findings

    gateway = payload.get("gateway", {}) if isinstance(payload.get("gateway", {}), dict) else {}
    mode = str(gateway.get("mode", "")).strip().lower()
    bind = str(gateway.get("bind", "")).strip().lower()
    host = str(gateway.get("host", "")).strip().lower()
    auth_mode = str(gateway.get("auth", {}).get("mode", "")).strip().lower() if isinstance(gateway.get("auth"), dict) else ""

    has_mode_bind_schema = "mode" in gateway or "bind" in gateway
    has_host_schema = "host" in gateway

    if has_mode_bind_schema and has_host_schema:
        findings.append(Finding("网关暴露检测", "中", "检测到 mode/bind 与 host 混用，可能与当前 OpenClaw schema 不兼容。"))

    if mode == "local" and bind in LOCAL_BIND_VALUES:
        findings.append(Finding("网关暴露检测", "信息", "网关为本地模式（mode=local, bind=loopback），无需额外 host 配置。"))
        return findings

    if host in {"127.0.0.1", "localhost"}:
        findings.append(Finding("网关暴露检测", "信息", "网关仅监听本地地址。", details={"host": host}))
        return findings

    is_external_exposure = False
    if has_mode_bind_schema:
        if mode and mode != "local":
            is_external_exposure = True
        if bind and bind not in LOCAL_BIND_VALUES:
            is_external_exposure = True
    else:
        if host in {"", "0.0.0.0"}:
            is_external_exposure = True

    if not is_external_exposure:
        findings.append(Finding("网关暴露检测", "中", "无法明确判断网关绑定策略，请人工确认 gateway.mode/bind/host。"))
        return findings

    has_auth = bool(auth_mode and auth_mode not in {"none", "off", "disabled"})
    if allow_external_gateway:
        risk = "信息" if has_auth else "中"
        msg = "检测到外网监听，但已按用户策略允许。" if has_auth else "检测到外网监听且允许外网，但建议启用鉴权。"
        findings.append(Finding("网关暴露检测", risk, msg, details={"mode": mode, "bind": bind, "host": host, "auth_mode": auth_mode}))
        return findings

    if has_auth:
        findings.append(
            Finding(
                "网关暴露检测",
                "中",
                "检测到外网监听且已启用鉴权。若业务需要对外访问，可在命令中显式允许外网。",
                details={"mode": mode, "bind": bind, "host": host, "auth_mode": auth_mode},
            )
        )
    else:
        findings.append(
            Finding(
                "网关暴露检测",
                "高",
                "检测到外网监听且未发现有效鉴权，存在高风险。",
                details={"mode": mode, "bind": bind, "host": host},
            )
        )

    return findings


def _audit_permissions(runtime_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for target in [runtime_root / "openclaw.json", runtime_root / ".env", runtime_root / "credentials"]:
        if not target.exists():
            continue

        mode = stat.S_IMODE(target.stat().st_mode)
        mode_octal = f"{mode:03o}"

        if os.name == "nt":
            if mode & 0o077:
                findings.append(
                    Finding(
                        "配置权限校验",
                        "中",
                        f"{target.name} 在 Windows 回退权限位上表现为权限过宽。",
                        details={"mode": mode_octal},
                    )
                )
            continue

        if target.is_dir():
            if mode > 0o700:
                findings.append(
                    Finding(
                        "配置权限校验",
                        "中",
                        f"目录 {target.name} 权限超过 700。",
                        details={"mode": mode_octal},
                    )
                )
        else:
            if mode > 0o600:
                findings.append(
                    Finding(
                        "配置权限校验",
                        "中",
                        f"文件 {target.name} 权限超过 600。",
                        details={"mode": mode_octal},
                    )
                )
    return findings


def _audit_skills(runtime_root: Path) -> list[Finding]:
    skills_dir = runtime_root / "skills"
    findings: list[Finding] = []
    if not skills_dir.exists():
        findings.append(Finding("技能安全审计", "信息", "未找到 skills/ 目录，已跳过静态扫描。"))
        return findings

    scripts = list(skills_dir.rglob("*.py")) + list(skills_dir.rglob("*.sh"))
    if not scripts:
        findings.append(Finding("技能安全审计", "信息", "skills/ 目录下未发现 .py/.sh 脚本。"))
        return findings

    for script in scripts:
        content = script.read_text(encoding="utf-8", errors="ignore")
        rel = str(script.relative_to(runtime_root))

        for pattern, issue in SENSITIVE_PATTERNS.items():
            if re.search(pattern, content):
                risk = "中"
                if "os.system" in pattern or "eval" in pattern or "exec" in pattern:
                    risk = "高"
                findings.append(Finding("技能安全审计", risk, f"{rel}: {issue}"))

        if EXTERNAL_IP_POST_PATTERN.search(content):
            findings.append(Finding("技能安全审计", "高", f"{rel}: requests.post 指向非 localhost 目标。"))

    return findings


def _audit_workspace_isolation(runtime_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    workspace_root = _resolve_workspace_root(runtime_root)
    if workspace_root is None:
        findings.append(Finding("工作区隔离校验", "中", "未找到 workspace/ 目录，无法验证隔离策略。"))
        return findings

    nested_workspaces = list(workspace_root.glob("workspace-*"))
    if nested_workspaces:
        for p in nested_workspaces:
            resolved = p.resolve()
            if not str(resolved).startswith(str(workspace_root.resolve())):
                findings.append(
                    Finding(
                        "工作区隔离校验",
                        "高",
                        f"{p.name} 通过链接或路径穿越越出 workspace 根目录。",
                        details={"resolved": str(resolved)},
                    )
                )
        return findings

    # 单工作区场景：workspace 目录直接放置 SOUL.md / AGENT_RULES.md
    if (workspace_root / "SOUL.md").exists() or (workspace_root / "AGENT_RULES.md").exists():
        findings.append(Finding("工作区隔离校验", "信息", "检测到单工作区结构（workspace 目录直接承载规则文件）。"))
    else:
        findings.append(Finding("工作区隔离校验", "中", "未发现 workspace-* 子目录，也未发现 SOUL.md/AGENT_RULES.md。"))

    return findings


def _resolve_workspace_root(runtime_root: Path) -> Path | None:
    preferred = runtime_root / "workspace"
    legacy = runtime_root / "workspaces"
    if preferred.exists():
        return preferred
    if legacy.exists():
        return legacy
    return None
