import re

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

def validate_email(email: str) -> bool:
    """Validate email format."""
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email.strip()))

def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength."""
    if not password or not isinstance(password, str):
        return False, "Password is required"
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    return True, ""

def sanitize_string(text: str, max_len: int = 1000) -> str:
    """Sanitize and trim string input."""
    if not text:
        return ""
    return str(text).strip()[:max_len]
