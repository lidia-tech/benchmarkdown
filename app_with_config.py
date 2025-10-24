#!/usr/bin/env python3
"""
Benchmarkdown application with configuration UI.

This version allows users to configure Docling parameters through the UI
before running extractions.
"""

import asyncio
import os
from pathlib import Path
import gradio as gr

from benchmarkdown.config import DoclingConfig, TableFormerModeEnum, AcceleratorDeviceEnum
from benchmarkdown.config_ui import (
    create_gradio_component_from_field,
    build_config_from_ui_values,
    DOCLING_BASIC_FIELDS,
    DOCLING_ADVANCED_FIELDS
)
from benchmarkdown.docling import DoclingExtractor


# Global state for configured extractors
configured_extractors = {}


def create_config_ui():
    """Create the configuration UI for Docling."""
    components = []
    component_refs = {}  # Store references to components

    # Basic options
    with gr.Group():
        gr.Markdown("### Docling Configuration - Basic Options")

        for field_name in DOCLING_BASIC_FIELDS:
            if field_name not in DoclingConfig.model_fields:
                continue

            field_info = DoclingConfig.model_fields[field_name]
            field_type = field_info.annotation

            component, comp_id = create_gradio_component_from_field(
                field_name, field_info, field_type
            )
            components.append(component)
            component_refs[field_name] = component

    # Advanced options
    with gr.Accordion("Docling Configuration - Advanced Options", open=False):
        for field_name in DOCLING_ADVANCED_FIELDS:
            if field_name not in DoclingConfig.model_fields:
                continue

            field_info = DoclingConfig.model_fields[field_name]
            field_type = field_info.annotation

            component, comp_id = create_gradio_component_from_field(
                field_name, field_info, field_type
            )
            components.append(component)
            component_refs[field_name] = component

    return components, component_refs


def create_extractor_from_config(*args):
    """Create a DoclingExtractor from UI configuration values."""
    # Map args to field names
    all_fields = DOCLING_BASIC_FIELDS + DOCLING_ADVANCED_FIELDS
    ui_values = {field: value for field, value in zip(all_fields, args)}

    # Build config
    config = build_config_from_ui_values(DoclingConfig, ui_values)

    # Create extractor
    extractor = DoclingExtractor(config=config)

    # Store in global state with a descriptive name
    config_name = f"Docling (OCR={config.do_ocr}, Mode={config.table_structure_mode}, Threads={config.num_threads})"
    configured_extractors[config_name] = extractor

    return f"✓ Extractor configured: {config_name}"


async def extract_document(file_obj, config_name):
    """Extract markdown from a document using the configured extractor."""
    if not file_obj:
        return "❌ No file uploaded"

    if config_name not in configured_extractors:
        return "❌ Please configure an extractor first"

    extractor = configured_extractors[config_name]
    file_path = file_obj.name

    try:
        import time
        start = time.time()
        markdown_text = await extractor.extract_markdown(file_path)
        elapsed = time.time() - start

        # Generate preview
        preview = f"""
## Extraction Complete

**File:** {os.path.basename(file_path)}
**Extractor:** {config_name}
**Time:** {elapsed:.2f} seconds
**Characters:** {len(markdown_text):,}
**Words:** {len(markdown_text.split()):,}

---

### Markdown Preview

{markdown_text[:2000]}

{'...(truncated)' if len(markdown_text) > 2000 else ''}
        """
        return preview

    except Exception as e:
        return f"❌ Extraction failed: {str(e)}"


def sync_extract_document(file_obj, config_name):
    """Synchronous wrapper for extraction."""
    return asyncio.run(extract_document(file_obj, config_name))


def create_interface():
    """Create the Gradio interface."""
    with gr.Blocks(title="Benchmarkdown - Configure & Extract") as demo:
        gr.Markdown("# 📄 Benchmarkdown - Configure & Extract")
        gr.Markdown("Configure Docling parameters and extract markdown from documents.")

        # Configuration Section
        with gr.Tab("⚙️ Configuration"):
            gr.Markdown("## Configure Docling Extractor")

            config_components, config_refs = create_config_ui()

            with gr.Row():
                configure_btn = gr.Button("💾 Save Configuration", variant="primary", size="lg")
                config_status = gr.Textbox(
                    label="Configuration Status",
                    interactive=False,
                    value="No configuration saved yet"
                )

            # Wire up the configuration button
            configure_btn.click(
                fn=create_extractor_from_config,
                inputs=config_components,
                outputs=config_status
            )

        # Extraction Section
        with gr.Tab("🚀 Extract"):
            gr.Markdown("## Extract Documents")

            file_upload = gr.File(
                label="Upload Document (PDF, DOCX, etc.)",
                file_types=[".pdf", ".docx", ".doc"]
            )

            extractor_select = gr.Dropdown(
                label="Select Configured Extractor",
                choices=list(configured_extractors.keys()),
                value=None,
                allow_custom_value=True
            )

            extract_btn = gr.Button("🚀 Extract Markdown", variant="primary", size="lg")

            results_md = gr.Markdown(value="Upload a document and click Extract to begin.")

            # Wire up extraction
            extract_btn.click(
                fn=sync_extract_document,
                inputs=[file_upload, extractor_select],
                outputs=results_md
            )

            # Update extractor dropdown when configuration changes
            configure_btn.click(
                fn=lambda: gr.update(choices=list(configured_extractors.keys())),
                outputs=extractor_select
            )

        # Instructions
        with gr.Tab("📖 Instructions"):
            gr.Markdown("""
## How to Use

### 1. Configure Extractor
Go to the **Configuration** tab and adjust the Docling settings:

**Basic Options:**
- **Do OCR**: Enable optical character recognition for scanned documents
- **Do Table Structure**: Enable table recognition and extraction
- **Table Structure Mode**: Choose between FAST (faster) and ACCURATE (better quality)
- **Num Threads**: Number of CPU threads to use for processing

**Advanced Options** (click to expand):
- Various enrichment options (code, formulas, pictures)
- Image generation settings
- Hardware acceleration
- Timeouts and other advanced settings

Click "Save Configuration" to create an extractor with these settings.

### 2. Extract Documents
Go to the **Extract** tab:
1. Upload a document (PDF, DOCX, etc.)
2. Select your configured extractor from the dropdown
3. Click "Extract Markdown" to process the document

### 3. Compare Configurations
You can create multiple configurations with different settings and compare
their performance and output quality.

## Tips
- Start with default settings to test the basics
- Use FAST mode for quick experiments, ACCURATE for production
- Enable OCR only if you have scanned documents (it's slower)
- Adjust num_threads based on your CPU cores for best performance
            """)

    return demo


if __name__ == "__main__":
    # Check if Docling is available
    try:
        from benchmarkdown.docling import DoclingExtractor
        print("✓ Docling extractor available")
    except ImportError as e:
        print(f"❌ Docling not available: {e}")
        print("   Install with: uv sync --group docling")
        exit(1)

    print("\n🚀 Starting Benchmarkdown UI with configuration support...")

    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )
