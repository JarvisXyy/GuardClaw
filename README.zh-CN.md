# GuardClaw

GuardClaw 是面向 OpenClaw 的原生安全审计与自动化加固工具，提供环境审计、规则注入、行为追踪与回滚能力。

## 核心能力

- 安全审计引擎
  - 网关暴露检测（兼容 `gateway.mode/bind` 与 `gateway.host` 两种 schema）
  - 配置权限审计（`openclaw.json`、`.env`、`credentials/`）
  - 技能静态扫描（`skills/**/*.py`、`skills/**/*.sh`）
  - 工作区隔离校验（兼容多工作区 `workspace/workspace-*` 与单工作区 `workspace/SOUL.md`）
  - 彩色控制台表格 + `audit_report.json`
- 自动化加固
  - 可选强制本地网关（仅在显式参数下执行）
  - 权限收紧与三档锁策略（`off/soft/strict`）
  - 注入 GuardClaw 系统规则到 `AGENT_RULES.md` 或 `SOUL.md`
  - 原子备份与回滚
- 行为追踪
  - 记录每次工具调用（毫秒级时间戳、bot、工具名、参数、状态）
  - 敏感路径告警标记（`/etc/`、`C:\\Windows\\`、`../`）

## 安装

```bash
pip install -e .
```

如果遇到 `externally managed`（Homebrew Python 常见），请使用虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -U pip
python3 -m pip install -e .
```

## 命令用法

注意：全局参数 `--root` 需要写在子命令前面。

```bash
# 1) 审计
# 若你的 OpenClaw 根目录下存在 .openclaw，会自动使用它作为运行目录
guardclaw --root /path/to/openclaw audit

# 允许外网网关场景（降低相关风险提示）
guardclaw --root /path/to/openclaw audit --allow-external-gateway

# 2) 加固（默认不强改外网网关）
guardclaw --root /path/to/openclaw harden --skill-file /path/to/SKILL.md --lock-level soft

# 强制把网关改为本地监听（仅显式开启时）
guardclaw --root /path/to/openclaw harden --enforce-gateway-local --lock-level soft

# 3) 回滚
guardclaw --root /path/to/openclaw rollback

# 4) 解锁（恢复 openclaw.json / .env 写权限）
guardclaw --root /path/to/openclaw unlock

# 5) 工具调用追踪
guardclaw --root /path/to/openclaw track \
  --bot-id bot-1 \
  --tool-name fs.read \
  --status success \
  --input-args '{"path":"/etc/passwd"}'

# 6) 一键执行（audit + harden + track）
guardclaw --root /path/to/openclaw all \
  --skill-file /path/to/SKILL.md \
  --lock-level soft
```

## 输出目录

- 审计报告：`/path/to/openclaw/audit_report.json`
- 备份快照：`/path/to/openclaw/.openclaw/.guardclaw/backups/<snapshot-id>/`（若运行目录是 `.openclaw`）
- 行为日志：`/path/to/openclaw/.openclaw/.guardclaw/logs/tool_calls.log`
- 系统规则安装位置：`/path/to/openclaw/.openclaw/openclaw_system_rules/guardclaw-unified-rules/SKILL.md`

## 网关策略说明

- `mode=local` 且 `bind=loopback` 视为本地安全，不要求写 `host=127.0.0.1`。
- 对外监听不一定是风险，GuardClaw 默认“提示但不强改”。
- 仅在你显式传入 `--enforce-gateway-local` 时，才会自动改写网关到本地模式。

## 权限锁策略

- `off`：不额外加锁
- `soft`：保留 owner 写权限（推荐，便于维护）
- `strict`：移除 owner 写权限（更严格，需要 `unlock` 才便于后续手动修改）
