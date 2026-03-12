# GuardClaw

[English README](./README.md)

GuardClaw 是面向 OpenClaw 的安全审计与自动化加固工具。

## 快速开始（一键运行）

在 GuardClaw 仓库根目录执行：

```bash
./run_guardclaw.sh
```

脚本会自动探测运行根目录，优先级如下：
- `<OPENCLAW_ROOT>/.openclaw`（嵌套结构）
- `<OPENCLAW_ROOT>/../.openclaw`（同级结构）
- `<OPENCLAW_ROOT>`

可选参数：

```bash
./run_guardclaw.sh [OPENCLAW_ROOT] [SKILL_FILE] [LOCK_LEVEL]
```

`LOCK_LEVEL` 可选 `off`、`soft`、`strict`。

## 安装（手动方式）

### 环境要求
- Python 3.10+

### 推荐方式（pipx，一条命令）

```bash
pipx install git+https://github.com/JarvisXyy/GuardClaw.git
```

安装后可直接执行：

```bash
guardclaw --help
```

### 备选方式（虚拟环境）

```bash
cd /path/to/GuardClaw
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -U pip
python3 -m pip install -e .
```

如果你遇到 `This environment is externally managed`，请使用上述虚拟环境方式（Homebrew Python 常见）。

## 常用命令

注意：`--root` 是全局参数，必须放在子命令之前。

```bash
# 审计
guardclaw --root /path/to/openclaw audit

# 审计（允许外网网关场景）
guardclaw --root /path/to/openclaw audit --allow-external-gateway

# 加固（默认不强制改写网关）
guardclaw --root /path/to/openclaw harden --skill-file ./docs/SKILL.md --lock-level soft

# 强制网关本地化
guardclaw --root /path/to/openclaw harden --enforce-gateway-local --lock-level soft

# 回滚
guardclaw --root /path/to/openclaw rollback

# 解锁 openclaw.json/.env 的 owner 写权限
guardclaw --root /path/to/openclaw unlock

# CLI 一键执行
guardclaw --root /path/to/openclaw all --skill-file ./docs/SKILL.md --lock-level soft
```

## 主要能力

- 安全审计
  - 网关暴露检测（兼容 `mode/bind` 与 `host` 两种 schema）
  - 配置权限审计（`openclaw.json`、`.env`、`credentials/`）
  - 技能静态扫描（`skills/**/*.py`、`skills/**/*.sh`）
  - 工作区隔离校验，兼容：
    - 多工作区：`workspace/workspace-*`
    - 单工作区：`workspace/SOUL.md` 或 `workspace/AGENT_RULES.md`
- 自动化加固
  - 可选强制本地网关（`--enforce-gateway-local`）
  - 规则注入到工作区规则文件
  - 三档权限锁策略：`off | soft | strict`
  - 原子备份与回滚
- 行为追踪
  - 工具调用日志（毫秒级时间戳）
  - 敏感路径告警（`/etc/`、`C:\\Windows\\`、`../`）

## 输出路径

GuardClaw 会先自动解析运行根目录，然后将输出写入该运行根目录。

- 审计报告：`<display-root>/audit_report.json`
- 备份快照：`<runtime-root>/.guardclaw/backups/<snapshot-id>/`
- 行为日志：`<runtime-root>/.guardclaw/logs/tool_calls.log`
- 系统规则安装路径：`<runtime-root>/openclaw_system_rules/guardclaw-unified-rules/SKILL.md`
