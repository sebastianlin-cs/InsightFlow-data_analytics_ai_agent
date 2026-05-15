from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.dataset import (
    DatasetDeleteResponse,
    DatasetDetail,
    DatasetListItem,
    DatasetRead,
    DatasetSchemaRead,
)
from app.services.data_catalog_service import (
    generate_dataset_catalog,
    get_dataset_schema_rows,
)
from app.services.dataset_parser import DatasetParseError
from app.services.dataset_preview_service import load_head_preview
from app.services.dataset_service import (
    create_dataset,
    delete_user_dataset,
    get_user_dataset_by_hash,
    get_user_dataset_by_id,
    get_user_datasets,
    mark_dataset_failed,
    mark_dataset_ready,
)
from app.services.storage_service import compute_file_hash, save_uploaded_file_locally

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


def validate_upload_size(file_bytes: bytes) -> None:
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    size = len(file_bytes)

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
    file_bytes = file.file.read()
    validate_upload_size(file_bytes)
    file_hash = compute_file_hash(file_bytes)

    existing_dataset = get_user_dataset_by_hash(db, current_user.id, file_hash)
    if existing_dataset is not None:
        return existing_dataset

    dataset = None
    storage_uri = ""
    try:
        stored_filename, storage_uri = save_uploaded_file_locally(
            file_bytes=file_bytes,
            user_id=current_user.id,
            original_filename=file.filename or "upload",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded file",
        ) from exc

    dataset = create_dataset(
        db=db,
        user_id=current_user.id,
        original_filename=file.filename or "upload",
        stored_filename=stored_filename,
        file_type=file_type,
        file_size_bytes=len(file_bytes),
        file_hash=file_hash,
        storage_uri=storage_uri,
        description=description,
    )

    try:
        metadata = generate_dataset_catalog(db, dataset.id, storage_uri, file_type)
        return mark_dataset_ready(db, dataset, metadata)
    except DatasetParseError as exc:
        mark_dataset_failed(db, dataset)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        mark_dataset_failed(db, dataset)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate dataset catalog",
        ) from exc

@router.get("", response_model=list[DatasetListItem])
@router.get("/", response_model=list[DatasetListItem], include_in_schema=False)
def list_datasets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DatasetListItem]:
    return get_user_datasets(db, current_user.id)


@router.get("/{dataset_id}", response_model=DatasetDetail)
def read_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DatasetDetail:
    dataset = get_user_dataset_by_id(db, current_user.id, dataset_id)
    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )

    schema_rows = _get_or_generate_schema_rows(db, dataset)
    preview = _get_head_preview(dataset.storage_uri or dataset.file_path, dataset.file_type)

    dataset_data = DatasetRead.model_validate(dataset).model_dump()
    return DatasetDetail(
        **dataset_data,
        schema=schema_rows,
        **preview,
    )


@router.get("/{dataset_id}/schema", response_model=list[DatasetSchemaRead])
def read_dataset_schema(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DatasetSchemaRead]:
    dataset = get_user_dataset_by_id(db, current_user.id, dataset_id)
    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )

    return _get_or_generate_schema_rows(db, dataset)


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


def _get_or_generate_schema_rows(db: Session, dataset) -> list[DatasetSchemaRead]:
    schema_rows = get_dataset_schema_rows(db, dataset.id)
    if schema_rows:
        return schema_rows

    try:
        metadata = generate_dataset_catalog(
            db,
            dataset.id,
            dataset.storage_uri or dataset.file_path,
            dataset.file_type,
        )
        mark_dataset_ready(db, dataset, metadata)
    except DatasetParseError as exc:
        mark_dataset_failed(db, dataset)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        mark_dataset_failed(db, dataset)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate dataset catalog",
        ) from exc

    return get_dataset_schema_rows(db, dataset.id)


def _get_head_preview(file_path: str, file_type: str) -> dict[str, object]:
    try:
        return load_head_preview(file_path, file_type, limit=5)
    except DatasetParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
