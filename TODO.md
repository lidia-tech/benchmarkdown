# Task list

## Clean and refactor code base

There are different versions of the app commited to the codebase (app_old.py, app_with_config.py) as well as it is not clear where the app UI is implemented (in app.py, benchmarkdown/ui.py or benchmarkdown/config_ui.py). Clean unused old versions, and refactor the UI codebase breaking down into function components. A single monolithic 1000 lines of code file is difficult to maintain. You can move components to the benchmarkdown folder and module, creating a new ui submodule.

## Separate code for each text extractor engine and create proper plugin infrastructure

Currently there're two text extractor engines are implemented: docling and textract. However, both have their config structure in benchmarkdown/config.py.

Create proper modules for each engine, with a standard file structure (eg. engine_name/engine.py and engine_name/config.py). These modules must have a unified interface, eg. from the module `__init__.py` script the engine class that implements MarkdownExtractor protocol should be exported always the same predefined name (eg. `ExtractorEngine = DoclingExtractor` or `ExtractorEngine = TextractExtractor`). The intializers of the different engines should be also unified, and it must take its own appropriate config structure. The initalizer of the engine will take care about properly initializing its internal implementation.

The config strucutres should be put behind a similar unified interface, if it makes sense.

The ultimate goal of this task is to be able to add engine implementations as plugins to the framework, where the framework can dynamically explore the available engines and their config structures.

## Check what's missing for TextractEngine

... And test it.

## Implement LlamaParse extractor engine

https://developers.llamaindex.ai/python/cloud/llamaparse/getting_started

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
