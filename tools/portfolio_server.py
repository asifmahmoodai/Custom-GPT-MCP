"""Portfolio normalization MCP tool."""
from __future__ import annotations

import io
from typing import Any, Dict, List, Optional

from rich.console import Console

from .common import (
    RequestModel,
    decode_xlsx_base64,
    load_tool_config,
    normalize_weights,
    parse_csv_text,
    validate_payload,
)

CONSOLE = Console(stderr=True)


class PortfolioRow(RequestModel):
    ticker: str
    weight: float


class PortfolioRequest(RequestModel):
    rows: Optional[List[PortfolioRow]] = None
    csv_text: Optional[str] = None
    xlsx_base64: Optional[str] = None


def _rows_from_xlsx(b64: str) -> List[Dict[str, Any]]:
    data = decode_xlsx_base64(b64)
    try:
        import pandas as pd

        df = pd.read_excel(io.BytesIO(data))
        return df.to_dict(orient="records")
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("Failed to parse XLSX payload; ensure it has ticker and weight columns") from exc


def _collect_rows(request: PortfolioRequest) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if request.rows:
        rows.extend(row.dict_for_schema() for row in request.rows)
    if request.csv_text:
        rows.extend(parse_csv_text(request.csv_text))
    if request.xlsx_base64:
        rows.extend(_rows_from_xlsx(request.xlsx_base64))
    return rows


def run(params: Dict[str, Any]) -> Dict[str, Any]:
    request = PortfolioRequest(**params)
    config = load_tool_config().get("portfolio")
    if config and not config.enabled:
        raise RuntimeError("portfolio tool disabled via configuration")

    rows = _collect_rows(request)
    if not rows:
        raise ValueError("No portfolio rows provided")

    result = normalize_weights(rows)
    allowed = config.params.get("allowed_tickers") if config else None
    warnings = list(result.get("warnings", []))
    if allowed:
        invalid = [row["ticker"] for row in result["normalized_rows"] if row["ticker"] not in allowed]
        if invalid:
            warnings.append(
                "Tickers outside allowed universe: " + ", ".join(sorted(set(invalid)))
            )
    payload = {
        "normalized_rows": result["normalized_rows"],
        "sum": result["sum"],
        "warnings": warnings,
    }
    validate_payload(payload, "portfolio.v1.json#/properties/response")
    return payload
