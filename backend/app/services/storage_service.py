import hashlib
import uuid
from pathlib import Path

from app.core.config import settings
from app.services.file_storage import sanitize_filename

LOCAL_STORAGE_BACKEND = "local"
DATASET_STORAGE_ROOT = Path(settings.UPLOAD_DIR) / "datasets"


def compute_file_hash(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


def save_uploaded_file_locally(
    file_bytes: bytes,
    user_id: int,
    original_filename: str,
) -> tuple[str, str]:
    safe_filename = sanitize_filename(original_filename)
    suffix = Path(safe_filename).suffix.lower()
    stem = Path(safe_filename).stem or "dataset"
    stored_filename = f"{uuid.uuid4().hex}_{stem}{suffix}"

    user_dir = DATASET_STORAGE_ROOT / f"user_{user_id}"
    user_dir.mkdir(parents=True, exist_ok=True)

    destination = user_dir / stored_filename
    destination.write_bytes(file_bytes)
    return stored_filename, str(destination)


def get_local_path_from_storage_uri(storage_uri: str) -> Path:
    return Path(storage_uri)
