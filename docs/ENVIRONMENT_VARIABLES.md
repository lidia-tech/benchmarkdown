# Environment Variables

This document lists all environment variables that can be used to configure Benchmarkdown extractors.

## Authentication & Access

### TensorLake
- **`TENSORLAKE_API_KEY`** (required)
  API key for TensorLake Document Ingestion API
  Get your key at: https://cloud.tensorlake.ai/

### LlamaParse
- **`LLAMA_CLOUD_API_KEY`** (required)
  API key for LlamaIndex LlamaParse cloud service
  Get your key at: https://cloud.llamaindex.ai/

### AWS Textract
- **`TEXTRACT_S3_WORKSPACE`** (required)
  Full S3 URI for Textract workspace (e.g., `s3://bucket-name/textract-workspace/`)
  Also requires AWS credentials via standard AWS SDK methods (`~/.aws/credentials` or `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`)

### Azure Document Intelligence
- **`AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT`** (required)
  Azure endpoint URL for your Document Intelligence resource
  Format: `https://your-resource.cognitiveservices.azure.com/`
  Get from Azure Portal: https://portal.azure.com/

- **`AZURE_DOCUMENT_INTELLIGENCE_KEY`** (required)
  Azure API key for authentication
  Get from Azure Portal under your Document Intelligence resource → Keys and Endpoint

## System-Level Performance Settings

These environment variables control system-level settings like timeouts, worker counts, and verbosity. They are not exposed in the UI to keep it clean, but can be configured for advanced use cases.

### TensorLake System Settings

- **`TENSORLAKE_MAX_TIMEOUT`** (optional, default: `300`)
  Maximum timeout in seconds to wait for parsing to finish
  Valid range: 30-600 seconds
  Example: `export TENSORLAKE_MAX_TIMEOUT=600`

### LlamaParse System Settings

- **`LLAMAPARSE_NUM_WORKERS`** (optional, default: `4`)
  Number of workers for parallel page processing
  Valid range: 1-19
  Example: `export LLAMAPARSE_NUM_WORKERS=8`

- **`LLAMAPARSE_MAX_TIMEOUT`** (optional, default: `2000`)
  Maximum timeout in seconds to wait for parsing to finish
  Example: `export LLAMAPARSE_MAX_TIMEOUT=3000`

- **`LLAMAPARSE_VERBOSE`** (optional, default: `false`)
  Enable verbose logging
  Valid values: `true`, `false`, `1`, `0`, `yes`, `no`
  Example: `export LLAMAPARSE_VERBOSE=true`

- **`LLAMAPARSE_SHOW_PROGRESS`** (optional, default: `true`)
  Show progress when parsing multiple files
  Valid values: `true`, `false`, `1`, `0`, `yes`, `no`
  Example: `export LLAMAPARSE_SHOW_PROGRESS=false`

- **`LLAMAPARSE_IGNORE_ERRORS`** (optional, default: `false`)
  Whether to ignore and skip errors raised during parsing
  Valid values: `true`, `false`, `1`, `0`, `yes`, `no`
  Example: `export LLAMAPARSE_IGNORE_ERRORS=true`

### Docling System Settings

- **`DOCLING_NUM_THREADS`** (optional, default: CPU count)
  Number of CPU threads to use for processing
  Valid range: 1-32
  Example: `export DOCLING_NUM_THREADS=8`

- **`DOCLING_DOCUMENT_TIMEOUT`** (optional, default: None)
  Maximum processing time per document in seconds
  Minimum: 1.0
  Example: `export DOCLING_DOCUMENT_TIMEOUT=300.0`

## Usage Examples

### Quick Setup (Authentication Only)

```bash
# TensorLake
export TENSORLAKE_API_KEY="your-tensorlake-key"

# LlamaParse
export LLAMA_CLOUD_API_KEY="your-llamaparse-key"

# AWS Textract
export TEXTRACT_S3_WORKSPACE="s3://your-bucket/textract-workspace/"
export AWS_PROFILE="your-aws-profile"  # or use AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY

# Azure Document Intelligence
export AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="https://your-resource.cognitiveservices.azure.com/"
export AZURE_DOCUMENT_INTELLIGENCE_KEY="your-azure-key"
```

### Advanced Setup (With System Settings)

```bash
# TensorLake with increased timeout
export TENSORLAKE_API_KEY="your-tensorlake-key"
export TENSORLAKE_MAX_TIMEOUT=600

# LlamaParse with custom performance settings
export LLAMA_CLOUD_API_KEY="your-llamaparse-key"
export LLAMAPARSE_NUM_WORKERS=8
export LLAMAPARSE_MAX_TIMEOUT=3000
export LLAMAPARSE_VERBOSE=true

# Docling with custom thread count
export DOCLING_NUM_THREADS=16
export DOCLING_DOCUMENT_TIMEOUT=600.0
```

### Setting Environment Variables in .env File

You can also create a `.env` file in the project root:

```bash
# .env file
TENSORLAKE_API_KEY=your-tensorlake-key
TENSORLAKE_MAX_TIMEOUT=600

LLAMA_CLOUD_API_KEY=your-llamaparse-key
LLAMAPARSE_NUM_WORKERS=8
LLAMAPARSE_VERBOSE=true

TEXTRACT_S3_WORKSPACE=s3://your-bucket/textract-workspace/
AWS_PROFILE=your-aws-profile

AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=your-azure-key

DOCLING_NUM_THREADS=16
DOCLING_DOCUMENT_TIMEOUT=600.0
```

Then load it when running the app:

```bash
source .env
uv run python app.py
```

Or use python-dotenv (already included in dependencies):

```python
from dotenv import load_dotenv
load_dotenv()
```

## Notes

- System-level settings (timeouts, workers, verbosity) are **not exposed in the UI** to keep the interface clean and focused on extraction options
- Authentication variables are **required** for their respective extractors to be available
- All system settings have **sensible defaults** that work well for most use cases
- These settings are particularly useful for:
  - **CI/CD pipelines** where you need consistent behavior
  - **Large document processing** where you need longer timeouts
  - **High-performance servers** where you can increase worker counts
  - **Debugging** where verbose logging is helpful
