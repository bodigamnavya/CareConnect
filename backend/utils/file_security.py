import os
import uuid
from pathlib import Path
from werkzeug.utils import secure_filename
from config import Config

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
ALLOWED_REPORT_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "pdf", "txt"}

def allowed_file(filename: str, file_type: str = "image") -> bool:
    """Check if file extension is allowed."""
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    if file_type == "image":
        return ext in ALLOWED_IMAGE_EXTENSIONS
    elif file_type == "report":
        return ext in ALLOWED_REPORT_EXTENSIONS
    return ext in Config.ALLOWED_EXTENSIONS

def save_uploaded_file(file, subfolder: str = "") -> tuple[str, str]:
    """
    Saves uploaded file securely with UUID name.
    Returns (absolute_file_path, relative_file_url)
    """
    original_filename = secure_filename(file.filename or "upload.jpg")
    ext = original_filename.rsplit(".", 1)[1].lower() if "." in original_filename else "jpg"
    
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    target_dir = Config.UPLOAD_FOLDER
    if subfolder:
        target_dir = target_dir / subfolder
    os.makedirs(target_dir, exist_ok=True)
    
    file_path = target_dir / unique_name
    file.save(str(file_path))
    
    # Generate relative URL for static access
    rel_url = f"/uploads/{subfolder + '/' if subfolder else ''}{unique_name}"
    return str(file_path), rel_url
