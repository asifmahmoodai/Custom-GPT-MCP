"""Ymetric MCP tool implementation producing scatter chart payloads."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from rich.console import Console

from .common import DATA_DIR, RequestModel, ensure_schema, load_json_rows, load_tool_config

CONSOLE = Console(stderr=True)
TABLE_PATH = DATA_DIR / "tables" / "ymetric_table.parquet"


class YMetricRequest(RequestModel):
    x_col: str
    y_col: str
    scale: float = 1.0
    offset: float = 0.0
    label_col: Optional[str] = "label"


def _load_records() -> List[Dict[str, Any]]:
    if not TABLE_PATH.exists():
        raise FileNotFoundError(f"ymetric table not found at {TABLE_PATH}")
    try:
        import pandas as pd

        df = pd.read_parquet(TABLE_PATH)
        return df.to_dict(orient="records")
    except Exception:  # noqa: BLE001
        try:
            return load_json_rows(TABLE_PATH)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("Unable to load ymetric table as parquet or JSON") from exc


def run(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute ymetric scatter computation."""

    request = YMetricRequest(**params)
    config = load_tool_config().get("ymetric")
    if config and not config.enabled:
        raise RuntimeError("ymetric tool disabled via configuration")

    scale = float(params.get("scale", config.params.get("default_scale", request.scale))) if config else request.scale
    offset = float(params.get("offset", config.params.get("default_offset", request.offset))) if config else request.offset
    max_points = int(config.params.get("max_points", 1000)) if config else 1000

    records = _load_records()
    if not records:
        raise RuntimeError("ymetric table is empty")

    points: List[Dict[str, Any]] = []
    for row in records:
        if request.x_col not in row or request.y_col not in row:
            raise ValueError("Requested columns not present in dataset")
        try:
            x_val = float(row[request.x_col])
            y_val = float(row[request.y_col]) * scale + offset
        except (TypeError, ValueError):
            CONSOLE.print(
                f"Skipping row due to non-numeric values: {row}", style="yellow"
            )
            continue
        point: Dict[str, Any] = {"x": x_val, "y": y_val}
        if request.label_col and request.label_col in row:
            point["label"] = str(row[request.label_col])
        points.append(point)

    if len(points) > max_points:
        points = points[:max_points]

    chart = {
        "chart_type": "scatter",
        "points": points,
        "meta": {
            "scale": scale,
            "offset": offset,
            "source": TABLE_PATH.name,
            "count": len(points),
        },
    }
    ensure_schema(chart, "charts.v1.json")
    return chart
