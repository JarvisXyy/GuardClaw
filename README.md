# GuardClaw

[中文文档 (README.zh-CN.md)](./README.zh-CN.md)

GuardClaw is a security auditing and hardening toolkit for OpenClaw.

## Quick Start (One Command)

From the GuardClaw repository root:

```bash
./run_guardclaw.sh
```

The script supports auto-detection and will try runtime roots in this order:
- `<OPENCLAW_ROOT>/.openclaw` (nested layout)
- `<OPENCLAW_ROOT>/../.openclaw` (sibling layout)
- `<OPENCLAW_ROOT>`

Optional arguments:

```bash
./run_guardclaw.sh [OPENCLAW_ROOT] [SKILL_FILE] [LOCK_LEVEL]
```

`LOCK_LEVEL` can be `off`, `soft`, or `strict`.

## Installation (Manual)

### Requirements
- Python 3.10+

### Recommended (pipx, one-line)

```bash
pipx install git+https://github.com/JarvisXyy/GuardClaw.git
```

Then run:

```bash
guardclaw --help
```

### Alternative (virtual environment)

```bash
cd /path/to/GuardClaw
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -U pip
python3 -m pip install -e .
```

If you see `This environment is externally managed`, use a venv as shown above (recommended for Homebrew Python).

## Common Usage

Note: `--root` is a global option and must be placed before subcommands.

```bash
# Audit
guardclaw --root /path/to/openclaw audit

# Audit and allow external gateway scenario
guardclaw --root /path/to/openclaw audit --allow-external-gateway

# Harden (default: no forced gateway rewrite)
guardclaw --root /path/to/openclaw harden --skill-file ./docs/SKILL.md --lock-level soft

# Force gateway to local-only
guardclaw --root /path/to/openclaw harden --enforce-gateway-local --lock-level soft

# Rollback
guardclaw --root /path/to/openclaw rollback

# Unlock owner write permission for openclaw.json/.env
guardclaw --root /path/to/openclaw unlock

# One-click via CLI
guardclaw --root /path/to/openclaw all --skill-file ./docs/SKILL.md --lock-level soft
```

## Features

- Security audit
  - Gateway exposure checks (`mode/bind` and `host` schemas)
  - Permission checks for `openclaw.json`, `.env`, `credentials/`
  - Skill SAST scan for `skills/**/*.py` and `skills/**/*.sh`
  - Workspace isolation checks for both:
    - multi-workspace: `workspace/workspace-*`
    - single-workspace: `workspace/SOUL.md` or `workspace/AGENT_RULES.md`
- Automated hardening
  - Optional local-only gateway enforcement (`--enforce-gateway-local`)
  - Auto-set `messages.queue.mode=interrupt` when queue is not configured
  - Rule injection into workspace rule files
  - Permission tightening with lock levels: `off | soft | strict`
  - Atomic backup and rollback
- Behavioral tracking
  - Tool-call logging with millisecond timestamps
  - Sensitive path warnings (`/etc/`, `C:\\Windows\\`, `../`)

## Output Paths

GuardClaw resolves runtime root automatically, then writes outputs inside that runtime root.

- Audit report: `<display-root>/audit_report.json`
- Backups: `<runtime-root>/.guardclaw/backups/<snapshot-id>/`
- Tool logs: `<runtime-root>/.guardclaw/logs/tool_calls.log`
- Installed system rule: `<runtime-root>/openclaw_system_rules/guardclaw-unified-rules/SKILL.md`
