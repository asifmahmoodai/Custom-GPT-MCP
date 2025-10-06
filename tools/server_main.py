"""Entry point for the MCP tool server."""
from __future__ import annotations

import json
import sys
from typing import Any, Callable, Dict

import typer
from rich.console import Console
from rich.table import Table

from . import portfolio_server, xmetric_server, ymetric_server

console = Console(stderr=True)
app = typer.Typer(help="One-Week Custom GPT MCP tool server")

ToolHandler = Callable[[Dict[str, Any]], Dict[str, Any]]


def _tool_registry() -> Dict[str, ToolHandler]:
    return {
        "xmetric.run": xmetric_server.run,
        "ymetric.run": ymetric_server.run,
        "portfolio.normalize": portfolio_server.run,
    }


def _print_banner() -> None:
    table = Table(title="MCP Tools", show_lines=False)
    table.add_column("Tool")
    table.add_column("Description")
    table.add_row("xmetric.run", "Time-series computations from CSV")
    table.add_row("ymetric.run", "Scatter computations from parquet/JSON")
    table.add_row("portfolio.normalize", "Normalize portfolio weights")
    console.print(table)
    console.print("Listening for JSON-RPC messages on stdin…", style="green")


def _handle_call(tool: str, params: Dict[str, Any]) -> Dict[str, Any]:
    registry = _tool_registry()
    if tool not in registry:
        raise ValueError(f"Unknown tool '{tool}'")
    handler = registry[tool]
    return handler(params)


@app.command()
def serve() -> None:
    """Start the stdio-based MCP loop."""

    _print_banner()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
            tool = payload.get("tool")
            params = payload.get("params", {})
            if not isinstance(params, dict):
                raise ValueError("params must be an object")
            result = _handle_call(str(tool), params)
            response = {"ok": True, "result": result}
        except Exception as exc:  # noqa: BLE001
            response = {"ok": False, "error": str(exc)}
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


@app.command()
def call(tool: str, params: str) -> None:
    """Invoke a tool once using JSON params."""

    data = json.loads(params or "{}")
    result = _handle_call(tool, data)
    console.print_json(result)


def main() -> None:
    if len(sys.argv) == 1:
        serve()
    else:
        app()


if __name__ == "__main__":
    main()
