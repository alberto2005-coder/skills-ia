from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

@dataclass
class Finding:
    id: str
    category: str
    severity: str
    title: str
    evidence: str
    recommendation: str
    url: str = ""
    confidence: str = "medium"
    effort: str = "medium"
    impact: str = "medium"
    # Campos de la Fase 4: id estable + severidad must/should/nice + cita.
    citation: str = ""
    dimension: str = "tecnico"
    severity_level: str = "should"
    status: str = "fail"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
