# Task list

## Separate code for each text extractor engine and create proper plugin infrastructure

Priority: 1

Currently there're two text extractor engines are implemented: docling and textract. However, both have their config structure in benchmarkdown/config.py.

Create proper modules for each engine, with a standard file structure (eg. engine_name/engine.py and engine_name/config.py). These modules must have a unified interface, eg. from the module `__init__.py` script the engine class that implements MarkdownExtractor protocol should be exported always the same predefined name (eg. `ExtractorEngine = DoclingExtractor` or `ExtractorEngine = TextractExtractor`). The intializers of the different engines should be also unified, and it must take its own appropriate config structure. The initalizer of the engine will take care about properly initializing its internal implementation.

The config strucutres should be put behind a similar unified interface, if it makes sense.

The ultimate goal of this task is to be able to add engine implementations as plugins to the framework, where the framework can dynamically explore the available engines and their config structures.

### Clarifications

The current architecture has several coupling points that prevent easy addition of new extractors:

1. **app.py** hardcodes imports and availability checking for each extractor
2. **config.py** is monolithic with all extractor configs
3. **config_ui.py** has hardcoded field groupings
4. **ui/app_builder.py** has hardcoded UI generation (lines 194-388)
5. Extractor classes are tightly coupled to config.py

However, some parts work well:
- MarkdownExtractor protocol is clean
- BenchmarkUI.register_extractor() is generic
- ProfileManager is extractor-agnostic
- Pydantic → Gradio mapping is reusable

### Thoughts, proposed solution

Implement a plugin-based architecture where each extractor lives in `benchmarkdown/extractors/{engine_name}/`:

**Directory structure:**
```
benchmarkdown/extractors/
├── __init__.py          # Plugin registry & discovery
├── base.py              # Base classes & protocol
├── docling/
│   ├── __init__.py      # Exports: Extractor, Config, BASIC_FIELDS, ADVANCED_FIELDS
│   ├── extractor.py     # DoclingExtractor class
│   └── config.py        # DoclingConfig + OCR configs
└── textract/
    ├── __init__.py      # Standard exports
    ├── extractor.py     # TextractExtractor class
    └── config.py        # TextractConfig
```

**Plugin interface** (each extractor __init__.py exports):
- `Extractor` class (implements MarkdownExtractor)
- `Config` class (Pydantic model)
- `BASIC_FIELDS` and `ADVANCED_FIELDS` lists
- `ENGINE_NAME` and `ENGINE_DISPLAY_NAME` constants
- `is_available()` function returning `(bool, str)` for dependency checking

**Implementation phases:**
1. Create plugin infrastructure with ExtractorRegistry
2. Migrate Docling to extractors/docling/
3. Migrate Textract to extractors/textract/
4. Update app.py for dynamic discovery
5. Update UI for dynamic config generation
6. Test backward compatibility with existing profiles

**Key benefits:**
- Adding new extractors: just create extractors/{name}/ directory
- Clean separation: each extractor is self-contained
- No UI changes needed when adding extractors
- Dynamic discovery: no hardcoded imports
- Backward compatible: existing imports and profiles still work

### What was implemented

**Phase 1: Plugin Infrastructure Created**
- Created `benchmarkdown/extractors/` directory structure
- Implemented `base.py` with `MarkdownExtractor` and `ExtractorPlugin` protocols
- Implemented `__init__.py` with `ExtractorRegistry` class for automatic plugin discovery
- Registry validates plugin interface, checks availability, and manages instances

**Phase 2: Docling Migrated to Plugin**
- Created `benchmarkdown/extractors/docling/` with:
  - `config.py`: All Docling configs (DoclingConfig, OCR configs, enums, field groupings)
  - `extractor.py`: DoclingExtractor implementation
  - `__init__.py`: Standard plugin interface (Extractor, Config, BASIC_FIELDS, ADVANCED_FIELDS, ENGINE_NAME, ENGINE_DISPLAY_NAME, is_available())
- Maintained old `benchmarkdown/docling.py` as backward compatibility wrapper

**Phase 3: Textract Migrated to Plugin**
- Created `benchmarkdown/extractors/textract/` with same structure:
  - `config.py`: TextractConfig and field groupings
  - `extractor.py`: TextractExtractor implementation
  - `__init__.py`: Standard plugin interface
- Maintained old `benchmarkdown/textract.py` as backward compatibility wrapper

**Phase 4: Backward Compatibility**
- Updated `benchmarkdown/config.py` to re-export all config classes from plugins
- Updated `benchmarkdown/config_ui.py` to re-export field groupings from plugins
- All existing imports continue to work: `from benchmarkdown.config import DoclingConfig`

**Phase 5: Dynamic Discovery in app.py** ✅
- Replaced hardcoded imports with `ExtractorRegistry.discover_extractors()`
- Dynamic availability checking via plugin `is_available()` method
- Passes registry to `create_app()` instead of boolean flags

**Phase 6: Testing** ✅
- Verified plugin discovery works correctly
- Verified backward compatibility (old imports still work)
- Verified extractor instance creation through registry
- All tests pass without breaking existing functionality

**⚠️ Phase 7: Dynamic UI Generation - NOT COMPLETED**

The UI (app_builder.py) still has ~500 lines of hardcoded extractor-specific code:
- ❌ Hardcoded imports (28 import statements for Docling/Textract configs)
- ❌ Hardcoded engine selector (if has_docling / if has_textract)
- ❌ Hardcoded config UI generation (183 lines for Docling, separate for Textract)
- ❌ Hardcoded event handlers with engine-specific logic

**This means adding a new extractor still requires modifying app_builder.py!**

See IMPLEMENTATION_GAPS.md for detailed analysis.

**What was achieved:**
- ✅ Backend plugin infrastructure is excellent
- ✅ Zero breaking changes - existing code works unchanged
- ✅ Backward compatible imports maintained
- ✅ Dynamic plugin discovery at app startup
- ✅ Clean plugin interface for extractor development
- ✅ Graceful degradation - plugins with missing dependencies are skipped

**What's missing:**
- ❌ UI doesn't use registry to generate config forms dynamically
- ❌ Still need to modify UI code to add new extractors

**How to Add New Extractors (Current State):**
1. Create `benchmarkdown/extractors/{name}/` directory with:
   - `config.py` - Pydantic config model with BASIC_FIELDS and ADVANCED_FIELDS
   - `extractor.py` - Class implementing MarkdownExtractor protocol
   - `__init__.py` - Exports: Extractor, Config, fields, ENGINE_NAME, ENGINE_DISPLAY_NAME, is_available()

2. **⚠️ Still required:** Modify `benchmarkdown/ui/app_builder.py`:
   - Add imports for new config classes
   - Add field grouping imports
   - Add hardcoded config UI section (100+ lines)
   - Add event handler cases for the new engine

**Goal:** Steps should be just #1 above, no UI modifications needed!

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

## BUG: In dark mode the markdown preview is unreadable

In dark mode, after a successful extraction task, the markdown preview is shown with a very light gray color on a white background, so unreadable.
