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

## API grounding (verified against the installed `mistralai` 2.5.1 SDK)

- Import: `from mistralai.client import Mistral` (v2.x is a namespace package;
  the client lives under `mistralai.client`). Construct: `Mistral(api_key=...)`.
- Local file → OCR uses the documented three-step path:
  1. `client.files.upload(file={"file_name": <name>, "content": <bytes>}, purpose="ocr")` → returns an object with `.id`.
  2. `client.files.get_signed_url(file_id=<id>, expiry=1)` → returns an object with `.url`.
  3. `client.ocr.process(model=..., document={"type": "document_url", "document_url": <url>}, ...)`.
- Response `OCRResponse.pages[]`: each `OCRPageObject` has `.index`, `.markdown`, `.images[]`. Final markdown = `"\n\n".join(page.markdown for page in pages)` (mirrors how `tensorlake` joins chunks).
- **`OCRRequest` parameters actually supported by `ocr.process` in 2.5.1**
  (verified by signature + `models/ocrrequest.py` introspection): `model`,
  `document`, `pages`, `include_image_base64`, `image_limit`, `image_min_size`,
  `table_format` (`Literal['markdown','html']`), `extract_header` (`bool`),
  `extract_footer` (`bool`), `document_annotation_format`,
  `document_annotation_prompt`, `bbox_annotation_format`, `include_blocks`,
  `confidence_scores_granularity`.

> **Correction to the issue's premise (and my first draft):** the issue's
> `table_format` / `extract_header` / `extract_footer` fields ARE real
> parameters in the current SDK — an earlier reading against the older OpenAPI
> spec wrongly concluded they were phantom. They are exposed.
>
> `pages` natively accepts a **string** of comma-separated numbers and ranges
> (`"0,1,2"`, `"0-5"`, `"0,2-4"`, 0-based) as well as `list[int]`, so it is
> passed through as a string — no fragile client-side parsing, and page ranges
> work for free.

## Decisions

1. **Config surface — the real, markdown-relevant API params.**
   - **Basic:** `model` (default `mistral-ocr-latest`), `pages`, `table_format`, `extract_header`, `extract_footer`.
   - **Advanced:** `include_image_base64`, `image_limit`, `image_min_size`.
   - **Out of scope:** `document_annotation_format` / `bbox_annotation_format`
     (require a JSON `response_format`/schema for *structured* extraction, not
     markdown), `document_annotation_prompt` (only meaningful with an annotation
     format), `include_blocks` and `confidence_scores_granularity` (return
     bounding boxes / confidence metadata, not markdown content). Deliberate
     cuts for a markdown-quality benchmark; revisit if structured-output
     benchmarking is ever wanted.

2. **`pages` is `Optional[str]`, passed through to the API verbatim.**
   The dynamic UI has no clean `list[int]` component, and the API parses
   comma/range strings itself. `pages` renders as a Textbox (e.g. `"0,2-4"`);
   empty/None ⇒ all pages (param omitted). `table_format` is a `str` `Enum`
   (`markdown`/`html`) → Dropdown; `extract_header`/`extract_footer` are
   `bool` → Checkbox, defaulting to `True` (include all page content — the
   faithful "extract everything" stance for a fidelity benchmark) and always
   sent so behavior is deterministic.

3. **Local file input — upload → signed URL → `document_url`.**
   Matches the issue and the canonical SDK path; handles large files without
   base64 payload bloat. The uploaded file is deleted in a `finally` block so
   the workspace isn't littered with per-run uploads.

4. **Async via thread-pool executor**, identical to the other cloud extractors
   (`run_in_executor` wrapping the blocking SDK calls).

## Components

`benchmarkdown/extractors/mistral_ocr/`

- **`config.py`** — `TableFormatEnum(str, Enum)` (`markdown`/`html`) and
  `MistralOCRConfig(BaseModel)`:
  - `api_key: str` (default from `MISTRAL_API_KEY`; excluded from UI fields).
  - `model: str = "mistral-ocr-latest"`.
  - `pages: Optional[str] = None` — comma-separated numbers/ranges (0-based).
  - `table_format: TableFormatEnum = TableFormatEnum.MARKDOWN`.
  - `extract_header: bool = True`.
  - `extract_footer: bool = True`.
  - `include_image_base64: bool = False`.
  - `image_limit: Optional[int] = None`.
  - `image_min_size: Optional[int] = None`.
  - `class Config: use_enum_values = True` (so `table_format` serializes to its
    string value, matching the other plugins).
  - Helper `to_ocr_kwargs() -> dict`: builds the kwargs for `ocr.process` —
    always includes `model`, `table_format`, `extract_header`,
    `extract_footer`, `include_image_base64`; includes `pages` only when it is a
    non-empty string; includes `image_limit`/`image_min_size` only when not
    `None`.
  - `MISTRAL_OCR_BASIC_FIELDS = ["model", "pages", "table_format", "extract_header", "extract_footer"]`,
    `MISTRAL_OCR_ADVANCED_FIELDS = ["include_image_base64", "image_limit", "image_min_size"]`.
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
  always sends `model`/`table_format`/`extract_header`/`extract_footer`/
  `include_image_base64`, passes `pages` through as a string only when set, and
  omits `None` image controls; `is_available()` contract (False without key);
  plugin is discovered by `ExtractorRegistry` with the expected display name and
  exported symbols.
- **`@pytest.mark.integration @pytest.mark.live`:** end-to-end extraction
  against real Mistral OCR, guarded by `pytest.skip` when `MISTRAL_API_KEY` or a
  test document is missing. Deselected by default; runs only with
  `uv run pytest -m integration --live`.

## Acceptance criteria mapping

All issue acceptance criteria are covered, including "Config exposes at least:
model, pages, table_format, extract_header/footer, image controls". The only
deliberate omissions are `document_annotation_format` /
`document_annotation_prompt` / `bbox_annotation_format` / `include_blocks` /
`confidence_scores_granularity` (structured-output and metadata params outside a
markdown-quality benchmark), per Decision 1.
