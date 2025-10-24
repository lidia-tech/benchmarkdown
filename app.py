#!/usr/bin/env python3
"""
Main application file for Benchmarkdown Gradio UI.

This script initializes the extractors and launches the Gradio interface with
configuration support for Docling extractors.

Users can:
1. Use pre-configured extractors (default Docling and Textract if available)
2. Create custom Docling configurations through the Configuration tab
3. Compare different extractor configurations side-by-side
"""

import os
import gradio as gr
from benchmarkdown.ui import BenchmarkUI

# Check available extractors
has_docling = False
has_textract = False

try:
    from benchmarkdown.docling import DoclingExtractor
    from benchmarkdown.config import DoclingConfig
    from benchmarkdown.config_ui import (
        create_gradio_component_from_field,
        build_config_from_ui_values,
        DOCLING_BASIC_FIELDS,
        DOCLING_ADVANCED_FIELDS
    )
    has_docling = True
    print("✓ Docling extractor available")
except ImportError as e:
    print(f"⚠️  Docling not available: {e}")
    print("   Install with: uv sync --group docling")

try:
    from benchmarkdown.textract import TextractExtractor
    from textractor.data.constants import TextractFeatures
    s3_bucket = os.environ.get("TEXTRACT_S3_BUCKET", "your-bucket-name")
    if s3_bucket != "your-bucket-name":
        has_textract = True
        print("✓ AWS Textract extractor available")
    else:
        print("⚠️  AWS Textract available but not configured")
        print("   Set TEXTRACT_S3_BUCKET environment variable")
except ImportError as e:
    print(f"⚠️  AWS Textract not available: {e}")
    print("   Install with: uv sync --group textract")

if not has_docling and not has_textract:
    print("\n❌ No extractors available! Please install at least one:")
    print("   - Docling: uv sync --group docling")
    print("   - Textract: uv sync --group textract")
    exit(1)


