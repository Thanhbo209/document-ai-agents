from datetime import datetime
from pathlib import Path
from typing import Any

from app.ingestion.errors import ExtractionError
from app.ingestion.types import ExtractedTextBlock, InputType, NormalizedDocument

DEFAULT_ROW_WINDOW = 25


def extract_csv_file(path: Path, title: str) -> NormalizedDocument:
    blocks = extract_csv_blocks(path)

    if not blocks:
        raise ExtractionError("CSV does not contain extractable table rows.")

    return NormalizedDocument(
        title=title,
        source_type=InputType.CSV,
        blocks=blocks,
    )


def extract_xlsx_file(path: Path, title: str) -> NormalizedDocument:
    blocks = extract_xlsx_blocks(path)

    if not blocks:
        raise ExtractionError("XLSX does not contain extractable table rows.")

    return NormalizedDocument(
        title=title,
        source_type=InputType.XLSX,
        blocks=blocks,
    )


def extract_csv_blocks(file_path: Path) -> list[ExtractedTextBlock]:
    pd = _pandas()

    try:
        dataframe = pd.read_csv(file_path, dtype=object, keep_default_na=False)
    except Exception as exc:
        raise ExtractionError(f"Could not read CSV file: {exc}") from exc

    return _dataframe_blocks(
        dataframe=dataframe,
        filename=file_path.name,
        source_type=InputType.CSV,
        sheet_name=None,
    )


def extract_xlsx_blocks(file_path: Path) -> list[ExtractedTextBlock]:
    pd = _pandas()

    try:
        sheets = pd.read_excel(
            file_path,
            sheet_name=None,
            dtype=object,
            keep_default_na=False,
            engine="openpyxl",
        )
    except Exception as exc:
        raise ExtractionError(f"Could not read XLSX file: {exc}") from exc

    blocks: list[ExtractedTextBlock] = []

    for sheet_name, dataframe in sheets.items():
        blocks.extend(
            _dataframe_blocks(
                dataframe=dataframe,
                filename=file_path.name,
                source_type=InputType.XLSX,
                sheet_name=str(sheet_name),
            )
        )

    return blocks


def _dataframe_blocks(
    dataframe,
    filename: str,
    source_type: InputType,
    sheet_name: str | None,
    row_window: int = DEFAULT_ROW_WINDOW,
) -> list[ExtractedTextBlock]:
    dataframe = dataframe.copy()
    dataframe.columns = _normalize_column_names(dataframe.columns)
    dataframe = dataframe.fillna("")

    if dataframe.empty:
        return []

    profile = _profile_dataframe(dataframe)
    blocks: list[ExtractedTextBlock] = []

    for start_index in range(0, len(dataframe), row_window):
        window = dataframe.iloc[start_index : start_index + row_window]

        if _window_is_empty(window):
            continue

        row_start = start_index + 2
        row_end = start_index + len(window) + 1
        text = _table_window_text(
            dataframe=window,
            source_type=source_type,
            sheet_name=sheet_name,
            row_start=row_start,
            row_end=row_end,
        )

        blocks.append(
            ExtractedTextBlock(
                text=text,
                source_page=None,
                source_start_offset=0,
                source_end_offset=len(text),
                metadata={
                    "filename": filename,
                    "source_type": source_type.value,
                    "sheet_name": sheet_name,
                    "row_start": row_start,
                    "row_end": row_end,
                    "column_names": list(dataframe.columns),
                    "row_count": int(len(dataframe)),
                    "column_count": int(len(dataframe.columns)),
                    "empty_cell_count": profile["empty_cell_count"],
                    "profile": profile["profile"],
                },
            )
        )

    return blocks


def _table_window_text(
    dataframe,
    source_type: InputType,
    sheet_name: str | None,
    row_start: int,
    row_end: int,
) -> str:
    lines: list[str] = []

    if source_type == InputType.XLSX:
        lines.append(f"Sheet: {sheet_name}")
    else:
        lines.append("CSV Table")

    lines.extend(
        [
            f"Rows: {row_start}-{row_end}",
            f"Columns: {' | '.join(dataframe.columns)}",
            "",
        ]
    )

    for offset, (_, row) in enumerate(dataframe.iterrows()):
        human_row_number = row_start + offset
        values = [f"{column}={_cell_to_text(row[column])}" for column in dataframe.columns]
        lines.append(f"Row {human_row_number}: {' | '.join(values)}")

    return "\n".join(lines)


def _normalize_column_names(columns) -> list[str]:
    names: list[str] = []

    for index, value in enumerate(columns, start=1):
        name = _cell_to_text(value)

        if not name or name.lower().startswith("unnamed:"):
            name = f"Column {index}"

        names.append(name)

    return names


def _profile_dataframe(dataframe) -> dict[str, Any]:
    empty_cell_count = 0
    numeric_columns: list[str] = []
    date_like_columns: list[str] = []
    text_columns: list[str] = []

    for column in dataframe.columns:
        values = [_cell_to_text(value) for value in dataframe[column].tolist()]
        non_empty_values = [value for value in values if value]
        empty_cell_count += len(values) - len(non_empty_values)

        if non_empty_values and _all_numeric(non_empty_values):
            numeric_columns.append(column)
        elif non_empty_values and _all_date_like(non_empty_values):
            date_like_columns.append(column)
        else:
            text_columns.append(column)

    return {
        "row_count": int(len(dataframe)),
        "column_count": int(len(dataframe.columns)),
        "columns": list(dataframe.columns),
        "empty_cell_count": int(empty_cell_count),
        "profile": {
            "numeric_columns": numeric_columns,
            "date_like_columns": date_like_columns,
            "text_columns": text_columns,
        },
    }


def _all_numeric(values: list[str]) -> bool:
    for value in values:
        try:
            float(value.replace(",", ""))
        except ValueError:
            return False

    return True


def _all_date_like(values: list[str]) -> bool:
    return all(_is_date_like(value) for value in values)


def _is_date_like(value: str) -> bool:
    if not any(separator in value for separator in ("-", "/", ".")):
        return False

    normalized = value.replace("/", "-").replace(".", "-")

    try:
        datetime.fromisoformat(normalized)
    except ValueError:
        return False

    return True


def _window_is_empty(dataframe) -> bool:
    for _, row in dataframe.iterrows():
        if any(_cell_to_text(value) for value in row.tolist()):
            return False

    return True


def _cell_to_text(value: object) -> str:
    if value is None:
        return ""

    return " ".join(str(value).split()).strip()


def _pandas():
    try:
        import pandas as pd
    except ImportError as exc:
        raise ExtractionError("Table ingestion requires pandas and openpyxl.") from exc

    return pd
