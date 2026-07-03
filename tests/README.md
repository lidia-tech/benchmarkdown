# Tests Directory

This directory contains the functional and integration tests for Benchmarkdown. They run under **pytest** (configured in `pyproject.toml`; markers and the `--live` flag live in `conftest.py`).

## Running tests

```bash
uv run pytest                          # offline unit suite (integration deselected)
uv run pytest tests/test_config_ui.py  # a single file
uv run pytest tests/test_config_ui.py::test_name   # a single test
uv run pytest --cov=benchmarkdown --cov-report=term-missing   # with coverage
```

### Markers

- `@pytest.mark.integration` — needs live API credentials, a running app, or a browser. **Deselected by default** via `addopts = "-m 'not integration'"`, so a bare `pytest` run is the offline unit suite (this is what CI runs). Run them with `uv run pytest -m integration`.
- `@pytest.mark.live` — hits real, billable external services. **Collected but skipped** unless `--live` is passed. A live integration test needs both: `uv run pytest -m integration --live`.

Integration tests that drive a running app (`test_browser.py`, `test_workflow_api.py`) require the app started first:

```bash
uv run python app.py &   # start in background
sleep 5
uv run pytest -m integration
kill %1
```

## Test categories

### Configuration system
- **test_config_ui.py** — Pydantic field → Gradio component mapping, config building, field groupings.
- **test_config_extraction.py** — end-to-end config-based extraction (default vs custom); skips without sample docs.
- **test_multiple_configs.py** — multiple extractor instances side-by-side; skips without sample docs.
- **test_env_vars.py** — env-var-backed config fields across extractors.

### Application integration
- **test_ui.py** — `BenchmarkUI` document processing and metrics; skips without sample docs.
- **test_integrated_app.py** — dynamic extractor registration and config storage.
- **test_redesigned_workflow.py** — select → configure → queue → extract; queue add/clear.
- **test_app_simple.py** — the app object builds from a discovered registry.
- **test_persistence.py** — task-queue save/load schema (self-contained, temp file).

### Metrics
- **test_metrics_basic.py**, **test_rouge2_metric.py**, **test_gt_upload_list.py**, **test_validation_workflow.py**.

### Extractor plugins
- **test_tensorlake_plugin.py**, **test_tensorlake_profile_save.py**, **test_tensorlake_ui_bug.py**, **test_azure_config_refactoring.py**, **test_azure_component_count.py**.
- **test_textract_config.py** — Textract config unit tests; extractor instantiation is `integration`, real extraction is `integration` + `live`.
- **test_azure_document_intelligence.py** — plugin/config/registry unit tests; extractor instantiation is `integration`.

### Running app / browser (integration)
- **test_browser.py** — smoke test via Gradio's Python HTTP client (`gradio_client`), marked `integration`.
- **test_workflow_api.py** — complete workflow automation via the Gradio API, marked `integration`.

## Test data

Tests use documents from `data/input/lidia-anon/*.docx` (anonymized Italian legal documents, gitignored). Tests that need them call `pytest.skip(...)` when absent, so they show as *skipped* rather than passing vacuously.

## Adding new tests

1. Name the file `test_<feature>.py` and the functions `test_*`.
2. Use plain `assert` — do **not** wrap assertions in `try/except` that swallows failures, and do not `return` a value from a test.
3. `async def test_*` is supported directly (`asyncio_mode = "auto"`).
4. Mark tests that need credentials / a running app / a browser with `@pytest.mark.integration`; mark real billable calls `@pytest.mark.live`.
5. Use `pytest.skip("reason")` for missing optional fixtures (test documents, credentials).
6. Update the category list above.

## Continuous integration

CI (`.github/workflows/ci.yml`) runs `uv run pytest` (integration deselected) with coverage and posts a coverage summary as a PR comment.
