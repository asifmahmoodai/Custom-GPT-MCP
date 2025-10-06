"""Shared utilities for MCP metric tools."""
from __future__ import annotations

import base64
import csv
import io
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jsonschema import Draft202012Validator, validate
from pydantic import BaseModel
from rich.console import Console

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
DATA_DIR = ROOT / "data"
CONSOLE = Console(stderr=True)


class SchemaValidationError(RuntimeError):
    """Raised when responses fail schema validation."""


@lru_cache(maxsize=16)
def _load_schema(schema_name: str) -> Dict[str, Any]:
    if '#' in schema_name:
        file_name, fragment = schema_name.split('#', 1)
    else:
        file_name, fragment = schema_name, None
    schema_path = SCHEMA_DIR / file_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema {schema_name} not found at {schema_path}")
    with schema_path.open('r', encoding='utf-8') as handle:
        data = json.load(handle)
    if fragment:
        pointer = fragment.lstrip('/').split('/') if fragment else []
        for key in pointer:
            if not key:
                continue
            data = data[key]
    return data


def validate_payload(instance: Any, schema_name: str) -> None:
    """Validate instance against a schema file."""
    schema = _load_schema(schema_name)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
    if errors:
        messages = "; ".join(error.message for error in errors)
        raise SchemaValidationError(f"Validation failed for {schema_name}: {messages}")


def parse_csv_text(csv_text: str) -> List[Dict[str, Any]]:
    reader = csv.DictReader(io.StringIO(csv_text))
    rows = []
    for row in reader:
        rows.append({key: row[key] for key in row})
    return rows


def decode_xlsx_base64(xlsx_base64: str) -> bytes:
    try:
        return base64.b64decode(xlsx_base64)
    except Exception as exc:  # noqa: BLE001
        raise ValueError("Invalid base64 payload for xlsx_base64") from exc


@dataclass
class ToolConfig:
    enabled: bool
    params: Dict[str, Any]


def load_tool_config() -> Dict[str, ToolConfig]:
    config_path = ROOT / "config" / "tools.yaml"
    if not config_path.exists():
        return {}
    import yaml  # type: ignore

    with config_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    configs: Dict[str, ToolConfig] = {}
    for key, value in raw.items():
        enabled = bool(value.get("enabled", True))
        params = {k: v for k, v in value.items() if k != "enabled"}
        configs[key] = ToolConfig(enabled=enabled, params=params)
    return configs


class RequestModel(BaseModel):
    """Base request wrapper to provide schema validation hooks."""

    def dict_for_schema(self) -> Dict[str, Any]:
        return json.loads(self.json(exclude_none=True))


def ensure_schema(instance: Any, schema: str) -> None:
    try:
        validate(instance=instance, schema=_load_schema(schema))
    except Exception as exc:  # noqa: BLE001
        raise SchemaValidationError(str(exc)) from exc


def normalize_weights(rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    total = 0.0
    cleaned: List[Dict[str, Any]] = []
    warnings: List[str] = []
    for row in rows:
        ticker = str(row.get("ticker", "")).strip().upper()
        weight_raw = row.get("weight")
        try:
            weight = float(weight_raw)
        except (TypeError, ValueError):
            warnings.append(
                f"Ticker {ticker or '?'} has invalid weight {weight_raw!r}; treating as 0."
            )
            weight = 0.0
        if weight < 0:
            warnings.append(f"Ticker {ticker} has negative weight {weight}; clipped to 0.")
            weight = 0.0
        cleaned.append({"ticker": ticker, "weight": weight})
        total += weight
    if total == 0:
        raise ValueError("Weights sum to zero after cleaning; cannot normalize.")
    normalized_rows = [
        {"ticker": row["ticker"], "weight": row["weight"] / total} for row in cleaned
    ]
    return {"normalized_rows": normalized_rows, "sum": 1.0, "warnings": warnings}


def load_json_rows(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("Expected a list in JSON file")
    return [dict(item) for item in data]
