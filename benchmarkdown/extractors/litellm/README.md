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
```bash
export OPENAI_API_KEY="sk-..."
```

### Anthropic
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Google Gemini
```bash
export GEMINI_API_KEY="..."
```

### AWS Bedrock
```bash
# Uses standard AWS credentials (IAM, ~/.aws/credentials, etc.)
# Ensure you have bedrock:InvokeModel and bedrock:Converse permissions
export AWS_REGION="us-east-1"  # Optional, defaults to us-east-1

# Verify model availability in your region:
# aws bedrock list-foundation-models --region us-east-1
```

**Important**: For vision models, use the `bedrock/converse/` prefix (e.g., `bedrock/converse/us.anthropic.claude-3-5-sonnet-20241022-v2:0`) instead of just `bedrock/` to ensure proper image support.

### Azure OpenAI
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
    concurrent_pages=2  # Process 2 pages at once
)
extractor = Extractor(config=config)
markdown = await extractor.extract_markdown("document.pdf")
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

1. **Page Rendering**: Each PDF page is rendered to a PNG image at the specified DPI using PyMuPDF
2. **Image Encoding**: Images are encoded to base64 for transmission to the LLM
3. **Vision API Call**: The image and extraction prompt are sent to the vision-capable LLM
4. **Text Extraction**: The LLM analyzes the image and extracts text in markdown format
5. **Combination**: Results from all pages are combined with the specified separator

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
- Use lower DPI (150-200) for clean text documents
- Choose cheaper models (gpt-4o-mini, claude-3-5-haiku, gemini-1.5-flash)
- Set appropriate max_tokens limits
- Use 'low' image quality for simple documents

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

## References

- [LiteLLM Documentation](https://docs.litellm.ai/)
- [LiteLLM Vision API Guide](https://docs.litellm.ai/docs/completion/vision)
- [OpenAI Vision API](https://platform.openai.com/docs/guides/vision)
- [Anthropic Claude Vision](https://docs.anthropic.com/claude/docs/vision)
- [Google Gemini Vision](https://ai.google.dev/gemini-api/docs/vision)
