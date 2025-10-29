# Azure Document Intelligence Extractor

Microsoft's cloud-based document processing service with native markdown output support.

## Features

- Multiple pre-built models (layout, read, document)
- Native markdown output (no conversion needed)
- Page range selection
- Locale hints for better accuracy
- OCR for scanned documents
- Table and form extraction

## Installation

```bash
uv sync --group azure-document-intelligence
```

## Environment Variables

### Required

- **`AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT`** (required)
  - Azure endpoint URL for your Document Intelligence resource
  - Format: `https://your-resource.cognitiveservices.azure.com/`
  - Get from: [Azure Portal](https://portal.azure.com/) → Your Document Intelligence resource → Overview

- **`AZURE_DOCUMENT_INTELLIGENCE_KEY`** (required)
  - Azure API key for authentication
  - Get from: [Azure Portal](https://portal.azure.com/) → Your Document Intelligence resource → Keys and Endpoint

### Example Setup

```bash
export AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="https://your-resource.cognitiveservices.azure.com/"
export AZURE_DOCUMENT_INTELLIGENCE_KEY="your-api-key-here"
```

## Configuration Options

### Basic Options

- **Model ID**: Choose extraction model
  - `prebuilt-layout`: Full document structure with tables, forms, and layout
  - `prebuilt-read`: OCR-focused, text extraction only
  - `prebuilt-document`: General document analysis

- **Output Format**: Choose output type
  - `markdown`: Structured markdown (recommended)
  - `text`: Plain text only

### Advanced Options

- **Pages**: Specify page range (e.g., "1-5", "1,3,5-7")
- **Locale**: Document language hint (e.g., "en-US", "it-IT", "de-DE")

## Usage

### Programmatic

```python
from benchmarkdown.extractors.azure_document_intelligence import Extractor, Config

# Create configuration
config = Config(
    model_id="prebuilt-layout",
    output_content_format="markdown",
    pages="1-10",
    locale="en-US"
)

# Create extractor
extractor = Extractor(config=config)

# Extract markdown
markdown = await extractor.extract_markdown("document.pdf")
```

### Via UI

1. Launch the app: `uv run python app.py`
2. Select "Azure Document Intelligence" from the engine dropdown
3. Configure options (or load a saved profile)
4. Add to extraction queue
5. Upload documents and run extraction

## Pricing

Azure Document Intelligence is a paid cloud service. Pricing depends on:
- Model type (Read, Layout, Document)
- Number of pages processed
- Request volume

Check current pricing: https://azure.microsoft.com/en-us/pricing/details/form-recognizer/

## Resources

- [Official Documentation](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/)
- [Python SDK](https://learn.microsoft.com/en-us/python/api/overview/azure/ai-documentintelligence-readme)
- [Azure Portal](https://portal.azure.com/)
