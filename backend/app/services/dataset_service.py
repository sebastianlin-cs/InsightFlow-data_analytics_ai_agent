from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.services.file_storage import delete_file_if_exists


def create_dataset(
    db: Session,
    user_id: int,
    original_filename: str,
    stored_filename: str,
    file_type: str,
    file_size_bytes: int,
    file_hash: str,
    storage_uri: str,
    description: str | None,
) -> Dataset:
    name = Path(original_filename).stem or original_filename
    dataset = Dataset(
        user_id=user_id,
        name=name,
        description=description,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_type=file_type,
        file_size_bytes=file_size_bytes,
        file_hash=file_hash,
        storage_backend="local",
        storage_uri=storage_uri,
        file_path=storage_uri,
        status="uploaded",
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


def get_user_dataset_by_hash(db: Session, user_id: int, file_hash: str) -> Dataset | None:
    return db.scalar(
        select(Dataset).where(
            Dataset.user_id == user_id,
            Dataset.file_hash == file_hash,
        )
    )


def mark_dataset_ready(
    db: Session,
    dataset: Dataset,
    metadata: dict[str, int],
) -> Dataset:
    dataset.row_count = metadata["row_count"]
    dataset.column_count = metadata["column_count"]
    dataset.sheet_count = metadata["sheet_count"]
    dataset.status = "ready"
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


def mark_dataset_failed(db: Session, dataset: Dataset) -> Dataset:
    dataset.status = "failed"
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


def get_user_datasets(db: Session, user_id: int) -> list[Dataset]:
    return list(
        db.scalars(
            select(Dataset)
            .where(Dataset.user_id == user_id)
            .order_by(Dataset.created_at.desc())
        )
    )


def get_user_dataset_by_id(
    db: Session,
    user_id: int,
    dataset_id: int,
) -> Dataset | None:
    return db.scalar(
        select(Dataset).where(
            Dataset.id == dataset_id,
            Dataset.user_id == user_id,
        )
    )


def delete_user_dataset(db: Session, user_id: int, dataset_id: int) -> bool:
    dataset = get_user_dataset_by_id(db, user_id, dataset_id)
    if dataset is None:
        return False

    file_path = dataset.storage_uri or dataset.file_path
    db.delete(dataset)
    db.commit()
    delete_file_if_exists(file_path)
    return True
