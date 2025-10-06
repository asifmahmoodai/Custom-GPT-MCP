"""Implementation of the xmetric MCP tool."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from rich.console import Console

from .common import DATA_DIR, RequestModel, ensure_schema, load_tool_config

CONSOLE = Console(stderr=True)
TABLE_PATH = DATA_DIR / "tables" / "xmetric_table.csv"


class XMetricRequest(RequestModel):
    columns: List[str]
    scale: float = 1.0
    offset: float = 0.0
    groupby: Optional[str] = "series"
    date_col: str = "date"


def _load_dataframe() -> List[Dict[str, Any]]:
    if not TABLE_PATH.exists():
        raise FileNotFoundError(f"xmetric table not found at {TABLE_PATH}")
    try:
        import pandas as pd

        df = pd.read_csv(TABLE_PATH)
        return df.to_dict(orient="records")
    except Exception:  # noqa: BLE001
        import csv

        with TABLE_PATH.open("r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            return [dict(row) for row in reader]


def _coerce_date(value: Any) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")
    text = str(value)
    try:
        date_obj = datetime.fromisoformat(text)
    except ValueError:
        return text
    if date_obj.tzinfo is None:
        return date_obj.strftime("%Y-%m-%dT%H:%M:%SZ")
    return date_obj.isoformat()


def run(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the xmetric tool and return a chart payload."""

    request = XMetricRequest(**params)
    config = load_tool_config().get("xmetric")
    if config and not config.enabled:
        raise RuntimeError("xmetric tool disabled via configuration")

    if config:
        allowed = config.params.get("allowed_columns")
        if allowed:
            invalid = [col for col in request.columns if col not in allowed]
            if invalid:
                raise ValueError(f"Columns {invalid} are not allowed; permitted: {allowed}")
        scale = float(params.get("scale", config.params.get("default_scale", request.scale)))
        offset = float(params.get("offset", config.params.get("default_offset", request.offset)))
    else:
        scale = request.scale
        offset = request.offset

    records = _load_dataframe()
    if not records:
        raise RuntimeError("xmetric table is empty")

    group_col = request.groupby or "series"
    date_col = request.date_col
    if any(date_col not in row for row in records):
        raise ValueError(f"Date column '{date_col}' missing in dataset")

    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for row in records:
        group_key = str(row.get(group_col, "default")) if group_col else "default"
        grouped.setdefault(group_key, []).append(row)

    series_payload: List[Dict[str, Any]] = []
    for group_name, rows in grouped.items():
        rows_sorted = sorted(rows, key=lambda item: item[date_col])
        for column in request.columns:
            if column not in rows_sorted[0]:
                raise ValueError(f"Column '{column}' missing in dataset")
            name = f"{group_name}:{column}" if group_col else column
            points: List[Dict[str, Any]] = []
            for row in rows_sorted:
                value_raw = row[column]
                try:
                    value_float = float(value_raw)
                except (TypeError, ValueError):
                    CONSOLE.print(
                        f"Skipping row with non-numeric value for {column}: {value_raw}",
                        style="yellow",
                    )
                    continue
                scaled_value = value_float * scale + offset
                points.append({"t": _coerce_date(row[date_col]), "v": scaled_value})
            if points:
                series_payload.append({"name": name, "points": points})

    if not series_payload:
        raise RuntimeError("No points produced for the requested columns")

    chart = {
        "chart_type": "timeseries",
        "series": series_payload,
        "meta": {"scale": scale, "offset": offset, "source": TABLE_PATH.name},
    }
    ensure_schema(chart, "charts.v1.json")
    return chart
