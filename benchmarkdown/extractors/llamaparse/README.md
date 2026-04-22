# LlamaParse Extractor

LlamaIndex's cloud-based document parsing service with advanced OCR and layout understanding.

## Features

- Cloud-based parsing (powered by LlamaIndex)
- Advanced OCR and layout analysis
- GPT-4o integration for complex documents
- Multi-language support
- Custom parsing instructions
- Page range selection
- Parallel processing

## Installation

```bash
uv sync --group llamaparse
```

## Getting Your API Key

1. Go to [cloud.llamaindex.ai](https://cloud.llamaindex.ai/) and sign up for a free account
2. Once logged in, go to **API Keys** in the left sidebar
3. Click **"Create new key"** and copy the key (starts with `llx-`)
4. A free tier is included — no credit card required to start

For GPT-4o enhanced mode (optional): get an OpenAI API key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys) (requires OpenAI account with billing enabled).

## Environment Variables

### Required

- **`LLAMA_CLOUD_API_KEY`** (required)
  - API key for LlamaIndex LlamaParse cloud service
  - Get your key at: [LlamaIndex Cloud](https://cloud.llamaindex.ai/)
  - Format: `llx-...`

### Optional (GPT-4o Mode)

- **`OPENAI_API_KEY`** (optional, for GPT-4o mode)
  - OpenAI API key for GPT-4o enhanced parsing
  - Get your key at: [OpenAI Platform](https://platform.openai.com/)
  - Format: `sk-...`

### Optional Performance Tuning

- **`LLAMAPARSE_NUM_WORKERS`** (optional, default: 4)
  - Number of workers for parallel page processing
  - Valid range: 1-19
  - Example: `export LLAMAPARSE_NUM_WORKERS=8`

- **`LLAMAPARSE_MAX_TIMEOUT`** (optional, default: 2000)
  - Maximum timeout in seconds to wait for parsing
  - Example: `export LLAMAPARSE_MAX_TIMEOUT=3000`

- **`LLAMAPARSE_VERBOSE`** (optional, default: false)
  - Enable verbose logging
  - Valid values: `true`, `false`, `1`, `0`, `yes`, `no`
  - Example: `export LLAMAPARSE_VERBOSE=true`

- **`LLAMAPARSE_SHOW_PROGRESS`** (optional, default: true)
  - Show progress when parsing multiple files
  - Valid values: `true`, `false`, `1`, `0`, `yes`, `no`
  - Example: `export LLAMAPARSE_SHOW_PROGRESS=false`

- **`LLAMAPARSE_IGNORE_ERRORS`** (optional, default: false)
  - Skip errors during parsing
  - Valid values: `true`, `false`, `1`, `0`, `yes`, `no`
  - Example: `export LLAMAPARSE_IGNORE_ERRORS=true`

### Example Setup

```bash
# Basic setup
export LLAMA_CLOUD_API_KEY="llx-your-key-here"

# With GPT-4o mode (optional)
export LLAMA_CLOUD_API_KEY="llx-your-key-here"
export OPENAI_API_KEY="sk-your-openai-key-here"

# With performance tuning
export LLAMA_CLOUD_API_KEY="llx-your-key-here"
export LLAMAPARSE_NUM_WORKERS=8
export LLAMAPARSE_MAX_TIMEOUT=3000
export LLAMAPARSE_VERBOSE=true
```

## Configuration Options

### Basic Options

- **Result Type**: Output format (markdown/text)
- **Language**: Document language (en, es, de, fr, etc.)
- **Parsing Instruction**: Custom instructions for the parser
  - Example: "Extract tables and preserve formatting"
  - Example: "Focus on financial data"

### Advanced Options

- **GPT-4o Mode**: Enable enhanced parsing with GPT-4o (requires OpenAI API key)
- **Skip Diagonal Text**: Skip text at non-standard angles
- **Invalidate Cache**: Force re-parsing (don't use cache)
- **Do Not Cache**: Don't cache this parsing result
- **Page Separator**: Custom separator between pages
- **Page Range**: Specify pages to parse (e.g., "1-5")

## Usage

### Programmatic

```python
from benchmarkdown.extractors.llamaparse import Extractor, Config

# Create configuration
config = Config(
    result_type="markdown",
    language="en",
    parsing_instruction="Extract all tables with headers",
    gpt4o_mode=True  # Optional: requires OPENAI_API_KEY
)

# Create extractor
extractor = Extractor(config=config)

# Extract markdown
markdown = await extractor.extract_markdown("document.pdf")
```

### Via UI

1. Set environment variables (see above)
2. Launch the app: `uv run python app.py`
3. Select "LlamaParse (Cloud)" from the engine dropdown
4. Configure options (or load a saved profile)
5. Add to extraction queue
6. Upload documents and run extraction

## Pricing

LlamaParse is a paid cloud service from LlamaIndex. Pricing includes:
- Free tier available for testing
- Per-page pricing for production use
- Additional costs for GPT-4o mode (OpenAI charges)

Check current pricing: https://cloud.llamaindex.ai/pricing

## Resources

- [Official Documentation](https://docs.llamaindex.ai/en/stable/llama_cloud/llama_parse/)
- [LlamaParse Homepage](https://www.llamaindex.ai/enterprise/llama-parse)
- [Cloud Platform](https://cloud.llamaindex.ai/)
- [Python SDK](https://github.com/run-llama/llama_parse)
