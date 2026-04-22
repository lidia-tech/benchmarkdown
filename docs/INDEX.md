# Benchmarkdown Documentation

## For Users

- **[README.md](../README.md)** — Start here: what Benchmarkdown does, installation, how to use the web interface
- **[CONFIG_UI_README.md](CONFIG_UI_README.md)** — Configuration guide: creating profiles, engine-specific settings, performance tips
- **[ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md)** — All environment variables: API keys, credentials, performance tuning, logging

Each extractor also has its own detailed README:
- [Docling](../benchmarkdown/extractors/docling/README.md) — Local, free, OCR engines, table extraction
- [AWS Textract](../benchmarkdown/extractors/textract/README.md) — AWS cloud service, IAM setup
- [LlamaParse](../benchmarkdown/extractors/llamaparse/README.md) — LlamaIndex cloud service, GPT-4o mode
- [TensorLake](../benchmarkdown/extractors/tensorlake/README.md) — Cloud service, signature detection
- [Azure Document Intelligence](../benchmarkdown/extractors/azure_document_intelligence/README.md) — Microsoft cloud service
- [LiteLLM](../benchmarkdown/extractors/litellm/README.md) — Vision LLMs (GPT-4o, Claude, Gemini)

## For Developers

- **[CLAUDE.md](../CLAUDE.md)** — Architecture overview, plugin system, adding new extractors
- **[tests/README.md](../tests/README.md)** — Test suite: categories, running tests, adding new tests
- **[implementation_notes/](implementation_notes/README.md)** — Design decisions and architectural patterns

## Task Management

Tasks are tracked as [GitHub Issues](https://github.com/lidia-tech/benchmarkdown/issues).

## Archive

Historical documentation:

- `archive/DONE.md` — Completed tasks and implementation history (pre-GitHub Issues)
- `archive/IMPLEMENTATION_GAPS.md` — Pre-plugin analysis
- `archive/PLUGIN_IMPLEMENTATION_SUMMARY.md` — Plugin infrastructure summary
- `archive/UI_REFACTORING_GUIDE.md` — UI refactoring guide
- `archive/UI_README.md` — Old UI documentation (superseded by README.md)

## Quick Navigation

| I want to... | Go to |
|---|---|
| Use the app for the first time | [README.md](../README.md) |
| Set up API credentials | [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md) |
| Configure an extractor | [CONFIG_UI_README.md](CONFIG_UI_README.md) |
| Add a new extractor plugin | [CLAUDE.md](../CLAUDE.md#adding-new-extractors) |
| Run tests | [tests/README.md](../tests/README.md) |
| Understand the architecture | [CLAUDE.md](../CLAUDE.md#architecture) |
