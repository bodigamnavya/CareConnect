from dataclasses import dataclass
from typing import Optional, List

@dataclass
class ConversationMessage:
    id: str
    conversation_id: str
    sender: str # 'user' or 'assistant'
    message: str
    triage_level: Optional[str] = None
    created_at: Optional[str] = None

    def to_dict(self):
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "sender": self.sender,
            "message": self.message,
            "triage_level": self.triage_level,
            "created_at": str(self.created_at) if self.created_at else None
        }

@dataclass
class Conversation:
    id: str
    user_id: str
    title: str = "Health Inquiry"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    messages: Optional[List[ConversationMessage]] = None

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "created_at": str(self.created_at) if self.created_at else None,
            "messages": [m.to_dict() for m in (self.messages or [])]
        }
