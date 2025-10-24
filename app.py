#!/usr/bin/env python3
"""
Benchmarkdown - Redesigned UI with clearer workflow.

Workflow:
1. Select extractor engine (Docling, Textract, etc.)
2. Configure settings (load profile or customize)
3. Add to extraction queue
4. Upload documents and run all configured extractors
5. Compare results
"""

import os
import asyncio
import gradio as gr
from benchmarkdown.ui import BenchmarkUI
from benchmarkdown.docling import DoclingExtractor
from benchmarkdown.config import DoclingConfig
from benchmarkdown.config_ui import (
    create_gradio_component_from_field,
    build_config_from_ui_values,
    DOCLING_BASIC_FIELDS,
    DOCLING_ADVANCED_FIELDS
)

# Check available extractors
has_docling = False
has_textract = False

try:
    from benchmarkdown.docling import DoclingExtractor
    has_docling = True
    print("✓ Docling extractor available")
except ImportError as e:
    print(f"⚠️  Docling not available: {e}")

try:
    from benchmarkdown.textract import TextractExtractor
    from textractor.data.constants import TextractFeatures
    s3_bucket = os.environ.get("TEXTRACT_S3_BUCKET", "your-bucket-name")
    if s3_bucket != "your-bucket-name":
        has_textract = True
        print("✓ AWS Textract extractor available")
    else:
        print("⚠️  AWS Textract not configured (set TEXTRACT_S3_BUCKET)")
except ImportError:
    print("⚠️  AWS Textract not available")

if not has_docling and not has_textract:
    print("\n❌ No extractors available! Install with: uv sync --group docling")
    exit(1)


