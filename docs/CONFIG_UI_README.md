# Configuration Guide

This guide covers how to configure extraction engines in Benchmarkdown. Each engine has its own settings that control how documents are processed.

## How Configuration Works

Benchmarkdown uses **profiles** to save and reuse configurations. A profile is a named set of settings for a specific extractor engine (e.g., "Fast Mode" for Docling, or "High Quality" for LlamaParse).

Profiles are saved as JSON files in the `./config/` directory and persist across sessions.

## Creating a Profile

1. Click **"Add Task"** to open the task editor
2. Select an **extractor engine** from the dropdown
3. Click **"New Profile"**
4. Enter a **profile name** (e.g., "Fast Mode")
5. Adjust the settings:
   - **Basic options** are shown by default
   - **Advanced options** are in a collapsible "Advanced" section — click to expand
   - For engines with sub-configurations (like Docling's OCR engines), additional settings appear when you select a specific option
6. Click **"Save Profile"**

The profile is now saved and can be reused in any future session.

## Loading and Editing Profiles

- **To load**: Select an engine, then pick a profile from the "Saved Profiles" dropdown. Its settings are loaded automatically.
- **To edit**: Select a profile, click **"Edit Profile"**, change settings, then click **"Save Profile"**.
- **To delete**: Select a profile and click **"Delete Profile"**.
- **To refresh the list**: Click the refresh button next to the dropdown if profiles were added outside the UI.

## Configuration Patterns

Here are some useful starting configurations for common scenarios:

### Fast Preview (Docling)

For quickly checking if extraction works on your documents, without spending time on OCR or enrichment:

- Do OCR: off
- Table Structure Mode: FAST
- Num Threads: 16 (or your CPU count)
- All enrichment options: off

### High Quality (Docling)

For production-grade extraction where accuracy matters:

- Do OCR: on
- Table Structure Mode: ACCURATE
- Num Threads: 4-8
- Do Cell Matching: on

### Technical Documents (Docling)

For academic papers or code documentation:

- Do OCR: on
- Do Code Enrichment: on
- Do Formula Enrichment: on
- Table Structure Mode: ACCURATE

### Quick Comparison Across Engines

To compare how different engines handle the same document, create one task per engine with default settings:

1. Add a Docling task with a "Default" profile (no changes)
2. Add a Textract task with a "Default" profile
3. Add a LlamaParse task with a "Default" profile
4. Upload your documents and run — the results table shows timing and word counts for all three

## Engine-Specific Settings

Each engine has different configuration options. Basic options cover the most common settings; advanced options are for fine-tuning.

For detailed documentation on each engine's options, see:

- [Docling README](benchmarkdown/extractors/docling/README.md) — OCR engines, table extraction, threading, image generation, hardware acceleration
- [AWS Textract README](benchmarkdown/extractors/textract/README.md) — feature selection, markdown formatting
- [LlamaParse README](benchmarkdown/extractors/llamaparse/README.md) — result types, GPT-4o enhanced mode, parsing instructions
- [TensorLake README](benchmarkdown/extractors/tensorlake/README.md) — chunking, table output, signature detection
- [Azure Document Intelligence README](benchmarkdown/extractors/azure_document_intelligence/README.md) — model selection, page ranges, locale
- [LiteLLM README](benchmarkdown/extractors/litellm/README.md) — model selection, DPI, custom prompts, batching

## Programmatic Usage

You can also use extractors directly in Python (e.g., in Jupyter notebooks):

```python
from benchmarkdown.extractors.docling import Config as DoclingConfig, Extractor as DoclingExtractor

config = DoclingConfig(
    do_ocr=False,
    table_structure_mode="FAST",
    num_threads=16
)

extractor = DoclingExtractor(config=config)
markdown = await extractor.extract_markdown("document.pdf")
```

See `notebooks/` for working examples.

## Performance Tips

- **Disable OCR** if your documents have native (selectable) text — it's much faster
- **Use FAST table mode** for speed; use ACCURATE only for complex tables
- **Increase threads** (Docling) to match your CPU core count for parallel processing
- **Set timeouts** if some documents hang — this prevents one bad file from blocking the batch
- **Enrichment features** (code, formulas, image classification) add processing time — enable only when needed
