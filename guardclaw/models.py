from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Finding:
    check: str
    risk: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditReport:
    generated_at: str
    root: str
    findings: list[Finding]

    @classmethod
    def new(cls, root: str, findings: list[Finding]) -> "AuditReport":
        now = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        return cls(generated_at=now, root=root, findings=findings)
