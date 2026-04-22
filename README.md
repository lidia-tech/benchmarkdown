# Benchmarkdown

**Compare document-to-markdown extraction services side by side.**

Benchmarkdown helps you find the best extraction technology for your documents. Upload PDFs or Word files, run multiple extraction engines on them, and compare the results — all from a web interface, no coding required.

## Why Benchmarkdown?

There are many services that convert documents (PDF, DOCX) to Markdown: some run locally, others are cloud APIs with different pricing and quality trade-offs. Benchmarkdown lets you:

- **Run multiple extractors on the same documents** and see the results side by side
- **Compare quality and speed** with built-in metrics (word count, character count, heading detection)
- **Validate against ground truth** by uploading reference markdown and measuring accuracy
- **Save and reuse configurations** as named profiles, so you can reproduce benchmarks
- **Export results** as ZIP (all markdown files) or HTML comparison reports

## Supported Extractors

| Extractor | Type | Cost | Notes |
|-----------|------|------|-------|
| **[Docling](benchmarkdown/extractors/docling/README.md)** | Local | Free | IBM's open-source library, no API key needed |
| **[AWS Textract](benchmarkdown/extractors/textract/README.md)** | Cloud | Paid | Amazon's OCR service, requires AWS account |
| **[LlamaParse](benchmarkdown/extractors/llamaparse/README.md)** | Cloud | Free tier + paid | LlamaIndex's parsing service |
| **[TensorLake](benchmarkdown/extractors/tensorlake/README.md)** | Cloud | Paid | Advanced OCR with table and signature detection |
| **[Azure Document Intelligence](benchmarkdown/extractors/azure_document_intelligence/README.md)** | Cloud | Paid | Microsoft's document analysis service |
| **[LiteLLM](benchmarkdown/extractors/litellm/README.md)** | Cloud | Varies | Uses vision LLMs (GPT-4o, Claude, Gemini, etc.) to extract text |

Only extractors with valid credentials appear in the UI. You can start with just Docling (free, no setup) and add cloud services later.

## Quick Start

### 1. Install

