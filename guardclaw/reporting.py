from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import AuditReport, Finding

_RISK_COLOR = {
    "高": "\033[91m",
    "中": "\033[93m",
    "低": "\033[96m",
    "信息": "\033[92m",
}
_RESET = "\033[0m"


def write_report(report: AuditReport, output_path: Path) -> None:
    payload = {
        "generated_at": report.generated_at,
        "root": report.root,
        "findings": [asdict(f) for f in report.findings],
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def render_console_table(findings: list[Finding]) -> str:
    headers = ["风险", "检查项", "说明"]
    rows = [[f.risk, f.check, f.message] for f in findings]
    widths = [len(h) for h in headers]
    for row in rows:
        for i, col in enumerate(row):
            widths[i] = max(widths[i], len(col))

    line = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    header_row = "| " + " | ".join(headers[i].ljust(widths[i]) for i in range(3)) + " |"

    output = [line, header_row, line]
    for row in rows:
        risk = row[0]
        color = _RISK_COLOR.get(risk, "")
        risk_text = f"{color}{risk}{_RESET}" if color else risk
        output.append(
            "| "
            + " | ".join(
                [
                    risk_text.ljust(widths[0] + (len(color) + len(_RESET) if color else 0)),
                    row[1].ljust(widths[1]),
                    row[2].ljust(widths[2]),
                ]
            )
            + " |"
        )
    output.append(line)
    return "\n".join(output)
