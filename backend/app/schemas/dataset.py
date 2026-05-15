from datetime import datetime

from pydantic import BaseModel


class DatasetRead(BaseModel):
    id: int
    name: str
    description: str | None
    original_filename: str
    file_type: str
    status: str
    row_count: int | None
    column_count: int | None
    sheet_count: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DatasetListItem(DatasetRead):
    pass


class DatasetDeleteResponse(BaseModel):
    message: str
