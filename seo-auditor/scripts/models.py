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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
