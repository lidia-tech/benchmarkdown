# TensorLake Extractor

TensorLake's cloud-based document parsing service powered by advanced AI models.

## Features

- Cloud-based parsing with TensorLake API
- Advanced OCR and layout analysis
- Table extraction (markdown/html output)
- Signature detection
- Figure and table summarization
- Strike-through text detection
- Multiple chunking strategies

## Installation

```bash
uv sync --group tensorlake
```

## Getting Your API Key

1. Go to [cloud.tensorlake.ai](https://cloud.tensorlake.ai/) and create an account
2. Once logged in, navigate to **API Keys**
3. Create a new key and copy it

## Environment Variables

### Required

- **`TENSORLAKE_API_KEY`** (required)
  - API key for TensorLake Document Ingestion API
  - Get your key at: [TensorLake Cloud](https://cloud.tensorlake.ai/)

### Optional Performance Tuning

- **`TENSORLAKE_MAX_TIMEOUT`** (optional, default: 300)
  - Maximum timeout in seconds to wait for parsing to finish
  - Valid range: 30-600 seconds
  - Example: `export TENSORLAKE_MAX_TIMEOUT=600`

### Example Setup

```bash
# Basic setup
export TENSORLAKE_API_KEY="your-tensorlake-key"

# With custom timeout
export TENSORLAKE_API_KEY="your-tensorlake-key"
export TENSORLAKE_MAX_TIMEOUT=600
```

## Configuration Options

### Basic Options

- **Chunking Strategy**: How to split the document
  - `section`: Split by document sections (preserves structure)
  - `page`: Split by pages (simpler, fixed-size chunks)

- **Table Output Mode**: Format for extracted tables
  - `markdown`: Tables in markdown format (recommended)
  - `html`: Tables in HTML format

- **Signature Detection**: Enable signature detection in documents

### Advanced Options

- **Figure Summarization**: Generate summaries for figures and images
- **Table Summarization**: Generate summaries for tables
- **Strike Through Detection**: Detect and mark strikethrough text
- **Max Timeout**: Maximum wait time for parsing (seconds)

## Usage

### Programmatic

```python
from benchmarkdown.extractors.tensorlake import Extractor, Config

# Create configuration
config = Config(
    chunking_strategy="section",
    table_output_mode="markdown",
    signature_detection=True,
    figure_summarization=True
)

# Create extractor
extractor = Extractor(config=config)

# Extract markdown
markdown = await extractor.extract_markdown("document.pdf")
```

### Via UI

1. Set environment variables (see above)
2. Launch the app: `uv run python app.py`
3. Select "TensorLake (Cloud)" from the engine dropdown
4. Configure options (or load a saved profile)
5. Add to extraction queue
6. Upload documents and run extraction

## API Details

TensorLake uses a read-analyze-wait workflow:
1. Upload document via `read()` API
2. Get content ID from response
3. Poll for completion with `wait_for_completion()`
4. Extract markdown from parsed results

The extractor handles this workflow automatically.

## Pricing

TensorLake is a paid cloud service. Pricing depends on:
- Number of documents processed
- Document complexity
- Features enabled (summarization, etc.)

Check current pricing: https://cloud.tensorlake.ai/pricing

## Resources

- [Official Documentation](https://docs.tensorlake.ai/)
- [Document Parsing Guide](https://docs.tensorlake.ai/document-ingestion/parsing/read)
- [Cloud Platform](https://cloud.tensorlake.ai/)
- [Python SDK](https://pypi.org/project/tensorlake/)
