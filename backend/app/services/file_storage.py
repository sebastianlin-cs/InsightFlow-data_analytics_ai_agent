import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings

STORAGE_ROOT = Path(settings.UPLOAD_DIR)


def sanitize_filename(filename: str) -> str:
    safe_name = Path(filename or "upload").name
    safe_name = "".join(
        char if char.isalnum() or char in {".", "-", "_"} else "_"
        for char in safe_name
    ).strip("._")
    return safe_name or "upload"


def save_upload_file(file: UploadFile, user_id: int) -> str:
    safe_filename = sanitize_filename(file.filename or "upload")
    suffix = Path(safe_filename).suffix.lower()
    stem = Path(safe_filename).stem or "upload"
    stored_filename = f"{uuid.uuid4().hex}_{stem}{suffix}"

    user_dir = STORAGE_ROOT / f"user_{user_id}"
    user_dir.mkdir(parents=True, exist_ok=True)

    destination = user_dir / stored_filename
    with destination.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return str(destination)


def delete_file_if_exists(file_path: str) -> None:
    path = Path(file_path)
    if path.exists() and path.is_file():
        path.unlink()
