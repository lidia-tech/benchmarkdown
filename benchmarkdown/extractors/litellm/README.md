# LiteLLM Vision Extractor

Multi-modal LLM-based document extraction using vision-capable models via the LiteLLM framework.

## Overview

The LiteLLM extractor converts PDF pages to images and uses vision-capable Large Language Models to extract text. It supports multiple AI providers through the [LiteLLM](https://github.com/BerriAI/litellm) framework, including:

- **OpenAI**: GPT-4o, GPT-4o-mini, GPT-4-turbo
- **Anthropic**: Claude 3.5 Sonnet, Claude 3.5 Haiku, Claude 3 Opus/Sonnet/Haiku
- **Google**: Gemini 1.5 Pro, Gemini 1.5 Flash, Gemini 2.0 Flash
- **AWS Bedrock**: Claude, Llama, Stable Diffusion models via AWS
- **Azure OpenAI**: GPT-4o, GPT-4-turbo via Azure
- **Local models**: Ollama, vLLM, LM Studio (no API keys needed)
- **Custom models**: Any vision-capable model supported by LiteLLM

## Installation

Install the LiteLLM extractor dependencies:

```bash
uv sync --group litellm
```

This installs:
- `litellm`: Multi-provider LLM framework
- `pymupdf`: PDF rendering library (also used by Docling)

## Authentication

LiteLLM supports many providers with different authentication mechanisms. Configure the appropriate credentials for your chosen provider:

### OpenAI
Sign up at [platform.openai.com](https://platform.openai.com/) and create an API key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys). Billing must be enabled.
```bash
export OPENAI_API_KEY="sk-..."
```

### Anthropic
Sign up at [console.anthropic.com](https://console.anthropic.com/) and create an API key under Settings → API Keys. Billing must be enabled.
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Google Gemini
Get an API key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey) (free tier available with usage limits).
```bash
export GEMINI_API_KEY="..."
```

### AWS Bedrock
Requires an AWS account with Bedrock model access enabled. Go to the [Bedrock Console](https://console.aws.amazon.com/bedrock/) → Model access → Request access to the models you want to use. Uses standard AWS credentials (see [Textract README](../textract/README.md#getting-your-credentials) for AWS setup).
```bash
# Uses standard AWS credentials (IAM, ~/.aws/credentials, etc.)
# Ensure you have bedrock:InvokeModel and bedrock:Converse permissions
export AWS_REGION="us-east-1"  # Optional, defaults to us-east-1

# Verify model availability in your region:
# aws bedrock list-foundation-models --region us-east-1
```

**Important**: For vision models, use the `bedrock/converse/` prefix (e.g., `bedrock/converse/us.anthropic.claude-3-5-sonnet-20241022-v2:0`) instead of just `bedrock/` to ensure proper image support.

### Azure OpenAI
Requires an Azure account with an OpenAI resource deployed. See [Azure OpenAI quickstart](https://learn.microsoft.com/en-us/azure/ai-services/openai/quickstart) for setup instructions.
```bash
export AZURE_API_KEY="..."
export AZURE_API_BASE="https://your-resource.openai.azure.com"
export AZURE_API_VERSION="2024-02-15-preview"
```

### Local Models (Ollama, vLLM, LM Studio)
```bash
# No authentication required - just point to your local endpoint
# Configure the model name in the UI as: ollama/llava or vllm/llava-v1.6
```

**Note**: The extractor is available as long as dependencies are installed. Authentication is validated at runtime when you extract documents.

## Configuration Options

### Basic Options

- **model**: LiteLLM model identifier (text field)
  - Default: `gpt-4o-mini`
  - Enter any vision-capable model supported by LiteLLM
  - **OpenAI**: `gpt-4o-mini`, `gpt-4o`, `gpt-4-turbo`
  - **Anthropic**: `claude-3-5-sonnet-20241022`, `claude-3-5-haiku-20241022`
  - **Google**: `gemini-1.5-flash`, `gemini-1.5-pro`, `gemini-2.0-flash-exp`
  - **AWS Bedrock** (use `bedrock/converse/` prefix for vision models):
    - `bedrock/converse/global.anthropic.claude-sonnet-4-5-20250929-v1:0`
    - `bedrock/converse/us.anthropic.claude-3-5-sonnet-20241022-v2:0`
    - `bedrock/converse/us.amazon.nova-pro-v1:0`
    - `bedrock/converse/mistral.pixtral-large-latest`
    - `bedrock/converse/qwen.qwen3-vl-235b-a22b` (if available in your region)
  - **Azure**: `azure/my-gpt4o-deployment`
  - **Local**: `ollama/llava`, `vllm/llava-v1.6`
  - See [LiteLLM docs](https://docs.litellm.ai/docs/providers) for complete provider list

- **dpi**: DPI for page rendering (72-600)
  - Default: 300
  - Higher = better quality but slower and more expensive
  - 150-200 suitable for clean text documents
  - 300+ recommended for dense text or complex layouts

- **extraction_prompt**: Instruction prompt for the LLM
  - Default: "Extract all text from this document page. Preserve the exact layout, formatting, and structure..."
  - Customize to guide extraction behavior
  - Examples:
    - `"Extract text and tables in markdown format"`
    - `"Extract only the main body text, ignore headers and footers"`
    - `"Extract text preserving original language and special characters"`

- **page_separator**: Separator between pages in output
  - Default: `"\n\n---\n\n"`

### Advanced Options

- **max_tokens**: Maximum tokens for each LLM response (256-32000, default: 4096)
  - Increase for pages with very dense text
  - Decrease to control costs

- **temperature**: Sampling temperature (0.0-2.0, default: 0.0)
  - 0.0 = deterministic, consistent results
  - Higher values = more creative but less consistent

- **image_quality**: Image quality for vision API ('low', 'high', 'auto')
  - Default: 'high'
  - 'low' is faster and cheaper but less accurate
  - 'high' provides better accuracy for complex layouts

- **max_retries**: Maximum retries for failed API calls (0-10, default: 3)

- **timeout**: Timeout in seconds for each API call (10-600, default: 120)

- **concurrent_pages**: Number of pages to process concurrently (1-10, default: 1)
  - **Warning**: Be careful with rate limits when increasing this
  - Setting > 1 can speed up multi-page documents
  - Monitor API costs and rate limits

- **batch_size**: Number of pages per API call (1-20, default: 1)
  - **1** = One API call per page (current behavior, most reliable)
  - **2-20** = Batch multiple pages into single API call (reduces costs and API calls)
  - **Cost savings**: batch_size=5 → 5x fewer API calls
  - **Context benefit**: LLM can see multiple pages together (useful for tables/lists spanning pages)
  - **Max 20 images** for AWS Bedrock Converse API
  - **Trade-off**: Larger batches use more tokens per call and may hit context limits
  - **Important**: Set appropriate batch size for your use case - no automatic fallback if batch fails

## Usage Examples

### Python API

```python
from benchmarkdown.extractors.litellm import Extractor, Config

# Default configuration (GPT-4o-mini)
config = Config()
extractor = Extractor(config=config)

# Extract from a PDF file
markdown = await extractor.extract_markdown("document.pdf")
```

### Custom Configuration

```python
from benchmarkdown.extractors.litellm import Extractor, Config

# High-quality extraction with Claude
config = Config(
    model="claude-3-5-sonnet-20241022",
    dpi=300,
    extraction_prompt="Extract all text preserving exact formatting. Include tables in markdown format.",
    temperature=0.0,
    concurrent_pages=2,  # Process 2 batches at once
    batch_size=5          # Send 5 pages per API call (reduces costs 5x)
)
extractor = Extractor(config=config)
markdown = await extractor.extract_markdown("document.pdf")
```

### Batched Processing (Cost Optimization)

```python
from benchmarkdown.extractors.litellm import Extractor, Config

# Process 10 pages per API call to reduce costs
config = Config(
    model="bedrock/converse/global.anthropic.claude-sonnet-4-5-20250929-v1:0",
    dpi=300,
    batch_size=10,        # 10 pages per API call = 10x cost reduction
    concurrent_pages=2,   # Process 2 batches in parallel = 20 pages at once
    max_tokens=8000       # Increase tokens to handle multiple pages
)
extractor = Extractor(config=config)

# For a 100-page document:
# - Without batching: 100 API calls
# - With batch_size=10: 10 API calls (90% cost reduction!)
markdown = await extractor.extract_markdown("large_document.pdf")
```

### Cost-Optimized Configuration

```python
# Fast and cheap with GPT-4o-mini
config = Config(
    model="gpt-4o-mini",
    dpi=150,  # Lower DPI for clean documents
    max_tokens=2048,  # Limit token usage
    image_quality="low"
)
```

### AWS Bedrock Configuration

```python
# Using Claude Sonnet 4.5 via AWS Bedrock (requires AWS credentials)
# IMPORTANT: Use bedrock/converse/ prefix for vision models
config = Config(
    model="bedrock/converse/global.anthropic.claude-sonnet-4-5-20250929-v1:0",
    dpi=300,
    extraction_prompt="Extract all text from this document page in markdown format.",
    temperature=0.0
)
extractor = Extractor(config=config)
markdown = await extractor.extract_markdown("document.pdf")
```

**Common Bedrock vision models**:
- Claude Sonnet 4.5: `bedrock/converse/global.anthropic.claude-sonnet-4-5-20250929-v1:0`
- Claude 3.5 Sonnet: `bedrock/converse/us.anthropic.claude-3-5-sonnet-20241022-v2:0`
- Amazon Nova Pro: `bedrock/converse/us.amazon.nova-pro-v1:0`
- Mistral Pixtral: `bedrock/converse/mistral.pixtral-large-latest`
- Qwen VL: `bedrock/converse/qwen.qwen3-vl-235b-a22b` (check regional availability)

### Local Model Configuration

```python
# Using local Ollama model (no API key needed)
config = Config(
    model="ollama/llava",
    dpi=200,
    extraction_prompt="Extract the text from this image."
)
extractor = Extractor(config=config)
markdown = await extractor.extract_markdown("document.pdf")
```

### Web UI

The LiteLLM extractor integrates automatically with the Gradio UI:

1. Launch the app: `uv run python app.py`
2. Select "LiteLLM Vision (Multi-Provider)" from the engine dropdown
3. Configure model, DPI, and extraction prompt
4. Create/load a profile
5. Add to queue and extract

## How It Works

### Single-Page Mode (batch_size=1, default)

1. **Page Rendering**: Each PDF page is rendered to a PNG image at the specified DPI using PyMuPDF
2. **Image Encoding**: Images are encoded to base64 for transmission to the LLM
3. **Vision API Call**: One image and extraction prompt are sent per API call
4. **Text Extraction**: The LLM analyzes the image and extracts text in markdown format
5. **Combination**: Results from all pages are combined with the specified separator

### Batched Mode (batch_size>1)

1. **Batch Creation**: Pages are grouped into batches (e.g., batch_size=5 → groups of 5 pages)
2. **Page Rendering**: All pages in the batch are rendered to PNG images
3. **Multi-Image API Call**: All images are sent in a single API call with modified prompt
4. **LLM Instructions**: Prompt instructs the LLM to label each page (e.g., "=== PAGE 1 ===", "=== PAGE 2 ===")
5. **Response Parsing**: Response is split by page markers to extract individual page results
6. **Combination**: All page results are combined with the specified separator

**Batching Benefits**:
- **Cost reduction**: N pages with batch_size=N → 1 API call instead of N calls
- **Cross-page context**: LLM can see relationships between pages (useful for tables, lists)
- **Fewer API calls**: Reduces rate limit pressure

**Batching Considerations**:
- **Token usage**: Larger batches consume more tokens per call
- **Context limits**: Very large batches may exceed model context windows
- **Error handling**: If a batch fails, all pages in that batch fail (user sets appropriate batch_size)
- **Parsing reliability**: Depends on LLM following page marker instructions

## Cost Considerations

Vision API calls are typically more expensive than standard text extraction:

- **GPT-4o-mini**: ~$0.002-0.005 per page (depending on DPI)
- **GPT-4o**: ~$0.01-0.03 per page
- **Claude 3.5 Haiku**: ~$0.001-0.003 per page
- **Claude 3.5 Sonnet**: ~$0.01-0.02 per page
- **Gemini 1.5 Flash**: ~$0.001-0.002 per page

Costs vary based on:
- Image resolution (DPI)
- Page complexity
- Response length (max_tokens)
- Image quality setting

**Tips to reduce costs:**
- **Use batching**: Set batch_size=5-10 to reduce API calls by 5-10x
- Use lower DPI (150-200) for clean text documents
- Choose cheaper models (gpt-4o-mini, claude-3-5-haiku, gemini-1.5-flash)
- Set appropriate max_tokens limits
- Use 'low' image quality for simple documents
- Combine batching with concurrent_pages for maximum throughput

## When to Use This Extractor

**Best for:**
- Scanned documents with complex layouts
- Documents with mixed languages or special characters
- Cases where traditional OCR struggles
- Documents requiring semantic understanding of content
- When you need the highest possible accuracy

**Not ideal for:**
- Large batch processing (expensive)
- Digital PDFs with embedded text (use Docling or native extraction instead)
- Time-sensitive applications (slower than specialized extractors)
- Budget-constrained projects

## Comparison with Other Extractors

- **vs Docling**: Slower and more expensive, but may handle complex layouts better
- **vs Textract**: More flexible model choice, comparable accuracy, similar costs
- **vs LlamaParse**: More control over model and prompt, similar approach
- **vs Azure Document Intelligence**: More model options, typically lower cost per page

## Troubleshooting

### Extractor Not Available in UI

Check that:
1. Dependencies are installed: `uv sync --group litellm`
2. Restart the app after installing dependencies

### API Authentication Errors

Authentication errors occur at runtime when extracting documents:

- **OpenAI**: Verify `OPENAI_API_KEY` is set correctly
- **Anthropic**: Verify `ANTHROPIC_API_KEY` starts with "sk-ant-"
- **Google**: Verify `GEMINI_API_KEY` is valid
- **AWS Bedrock**:
  - Verify AWS credentials are configured (`~/.aws/credentials` or IAM role)
  - Ensure you have `bedrock:InvokeModel` and `bedrock:Converse` permissions
  - Check that the model is available in your region
  - For vision models, use `bedrock/converse/` prefix (see Bedrock Validation Errors below)
- **Azure OpenAI**:
  - Verify `AZURE_API_KEY`, `AZURE_API_BASE`, and `AZURE_API_VERSION` are set
  - Check that your deployment name matches the model identifier
- **Local models**:
  - Verify the local endpoint is running and accessible
  - Use correct model format (e.g., `ollama/llava`, `vllm/llava-v1.6`)

### AWS Bedrock Validation Errors

If you get errors like:
```
BedrockException - "unknown variant `prompt`", "validation_error"
```

**Cause**: You're using the legacy InvokeModel API (`bedrock/<model-id>`) instead of the Converse API.

**Solution**: Add `/converse/` to the model identifier:
- ❌ Wrong: `bedrock/qwen.qwen3-vl-235b-a22b`
- ✅ Correct: `bedrock/converse/qwen.qwen3-vl-235b-a22b`

**Why**: LiteLLM has two routing modes for Bedrock:
- `bedrock/<model-id>` → InvokeModel API (legacy, provider-specific formats)
- `bedrock/converse/<model-id>` → Converse API (modern, unified interface for vision)

The Converse API provides:
- Better vision support and feature detection
- Consistent interface across all model providers
- Support for up to 20 images per request
- JSON tool calling (vs XML in legacy API)

**Checking model availability**:
```bash
# List all available models in your region
aws bedrock list-foundation-models --region us-east-1

# List only vision-capable models
aws bedrock list-foundation-models --region us-east-1 \
  --query 'modelSummaries[?contains(modelName, `vision`) || contains(modelName, `VL`)].modelId'
```

**Note**: Not all Bedrock models support the Converse API. If a model still fails with the `/converse/` prefix, it may:
- Only support the legacy InvokeModel API
- Not support vision/multimodal inputs
- Not be available in your AWS region

Try using well-supported vision models like Claude, Amazon Nova, or Mistral Pixtral instead.

### Rate Limit Errors

- Decrease `concurrent_pages` to 1
- Add delays between API calls
- Upgrade your API plan
- Switch to a different provider

### Poor Quality Results

- Increase `dpi` (try 300-400)
- Use 'high' for `image_quality`
- Choose a more capable model (claude-3-5-sonnet, gpt-4o)
- Refine the `extraction_prompt` with more specific instructions

### Timeout Errors

- Increase `timeout` value
- Decrease `dpi` to speed up processing
- Use a faster model (gpt-4o-mini, claude-3-5-haiku)

### Batching Issues

**Problem**: Pages are missing or duplicated in output

**Solutions**:
- Check logs for parsing warnings: `"Expected N page sections, got M"`
- LLM may not be following page marker instructions consistently
- Try reducing `batch_size` (e.g., from 10 to 5)
- Use more explicit extraction prompt
- Consider using single-page mode (`batch_size=1`) for critical documents

**Problem**: Hitting token/context limits with batching

**Solutions**:
- Reduce `batch_size` (fewer pages per call)
- Reduce `dpi` (smaller images = fewer tokens)
- Increase `max_tokens` to accommodate larger responses
- Use models with larger context windows

**Problem**: Batch fails but individual pages work

**Solutions**:
- Reduce `batch_size` to find the working limit
- Some models have stricter image count limits
- Check provider documentation for multi-image limits

## Logging and Debugging

The LiteLLM extractor provides comprehensive logging for troubleshooting, optimization, and cost tracking.

### Logging Levels

The extractor uses Python's standard `logging` module with four levels:

**INFO** (default):
- Extraction start/complete with summary
- Batch/page processing progress
- Key configuration (model, DPI, batch_size)

**DEBUG** (enable for detailed telemetry):
- Image rendering details (dimensions, file sizes)
- Prompt length and preview
- API call parameters
- Response metadata
- Token usage tracking
- Timing information

**WARNING**:
- Batch parsing issues (when LLM doesn't follow page marker format)
- Non-fatal problems

**ERROR**:
- API failures
- Extraction errors
- Critical issues

### Enabling DEBUG Logging

**Method 1: Programmatically**
```python
import logging

# Enable DEBUG for LiteLLM extractor only
logging.getLogger('benchmarkdown.extractors.litellm').setLevel(logging.DEBUG)

# Or enable for all of benchmarkdown
logging.getLogger('benchmarkdown').setLevel(logging.DEBUG)
```

**Method 2: Application-wide**
```python
# In your script or app.py
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
```

**Method 3: Environment variable (recommended)**
```bash
export BENCHMARKDOWN_LOG_LEVEL=DEBUG
uv run python app.py
```

**Note**: The app is configured to only apply this log level to `benchmarkdown` code. Third-party libraries (httpx, litellm, boto3, etc.) remain at WARNING level to avoid verbose output and base64 spam in logs.

### DEBUG Log Output

When DEBUG logging is enabled, you'll see detailed information:

#### Configuration
```
[LiteLLM] Config: temperature=0.0, max_tokens=4096, concurrent_pages=2, image_quality=high
```

#### Image Rendering (per page)
```
[LiteLLM] Rendered page 1: 2550x3300 pixels, 1,234,567 bytes (1205.6 KB)
[LiteLLM] Rendered page 2: 2550x3300 pixels, 1,198,432 bytes (1170.3 KB)
```

#### Batch Information
```
[LiteLLM] Batch total image size: 3,720,653 bytes (3633.4 KB, 3.55 MB)
[LiteLLM] Batch prompt length: 528 chars, first 200 chars: Extract all text from...
```

#### API Call Details
```
[LiteLLM] API call parameters: model=gpt-4o-mini, max_tokens=8000, temperature=0.0, timeout=120, num_images=3
[LiteLLM] API call completed in 12.87s, response length: 8234 chars
```

#### Token Usage (when available)
```
[LiteLLM] Token usage: prompt=18456, completion=2456, total=20912
```

#### Batch Parsing
```
[LiteLLM] Successfully parsed 3 pages from batch response
```

### Example Complete Log

For a 3-page document with batch_size=3:

```
23:15:42 - INFO - [LiteLLM] Starting extraction: document.pdf (model=gpt-4o-mini, dpi=300, batch_size=3)
23:15:42 - DEBUG - [LiteLLM] Config: temperature=0.0, max_tokens=8000, concurrent_pages=1, image_quality=high
23:15:42 - INFO - [LiteLLM] Processing 3 pages
23:15:42 - INFO - [LiteLLM] Processing batch: pages 1-3/3 (3 pages)
23:15:43 - DEBUG - [LiteLLM] Rendered page 1: 2550x3300 pixels, 1,234,567 bytes (1205.6 KB)
23:15:43 - DEBUG - [LiteLLM] Rendered page 2: 2550x3300 pixels, 1,198,432 bytes (1170.3 KB)
23:15:44 - DEBUG - [LiteLLM] Rendered page 3: 2550x3300 pixels, 1,287,654 bytes (1257.5 KB)
23:15:44 - DEBUG - [LiteLLM] Batch total image size: 3,720,653 bytes (3633.4 KB, 3.55 MB)
23:15:44 - DEBUG - [LiteLLM] Batch prompt length: 528 chars, first 200 chars: Extract all text from this document page...
23:15:44 - DEBUG - [LiteLLM] API call parameters: model=gpt-4o-mini, max_tokens=8000, temperature=0.0, timeout=120, num_images=3
23:15:57 - DEBUG - [LiteLLM] API call completed in 12.87s, response length: 8234 chars
23:15:57 - DEBUG - [LiteLLM] Token usage: prompt=18456, completion=2456, total=20912
23:15:57 - DEBUG - [LiteLLM] Successfully parsed 3 pages from batch response
23:15:57 - INFO - [LiteLLM] Completed batch: pages 1-3/3 (api_time=12.87s)
23:15:57 - INFO - [LiteLLM] Completed extraction: document.pdf (duration: 15.12s, pages: 3)
```

### Using Logs for Optimization

**Cost Tracking:**
- Monitor `Token usage` to track actual consumption
- Calculate costs: `total_tokens * price_per_token`
- Compare batch_size settings to find optimal cost/performance balance

**Performance Profiling:**
- Check `api_time` to identify slow API calls
- Compare single-page vs batched processing times
- Monitor `API call completed in X.XXs` for individual requests

**Image Size Optimization:**
- Review `Rendered page` sizes to validate DPI settings
- If images are too large (>5 MB per batch), reduce DPI
- Compare file sizes at different DPI values (150, 200, 300, 400)

**Troubleshooting Batching:**
- Watch for `Expected N page sections, got M` warnings
- If parsing fails frequently, reduce batch_size
- Check `Successfully parsed N pages` confirmations

**Example optimization workflow:**
```python
import logging

# Enable DEBUG logging
logging.getLogger('benchmarkdown.extractors.litellm').setLevel(logging.DEBUG)

# Test different configurations
configs = [
    Config(dpi=150, batch_size=5),
    Config(dpi=200, batch_size=5),
    Config(dpi=300, batch_size=5),
]

for config in configs:
    extractor = Extractor(config=config)
    result = await extractor.extract_markdown("test.pdf")
    # Review logs to compare:
    # - Image sizes
    # - API call times
    # - Token usage
    # - Total cost
```

### Privacy and Security

**What is NOT logged:**
- ✅ Base64-encoded image data (never logged)
- ✅ Full API responses (only length and metadata)
- ✅ API keys (handled by environment/config)

**What IS logged:**
- ✅ Image dimensions and file sizes (metadata only)
- ✅ Prompt length and preview (first 200 characters)
- ✅ API parameters (model, tokens, temperature)
- ✅ Response metadata (timing, length, tokens)

All sensitive data remains secure while providing comprehensive debugging information.

## References

- [LiteLLM Documentation](https://docs.litellm.ai/)
- [LiteLLM Vision API Guide](https://docs.litellm.ai/docs/completion/vision)
- [OpenAI Vision API](https://platform.openai.com/docs/guides/vision)
- [Anthropic Claude Vision](https://docs.anthropic.com/claude/docs/vision)
- [Google Gemini Vision](https://ai.google.dev/gemini-api/docs/vision)
