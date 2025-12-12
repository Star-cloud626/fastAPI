from __future__ import annotations

import io
import re
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="Xovate Data Validation API",
    description="Validates uploaded CSV data for completeness and correctness.",
    version="1.0.0",
)

allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://frontend:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _normalize_id(value: Any) -> Optional[Any]:
    """Return the original id value unless it is missing/NaN."""
    if pd.isna(value):
        return None
    return value


def _build_error(row_index: Optional[int], id_value: Optional[Any], column: str, message: str) -> Dict[str, Any]:
    return {
        "row_index": row_index,
        "id": _normalize_id(id_value),
        "column": column,
        "error_message": message,
    }


def _validate_columns(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    required_columns = {"id", "email", "age"}
    missing = sorted(required_columns - set(df.columns))
    if missing:
        return _build_error(
            None,
            None,
            "columns",
            f"Missing required columns: {', '.join(missing)}",
        )
    return None


def _volume_check(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    row_count = len(df.index)
    if row_count <= 10:
        return _build_error(
            None,
            None,
            "global",
            f"File must contain more than 10 data rows. Found {row_count}.",
        )
    return None


def _validate_email(row_index: int, row: pd.Series, errors: List[Dict[str, Any]]) -> None:
    email = row.get("email")
    if pd.isna(email) or str(email).strip() == "":
        errors.append(
            _build_error(
                row_index=row_index,
                id_value=row.get("id"),
                column="email",
                message="Email is required.",
            )
        )


def _validate_age(row_index: int, row: pd.Series, errors: List[Dict[str, Any]]) -> None:
    raw_age = row.get("age")
    age_value = "" if pd.isna(raw_age) else str(raw_age).strip()

    if age_value == "":
        errors.append(
            _build_error(
                row_index=row_index,
                id_value=row.get("id"),
                column="age",
                message="Age is missing or has an invalid format.",
            )
        )
        return

    if not re.fullmatch(r"-?\d+", age_value):
        errors.append(
            _build_error(
                row_index=row_index,
                id_value=row.get("id"),
                column="age",
                message=f"Invalid age format: '{raw_age}'.",
            )
        )
        return

    age_int = int(age_value)
    if age_int < 18 or age_int > 100:
        errors.append(
            _build_error(
                row_index=row_index,
                id_value=row.get("id"),
                column="age",
                message=f"Age {age_int} is out of allowed range (18-100).",
            )
        )


@app.post("/validate")
async def validate(file: UploadFile = File(...)) -> Dict[str, Any]:
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a CSV.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        df = pd.read_csv(io.BytesIO(content), dtype=str)
    except Exception as exc:  # pragma: no cover - defensive path
        raise HTTPException(status_code=400, detail=f"Unable to read CSV: {exc}") from exc

    column_error = _validate_columns(df)     #validate the columns(id, email, age)
    if column_error:
        return {"status": "fail", "errors": [column_error]}

    volume_error = _volume_check(df)
    if volume_error:
        return {"status": "fail", "errors": [volume_error]}

    errors: List[Dict[str, Any]] = []
    for idx, row in df.iterrows():
        row_index = idx + 1  # data rows start at 1
        _validate_email(row_index, row, errors)
        _validate_age(row_index, row, errors)

    status = "pass" if not errors else "fail"
    return {"status": status, "errors": errors}

