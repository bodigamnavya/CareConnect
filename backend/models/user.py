from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    id: str
    name: str
    email: str
    password_hash: str
    phone: Optional[str] = None
    blood_group: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self, include_sensitive: bool = False):
        data = {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone or "",
            "blood_group": self.blood_group or "",
            "emergency_contact": self.emergency_contact or "",
            "emergency_phone": self.emergency_phone or "",
            "created_at": str(self.created_at) if self.created_at else None
        }
        if include_sensitive:
            data["password_hash"] = self.password_hash
        return data
