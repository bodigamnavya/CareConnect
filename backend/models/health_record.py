from dataclasses import dataclass
from typing import Optional

@dataclass
class HealthRecord:
    id: str
    user_id: str
    category: str # Allergy, Condition, Medication, History, Note
    title: str
    details: Optional[str]
    severity: Optional[str] # Mild, Moderate, Severe
    start_date: Optional[str]
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "category": self.category,
            "title": self.title,
            "details": self.details or "",
            "severity": self.severity or "Moderate",
            "start_date": self.start_date or "",
            "is_active": bool(self.is_active),
            "created_at": str(self.created_at) if self.created_at else None,
            "updated_at": str(self.updated_at) if self.updated_at else None
        }
