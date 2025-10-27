# OCR Engine Selection in Benchmarkdown

Benchmarkdown now supports selecting and configuring different OCR engines for Docling document extraction. This allows you to choose the best OCR engine for your specific use case.

## Available OCR Engines

1. **EasyOCR** (default) - Popular open-source OCR with good accuracy
2. **Tesseract** - Google's open-source OCR engine (Python API)
3. **TesseractCLI** - Tesseract via command-line interface
4. **OcrMac** - macOS native OCR (macOS only)
5. **RapidOCR** - Fast and lightweight OCR engine

## Basic Usage

### Using Python API

```python
from benchmarkdown.config import (
    DoclingConfig,
    OcrEngineEnum,
    EasyOcrConfig,
    TesseractOcrConfig,
    TesseractCliOcrConfig,
    RapidOcrConfig
)
from benchmarkdown.docling import DoclingExtractor

# Example 1: Using EasyOCR (default)
easyocr_config = EasyOcrConfig(
    lang=["en"],
    use_gpu=False,
    force_full_page_ocr=True
)

config = DoclingConfig(
    do_ocr=True,
    ocr_engine=OcrEngineEnum.EASYOCR,
    easyocr_config=easyocr_config
)

extractor = DoclingExtractor(config=config)

# Example 2: Using Tesseract
tesseract_config = TesseractOcrConfig(
    lang=["eng"],
    force_full_page_ocr=False
)

config = DoclingConfig(
    do_ocr=True,
    ocr_engine=OcrEngineEnum.TESSERACT,
    tesseract_config=tesseract_config
)

extractor = DoclingExtractor(config=config)

# Example 3: Using RapidOCR
rapidocr_config = RapidOcrConfig(
    lang=["en"],
    use_det=True,
    use_rec=True,
    text_score=0.5
)

config = DoclingConfig(
    do_ocr=True,
    ocr_engine=OcrEngineEnum.RAPID_OCR,
    rapidocr_config=rapidocr_config
)

extractor = DoclingExtractor(config=config)
```

## OCR Engine Configuration Options

### EasyOCR

**Basic Options:**
- `lang`: List of language codes (default: `["en"]`)
- `use_gpu`: Enable GPU acceleration (default: `False`)
- `force_full_page_ocr`: Force OCR on entire page (default: `False`)

**Advanced Options:**
- `confidence_threshold`: Minimum confidence threshold (default: `0.5`)
- `bitmap_area_threshold`: Minimum area threshold for bitmaps (default: `0.05`)
- `model_storage_directory`: Custom directory for models (default: `None`)

### Tesseract (Python API)

**Basic Options:**
- `lang`: List of language codes (default: `["eng"]`)
- `force_full_page_ocr`: Force OCR on entire page (default: `False`)

**Advanced Options:**
- `bitmap_area_threshold`: Minimum area threshold (default: `0.05`)
- `path`: Path to Tesseract installation (default: `None` for auto-detect)

### Tesseract CLI

**Basic Options:**
- `lang`: List of language codes (default: `["eng"]`)
- `force_full_page_ocr`: Force OCR on entire page (default: `False`)

**Advanced Options:**
- `bitmap_area_threshold`: Minimum area threshold (default: `0.05`)
- `tesseract_cmd`: Path to tesseract executable (default: `None` for auto-detect)
- `path`: Path to Tesseract data directory (default: `None`)

### OcrMac (macOS only)

**Basic Options:**
- `lang`: List of language codes (default: `["en-US"]`)
- `force_full_page_ocr`: Force OCR on entire page (default: `False`)

**Advanced Options:**
- `bitmap_area_threshold`: Minimum area threshold (default: `0.05`)

### RapidOCR

**Basic Options:**
- `lang`: List of language codes (default: `["en"]`)
- `force_full_page_ocr`: Force OCR on entire page (default: `False`)
- `use_det`: Enable text detection module (default: `True`)
- `use_rec`: Enable text recognition module (default: `True`)

**Advanced Options:**
- `use_cls`: Enable classification/orientation detection (default: `False`)
- `text_score`: Minimum detection confidence score (default: `0.5`)
- `bitmap_area_threshold`: Minimum area threshold (default: `0.05`)
- `print_verbose`: Enable verbose debug output (default: `False`)

## Multi-Language Support

All OCR engines support multiple languages. You can specify multiple language codes:

```python
# EasyOCR with multiple languages
easyocr_config = EasyOcrConfig(
    lang=["en", "fr", "de"],  # English, French, German
    use_gpu=False
)

# Tesseract with multiple languages
tesseract_config = TesseractOcrConfig(
    lang=["eng", "fra", "deu"],  # Note: Different naming convention
    force_full_page_ocr=False
)

# Tesseract with automatic language detection
tesseract_auto_config = TesseractOcrConfig(
    lang=["auto"],  # Automatic language detection
    force_full_page_ocr=True
)
```

## Configuration Serialization

OCR configurations can be serialized to/from dictionaries for storage:

```python
# Serialize to dictionary
config = DoclingConfig(
    do_ocr=True,
    ocr_engine=OcrEngineEnum.EASYOCR,
    easyocr_config=EasyOcrConfig(lang=["en", "fr"])
)

config_dict = config.model_dump()

# Deserialize from dictionary
config2 = DoclingConfig(**config_dict)
```

## Testing

A comprehensive test suite is available in `tests/test_ocr_engines.py`:

```bash
uv run python tests/test_ocr_engines.py
```

This test demonstrates:
- Creating configurations for each OCR engine
- Initializing extractors with different engines
- Serializing/deserializing configurations

## UI Integration (Coming Soon)

The Gradio UI will be updated to include:
- OCR engine dropdown selector
- Dynamic configuration panels for each engine
- Profile-based OCR configuration management

For now, use the Python API as shown above.

## Best Practices

1. **Choose the right engine for your use case:**
   - EasyOCR: Good general-purpose OCR with multi-language support
   - Tesseract: Well-established, good for standard documents
   - RapidOCR: Faster processing, good for high-volume workflows
   - OcrMac: Best quality on macOS for supported languages

2. **Enable full page OCR only when needed:**
   - `force_full_page_ocr=True` processes the entire page via OCR
   - Default behavior is selective OCR on specific regions
   - Full page OCR is slower but more thorough

3. **Multi-language documents:**
   - Specify all expected languages for best results
   - Use Tesseract's `["auto"]` for automatic detection if languages are unknown

4. **GPU acceleration (EasyOCR only):**
   - Enable `use_gpu=True` if you have a compatible GPU
   - Significantly faster for large batches of documents

## Troubleshooting

**Tesseract not found:**
- Install Tesseract: `brew install tesseract` (macOS) or `apt-get install tesseract-ocr` (Linux)
- Set TESSDATA_PREFIX environment variable if needed

**Language packs missing:**
- Install language data for Tesseract: `brew install tesseract-lang` (macOS)
- For EasyOCR, models are downloaded automatically on first use

**OcrMac not available:**
- OcrMac only works on macOS
- On other platforms, it automatically falls back to EasyOCR

## Examples

See `tests/test_ocr_engines.py` for complete working examples of all OCR engines.