Install [uv](https://github.com/astral-sh/uv) (a fast Python package manager), then:

```bash
git clone <repository-url>
cd benchmarkdown

# Install with all extractors
uv sync --all-groups

# Or install only what you need:
uv sync                        # Core + Docling (free, local)
uv sync --group textract       # + AWS Textract
uv sync --group llamaparse     # + LlamaParse
uv sync --group tensorlake     # + TensorLake
uv sync --group azure-document-intelligence  # + Azure
uv sync --group litellm        # + LiteLLM (vision LLMs)
```

### 2. Set up credentials (optional)

Copy the template and fill in the API keys for the services you want to use:

```bash
cp .env.template .env
# Edit .env with your credentials
```

Or export them directly:

```bash
# LlamaParse
export LLAMA_CLOUD_API_KEY="your-key"

# TensorLake
export TENSORLAKE_API_KEY="your-key"

# AWS Textract
export TEXTRACT_S3_WORKSPACE="s3://your-bucket/workspace/"

# Azure Document Intelligence
export AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="https://your-resource.cognitiveservices.azure.com/"
export AZURE_DOCUMENT_INTELLIGENCE_KEY="your-key"
```

See [docs/ENVIRONMENT_VARIABLES.md](docs/ENVIRONMENT_VARIABLES.md) for the full reference, and each extractor's README in `benchmarkdown/extractors/{name}/README.md` for detailed setup instructions.

### 3. Launch

```bash
uv run python app.py
```

Open **http://localhost:7860** in your browser.

## How to Use the Web Interface

The workflow has three phases: **configure tasks**, **upload documents**, and **view results**.

### Phase 1: Configure Extraction Tasks

A "task" is an extractor engine paired with a configuration profile. You can queue multiple tasks to compare different engines or settings.

1. Click **"Add Task"**
2. **Select an extractor engine** from the dropdown (only engines with valid credentials appear)
3. **Choose a profile**: select an existing saved profile, or click **"New Profile"** to create one
4. If creating a new profile:
   - Give it a name (e.g., "Fast Mode", "High Quality OCR")
   - Adjust the settings — basic options are shown by default, advanced options are in a collapsible section
   - Click **"Save Profile"** — your profile is saved for future sessions
5. Click **"Add Task to Queue"**
6. Repeat to add more tasks (e.g., same document with Docling vs. Textract vs. LlamaParse)

Your task queue is saved automatically and persists across app restarts.

### Phase 2: Upload and Extract

1. **Upload documents** (PDF, DOCX, DOC, or TXT files) — you can upload multiple files at once
2. Click **"Run Extraction"**
3. All queued extractors process all uploaded documents in parallel. Progress updates appear as each extraction completes.

### Phase 3: View and Compare Results

After extraction completes:

- **Results table**: shows extraction time, word count, character count, and pages-per-second for each extractor on each document
- **Markdown preview**: switch between **Tabbed** or **Side-by-Side** view to compare the extracted markdown
- **Download**: get all results as a ZIP file or an HTML comparison report

### Phase 4 (Optional): Validate Against Ground Truth

If you have reference ("ground truth") markdown for your documents:

1. In the **Validation** section, upload your ground truth `.md` or `.txt` files
2. Select which documents, extractors, and metrics to compare
3. Click **"Run Validation"** to see how each extractor's output compares to the reference

Available metrics include word count similarity, character count similarity, and heading detection (F1 score).

## Managing Profiles

- Profiles are saved as JSON files in `./config/` and persist across sessions
- Each profile is tied to a specific extractor engine
- Use profiles to save different configurations (e.g., "Fast Mode" vs. "High Quality" for Docling)
- You can edit, delete, and create profiles from the UI

## Configuration Reference

Each extractor has its own set of configuration options. For detailed documentation:

- **Docling**: [benchmarkdown/extractors/docling/README.md](benchmarkdown/extractors/docling/README.md) — OCR settings, table extraction, threading, hardware acceleration
- **AWS Textract**: [benchmarkdown/extractors/textract/README.md](benchmarkdown/extractors/textract/README.md) — features, markdown formatting options
- **LlamaParse**: [benchmarkdown/extractors/llamaparse/README.md](benchmarkdown/extractors/llamaparse/README.md) — result types, GPT-4o mode, language settings
- **TensorLake**: [benchmarkdown/extractors/tensorlake/README.md](benchmarkdown/extractors/tensorlake/README.md) — chunking, table output, signature detection
- **Azure Document Intelligence**: [benchmarkdown/extractors/azure_document_intelligence/README.md](benchmarkdown/extractors/azure_document_intelligence/README.md) — model selection, page ranges, locale
- **LiteLLM**: [benchmarkdown/extractors/litellm/README.md](benchmarkdown/extractors/litellm/README.md) — model selection, DPI, prompt customization, batching

See also [docs/ENVIRONMENT_VARIABLES.md](docs/ENVIRONMENT_VARIABLES.md) for environment variables and performance tuning.

## Troubleshooting

**An extractor doesn't appear in the engine dropdown**
- Its credentials are not set. Check [docs/ENVIRONMENT_VARIABLES.md](docs/ENVIRONMENT_VARIABLES.md) for what's required.
- Docling always appears (no credentials needed). If even Docling is missing, the installation may be incomplete — try `uv sync --all-groups`.

**Extraction is slow**
- Cloud extractors depend on network speed and API load. Check timeout settings in each extractor's README.
- For Docling, try increasing threads (`DOCLING_NUM_THREADS`) or using FAST table mode in the profile settings.

**"No extractors available" on startup**
- Run `uv sync --all-groups` to install all dependencies, or at minimum `uv sync --group docling`.

**Want more detail in logs?**
```bash
BENCHMARKDOWN_LOG_LEVEL=INFO uv run python app.py    # See plugin discovery and extraction progress
BENCHMARKDOWN_LOG_LEVEL=DEBUG uv run python app.py   # Full debug output
```

## For Developers

- **[CLAUDE.md](CLAUDE.md)** — Architecture overview, plugin system, adding new extractors
- **[tests/README.md](tests/README.md)** — Test suite documentation
- **[docs/implementation_notes/](docs/implementation_notes/README.md)** — Design decisions and patterns

### Adding New Extractors

The plugin architecture makes this simple: create a directory `benchmarkdown/extractors/{name}/` with three files (`__init__.py`, `config.py`, `extractor.py`). The UI discovers and integrates it automatically. See [CLAUDE.md](CLAUDE.md#adding-new-extractors) for details.

### Running Tests

```bash
uv run python tests/test_config_ui.py           # Configuration UI
uv run python tests/test_integrated_app.py      # Plugin integration
uv run python tests/test_redesigned_workflow.py  # Queue workflow
```

See [tests/README.md](tests/README.md) for the full test list.

## License

[Add license information]

## Contributing

[Add contribution guidelines]
