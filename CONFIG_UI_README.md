# Configuration UI Guide

This document explains how to use the Pydantic-based configuration system in Benchmarkdown to create and compare different extractor configurations.

## Overview

The configuration system allows you to:
- Create custom Docling extractor configurations through a web UI
- Compare different configurations side-by-side
- Save multiple named configurations for different use cases
- All without writing code

## Quick Start

### 1. Launch the Application

```bash
uv run python app.py
```

The app will open at `http://localhost:7860`

### 2. Create a Configuration

1. Go to the **"Configuration"** tab
2. Enter a name for your configuration (e.g., "Fast Mode")
3. Adjust the settings:
   - **Basic Options**: Common settings like OCR, tables, threading
   - **Advanced Options**: Click the accordion for enrichment features, image generation, etc.
4. Click **"Save Configuration"**

Your configuration is now available as an extractor!

### 3. Extract and Compare

1. Go to the **"Extract & Compare"** tab
2. Upload one or more documents
3. Select which extractors to use (including your custom configurations)
4. Click **"Extract All"**
5. View side-by-side or tabbed comparisons

## Configuration Options

### Basic Options

| Option | Type | Description | Default |
|--------|------|-------------|---------|
| **Do OCR** | Checkbox | Enable OCR for scanned documents | True |
| **Do Table Structure** | Checkbox | Extract table structures | True |
| **Table Structure Mode** | Dropdown | FAST (faster) or ACCURATE (better quality) | ACCURATE |
| **Num Threads** | Slider (1-32) | CPU threads for processing | CPU count |

### Advanced Options

| Option | Type | Description | Default |
|--------|------|-------------|---------|
| **Force Backend Text** | Checkbox | Re-extract text instead of using PDF native text | False |
| **Do Cell Matching** | Checkbox | Match table cells with text content | True |
| **Do Code Enrichment** | Checkbox | Identify and enrich code blocks | False |
| **Do Formula Enrichment** | Checkbox | Process mathematical formulas | False |
| **Do Picture Classification** | Checkbox | Classify detected images (requires AI model) | False |
| **Do Picture Description** | Checkbox | Generate image descriptions (requires AI model) | False |
| **Generate Page Images** | Checkbox | Create rendered page images (uses memory) | False |
| **Generate Picture Images** | Checkbox | Extract detected images | False |
| **Images Scale** | Slider (0.1-2.0) | Scale factor for generated images | 1.0 |
| **Accelerator Device** | Dropdown | Hardware acceleration (auto/cpu/cuda/mps) | auto |
| **Document Timeout** | Number | Max processing time per document (seconds) | None |

## Common Configuration Patterns

### Fast Processing Mode

Best for: Quick previews, large batches

```
Name: Fast Mode
- Do OCR: ❌ False
- Do Table Structure: ✓ True
- Table Structure Mode: FAST
- Num Threads: 16 (or max available)
- All Advanced: ❌ False
```

### Accurate Mode

Best for: Production use, quality-critical documents

```
Name: Accurate
- Do OCR: ✓ True
- Do Table Structure: ✓ True
- Table Structure Mode: ACCURATE
- Num Threads: 4-8
- All Advanced: ❌ False (unless needed)
```

### Code & Formula Extraction

Best for: Technical documents, academic papers

```
Name: Technical
- Do OCR: ✓ True
- Do Table Structure: ✓ True
- Table Structure Mode: ACCURATE
- Do Code Enrichment: ✓ True
- Do Formula Enrichment: ✓ True
- Num Threads: 8
```

### Image-Rich Documents

Best for: Documents with many diagrams/photos

```
Name: Image Mode
- Do OCR: ✓ True
- Do Picture Classification: ✓ True
- Do Picture Description: ✓ True
- Generate Picture Images: ✓ True
- Images Scale: 1.5-2.0
```

## Programmatic Usage

You can also create configurations programmatically:

```python
from benchmarkdown.extractors.docling import Config as DoclingConfig, Extractor as DoclingExtractor
from benchmarkdown.extractors.docling.config import TableFormerModeEnum

# Create configuration
config = DoclingConfig(
    do_ocr=False,
    table_structure_mode=TableFormerModeEnum.FAST,
    num_threads=16,
    do_code_enrichment=True
)

# Create extractor with config
extractor = DoclingExtractor(config=config)

# Use for extraction
markdown = await extractor.extract_markdown("document.pdf")
```

## Architecture

### Components

```
benchmarkdown/
├── config.py           # Pydantic models (DoclingConfig, etc.)
├── config_ui.py        # UI generation from Pydantic models
├── docling.py          # DoclingExtractor with config support
└── ui.py               # BenchmarkUI with dynamic extractor registration

app.py                  # Main application with Configuration tab
```

### How It Works

1. **Pydantic Models** (`config.py`):
   - Define configuration schema with types, defaults, constraints
   - Include field descriptions for UI generation
   - Validate input values

2. **UI Generation** (`config_ui.py`):
   - Maps Pydantic field types to Gradio components
   - `bool` → `Checkbox`
   - `Enum` → `Dropdown`
   - `int` with constraints → `Slider`
   - `float` with constraints → `Slider`

3. **Dynamic Registration** (`app.py`):
   - User configures settings in Configuration tab
   - UI values converted to `DoclingConfig` object
   - `DoclingExtractor` created with config
   - Registered with `BenchmarkUI` under custom name

4. **Extraction** (`ui.py`):
   - User selects configured extractors
   - Documents processed in parallel
   - Results compared side-by-side

## Testing

Run the comprehensive test suite:

```bash
# Test configuration models
uv run python test_config_ui.py

# Test configuration extraction
uv run python test_config_extraction.py

# Test integrated app workflow
uv run python test_integrated_app.py
```

## Extending to Other Extractors

To add configuration support for other extractors (e.g., Textract):

1. Create Pydantic model in `config.py`:
   ```python
   class TextractConfig(BaseModel):
       features: list[TextractFeaturesEnum] = Field(...)
       # ... other fields
   ```

2. Update extractor to accept config:
   ```python
   class TextractExtractor:
       def __init__(self, config: Optional[TextractConfig] = None, **kwargs):
           # ...
   ```

3. Add to Configuration tab in `app.py`
4. Define field groupings in `config_ui.py`

## Performance Tips

- **OCR**: Disable if documents have native text (PDFs from Word, etc.)
- **Table Mode**: Use FAST for speed, ACCURATE for complex tables
- **Threads**: Set to CPU core count for balanced performance
- **Timeouts**: Set if you have documents that occasionally hang
- **Enrichment Features**: Enable only if needed (they're slower)

## Troubleshooting

**Configuration not appearing in extractor list:**
- Make sure you clicked "Save Configuration"
- Check the status message for errors
- Refresh the extractor dropdown manually if needed

**Extraction fails with custom config:**
- Verify configuration values are valid
- Check logs for error messages
- Try default configuration to isolate issue

**UI components not updating:**
- Some Gradio components require manual refresh
- Try switching tabs and back
- Reload the page if needed

## Future Enhancements

Planned features:
- [ ] Save/load configuration presets to JSON files
- [ ] Import/export configuration sets
- [ ] Configuration templates library
- [ ] Performance profiling per configuration
- [ ] Cost estimation for cloud extractors
- [ ] A/B testing framework for configurations

## Support

For issues or questions:
1. Check `CLAUDE.md` for project architecture
2. Run tests to verify installation
3. File an issue on GitHub with configuration details
