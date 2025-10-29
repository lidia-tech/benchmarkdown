# Task list

## Fix Docling OCR engine conditional settings display bug

**Priority:** 1

### Description

When selecting different OCR engines in Docling configuration (e.g., tesseract, tesseract_cli, ocr_mac, rapid_ocr), only the EasyOCR settings are shown regardless of the selected engine. The nested config sections should show/hide based on the ocr_engine dropdown selection.

### Investigation needed

- Check how nested_groups event handlers are wired up in app_builder.py
- Verify if the issue is similar to the LlamaParse conditional fields bug (InvalidComponentError with layout containers as outputs)
- Ensure unified solution for both nested configs (Docling) and conditional fields (LlamaParse)

## Implement TensorLake extractor engine

https://docs.tensorlake.ai/document-ingestion/parsing/read

## Implement litellm based multi-modal LLM engine

1. Save each page of the PDF into a separate PNG file:

```python
import fitz  # PyMuPDF

# Open the PDF file
doc = fitz.open("../data/input/lidia-internal/EDPB Opinion 12-2018.pdf")

# Choose the page (0-based index)
page_number = 0
page = doc.load_page(page_number)

# Render the page to a pixmap (image)
pix = page.get_pixmap(dpi=300)  # use higher dpi for better quality

# Save the pixmap as an image
pix.save("page_screenshot.png")
```

The dpi should be configurable.

2. Call an LLM model with an appropiate prompt ("Extract all text literally from the page" or something similar; experiment with it). Use litellm framework: https://docs.litellm.ai/docs/completion/vision

## Implement Aspose extractor engine

https://docs.aspose.com/pdf/python-cpp/extract-text/


## Implement Microsoft DocumentAI based extractor engine

TBD
