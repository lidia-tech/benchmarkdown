# Benchmarkdown

A benchmark suite for comparing document-to-markdown extraction technologies with a user-friendly web interface.

## Features

- 🎯 **Multiple Extractors**: Compare Docling (local), AWS Textract, TensorLake, and LlamaParse (cloud)
- 🔌 **Plugin Architecture**: Add new extractors by simply creating a directory—no code changes needed
- ⚙️ **Configurable**: UI-driven configuration with 15+ parameters per extractor
- 📊 **Side-by-Side Comparison**: Visual comparison of extraction results
- 🚀 **Batch Processing**: Process multiple documents with multiple extractors
- 📈 **Metrics**: Execution time, character/word counts
- 💾 **Export**: Download results as ZIP or HTML comparison report

## Quick Start

### Installation

1. [Install uv](https://github.com/astral-sh/uv) (recommended)
2. Clone and setup:
```bash
git clone <repository-url>
cd benchmarkdown
uv sync --all-groups         # Install all extractors
# OR install specific extractors:
uv sync --group docling      # Local processing with Docling
uv sync --group textract     # AWS Textract cloud service
uv sync --group tensorlake   # TensorLake cloud service
uv sync --group llamaparse   # LlamaParse cloud service
```

### Launch the Web UI

```bash
uv run python app.py
```

Open http://localhost:7860 in your browser.

### Using the Interface

1. **Add Task**: Click "➕ Add Task" to open the task editor
2. **Select Engine**: Choose Docling or AWS Textract
3. **Select/Create Profile**: Load an existing configuration profile or create a new one
4. **Configure Settings**: Adjust extractor parameters (OCR, tables, etc.)
5. **Save & Add to Queue**: Profile is saved and task is added to extraction queue
6. **Launch Extraction**: Click "🚀 Launch Extraction" when ready
7. **Upload Documents**: Add PDF/DOCX files to process
8. **Run & Compare**: Process documents and view side-by-side or tabbed comparisons

See [CONFIG_UI_README.md](CONFIG_UI_README.md) for detailed configuration guide and [docs/ENVIRONMENT_VARIABLES.md](docs/ENVIRONMENT_VARIABLES.md) for system-level settings.

## Project Structure

- `/benchmarkdown` - Core package with extractors and configuration
  - `/extractors` - **Plugin-based extractor architecture**
    - `base.py` - Protocol definitions
    - `__init__.py` - ExtractorRegistry with automatic discovery
    - `/docling` - Docling extractor plugin (local)
    - `/textract` - AWS Textract extractor plugin (cloud)
    - `/tensorlake` - TensorLake extractor plugin (cloud)
    - `/llamaparse` - LlamaParse extractor plugin (cloud)
  - `config.py` - Re-exports from plugins (backward compatibility)
  - `config_ui.py` - Automatic UI generation from Pydantic models
  - `profile_manager.py` - Configuration profile persistence
  - `types.py` - Protocol definitions
  - `/ui` - Modular UI components
    - `core.py` - BenchmarkUI class and ExtractionResult dataclass
    - `results.py` - HTML generation for results display
    - `queue.py` - Task queue management (load/save/display)
    - `dynamic_config.py` - Dynamic UI generation from plugin metadata
    - `app_builder.py` - Main Gradio interface creation
- `/data` - Document storage (not versioned)
  - `input/` - Source documents organized by category
  - `raw_markdown/` - Initial extraction outputs
  - `clean_markdown/` - Processed outputs
- `/config` - Saved configuration profiles (JSON)
- `/docs` - Additional documentation
  - `/archive` - Historical implementation documentation
- `/notebooks` - Jupyter notebooks with examples
- `/tests` - Comprehensive test suite (see [tests/README.md](tests/README.md))
- `app.py` - Main application entry point (extractor discovery + launch)
- `.task_queue.json` - Persisted task queue
- `CLAUDE.md` - Developer guide and architecture docs

## Testing

Run the full test suite:
```bash
# Quick tests (no app required)
uv run python tests/test_config_ui.py
uv run python tests/test_config_extraction.py
uv run python tests/test_integrated_app.py

# API tests (requires running app)
uv run python app.py &
sleep 5
uv run python tests/test_workflow_api.py
```

See [tests/README.md](tests/README.md) for detailed test documentation.

## Configuration

### Extractor Authentication

Each cloud-based extractor requires its own API key or credentials:

```bash
# TensorLake (required for TensorLake extractor)
export TENSORLAKE_API_KEY="your-tensorlake-api-key"

# LlamaParse (required for LlamaParse extractor)
export LLAMA_CLOUD_API_KEY="your-llamaparse-api-key"

# AWS Textract (required for Textract extractor)
export TEXTRACT_S3_WORKSPACE="s3://your-bucket-name/textract-workspace/"
# Configure AWS credentials via ~/.aws/credentials or environment variables
```

### System-Level Settings

Optional environment variables for advanced performance tuning (timeouts, worker counts, etc.):

```bash
# Logging (controls operational log verbosity)
export BENCHMARKDOWN_LOG_LEVEL=WARNING  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# TensorLake
export TENSORLAKE_MAX_TIMEOUT=600  # seconds

# LlamaParse
export LLAMAPARSE_NUM_WORKERS=8
export LLAMAPARSE_MAX_TIMEOUT=3000  # seconds

# Docling
export DOCLING_NUM_THREADS=16
export DOCLING_DOCUMENT_TIMEOUT=600.0  # seconds
```

See [docs/ENVIRONMENT_VARIABLES.md](docs/ENVIRONMENT_VARIABLES.md) for complete documentation of all environment variables.

## Documentation

- **[CONFIG_UI_README.md](CONFIG_UI_README.md)** - User guide for configuration UI
- **[CLAUDE.md](CLAUDE.md)** - Architecture and development guide
- **[tests/README.md](tests/README.md)** - Testing documentation

## Development

### Using Notebooks

```bash
uv sync --all-groups
# Set kernel to .venv/bin/python in your notebook environment
jupyter notebook notebooks/
```

### Adding New Extractors

The plugin architecture makes adding new extractors simple:

1. Create `benchmarkdown/extractors/{name}/` directory with:
   - `config.py` - Pydantic config model with `BASIC_FIELDS`, `ADVANCED_FIELDS`
   - `extractor.py` - Class implementing `MarkdownExtractor` protocol
   - `__init__.py` - Standard exports: `Extractor`, `Config`, fields, metadata, `is_available()`

2. **Done!** The UI automatically discovers and integrates it. No code changes needed!

See [CLAUDE.md](CLAUDE.md#adding-new-extractors) for detailed implementation guide.

## Architecture

- **Plugin-based extractors**: Automatic discovery, zero-code integration for new extractors
- **Protocol-based design**: Loose coupling via `MarkdownExtractor` protocol
- **ExtractorRegistry**: Validates plugins, checks dependencies, manages instances
- **Dynamic UI generation**: Gradio components generated from plugin metadata at runtime
- **Nested configuration support**: Complex configs like OCR engines handled automatically
- **Pydantic configuration**: Type-safe, validated settings with field metadata
- **Profile management**: Save/load configurations as reusable named profiles
- **Task queue system**: Build extraction queue with multiple extractor configurations
- **Async processing**: Parallel document × extractor processing with `asyncio.gather()`
- **Modular UI**: Separated concerns (core logic, results, queue, dynamic config, app building)

## License

[Add license information]

## Contributing

[Add contribution guidelines]
