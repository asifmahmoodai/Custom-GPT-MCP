PYTHON?=python3
VENV?=.venv

.PHONY: setup dev eval lint

setup:
$(PYTHON) -m venv $(VENV)
$(VENV)/bin/pip install -U pip
$(VENV)/bin/pip install -r requirements.txt

dev:
$(PYTHON) -m tools.server_main

eval:
$(PYTHON) -m eval.run_eval

lint:
$(VENV)/bin/ruff check .
$(VENV)/bin/mypy tools eval
