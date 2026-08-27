from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class Report:
    id: str
    user_id: str
    scan_id: Optional[str]
    report_type: str
    title: str
    file_path: Optional[str]
    content_json: Optional[Any]
    summary_text: Optional[str]
    created_at: Optional[str] = None

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "scan_id": self.scan_id,
            "report_type": self.report_type,
            "title": self.title,
            "file_path": self.file_path,
            "content_json": self.content_json,
            "summary_text": self.summary_text,
            "created_at": str(self.created_at) if self.created_at else None
        }
