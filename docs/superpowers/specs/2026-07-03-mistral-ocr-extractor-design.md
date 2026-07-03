# Mistral OCR Extractor — Design Spec

Issue: [#8 — Integrate Mistral OCR as a new extractor](https://github.com/lidia-tech/benchmarkdown/issues/8)

## Goal

Add [Mistral OCR](https://docs.mistral.ai/api/endpoint/ocr) (`POST /v1/ocr`, model
`mistral-ocr-latest`) as a self-contained extractor plugin under
`benchmarkdown/extractors/mistral_ocr/`, implementing the `MarkdownExtractor`
protocol. Mistral OCR returns markdown directly, one entry per page — a natural
fit for the benchmark. No UI/registry changes are needed (auto-discovery via
`pkgutil`). `tensorlake/` is the closest existing template (simple cloud API:
upload → call → join per-chunk markdown).

## API grounding (verified against the `mistralai` Python SDK)

- Client: `Mistral(api_key=...)`.
- Local file → OCR uses the documented three-step path:
  1. `client.files.upload(file={"file_name": <name>, "content": <bytes>}, purpose="ocr")` → returns an object with `.id`.
  2. `client.files.get_signed_url(file_id=<id>, expiry=1)` → returns an object with `.url`.
  3. `client.ocr.process(model=..., document={"type": "document_url", "document_url": <url>}, ...)`.
- Response `OCRResponse.pages[]`: each `OCRPageObject` has `.index`, `.markdown`, `.images[]`. Final markdown = `"\n\n".join(page.markdown for page in pages)` (mirrors how `tensorlake` joins chunks).
- **Real `OCRRequest` parameters** (the only knobs the endpoint accepts): `model`, `document`, `pages` (`list[int]`), `include_image_base64` (`bool`), `image_limit` (`int`), `image_min_size` (`int`), `bbox_annotation_format`, `document_annotation_format`.

### Fields the issue proposed that do NOT exist in the API

`table_format`, `extract_header`, `extract_footer` are **not** `/v1/ocr`
parameters. They are dropped — exposing dead UI controls that silently do
nothing would be misleading.

## Decisions

1. **Config surface — real API params only.**
   - **Basic:** `model` (default `mistral-ocr-latest`), `pages`, `include_image_base64`.
   - **Advanced:** `image_limit`, `image_min_size`.
   - `document_annotation_format` / `bbox_annotation_format` are **out of scope**: they require a JSON `response_format`/schema for *structured* extraction, not markdown, so they don't serve a markdown-quality benchmark. Noted here as a deliberate cut; can be revisited if structured-output benchmarking is ever wanted.

2. **`pages` is `Optional[str]`, parsed to `list[int]` in the extractor.**
   The dynamic UI has no clean `list[int]` component. `pages` renders as a
   Textbox accepting a comma-separated list (e.g. `"0,2,5"`); the extractor
   parses it to `list[int]`. Empty/None ⇒ all pages (omit the param).

3. **Local file input — upload → signed URL → `document_url`.**
   Matches the issue and the canonical SDK path; handles large files without
   base64 payload bloat. The uploaded file is deleted in a `finally` block so
   the workspace isn't littered with per-run uploads.

4. **Async via thread-pool executor**, identical to the other cloud extractors
   (`run_in_executor` wrapping the blocking SDK calls).

## Components

`benchmarkdown/extractors/mistral_ocr/`

- **`config.py`** — `MistralOCRConfig(BaseModel)`:
  - `api_key: str` (default from `MISTRAL_API_KEY`; excluded from UI fields).
  - `model: str = "mistral-ocr-latest"`.
  - `pages: Optional[str] = None` — comma-separated page indices (0-based).
  - `include_image_base64: bool = False`.
  - `image_limit: Optional[int] = None`.
  - `image_min_size: Optional[int] = None`.
  - Helper `to_ocr_kwargs() -> dict`: builds the kwargs dict for
    `ocr.process`, parsing `pages` into `list[int]` and omitting `None`/empty
    values so the API applies its own defaults.
  - `MISTRAL_OCR_BASIC_FIELDS = ["model", "pages", "include_image_base64"]`,
    `MISTRAL_OCR_ADVANCED_FIELDS = ["image_limit", "image_min_size"]`.
- **`extractor.py`** — `MistralOCRExtractor`:
  - `__init__(self, config=None, **kwargs)` mirroring `TensorLakeExtractor`
    (config takes precedence; kwargs fallback). Builds `Mistral(api_key=...)`.
  - `async extract_markdown(self, filename) -> str`: runs a blocking
    `upload → get_signed_url → ocr.process → join → delete` in the executor;
    friendly error mapping for auth / rate-limit like `tensorlake`.
- **`__init__.py`** — standard exports: `Extractor`, `Config`, `BASIC_FIELDS`,
  `ADVANCED_FIELDS`, `ENGINE_NAME="mistral_ocr"`,
  `ENGINE_DISPLAY_NAME="Mistral OCR (Cloud)"`, `is_available()`. Guards the
  `extractor` import behind a `try/except ImportError` dummy (mirrors
  `tensorlake`) so the plugin is importable without the SDK installed.
  `is_available()` returns `(False, msg)` if `MISTRAL_API_KEY` is unset or
  `mistralai` is not importable.

## Dependencies & docs

- `pyproject.toml`: new group `mistral = ["mistralai>=1.0.0"]`.
- Plugin `README.md` (mirror `tensorlake/README.md`): features, install
  (`uv sync --group mistral`), `MISTRAL_API_KEY` setup, config options, usage.
- `docs/ENVIRONMENT_VARIABLES.md`: add `MISTRAL_API_KEY` (Required) row, an
  availability bullet, and a cost row.
- `.env.template`: add a `MISTRAL_API_KEY=` entry if the file exists.

## Testing

`tests/test_mistral_ocr_plugin.py` (pytest, offline-safe):

- **Unit (always run):** config defaults + custom values; `to_ocr_kwargs()`
  parses `pages="0,2,5"` → `[0,2,5]` and omits `None` values; `is_available()`
  contract (False without key); plugin is discovered by `ExtractorRegistry`
  with the expected display name and exported symbols.
- **`@pytest.mark.integration @pytest.mark.live`:** end-to-end extraction
  against real Mistral OCR, guarded by `pytest.skip` when `MISTRAL_API_KEY` or a
  test document is missing. Deselected by default; runs only with
  `uv run pytest -m integration --live`.

## Acceptance criteria mapping

All issue criteria are covered except the three phantom config fields
(`table_format`, `extract_header/footer`), which are intentionally omitted per
Decision 1, and `document_annotation_format`, omitted per the scope cut. The
"Config exposes at least: model, pages, image controls" criterion is met with
real API parameters.
