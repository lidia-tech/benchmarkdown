# Task list

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


## Implement price per page estimation

TBD

## Extraction report improvements

1. in the beginning of the downloadable HTML report, add an initial summary table that lists all documents present in the table

2. use fitz (pymupdf) to open the pdf before the extraction tasks and get the number of pages. Include the number of pages in the beginning of the report.

## Implement improved valutation metrics

TBD

## Add a configurable timeout for the single tasks

If the task do not finish before a global timeout (settable from ui), kill it and mark it as failed.

AND/OR

Add a "stop" button that stops all running tasks and marks the non-finished as failed.
