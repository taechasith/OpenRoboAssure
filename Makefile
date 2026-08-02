.DEFAULT_GOAL := help

.PHONY: help setup lint typecheck test smoke reproduce-smoke reproduce-pilot build pre-commit

help:
	@echo "Targets: setup lint typecheck test smoke reproduce-smoke reproduce-pilot build pre-commit"

setup:
	uv sync --all-groups

lint:
	uv run ruff check .

typecheck:
	uv run mypy src tests

test:
	uv run pytest

smoke:
	uv run ora doctor --offline --output reports/environment/smoke.json

reproduce-smoke:
	uv run --offline ora reproduce smoke

reproduce-pilot:
	uv run --offline ora reproduce pilot

build:
	uv build

pre-commit:
	uv run pre-commit run --all-files
