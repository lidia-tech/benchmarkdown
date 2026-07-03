# Mistral OCR Extractor

Mistral's dedicated OCR endpoint (`/v1/ocr`, model `mistral-ocr-latest`). It
returns markdown directly, one entry per page, which this plugin concatenates
into a single markdown document.

## Features

- Cloud-based OCR powered by `mistral-ocr-latest`
- Markdown output per page, joined into one document
- Table output as markdown or HTML
- Optional header/footer extraction
- Page subset selection (numbers and ranges)
- Image extraction controls (base64, count limit, minimum size)

## Installation

```bash
uv sync --group mistral
```

## Getting Your API Key

1. Go to [console.mistral.ai](https://console.mistral.ai/) and create an account
2. Navigate to **API Keys**
3. Create a new key and copy it

## Environment Variables

### Required

- **`MISTRAL_API_KEY`** (required)
  - API key for the Mistral platform
  - Get your key at: [Mistral Console](https://console.mistral.ai/)

### Example Setup

```bash
export MISTRAL_API_KEY="your-mistral-key"
```

## Configuration Options

### Basic Options

- **Model**: OCR model to use (default `mistral-ocr-latest`)
- **Pages**: Specific pages to process as comma-separated numbers and ranges,
  0-based (e.g. `0,1,2` or `0-5` or `0,2-4`). Leave empty to process all pages.
- **Table Format**: `markdown` (recommended) or `html`
- **Extract Header**: Include page headers in the markdown output (default on)
- **Extract Footer**: Include page footers in the markdown output (default on)

### Advanced Options

- **Include Image Base64**: Return base64-encoded images of extracted figures
- **Image Limit**: Maximum number of images to extract (empty = no limit)
- **Image Min Size**: Minimum height/width in pixels for an image to be
  extracted (empty = no minimum)

## Usage

### Programmatic

```python
from benchmarkdown.extractors.mistral_ocr import Extractor, Config

config = Config(
    table_format="markdown",
    extract_header=True,
    extract_footer=False,
)
extractor = Extractor(config=config)
markdown = await extractor.extract_markdown("document.pdf")
```

### Via UI

1. Set `MISTRAL_API_KEY` (see above)
2. Launch the app: `uv run python app.py`
3. Select "Mistral OCR (Cloud)" from the engine dropdown
4. Configure options (or load a saved profile)
5. Add to the extraction queue
6. Upload documents and run extraction

## API Details

The extractor follows the standard Mistral OCR workflow for local files:

1. Upload the document via the Files API with `purpose="ocr"`
2. Request a signed URL for the uploaded file
3. Call `ocr.process` against that URL
4. Concatenate `pages[].markdown` into the final markdown string

The uploaded file is deleted afterwards as best-effort cleanup.

## Pricing

Mistral OCR is a paid cloud service billed per page. Check current pricing:
https://mistral.ai/pricing

## Resources

- [OCR Endpoint Docs](https://docs.mistral.ai/api/endpoint/ocr)
- [Mistral Console](https://console.mistral.ai/)
- [Python SDK](https://pypi.org/project/mistralai/)