def create_app():
    """Create the redesigned Gradio interface."""
    ui = BenchmarkUI()

    # State for extractor queue
    extractor_queue = []  # List of (name, extractor) tuples

    with gr.Blocks(title="Benchmarkdown - Document Extraction Comparison") as demo:
        gr.Markdown("# 📄 Benchmarkdown - Document Extraction Comparison")
        gr.Markdown("Configure extractors, run comparisons, analyze results.")

        # ============================================================
        # SECTION 1: Configure Extractors
        # ============================================================
        with gr.Group():
            gr.Markdown("## 1️⃣ Configure Extractors")

            # Step 1: Select Engine
            extractor_engines = []
            if has_docling:
                extractor_engines.append("Docling")
            if has_textract:
                extractor_engines.append("AWS Textract")

            with gr.Row():
                engine_selector = gr.Dropdown(
                    choices=extractor_engines,
                    label="Select Extractor Engine",
                    value=extractor_engines[0] if extractor_engines else None,
                    interactive=True
                )
                config_name_input = gr.Textbox(
                    label="Configuration Name",
                    placeholder="e.g., 'Fast Mode', 'High Quality', etc.",
                    value=""
                )

            # Configuration area (changes based on selected engine)
            with gr.Column(visible=has_docling) as docling_config_area:
                gr.Markdown("### Docling Configuration")

                # Generate Docling config UI
                docling_components = []

                with gr.Group():
                    gr.Markdown("#### Basic Options")
                    for field_name in DOCLING_BASIC_FIELDS:
                        if field_name not in DoclingConfig.model_fields:
                            continue
                        field_info = DoclingConfig.model_fields[field_name]
                        field_type = field_info.annotation
                        component, _ = create_gradio_component_from_field(
                            field_name, field_info, field_type
                        )
                        docling_components.append(component)

                with gr.Accordion("Advanced Options", open=False):
                    for field_name in DOCLING_ADVANCED_FIELDS:
                        if field_name not in DoclingConfig.model_fields:
                            continue
                        field_info = DoclingConfig.model_fields[field_name]
                        field_type = field_info.annotation
                        component, _ = create_gradio_component_from_field(
                            field_name, field_info, field_type
                        )
                        docling_components.append(component)

            with gr.Column(visible=False) as textract_config_area:
                gr.Markdown("### AWS Textract Configuration")
                gr.Markdown("*Configuration options coming soon*")

            # Add to queue button
            with gr.Row():
                add_to_queue_btn = gr.Button(
                    "➕ Add to Extraction Queue",
                    variant="primary",
                    size="lg"
                )
                queue_status = gr.Textbox(
                    label="Status",
                    value="Select engine and configure settings above",
                    interactive=False
                )

        # ============================================================
        # SECTION 2: Extraction Queue
        # ============================================================
        with gr.Group():
            gr.Markdown("## 2️⃣ Extraction Queue")
            gr.Markdown("Configured extractors that will be used for comparison:")

            queue_display = gr.HTML(
                value="<p style='color: #666;'>No extractors configured yet. Add one above.</p>"
            )

            with gr.Row():
                clear_queue_btn = gr.Button("🗑️ Clear Queue", size="sm")

        # ============================================================
        # SECTION 3: Extract Documents
        # ============================================================
        with gr.Group():
            gr.Markdown("## 3️⃣ Extract & Compare")

            file_upload = gr.File(
                label="Upload Documents (PDF, DOCX, etc.)",
                file_count="multiple",
                file_types=[".pdf", ".docx", ".doc", ".txt"]
            )

            with gr.Row():
                extract_btn = gr.Button(
                    "🚀 Run Extraction",
                    variant="primary",
                    size="lg"
                )
                clear_results_btn = gr.Button("🗑️ Clear Results", size="lg")

            results_table = gr.HTML(
                value="<p>Upload documents and click 'Run Extraction' to begin.</p>"
            )

            # Results controls (hidden initially)
            with gr.Row(visible=False) as results_controls:
                document_selector = gr.Dropdown(
                    label="Select Document to View",
                    choices=[],
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

            # Comparison view
            comparison_view = gr.HTML(value="")

        # ============================================================
        # Event Handlers
        # ============================================================

        def toggle_config_area(engine):
            """Show/hide config areas based on selected engine."""
            if engine == "Docling":
                return gr.update(visible=True), gr.update(visible=False)
            elif engine == "AWS Textract":
                return gr.update(visible=False), gr.update(visible=True)
            else:
                return gr.update(visible=False), gr.update(visible=False)

        def add_to_queue(engine, config_name, *config_values):
            """Add configured extractor to queue."""
            if not config_name:
                return "❌ Please enter a configuration name", generate_queue_html()

            if engine == "Docling":
                # Build config
                all_fields = DOCLING_BASIC_FIELDS + DOCLING_ADVANCED_FIELDS
                ui_values = {field: value for field, value in zip(all_fields, config_values)}
                config = build_config_from_ui_values(DoclingConfig, ui_values)

                # Create extractor
                extractor = DoclingExtractor(config=config)
                full_name = f"Docling ({config_name})"

                # Add to queue
                extractor_queue.append((full_name, extractor, None))  # (name, instance, cost)
                ui.register_extractor(full_name, extractor, cost_per_page=None)

                status = f"✓ Added: {full_name}\n  Settings: OCR={config.do_ocr}, Tables={config.do_table_structure}, Mode={config.table_structure_mode}"
            elif engine == "AWS Textract":
                # TODO: Implement Textract configuration
                return "⚠️  Textract configuration not yet implemented", generate_queue_html()
            else:
                return "❌ Unknown engine", generate_queue_html()

            return status, generate_queue_html()

        def generate_queue_html():
            """Generate HTML for the queue display."""
            if not extractor_queue:
                return "<p style='color: #666;'>No extractors configured yet. Add one above.</p>"

            html = "<div style='font-family: system-ui, sans-serif;'>"
            for i, (name, extractor, cost) in enumerate(extractor_queue):
                html += f"""
                <div style='border: 1px solid #ddd; padding: 12px; margin: 8px 0; border-radius: 4px; background: #f9f9f9;'>
                    <strong>{i+1}. {name}</strong>
                </div>
                """
            html += "</div>"
            return html

        def clear_queue():
            """Clear the extraction queue."""
            extractor_queue.clear()
            # Clear UI registry but keep it functional
            ui.extractors.clear()
            return (
                generate_queue_html(),
                "Queue cleared"
            )

        def sync_process_documents(files):
            """Process documents with all queued extractors."""
            if not extractor_queue:
                return (
                    "<p style='color: red;'>❌ No extractors in queue. Please configure at least one extractor.</p>",
                    gr.update(visible=False),
                    gr.update(visible=False),
                    ""
                )

            if not files:
                return (
                    "<p style='color: red;'>❌ No files uploaded.</p>",
                    gr.update(visible=False),
                    gr.update(visible=False),
                    ""
                )

            # Get all extractor names from queue
            extractor_names = [name for name, _, _ in extractor_queue]

            # Process documents
            result = asyncio.run(ui.process_documents(files, extractor_names))

            # Get filenames for dropdown
            filenames = list(ui.results.keys()) if ui.results else []
            first_filename = filenames[0] if filenames else None

            # Generate comparison view
            comparison = ""
            if first_filename:
                comparison = ui.generate_comparison_view_tabbed(first_filename)

            return (
                result[0],  # results_table
                gr.update(visible=True, choices=filenames, value=first_filename),  # results_controls
                gr.update(visible=True),  # download_row
                comparison  # comparison_view
            )

        def update_comparison(filename, view_mode_val):
            """Update comparison view."""
            if not filename:
                return ""
            if view_mode_val == "Side-by-Side":
                return ui.generate_comparison_view_sidebyside(filename)
            else:
                return ui.generate_comparison_view_tabbed(filename)

        # Wire up events
        engine_selector.change(
            fn=toggle_config_area,
            inputs=[engine_selector],
            outputs=[docling_config_area, textract_config_area]
        )

        add_to_queue_btn.click(
            fn=add_to_queue,
            inputs=[engine_selector, config_name_input] + docling_components,
            outputs=[queue_status, queue_display]
        )

        clear_queue_btn.click(
            fn=clear_queue,
            outputs=[queue_display, queue_status]
        )

        extract_btn.click(
            fn=sync_process_documents,
            inputs=[file_upload],
            outputs=[results_table, results_controls, download_row, comparison_view]
        )

        document_selector.change(
            fn=update_comparison,
            inputs=[document_selector, view_mode],
            outputs=[comparison_view]
        )

        view_mode.change(
            fn=update_comparison,
            inputs=[document_selector, view_mode],
            outputs=[comparison_view]
        )

        download_zip_btn.click(
            fn=lambda: gr.update(value=ui.get_download_zip(), visible=True) if ui.get_download_zip() else None,
            outputs=[download_zip_file]
        )

        download_report_btn.click(
            fn=lambda: gr.update(value=ui.get_comparison_report(), visible=True) if ui.get_comparison_report() else None,
            outputs=[download_report_file]
        )

        clear_results_btn.click(
            fn=lambda: (
                None,  # file_upload
                "<p>Upload documents and click 'Run Extraction' to begin.</p>",  # results_table
                "",  # comparison_view
                gr.update(visible=False, choices=[], value=None),  # results_controls
                gr.update(visible=False),  # download_row
                gr.update(visible=False),  # download_zip_file
                gr.update(visible=False),  # download_report_file
            ),
            outputs=[
                file_upload,
                results_table,
                comparison_view,
                results_controls,
                download_row,
                download_zip_file,
                download_report_file
            ]
        )

    return demo


if __name__ == "__main__":
    print("\n🚀 Starting Benchmarkdown UI (Redesigned)...")
    demo = create_app()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )
