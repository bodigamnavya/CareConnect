from dataclasses import dataclass
from typing import Optional

@dataclass
class Scan:
    id: str
    user_id: str
    scan_type: str
    image_path: str
    image_url: str
    result: str
    confidence: float
    explanation: str
    possible_meaning: str
    recommendation: str
    warning_signs: str
    disclaimer: str
    status: str = "COMPLETED"
    created_at: Optional[str] = None

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "scan_type": self.scan_type,
            "image_url": self.image_url,
            "result": self.result,
            "confidence": round(self.confidence, 1),
            "explanation": self.explanation,
            "possible_meaning": self.possible_meaning,
            "recommendation": self.recommendation,
            "warning_signs": self.warning_signs,
            "disclaimer": self.disclaimer,
            "status": self.status,
            "created_at": str(self.created_at) if self.created_at else None
        }
