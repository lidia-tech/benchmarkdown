# Benchmarkdown Gradio UI

A web-based interface for comparing document-to-markdown extraction tools.

## Features

- **Multi-document batch processing** - Upload multiple PDFs/DOCX files at once
- **Multiple extractor support** - Compare Docling (local) and AWS Textract (cloud)
- **Flexible comparison views**:
  - Tabbed view - See full details for each extractor separately
  - Side-by-side view - Quick visual comparison across extractors
- **Rich metrics** - Execution time, character/word counts, cost estimates
- **Export options**:
  - Individual markdown downloads
  - Bulk ZIP download
  - HTML comparison report

## Installation

Install the required dependencies:

```bash
# Install with Docling (local processing)
uv sync --group docling

# Or install with AWS Textract (cloud processing)
uv sync --group textract

# Or install both
uv sync --all-groups
```

## Configuration

### For AWS Textract

Set your S3 workspace URI for Textract:

```bash
export TEXTRACT_S3_WORKSPACE=s3://your-bucket-name/textract-workspace/
```

Make sure you have AWS credentials configured (via `~/.aws/credentials` or environment variables).

## Running the UI

```bash
uv run python app.py
```

Or using the Python interpreter directly:

```bash
uv run python -m benchmarkdown.ui
```

The UI will be available at: http://localhost:7860

## Usage

1. **Upload Documents** - Click or drag-and-drop PDF/DOCX files
2. **Select Extractors** - Choose which extraction tools to test (all selected by default)
3. **Click "Extract All"** - Process all documents with selected extractors
4. **View Results**:
   - Results table shows metrics for each document/extractor combination
   - Select a document from the dropdown to view detailed comparison
   - Toggle between "Tabbed" and "Side-by-Side" view modes
5. **Download Results**:
   - Click "Download All (ZIP)" for bulk download
   - Click "Generate Report (HTML)" for a formatted comparison report

## Project Structure

```
benchmarkdown/
├── app.py                    # Main application entry point
├── benchmarkdown/
│   ├── ui.py                # Gradio UI implementation
│   ├── types.py             # MarkdownExtractor protocol
│   ├── docling.py           # Docling extractor
│   └── textract.py          # AWS Textract extractor
├── data/
│   └── input/               # Sample documents
└── pyproject.toml           # Dependencies
```

## Adding New Extractors

To add a new extraction tool:

1. Create a class implementing the `MarkdownExtractor` protocol:

```python
class MyExtractor:
    async def extract_markdown(self, filename: os.PathLike) -> str:
        # Your extraction logic here
        return markdown_text
```

2. Register it in `app.py`:

```python
extractors["My Extractor"] = {
    "instance": MyExtractor(),
    "cost_per_page": 0.10  # Optional cost estimate
}
```

## Future Features

- Ground truth comparison with quality metrics (BLEU score, edit distance, etc.)
- Individual file downloads from the UI
- Real-time progress updates during extraction
- Cost tracking and budget warnings
- Diff view for comparing extraction results
