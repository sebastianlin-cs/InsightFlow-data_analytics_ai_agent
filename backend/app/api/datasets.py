from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.dataset import DatasetDeleteResponse, DatasetListItem, DatasetRead
from app.services.dataset_parser import DatasetParseError, parse_dataset_metadata
from app.services.dataset_service import (
    create_dataset,
    delete_user_dataset,
    get_user_dataset_by_id,
    get_user_datasets,
)
from app.services.file_storage import delete_file_if_exists, save_upload_file

router = APIRouter()

SUPPORTED_FILE_TYPES = {".csv": "csv", ".xlsx": "xlsx", ".xls": "xls"}


def get_file_type(filename: str | None) -> str:
    suffix = Path(filename or "").suffix.lower()
    file_type = SUPPORTED_FILE_TYPES.get(suffix)
    if file_type is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Supported types: .csv, .xlsx, .xls",
        )
    return file_type


def validate_upload_size(file: UploadFile) -> None:
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)

    if size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )
    if size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Uploaded file exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit",
        )


@router.post("/upload", response_model=DatasetRead, status_code=status.HTTP_201_CREATED)
def upload_dataset(
    file: UploadFile = File(...),
    description: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DatasetRead:
    file_type = get_file_type(file.filename)
    validate_upload_size(file)

    try:
        file_path = save_upload_file(file, current_user.id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded file",
        ) from exc

    try:
        metadata = parse_dataset_metadata(file_path, file_type)
    except DatasetParseError as exc:
        delete_file_if_exists(file_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        delete_file_if_exists(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse uploaded file",
        ) from exc

    return create_dataset(
        db=db,
        user_id=current_user.id,
        original_filename=file.filename or "upload",
        file_type=file_type,
        file_path=file_path,
        description=description,
        metadata=metadata,
    )


@router.get("", response_model=list[DatasetListItem])
@router.get("/", response_model=list[DatasetListItem], include_in_schema=False)
def list_datasets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DatasetListItem]:
    return get_user_datasets(db, current_user.id)


@router.get("/{dataset_id}", response_model=DatasetRead)
def read_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DatasetRead:
    dataset = get_user_dataset_by_id(db, current_user.id, dataset_id)
    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )
    return dataset


@router.delete("/{dataset_id}", response_model=DatasetDeleteResponse)
def delete_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DatasetDeleteResponse:
    deleted = delete_user_dataset(db, current_user.id, dataset_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )
    return DatasetDeleteResponse(message="Dataset deleted successfully")
