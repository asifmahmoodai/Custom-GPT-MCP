# One-Week Custom GPT MCP Prototype

This repository delivers a modular Custom GPT configuration with three MCP tools, corpus-first
retrieval, and schema-driven charting. It is designed as a fast-start template for teams building
a tailored GPT experience in roughly one week.

## Quickstart

1. **Create a virtual environment and install dependencies**
   ```bash
   make setup
   ```
2. **Run the stdio MCP tool server**
   ```bash
   make dev
   ```
   The server reads JSON-RPC payloads from `stdin` and responds on `stdout`. Example manual call:
   ```bash
   python -m tools.server_main call xmetric.run '{"columns": ["value"]}'
   ```
3. **Run evaluation checks**
   ```bash
   make eval
   ```

Python 3.11+ is required. Dependencies are listed in `requirements.txt`.

## Repository Highlights

- **MCP tools** (`xmetric.run`, `ymetric.run`, `portfolio.normalize`) exposed by `tools/server_main.py`.
- **Strict JSON Schemas** in `/schemas` enforce request/response contracts and chart payloads.
- **File Search-first GPT config** in `/gpt/config.json`, with prompts tailored for corpus-first RAG and
  optional web search fallback.
- **Sample data** under `/data` including a lightweight research corpus, metric tables, and portfolio
  examples.
- **Evaluation harness** under `/eval` for quick schema validation and smoke tests.

## Adding a New MCP Tool (≤10 steps)

1. Draft request/response schemas in `/schemas` (version them, e.g., `newtool.v1.json`).
2. Implement Pydantic request models and pure functions in a new module under `/tools`.
3. Reuse helpers from `tools/common.py` for schema loading, validation, and config handling.
4. Register the handler in `tools/server_main.py`'s `_tool_registry`.
5. Update `/tools/mcp.manifest.json` with command metadata and examples.
6. Expose configuration toggles via `/config/tools.yaml` if needed.
7. Add canned evaluations to `/eval/run_eval.py`.
8. Document usage in `README.md` and optionally add few-shot examples in `gpt/few_shots.md`.
9. Update `gpt/config.json` if the tool should be callable from the GPT experience.
10. Run `make eval` to confirm schemas stay valid.

## Wrapping Tools with FastAPI (future work)

You can expose these pure functions through a REST API. A minimal FastAPI skeleton might look like:

```python
# app.py (future enhancement)
from fastapi import FastAPI
from tools import xmetric_server

app = FastAPI()

@app.post("/xmetric")
def run_xmetric(request: dict):
    """TODO: Add request model & auth."""
    return xmetric_server.run(request)
```

Add authentication, rate limiting, and error handling before deploying.

## Expanding the Corpus to ~10 MB

1. Collect plaintext research files (filings, news, transcripts) and place them under
   `data/corpus/` (you can create nested folders under `samples/`).
2. Follow your platform's File Search reindexing workflow—typically this involves uploading the
   updated corpus directory or re-running the indexer command.
3. Update `gpt/system_prompt.md` or notes if topic coverage changes.

## Security Posture & TODOs

- **Input validation**: All tools validate against JSON Schemas and sanitize numeric conversions.
- **Warnings surfaced**: Portfolio normalization reports invalid tickers/weights without crashing.
- **TODOs**: Add authentication/authorization, rate limiting, structured auditing, and secure secret
  storage before deploying beyond prototypes.

## Performance Tips

- Tools read data fresh on each call to remain stateless; keep tables reasonably small or add caching.
- Adjust defaults (e.g., scaling factors, max scatter points) via `config/tools.yaml` without code
  changes.
- Use the lightweight `call` CLI to profile individual tool latency before integrating with GPT.

## Data Notes

- `data/tables/ymetric_table.parquet` falls back to JSON parsing if Parquet libraries are unavailable.
  Replace with a true Parquet file when dependencies are installed.
- Sample corpus files are small; expand to production scale as described above.
