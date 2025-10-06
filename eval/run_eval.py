"""Quick integration checks for MCP tools."""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict

from tools import portfolio_server, xmetric_server, ymetric_server
from tools.common import DATA_DIR

from .validate import validate_portfolio, validate_scatter, validate_timeseries


class EvalError(Exception):
    """Raised when a test fails."""


def _run_test(name: str, func: Callable[[], None]) -> None:
    try:
        func()
    except Exception as exc:  # noqa: BLE001
        raise EvalError(f"{name} FAILED: {exc}") from exc


def test_xmetric() -> None:
    chart = xmetric_server.run({"columns": ["value"]})
    validate_timeseries(chart)


def test_ymetric() -> None:
    chart = ymetric_server.run({"x_col": "x", "y_col": "y"})
    validate_scatter(chart)


def test_portfolio() -> None:
    csv_path = DATA_DIR / "portfolios" / "sample_portfolio.csv"
    payload = portfolio_server.run({"csv_text": csv_path.read_text()})
    validate_portfolio(payload)


def main() -> None:
    tests = [
        ("xmetric", test_xmetric),
        ("ymetric", test_ymetric),
        ("portfolio", test_portfolio),
    ]
    for name, test in tests:
        _run_test(name, test)
        print(f"{name}: PASSED")
    print("All eval checks PASSED")


if __name__ == "__main__":
    main()
