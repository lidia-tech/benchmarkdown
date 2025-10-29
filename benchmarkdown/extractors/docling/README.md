# Docling Extractor

IBM's open-source library for local document processing with powerful OCR and layout analysis.

## Features

- Local processing (no cloud dependencies)
- Multiple OCR engines (EasyOCR, Tesseract, RapidOCR, macOS OCR)
- Table extraction (fast/accurate modes)
- Image enrichment and classification
- Hardware acceleration support (CPU, CUDA, MPS)
- Configurable threading
- Free and open-source

## Installation

```bash
uv sync --group docling
```

## Environment Variables

### Optional Performance Tuning

- **`DOCLING_NUM_THREADS`** (optional, default: CPU count)
  - Number of CPU threads to use for processing
  - Valid range: 1-32
  - Example: `export DOCLING_NUM_THREADS=8`

- **`DOCLING_DOCUMENT_TIMEOUT`** (optional, default: None)
  - Maximum processing time per document in seconds
  - Minimum: 1.0
  - Example: `export DOCLING_DOCUMENT_TIMEOUT=300.0`

**Note:** Docling runs locally and doesn't require API keys or cloud credentials.

### Example Setup

```bash
# Optional: Configure performance
export DOCLING_NUM_THREADS=16
export DOCLING_DOCUMENT_TIMEOUT=600.0
```

## Configuration Options

### Basic Options

- **OCR Engine**: Choose OCR engine
  - `easyocr`: General-purpose, GPU support
  - `tesseract`: Classic OCR, CPU-based
  - `tesseract_cli`: Tesseract command-line interface
  - `ocr_mac`: macOS native OCR (macOS only)
  - `rapid_ocr`: Fast OCR engine

- **Do OCR**: Enable/disable OCR processing
- **Do Table Structure**: Enable table extraction
- **Table Mode**: Fast vs Accurate extraction
- **Accelerator Device**: Hardware acceleration (auto/cpu/cuda/mps)

### Advanced Options

- **Image Enrichment**: Classify and describe images
- **Threading**: Number of threads for processing
- **Document Timeout**: Max processing time per document
- **Artifacts Path**: Custom output directory

### OCR Engine Specific Options

Each OCR engine has its own configuration options (shown/hidden dynamically based on OCR engine selection):

- **EasyOCR**: Languages, GPU, confidence threshold, bitmap threshold
- **Tesseract**: Languages, path, bitmap threshold
- **Tesseract CLI**: Languages, path, bitmap threshold
- **macOS OCR**: Languages, recognition level
- **RapidOCR**: Model directory, bitmap threshold

## Usage

### Programmatic

```python
from benchmarkdown.extractors.docling import Extractor, Config

# Create configuration
config = Config(
    do_ocr=True,
    ocr_engine="easyocr",
    do_table_structure=True,
    table_mode="accurate",
    accelerator_device="auto"
)

# Create extractor
extractor = Extractor(config=config)

# Extract markdown
markdown = await extractor.extract_markdown("document.pdf")
```

### Via UI

1. Launch the app: `uv run python app.py`
2. Select "Docling (Local)" from the engine dropdown
3. Configure options (or load a saved profile)
4. Choose OCR engine and configure its specific options
5. Add to extraction queue
6. Upload documents and run extraction

## Hardware Acceleration

Docling supports multiple hardware accelerators:

- **CPU**: Default, works everywhere
- **CUDA**: NVIDIA GPUs (requires CUDA toolkit)
- **MPS**: Apple Silicon (M1/M2/M3 chips)
- **Auto**: Automatically selects best available

For GPU acceleration, install appropriate dependencies:

```bash
# For NVIDIA CUDA
pip install torch --index-url https://download.pytorch.org/whl/cu118

# For Apple Silicon MPS (already included with PyTorch on macOS)
```

## Pricing

Docling is **completely free** and open-source. No API keys, no cloud costs, no usage limits.

## Resources

- [Official Documentation](https://github.com/DS4SD/docling)
- [GitHub Repository](https://github.com/DS4SD/docling)
- [Example Notebooks](https://github.com/DS4SD/docling/tree/main/examples)
