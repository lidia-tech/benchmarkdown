# Benchmarkdown

A benchmark suite for comparing document-to-markdown extraction technologies with a user-friendly web interface.

## Features

- 🎯 **Multiple Extractors**: Compare Docling (local) and AWS Textract (cloud)
- ⚙️ **Configurable**: UI-driven configuration with 15+ parameters per extractor
- 📊 **Side-by-Side Comparison**: Visual comparison of extraction results
- 🚀 **Batch Processing**: Process multiple documents with multiple extractors
- 📈 **Metrics**: Execution time, character/word counts, cost estimates
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

1. **Configure Extractor**: Select engine (Docling/Textract), name your config, adjust settings
2. **Add to Queue**: Click "Add to Extraction Queue" - see it appear in the list
3. **Upload Documents**: Add PDF/DOCX files
4. **Run Extraction**: Click "Run Extraction" - all queued extractors process your documents
5. **Compare Results**: View side-by-side or tabbed comparisons

See [CONFIG_UI_README.md](CONFIG_UI_README.md) for detailed configuration guide.

## Project Structure

- `/benchmarkdown` - Core package with extractors and configuration
  - `docling.py` - Docling extractor implementation
  - `textract.py` - AWS Textract extractor implementation
  - `config.py` - Pydantic configuration models
  - `config_ui.py` - Automatic UI generation from models
  - `ui.py` - BenchmarkUI core functionality
  - `types.py` - Protocol definitions
- `/data` - Document storage (not versioned)
  - `input/` - Source documents organized by category
  - `raw_markdown/` - Initial extraction outputs
  - `clean_markdown/` - Processed outputs
- `/notebooks` - Jupyter notebooks with examples
- `/tests` - Comprehensive test suite (see [tests/README.md](tests/README.md))
- `app.py` - Main web application
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
export TEXTRACT_S3_BUCKET=s3://your-bucket-name/textract-workspace/
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
- **Pydantic configuration**: Type-safe, validated settings
- **Automatic UI generation**: Gradio components from Pydantic fields
- **Async processing**: Parallel document extraction
- **Queue-based workflow**: Configure multiple extractors before running

## License

[Add license information]

## Contributing

[Add contribution guidelines]
