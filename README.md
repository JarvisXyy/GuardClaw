# GuardClaw

GuardClaw is a native security hardening and behavior audit toolkit for OpenClaw.

## Features

- Security audit engine
  - Gateway exposure checks from `openclaw.json`
  - Permission audit for `openclaw.json`, `.env`, `credentials/`
  - Skill SAST scan for `skills/**/*.py` and `skills/**/*.sh`
  - Workspace isolation validation for `workspaces/workspace-*`
  - Colored console table + `audit_report.json`
- Automated hardening
  - Force `gateway.host = 127.0.0.1`
  - Lock permissions on sensitive files
  - Inject GuardClaw system rules into workspace `AGENT_RULES.md` or `SOUL.md`
  - Readonly lock for validated config files
  - Atomic backup and rollback
- Behavioral tracking
  - Tool call audit log with timestamp (milliseconds), bot id, tool name, args, status
  - Sensitive path warnings (`/etc/`, `C:\\Windows\\`, `../`)

## Install

```bash
pip install -e .
```

## Usage

```bash
guardclaw audit --root /path/to/openclaw-root

guardclaw harden --root /path/to/openclaw-root --skill-file /path/to/SKILL.md

guardclaw harden --root /path/to/openclaw-root --lock-level soft --allow-external-gateway

guardclaw rollback --root /path/to/openclaw-root

guardclaw unlock --root /path/to/openclaw-root

guardclaw track --root /path/to/openclaw-root --bot-id bot-1 --tool-name fs.read --status success --input-args '{"path":"/etc/passwd"}'

guardclaw all --root /path/to/openclaw-root --skill-file /path/to/SKILL.md --lock-level soft
```

## Outputs

- Audit report: `/path/to/openclaw-root/audit_report.json`
- Backups: `/path/to/openclaw-root/.guardclaw/backups/<snapshot-id>/`
- Tool logs: `/path/to/openclaw-root/.guardclaw/logs/tool_calls.log`
- Installed system rule: `/path/to/openclaw-root/openclaw_system_rules/guardclaw-unified-rules/SKILL.md`
