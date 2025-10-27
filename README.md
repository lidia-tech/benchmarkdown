# Benchmarkdown

A benchmark suite for comparing document-to-markdown extraction technologies with a user-friendly web interface.

## Features

- 🎯 **Multiple Extractors**: Compare Docling (local) and AWS Textract (cloud)
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
uv sync --all-groups  # Install all extractors
# OR
uv sync --group docling      # Local processing only
uv sync --group textract     # AWS Textract only
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

See [CONFIG_UI_README.md](CONFIG_UI_README.md) for detailed configuration guide.

## Project Structure

- `/benchmarkdown` - Core package with extractors and configuration
  - `docling.py` - Docling extractor implementation
  - `textract.py` - AWS Textract extractor implementation
  - `config.py` - Pydantic configuration models
  - `config_ui.py` - Automatic UI generation from models
  - `profile_manager.py` - Configuration profile persistence
  - `types.py` - Protocol definitions
  - `/ui` - Modular UI components
    - `core.py` - BenchmarkUI class and ExtractionResult dataclass
    - `results.py` - HTML generation for results display
    - `queue.py` - Task queue management (load/save/display)
    - `app_builder.py` - Main Gradio interface creation
- `/data` - Document storage (not versioned)
  - `input/` - Source documents organized by category
  - `raw_markdown/` - Initial extraction outputs
  - `clean_markdown/` - Processed outputs
- `/config` - Saved configuration profiles (JSON)
- `/notebooks` - Jupyter notebooks with examples
- `/tests` - Comprehensive test suite (see [tests/README.md](tests/README.md))
- `app.py` - Main application entry point
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

### AWS Textract Setup

```bash
export TEXTRACT_S3_WORKSPACE=s3://your-bucket-name/textract-workspace/
# Configure AWS credentials via ~/.aws/credentials or environment variables
```

### Environment Variables

Create `.env` from `.env.template` for additional configuration.

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

See [CLAUDE.md](CLAUDE.md#adding-new-extractors) for implementation guide.

## Architecture

- **Protocol-based design**: Loose coupling via `MarkdownExtractor` protocol
- **Pydantic configuration**: Type-safe, validated settings with field metadata
- **Automatic UI generation**: Gradio components generated from Pydantic fields
- **Profile management**: Save/load configurations as reusable named profiles
- **Task queue system**: Build extraction queue with multiple extractor configurations
- **Async processing**: Parallel document × extractor processing with `asyncio.gather()`
- **Modular UI**: Separated concerns (core logic, results, queue, app building)

## License

[Add license information]

## Contributing

[Add contribution guidelines]
