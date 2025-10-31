# Environment Variables Reference

Quick reference for all environment variables used by Benchmarkdown extractors.

> **Note:** For detailed information about each extractor's configuration options, see the individual README files in `benchmarkdown/extractors/{extractor_name}/README.md`

## Quick Reference Table

| Variable | Extractor | Required? | Description |
|----------|-----------|-----------|-------------|
| **Authentication** |
| `TENSORLAKE_API_KEY` | TensorLake | ✅ Required | TensorLake API key ([Get key](https://cloud.tensorlake.ai/)) |
| `LLAMA_CLOUD_API_KEY` | LlamaParse | ✅ Required | LlamaIndex LlamaParse API key ([Get key](https://cloud.llamaindex.ai/)) |
| `OPENAI_API_KEY` | LlamaParse | ⚙️ Optional | OpenAI API key for GPT-4o enhanced parsing mode |
| `TEXTRACT_S3_WORKSPACE` | AWS Textract | ✅ Required | S3 URI for workspace (e.g., `s3://bucket/path/`) |
| `AWS_PROFILE` | AWS Textract | ⚙️ Optional | AWS CLI profile name (alternative to access keys) |
| `AWS_ACCESS_KEY_ID` | AWS Textract | ⚙️ Optional | AWS access key (alternative to profile) |
| `AWS_SECRET_ACCESS_KEY` | AWS Textract | ⚙️ Optional | AWS secret key (alternative to profile) |
| `AWS_DEFAULT_REGION` | AWS Textract | ⚙️ Optional | AWS region (default: from AWS config) |
| `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT` | Azure | ✅ Required | Azure endpoint URL ([Azure Portal](https://portal.azure.com/)) |
| `AZURE_DOCUMENT_INTELLIGENCE_KEY` | Azure | ✅ Required | Azure API key |
| **Application Settings** |
| `BENCHMARKDOWN_LOG_LEVEL` | Application | ⚙️ Optional | Logging verbosity: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: WARNING) |
| **Performance Tuning** |
| `DOCLING_NUM_THREADS` | Docling | ⚙️ Optional | CPU threads (default: CPU count, range: 1-32) |
| `DOCLING_DOCUMENT_TIMEOUT` | Docling | ⚙️ Optional | Processing timeout in seconds (default: None, min: 1.0) |
| `TENSORLAKE_MAX_TIMEOUT` | TensorLake | ⚙️ Optional | API timeout in seconds (default: 300, range: 30-600) |
| `LLAMAPARSE_NUM_WORKERS` | LlamaParse | ⚙️ Optional | Parallel workers (default: 4, range: 1-19) |
| `LLAMAPARSE_MAX_TIMEOUT` | LlamaParse | ⚙️ Optional | API timeout in seconds (default: 2000) |
| `LLAMAPARSE_VERBOSE` | LlamaParse | ⚙️ Optional | Enable verbose logging (default: false) |
| `LLAMAPARSE_SHOW_PROGRESS` | LlamaParse | ⚙️ Optional | Show progress bars (default: true) |
| `LLAMAPARSE_IGNORE_ERRORS` | LlamaParse | ⚙️ Optional | Skip parsing errors (default: false) |

## Setup Instructions

### Using .env File (Recommended)

1. Copy `.env.template` to `.env`:
   ```bash
   cp .env.template .env
   ```

2. Edit `.env` and fill in credentials for the extractors you want to use

3. The app automatically loads `.env` on startup (via python-dotenv)

### Using Shell Export

```bash
# Example: Set up LlamaParse
export LLAMA_CLOUD_API_KEY="llx-your-key-here"
export LLAMAPARSE_NUM_WORKERS=8

# Then run the app
uv run python app.py
```

## Extractor Availability

Extractors only appear in the UI if their required environment variables are set:

- ✅ **Docling**: Always available (no credentials needed, runs locally)
- ✅ **AWS Textract**: Available when `TEXTRACT_S3_WORKSPACE` and AWS credentials are set
- ✅ **LlamaParse**: Available when `LLAMA_CLOUD_API_KEY` is set
- ✅ **TensorLake**: Available when `TENSORLAKE_API_KEY` is set
- ✅ **Azure Document Intelligence**: Available when both `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT` and `AZURE_DOCUMENT_INTELLIGENCE_KEY` are set

## Logging Configuration

**`BENCHMARKDOWN_LOG_LEVEL`** controls the verbosity of operational logs:

- **`DEBUG`**: Very detailed logs including internal state and API calls
- **`INFO`**: Plugin discovery, extractor availability, extraction start/completion with timing and job IDs
- **`WARNING`** (default): Only warnings and errors (clean output)
- **`ERROR`**: Only error messages
- **`CRITICAL`**: Only critical failures

**Examples:**
```bash
# Default: minimal logging (WARNING level - clean output)
uv run python app.py

# Enable info logs to see plugin discovery and extraction progress
BENCHMARKDOWN_LOG_LEVEL=INFO uv run python app.py

# Debug mode for troubleshooting
BENCHMARKDOWN_LOG_LEVEL=DEBUG uv run python app.py
```

**What you'll see at INFO level:**
- `✓ Docling (Local) extractor available`
- `⚠️  AWS Textract not available: TEXTRACT_S3_WORKSPACE environment variable not configured`
- `🔍 Discovering extractor plugins...`
- `[Extractor] Starting extraction: filename.pdf`
- `[Extractor] Completed extraction: filename.pdf (duration: 2.34s)`

**Tip:** Use `INFO` level during development to see what's happening. Use `WARNING` (default) in production for clean output.

## Performance Tuning Guide

**When to adjust performance settings:**

- 🚀 **High-volume processing**: Increase workers (`LLAMAPARSE_NUM_WORKERS`) for parallel processing
- ⏱️ **Large documents**: Increase timeouts (`*_MAX_TIMEOUT`, `DOCLING_DOCUMENT_TIMEOUT`)
- 🖥️ **Server deployment**: Set `DOCLING_NUM_THREADS` to match available CPU cores
- 🐛 **Debugging**: Set `BENCHMARKDOWN_LOG_LEVEL=INFO` or `DEBUG` for detailed operational logs
- 🔄 **CI/CD pipelines**: Set explicit timeouts and disable progress bars

**Default settings work well for most use cases.**

## Cost Considerations

| Extractor | Cost | Notes |
|-----------|------|-------|
| Docling | 💚 Free | Open-source, runs locally |
| AWS Textract | 💰 Paid | Per-page pricing ([pricing](https://aws.amazon.com/textract/pricing/)) |
| LlamaParse | 💰 Paid | Free tier available ([pricing](https://cloud.llamaindex.ai/pricing)) |
| TensorLake | 💰 Paid | Contact for pricing ([website](https://cloud.tensorlake.ai/)) |
| Azure Document Intelligence | 💰 Paid | Per-page pricing ([pricing](https://azure.microsoft.com/pricing/details/form-recognizer/)) |

## See Also

- **Detailed setup**: See individual extractor READMEs in `benchmarkdown/extractors/{extractor_name}/README.md`
- **Template file**: See `.env.template` for a complete example with all variables
- **User guide**: See `CONFIG_UI_README.md` for UI configuration instructions
