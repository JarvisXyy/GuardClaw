from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SENSITIVE_PATH_MARKERS = ["/etc/", "C:\\Windows\\", "../"]


def log_tool_call(
    root: Path,
    bot_id: str,
    tool_name: str,
    input_args: dict[str, Any],
    status: str,
) -> Path:
    logs_dir = root / ".guardclaw" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "tool_calls.log"

    mark = ""
    args_text = json.dumps(input_args, ensure_ascii=False)
    if any(marker in args_text for marker in SENSITIVE_PATH_MARKERS):
        mark = "[SENSITIVE_PATH_WARNING]"

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "bot_id": bot_id,
        "tool_name": tool_name,
        "input_args": input_args,
        "status": status,
        "mark": mark,
    }

    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return log_file
