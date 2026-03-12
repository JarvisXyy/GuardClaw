from __future__ import annotations

import argparse
import json
from pathlib import Path

from .audit import run_audit
from .backup import rollback_latest
from .hardening import run_hardening, unlock_permissions
from .paths import resolve_runtime_root
from .reporting import render_console_table, write_report
from .tracking import log_tool_call


def _run_audit(runtime_root: Path, output: str, display_root: Path, allow_external_gateway: bool) -> None:
    report = run_audit(runtime_root, display_root=display_root, allow_external_gateway=allow_external_gateway)
    output_path = display_root / output
    write_report(report, output_path)
    print(render_console_table(report.findings))
    print(f"审计报告已保存至: {output_path}")


def _run_hardening(
    runtime_root: Path,
    skill_file: str | None,
    enforce_gateway_local: bool,
    allow_external_gateway: bool,
    lock_level: str,
) -> None:
    skill = Path(skill_file).expanduser().resolve() if skill_file else None
    result = run_hardening(
        runtime_root,
        skill,
        enforce_gateway_local=enforce_gateway_local,
        allow_external_gateway=allow_external_gateway,
        lock_level=lock_level,
    )
    print(f"已创建备份快照: {result.snapshot}")
    for msg in result.messages:
        print(f"- {msg}")
    print(f"变更文件数量: {len(result.changed_files)}")


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="guardclaw", description="GuardClaw 安全审计与加固工具")
    p.add_argument("--root", default=".", help="OpenClaw 根目录（若存在 .openclaw 将自动使用）")

    sub = p.add_subparsers(dest="command", required=True)

    audit = sub.add_parser("audit", help="执行安全审计")
    audit.add_argument("--output", default="audit_report.json", help="审计报告输出文件名")
    audit.add_argument("--allow-external-gateway", action="store_true", help="允许 gateway 对外监听并降低相关风险提示")

    harden = sub.add_parser("harden", help="执行自动化加固")
    harden.add_argument("--skill-file", help="用于系统级规则注入的 GuardClaw SKILL.md 路径")
    harden.add_argument("--enforce-gateway-local", action="store_true", help="强制将 gateway 改为本地监听")
    harden.add_argument("--allow-external-gateway", action="store_true", help="允许外网监听，不自动改 gateway")
    harden.add_argument("--lock-level", choices=["off", "soft", "strict"], default="soft", help="配置锁级别")

    rollback = sub.add_parser("rollback", help="回滚到最新或指定快照")
    rollback.add_argument("--snapshot", help="指定快照 ID")

    unlock = sub.add_parser("unlock", help="恢复 openclaw.json/.env 的 owner 写权限")

    track = sub.add_parser("track", help="记录工具调用审计日志")
    track.add_argument("--bot-id", required=True)
    track.add_argument("--tool-name", required=True)
    track.add_argument("--status", required=True, choices=["success", "failed"])
    track.add_argument("--input-args", default="{}", help="JSON 格式参数")

    all_cmd = sub.add_parser("all", help="一键执行 audit + harden + track")
    all_cmd.add_argument("--output", default="audit_report.json", help="审计报告输出文件名")
    all_cmd.add_argument("--skill-file", help="用于系统级规则注入的 GuardClaw SKILL.md 路径")
    all_cmd.add_argument("--bot-id", default="guardclaw-system")
    all_cmd.add_argument("--tool-name", default="guardclaw.all")
    all_cmd.add_argument("--allow-external-gateway", action="store_true", help="允许 gateway 对外监听")
    all_cmd.add_argument("--enforce-gateway-local", action="store_true", help="强制将 gateway 改为本地监听")
    all_cmd.add_argument("--lock-level", choices=["off", "soft", "strict"], default="soft", help="配置锁级别")

    return p


def main() -> int:
    args = _parser().parse_args()
    input_root = Path(args.root).expanduser().resolve()
    runtime_root = resolve_runtime_root(input_root)

    if args.command == "audit":
        _run_audit(runtime_root, args.output, input_root, args.allow_external_gateway)
        return 0

    if args.command == "harden":
        _run_hardening(
            runtime_root,
            args.skill_file,
            enforce_gateway_local=args.enforce_gateway_local,
            allow_external_gateway=args.allow_external_gateway,
            lock_level=args.lock_level,
        )
        return 0

    if args.command == "rollback":
        snap = rollback_latest(runtime_root, args.snapshot)
        print(f"回滚完成，使用快照: {snap.name}")
        return 0

    if args.command == "unlock":
        changed = unlock_permissions(runtime_root)
        print(f"已恢复可写权限文件数量: {len(changed)}")
        for path in changed:
            print(f"- {path}")
        return 0

    if args.command == "track":
        try:
            input_args = json.loads(args.input_args)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"--input-args 不是合法 JSON: {exc}") from exc

        log_path = log_tool_call(runtime_root, args.bot_id, args.tool_name, input_args, args.status)
        print(f"日志已写入: {log_path}")
        return 0

    if args.command == "all":
        _run_audit(runtime_root, args.output, input_root, args.allow_external_gateway)
        _run_hardening(
            runtime_root,
            args.skill_file,
            enforce_gateway_local=args.enforce_gateway_local,
            allow_external_gateway=args.allow_external_gateway,
            lock_level=args.lock_level,
        )
        log_path = log_tool_call(
            runtime_root,
            args.bot_id,
            args.tool_name,
            {
                "command": "all",
                "output": args.output,
                "skill_file": bool(args.skill_file),
                "runtime_root": str(runtime_root),
                "allow_external_gateway": args.allow_external_gateway,
                "enforce_gateway_local": args.enforce_gateway_local,
                "lock_level": args.lock_level,
            },
            "success",
        )
        print(f"日志已写入: {log_path}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
