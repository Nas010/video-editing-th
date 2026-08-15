"""Safe persistence helpers for canonical Pydantic artifacts."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)


def write_model_atomic(path: Path, model: BaseModel) -> None:
    """Write a model as pretty JSON without exposing partially-written files."""

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = model.model_dump_json(indent=2) + "\n"
    file_descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        text=True,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def read_model(path: Path, model_type: type[ModelT]) -> ModelT:
    """Read and validate a canonical model from JSON."""

    return model_type.model_validate_json(path.read_text(encoding="utf-8"))
