# AGENTS.md

This file provides guidance to AI coding agents when working with code in this repository.
`CLAUDE.md` is a symlink to this file.

## Project Overview

Benchmarkdown is a benchmark suite for comparing document-to-markdown extraction technologies. It uses a **plugin-based architecture** where new extractors are added by creating a directory — no code changes needed. The Gradio web UI automatically discovers and integrates plugins at runtime. A parallel **metrics plugin system** evaluates extraction quality against ground truth.

## Essential Commands

```bash
# Environment setup (all extractors)
uv sync --all-groups

# Install specific extractor only
uv sync --group docling       # or: textract, llamaparse, tensorlake, azure-document-intelligence

# Launch the Gradio web UI
uv run python app.py

# Run a single test
uv run python tests/test_config_ui.py

# Update all dependencies
uv sync --all-extras --all-groups
```

Always use `uv run python` (not bare `python`) when executing scripts or the interpreter.

**Environment Variables**: Each extractor documents its own env vars in `benchmarkdown/extractors/{name}/README.md`. Consolidated reference: `docs/ENVIRONMENT_VARIABLES.md`.

## Architecture

### Two Plugin Systems

Both follow the same pattern: auto-discovery via `pkgutil`, standard exports in `__init__.py`, registry class with metadata dataclasses.

**Extractors** (`benchmarkdown/extractors/{name}/`):
- `__init__.py` — exports: `Extractor`, `Config`, `BASIC_FIELDS`, `ADVANCED_FIELDS`, `ENGINE_NAME`, `ENGINE_DISPLAY_NAME`, `is_available()`, optional `NESTED_CONFIGS`, `CONDITIONAL_FIELDS`
- `config.py` — Pydantic model with field groupings for UI generation
- `extractor.py` — implements `MarkdownExtractor` protocol (single async method: `extract_markdown(filename) -> str`)
- Registry: `benchmarkdown/extractors/__init__.py` (`ExtractorRegistry`)

**Metrics** (`benchmarkdown/metrics/{name}/`):
- Same plugin pattern as extractors
- Exports: `METRIC_NAME`, `METRIC_DISPLAY_NAME`, `METRIC_DESCRIPTION`, `METRIC_CATEGORY`, `Metric`, `is_available()`
- Registry: `benchmarkdown/metrics/__init__.py` (`MetricRegistry`)
- Current metrics: `char_count`, `heading_f1`, `heading_s`, `word_count`

### Core Types

`benchmarkdown/types.py` — `MarkdownExtractor` Protocol (the contract all extractors implement)
`benchmarkdown/extractors/base.py` — base class for extractors
`benchmarkdown/metrics/base.py` — `Metric` base class and `MetricResult` dataclass

### UI Layer (`benchmarkdown/ui/`)

| File | Purpose |
|---|---|
| `app_builder.py` | Main Gradio interface, `create_app()` entry point |
| `core.py` | `BenchmarkUI` — async processing pipeline, result storage |
| `dynamic_config.py` | Generates Gradio components from Pydantic models at runtime |
| `queue.py` | Task queue persistence (`.task_queue.json`) |
| `results.py` | Comparison views (tabbed, side-by-side) with metrics tables |
| `validation.py` | Ground truth comparison UI |

### Key Design Patterns

- All extractors use **async/await via thread pool executors** (blocking libs wrapped in `run_in_executor`)
- UI uses `asyncio.run()` wrapper for Gradio compatibility
- **Pydantic → Gradio mapping**: config field types automatically become UI components
- **Profile system**: named JSON configs saved in `./config/`, reusable across sessions
- **Queue-based workflow**: users build a task queue, then batch-extract all documents × all extractors in parallel

### Entry Point

`app.py` — auto-detects available extractors, calls `create_app()` from `benchmarkdown.ui`

## Adding New Extractors

Create `benchmarkdown/extractors/{name}/` with three files (`__init__.py`, `config.py`, `extractor.py`) following the pattern of existing plugins (e.g., `tensorlake/` for a simple cloud API, `docling/` for nested configs). Add optional dependency group to `pyproject.toml`. No other files need modification.

For nested configs (like Docling's OCR engines), export `NESTED_CONFIGS` dict — see `benchmarkdown/extractors/docling/__init__.py`.

## Testing

Tests are standalone scripts in `tests/` (not pytest). Run individually with `uv run python tests/test_*.py`. Tests use documents from `data/input/lidia-anon/` and skip gracefully if missing.

Browser/API tests (`test_browser.py`, `test_workflow_api.py`) require the app running first.

## Documentation Guidelines

When implementing significant features or architectural patterns, create implementation notes in `docs/implementation_notes/` and update its README. See existing notes for format. This is for developer reference, not user-facing docs.

## Task Management

Uses GitHub Issues workflow (skill: `github-issues-workflow`). Repo: [lidia-tech/benchmarkdown](https://github.com/lidia-tech/benchmarkdown). Do not use `TODO.md` / `DONE.md`.

## Runtime Artifacts (gitignored)

- `data/` — all gitignored; `data/input/` holds source documents (PDF, DOCX), `data/raw_markdown/` and `data/clean_markdown/` hold outputs
- `config/` — saved profile JSON files
- `.task_queue.json` — persisted task queue
