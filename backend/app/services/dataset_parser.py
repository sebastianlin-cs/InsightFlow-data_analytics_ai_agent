from pathlib import Path

import pandas as pd


class DatasetParseError(ValueError):
    pass


def parse_dataset_metadata(file_path: str, file_type: str) -> dict[str, int]:
    path = Path(file_path)
    if not path.exists() or path.stat().st_size == 0:
        raise DatasetParseError("Uploaded file is empty")

    try:
        if file_type == "csv":
            dataframe = pd.read_csv(path)
            sheet_count = 1
        elif file_type in {"xlsx", "xls"}:
            excel_file = pd.ExcelFile(path)
            if not excel_file.sheet_names:
                raise DatasetParseError("Excel file does not contain any sheets")
            dataframe = pd.read_excel(excel_file, sheet_name=excel_file.sheet_names[0])
            sheet_count = len(excel_file.sheet_names)
        else:
            raise DatasetParseError("Unsupported file type")
    except DatasetParseError:
        raise
    except pd.errors.EmptyDataError as exc:
        raise DatasetParseError("Uploaded file is empty") from exc
    except Exception as exc:
        raise DatasetParseError("Failed to parse uploaded file") from exc

    return {
        "row_count": int(len(dataframe.index)),
        "column_count": int(len(dataframe.columns)),
        "sheet_count": int(sheet_count),
    }
