"""Validation helpers for tool outputs."""
from __future__ import annotations

from typing import Any, Dict

from tools.common import ensure_schema


def validate_timeseries(chart: Dict[str, Any]) -> None:
    ensure_schema(chart, "charts.v1.json")


def validate_scatter(chart: Dict[str, Any]) -> None:
    ensure_schema(chart, "charts.v1.json")


def validate_portfolio(payload: Dict[str, Any]) -> None:
    ensure_schema(payload, "portfolio.v1.json#/properties/response")