def create_enhanced_ui():
    """Create the enhanced UI with configuration support."""
    ui = BenchmarkUI()

    # Register default extractors
    if has_docling:
        default_extractor = DoclingExtractor()
        ui.register_extractor("Docling (Default)", default_extractor, cost_per_page=None)
        print("  → Registered: Docling (Default)")

    if has_textract:
        s3_path = f"s3://{s3_bucket}/textract-temp/"
        textract_extractor = TextractExtractor(
            s3_upload_path=s3_path,
            features=[TextractFeatures.LAYOUT, TextractFeatures.TABLES]
        )
        ui.register_extractor("Textract (Layout+Tables)", textract_extractor, cost_per_page=0.05)
        print("  → Registered: Textract (Layout+Tables)")

    with gr.Blocks(title="Benchmarkdown - Document Extraction Comparison") as demo:
        gr.Markdown("# 📄 Benchmarkdown - Document Extraction Comparison")
        gr.Markdown("Configure extractors, upload documents, and compare results.")

        with gr.Tabs():
            # Tab 1: Configuration (only if Docling is available)
            if has_docling:
                with gr.Tab("⚙️ Configuration"):
                    gr.Markdown("## Configure Docling Extractors")
                    gr.Markdown("Create custom Docling configurations to compare different settings.")

                    # Configuration name input
                    with gr.Row():
                        config_name_input = gr.Textbox(
                            label="Configuration Name",
                            placeholder="e.g., 'Fast Mode' or 'No OCR'",
                            value=""
                        )

                    # Generate configuration UI
                    config_components = []

                    # Basic options
                    with gr.Group():
                        gr.Markdown("### Basic Options")
                        for field_name in DOCLING_BASIC_FIELDS:
                            if field_name not in DoclingConfig.model_fields:
                                continue
                            field_info = DoclingConfig.model_fields[field_name]
                            field_type = field_info.annotation
                            component, comp_id = create_gradio_component_from_field(
                                field_name, field_info, field_type
                            )
                            config_components.append(component)

                    # Advanced options
                    with gr.Accordion("Advanced Options", open=False):
                        for field_name in DOCLING_ADVANCED_FIELDS:
                            if field_name not in DoclingConfig.model_fields:
                                continue
                            field_info = DoclingConfig.model_fields[field_name]
                            field_type = field_info.annotation
                            component, comp_id = create_gradio_component_from_field(
                                field_name, field_info, field_type
                            )
                            config_components.append(component)

                    # Save configuration button
                    with gr.Row():
                        save_config_btn = gr.Button("💾 Save Configuration", variant="primary", size="lg")
                        config_status = gr.Textbox(
                            label="Status",
                            interactive=False,
                            value="Configure settings above and click Save"
                        )

                    def save_configuration(config_name, *config_values):
                        """Save a new Docling configuration."""
                        if not config_name:
                            return "❌ Please enter a configuration name"

                        # Build config from UI values
                        all_fields = DOCLING_BASIC_FIELDS + DOCLING_ADVANCED_FIELDS
                        ui_values = {field: value for field, value in zip(all_fields, config_values)}
                        config = build_config_from_ui_values(DoclingConfig, ui_values)

                        # Create extractor with this config
                        extractor = DoclingExtractor(config=config)

                        # Register with UI
                        full_name = f"Docling ({config_name})"
                        ui.register_extractor(full_name, extractor, cost_per_page=None)

                        return f"✓ Saved configuration: {full_name}\n  OCR={config.do_ocr}, Tables={config.do_table_structure}, Mode={config.table_structure_mode}, Threads={config.num_threads}"

                    save_config_btn.click(
                        fn=save_configuration,
                        inputs=[config_name_input] + config_components,
                        outputs=config_status
                    )

            # Tab 2: Extract & Compare (main workflow)
            with gr.Tab("🚀 Extract & Compare"):
                gr.Markdown("## 📄 Upload Documents")
                file_upload = gr.File(
                    label="Upload PDF, DOCX, or other documents",
                    file_count="multiple",
                    file_types=[".pdf", ".docx", ".doc", ".txt"]
                )

                gr.Markdown("## ✓ Select Extractors")
                extractor_choices = gr.CheckboxGroup(
                    choices=list(ui.extractors.keys()),
                    label="Choose which extractors to test",
                    value=list(ui.extractors.keys())  # All selected by default
                )

                with gr.Row():
                    extract_btn = gr.Button("🚀 Extract All", variant="primary", size="lg")
                    clear_btn = gr.Button("🗑️ Clear", size="lg")

                # Results section
                gr.Markdown("## 📋 Processing Results")
                results_table = gr.HTML(value="<p>No results yet. Upload documents and click 'Extract All' to begin.</p>")

                # Document selector and view controls (initially hidden)
                with gr.Row(visible=False) as controls_row:
                    document_selector = gr.Dropdown(
                        label="Select Document to View",
                        choices=[],
                        value=None,
                        interactive=True
                    )
                    view_mode = gr.Radio(
                        choices=["Tabbed", "Side-by-Side"],
                        value="Tabbed",
                        label="View Mode"
                    )

                # Download buttons
                with gr.Row(visible=False) as download_row:
                    download_zip_btn = gr.Button("📦 Download All (ZIP)", size="sm")
                    download_report_btn = gr.Button("📊 Generate Report (HTML)", size="sm")

                download_zip_file = gr.File(label="ZIP Download", visible=False)
                download_report_file = gr.File(label="Report Download", visible=False)

                # Visual Comparison
                comparison_view = gr.HTML(value="")

                # Event handlers
                import asyncio

                def sync_process_documents(files, selected_extractors):
                    """Synchronous wrapper for async processing."""
                    result = asyncio.run(ui.process_documents(files, selected_extractors))

                    # Get list of filenames for dropdown
                    filenames = list(ui.results.keys()) if ui.results else []
                    first_filename = filenames[0] if filenames else None

                    # Generate initial comparison view
                    comparison = ""
                    if first_filename:
                        comparison = ui.generate_comparison_view_tabbed(first_filename)

                    # Return results + show controls
                    return (
                        result[0],  # results_table
                        gr.update(visible=True, choices=filenames, value=first_filename),  # document_selector
                        gr.update(visible=True),  # controls_row
                        gr.update(visible=True),  # download_row
                        comparison,  # comparison_view
                        gr.update(choices=list(ui.extractors.keys()), value=list(ui.extractors.keys()))  # extractor_choices
                    )

                def update_comparison_view(filename, view_mode_val):
                    """Update comparison view based on selected document and view mode."""
                    if not filename:
                        return ""
                    if view_mode_val == "Side-by-Side":
                        return ui.generate_comparison_view_sidebyside(filename)
                    else:
                        return ui.generate_comparison_view_tabbed(filename)

                def download_zip():
                    """Generate and return ZIP file."""
                    zip_path = ui.get_download_zip()
                    return gr.update(value=zip_path, visible=True) if zip_path else None

                def download_report():
                    """Generate and return HTML report."""
                    report_path = ui.get_comparison_report()
                    return gr.update(value=report_path, visible=True) if report_path else None

                extract_btn.click(
                    fn=sync_process_documents,
                    inputs=[file_upload, extractor_choices],
                    outputs=[results_table, document_selector, controls_row, download_row, comparison_view, extractor_choices],
                )

                document_selector.change(
                    fn=update_comparison_view,
                    inputs=[document_selector, view_mode],
                    outputs=[comparison_view]
                )

                view_mode.change(
                    fn=update_comparison_view,
                    inputs=[document_selector, view_mode],
                    outputs=[comparison_view]
                )

                download_zip_btn.click(
                    fn=download_zip,
                    outputs=[download_zip_file]
                )

                download_report_btn.click(
                    fn=download_report,
                    outputs=[download_report_file]
                )

                clear_btn.click(
                    fn=lambda: (
                        None,  # file_upload
                        "<p>No results yet.</p>",  # results_table
                        "",  # comparison_view
                        gr.update(visible=False, choices=[], value=None),  # document_selector
                        gr.update(visible=False),  # controls_row
                        gr.update(visible=False),  # download_row
                        gr.update(visible=False),  # download_zip_file
                        gr.update(visible=False),  # download_report_file
                    ),
                    outputs=[
                        file_upload,
                        results_table,
                        comparison_view,
                        document_selector,
                        controls_row,
                        download_row,
                        download_zip_file,
                        download_report_file
                    ]
                )

        return demo

print(f"\n🚀 Starting Benchmarkdown UI...")
demo = create_enhanced_ui()

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )
