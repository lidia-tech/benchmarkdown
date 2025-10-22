"""
Gradio UI for benchmarking document-to-markdown extraction tools.
"""

import asyncio
import os
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import tempfile

import gradio as gr


@dataclass
class ExtractionResult:
    """Stores the result of a document extraction."""
    extractor_name: str
    filename: str
    markdown: str
    execution_time: float
    character_count: int
    word_count: int
    error: Optional[str] = None
    warnings: list[str] = None
    cost_estimate: Optional[float] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class BenchmarkUI:
    """Main UI class for the Benchmarkdown application."""

    def __init__(self):
        self.extractors = {}
        self.results = {}  # filename -> {extractor_name -> ExtractionResult}
        self.temp_dir = tempfile.mkdtemp()

    def register_extractor(self, name: str, extractor, cost_per_page: Optional[float] = None):
        """Register an extractor implementation.

        Args:
            name: Display name for the extractor
            extractor: Instance implementing the MarkdownExtractor protocol
            cost_per_page: Optional cost estimate per page (for cloud services)
        """
        self.extractors[name] = {
            "instance": extractor,
            "cost_per_page": cost_per_page
        }

    async def process_document(
        self,
        file_path: str,
        extractor_name: str,
    ) -> ExtractionResult:
        """Process a single document with a single extractor."""
        extractor_info = self.extractors[extractor_name]
        extractor = extractor_info["instance"]

        start_time = time.time()
        error = None
        markdown = ""
        warnings = []

        try:
            markdown = await extractor.extract_markdown(file_path)
        except Exception as e:
            error = str(e)
            warnings.append(f"Extraction failed: {str(e)}")

        execution_time = time.time() - start_time

        # Calculate metrics
        char_count = len(markdown)
        word_count = len(markdown.split())

        # Estimate cost (simplified - just using a rough page count)
        cost_estimate = None
        if extractor_info["cost_per_page"]:
            # Rough estimate: 3000 chars per page
            estimated_pages = max(1, char_count // 3000)
            cost_estimate = estimated_pages * extractor_info["cost_per_page"]

        return ExtractionResult(
            extractor_name=extractor_name,
            filename=os.path.basename(file_path),
            markdown=markdown,
            execution_time=execution_time,
            character_count=char_count,
            word_count=word_count,
            error=error,
            warnings=warnings,
            cost_estimate=cost_estimate,
        )

    async def process_documents(
        self,
        files: list,
        selected_extractors: list[str],
        progress=gr.Progress(),
    ):
        """Process multiple documents with selected extractors."""
        if not files:
            return "No files uploaded", "", ""

        if not selected_extractors:
            return "No extractors selected", "", ""

        total_tasks = len(files) * len(selected_extractors)
        current_task = 0

        self.results = {}

        for file_obj in files:
            file_path = file_obj.name
            filename = os.path.basename(file_path)
            self.results[filename] = {}

            # Process with all selected extractors in parallel
            tasks = []
            for extractor_name in selected_extractors:
                tasks.append(self.process_document(file_path, extractor_name))

            results = await asyncio.gather(*tasks)

            for result in results:
                self.results[filename][result.extractor_name] = result
                current_task += 1
                progress(current_task / total_tasks, desc=f"Processing {filename} with {result.extractor_name}")

        # Generate results table
        results_table = self.generate_results_table()

        # Generate comparison view for first document
        if files:
            first_filename = os.path.basename(files[0].name)
            comparison_tabs = self.generate_comparison_view(first_filename)
            return results_table, comparison_tabs, self.generate_download_options()

        return results_table, "", ""

    def generate_results_table(self) -> str:
        """Generate HTML table of results."""
        if not self.results:
            return "<p>No results yet. Upload documents and click 'Extract All' to begin.</p>"

        html = "<div style='font-family: monospace;'>"

        for filename, extractors in self.results.items():
            html += f"<h3>📋 {filename}</h3>"
            html += "<table style='width:100%; border-collapse: collapse; margin-bottom: 20px;'>"
            html += """
            <tr style='background-color: #f0f0f0; border-bottom: 2px solid #ccc;'>
                <th style='padding: 8px; text-align: left;'>Extractor</th>
                <th style='padding: 8px; text-align: left;'>Time</th>
                <th style='padding: 8px; text-align: left;'>Chars / Words</th>
                <th style='padding: 8px; text-align: left;'>Status</th>
            </tr>
            """

            for extractor_name, result in extractors.items():
                status = "✓ OK" if not result.error else f"✗ Error"
                cost_str = f" (~${result.cost_estimate:.3f})" if result.cost_estimate else ""

                html += f"""
                <tr style='border-bottom: 1px solid #eee;'>
                    <td style='padding: 8px;'>{result.extractor_name}</td>
                    <td style='padding: 8px;'>{result.execution_time:.1f}s{cost_str}</td>
                    <td style='padding: 8px;'>{result.character_count:,} / {result.word_count:,}</td>
                    <td style='padding: 8px;'>{status}</td>
                </tr>
                """

            html += "</table>"

        html += "</div>"
        return html

    def generate_comparison_view_tabbed(self, filename: str) -> str:
        """Generate tabbed comparison view for a specific document."""
        if filename not in self.results:
            return "<p>No results for this document.</p>"

        results = self.results[filename]

        # Create tabs for each extractor
        html = "<div style='font-family: system-ui, -apple-system, sans-serif;'>"
        html += f"<h3>📊 Extraction Comparison - {filename}</h3>"

        for extractor_name, result in results.items():
            html += f"<h4>{extractor_name}</h4>"

            if result.error:
                html += f"<div style='color: red; padding: 10px; background: #fee; border-radius: 4px; margin-bottom: 20px;'>Error: {result.error}</div>"
                continue

            # Rendered markdown preview
            html += "<div style='margin: 10px 0;'>"
            html += "<strong>Rendered Markdown:</strong>"
            html += f"<div style='border: 1px solid #ddd; padding: 15px; background: white; border-radius: 4px; max-height: 400px; overflow-y: auto;'>{result.markdown}</div>"
            html += "</div>"

            # Raw markdown
            html += "<div style='margin: 10px 0;'>"
            html += "<strong>Raw Markdown:</strong>"
            html += f"<pre style='border: 1px solid #ddd; padding: 15px; background: #f5f5f5; border-radius: 4px; max-height: 300px; overflow-y: auto; white-space: pre-wrap;'>{result.markdown}</pre>"
            html += "</div>"

            if result.warnings:
                html += "<div style='margin: 10px 0;'>"
                html += "<strong>⚠️ Warnings:</strong>"
                html += "<ul>"
                for warning in result.warnings:
                    html += f"<li>{warning}</li>"
                html += "</ul>"
                html += "</div>"

            html += "<hr style='margin: 30px 0;'>"

        html += "</div>"
        return html

    def generate_comparison_view_sidebyside(self, filename: str) -> str:
        """Generate side-by-side comparison view for a specific document."""
        if filename not in self.results:
            return "<p>No results for this document.</p>"

        results = self.results[filename]

        html = "<div style='font-family: system-ui, -apple-system, sans-serif;'>"
        html += f"<h3>📊 Side-by-Side Comparison - {filename}</h3>"

        # Create columns
        html += "<div style='display: flex; gap: 20px; overflow-x: auto;'>"

        for extractor_name, result in results.items():
            html += f"<div style='flex: 1; min-width: 400px; border: 1px solid #ddd; border-radius: 8px; padding: 15px;'>"
            html += f"<h4 style='margin-top: 0;'>{extractor_name}</h4>"

            if result.error:
                html += f"<div style='color: red; padding: 10px; background: #fee; border-radius: 4px;'>Error: {result.error}</div>"
            else:
                html += f"<div style='font-size: 0.9em; color: #666; margin-bottom: 10px;'>"
                html += f"Time: {result.execution_time:.1f}s | {result.word_count:,} words"
                if result.cost_estimate:
                    html += f" | ~${result.cost_estimate:.3f}"
                html += "</div>"

                # Rendered preview
                html += f"<div style='border: 1px solid #ddd; padding: 10px; background: white; border-radius: 4px; max-height: 500px; overflow-y: auto; font-size: 0.9em;'>{result.markdown[:2000]}{'...' if len(result.markdown) > 2000 else ''}</div>"

            html += "</div>"

        html += "</div>"
        html += "</div>"
        return html

    def get_download_file(self, filename: str, extractor_name: str) -> str:
        """Get path to a specific result markdown file."""
        if filename not in self.results or extractor_name not in self.results[filename]:
            return None

        result = self.results[filename][extractor_name]
        if result.error:
            return None

        # Save to temp file
        safe_extractor = extractor_name.replace(" ", "_").replace("(", "").replace(")", "")
        safe_filename = os.path.splitext(filename)[0]
        output_path = os.path.join(self.temp_dir, f"{safe_filename}_{safe_extractor}.md")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.markdown)

        return output_path

    def get_download_zip(self) -> str:
        """Create a ZIP file with all results."""
        if not self.results:
            return None

        zip_path = os.path.join(self.temp_dir, "benchmarkdown_results.zip")

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for filename, extractors in self.results.items():
                for extractor_name, result in extractors.items():
                    if not result.error:
                        safe_extractor = extractor_name.replace(" ", "_").replace("(", "").replace(")", "")
                        safe_filename = os.path.splitext(filename)[0]
                        arc_name = f"{safe_filename}_{safe_extractor}.md"
                        zipf.writestr(arc_name, result.markdown)

        return zip_path

    def get_comparison_report(self) -> str:
        """Generate an HTML comparison report."""
        if not self.results:
            return None

        report_path = os.path.join(self.temp_dir, "comparison_report.html")

        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Benchmarkdown Comparison Report</title>
    <style>
        body { font-family: system-ui, -apple-system, sans-serif; margin: 40px; }
        h1 { color: #333; }
        h2 { color: #666; margin-top: 40px; }
        h3 { color: #888; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #f0f0f0; }
        .result { border: 1px solid #ddd; padding: 20px; margin: 20px 0; border-radius: 8px; }
        .markdown-preview { border: 1px solid #ddd; padding: 15px; background: #fafafa; max-height: 400px; overflow-y: auto; }
        .error { color: red; background: #fee; padding: 10px; border-radius: 4px; }
        .timestamp { color: #999; font-size: 0.9em; }
    </style>
</head>
<body>
    <h1>📊 Benchmarkdown Comparison Report</h1>
    <p class="timestamp">Generated: """ + time.strftime("%Y-%m-%d %H:%M:%S") + """</p>
"""

        for filename, extractors in self.results.items():
            html += f"<h2>📄 {filename}</h2>"

            # Summary table
            html += "<table><tr><th>Extractor</th><th>Time</th><th>Characters</th><th>Words</th><th>Status</th></tr>"
            for extractor_name, result in extractors.items():
                status = "✓ OK" if not result.error else "✗ Error"
                cost = f" (~${result.cost_estimate:.3f})" if result.cost_estimate else ""
                html += f"""
                <tr>
                    <td>{extractor_name}</td>
                    <td>{result.execution_time:.1f}s{cost}</td>
                    <td>{result.character_count:,}</td>
                    <td>{result.word_count:,}</td>
                    <td>{status}</td>
                </tr>
                """
            html += "</table>"

            # Individual results
            for extractor_name, result in extractors.items():
                html += f"<div class='result'><h3>{extractor_name}</h3>"
                if result.error:
                    html += f"<div class='error'>Error: {result.error}</div>"
                else:
                    html += f"<div class='markdown-preview'>{result.markdown}</div>"
                html += "</div>"

        html += "</body></html>"

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)

        return report_path

    def create_interface(self):
        """Create the Gradio interface."""
        with gr.Blocks(title="Benchmarkdown - Document Extraction Comparison") as demo:
            gr.Markdown("# 📄 Benchmarkdown - Document Extraction Comparison")
            gr.Markdown("Upload documents, select extractors, and compare the results.")

            # Section 1: Input & Configuration
            with gr.Group():
                gr.Markdown("## 📄 Upload Documents")
                file_upload = gr.File(
                    label="Upload PDF, DOCX, or other documents",
                    file_count="multiple",
                    file_types=[".pdf", ".docx", ".doc", ".txt"]
                )

                gr.Markdown("## ✓ Select Extractors")
                extractor_choices = gr.CheckboxGroup(
                    choices=list(self.extractors.keys()),
                    label="Choose which extractors to test",
                    value=list(self.extractors.keys())  # All selected by default
                )

                gr.Markdown("## 📊 Optional Ground Truth (Coming Soon)")
                ground_truth_upload = gr.File(
                    label="Upload reference markdown files for quality metrics (optional)",
                    file_count="multiple",
                    visible=False  # Hide for now, future feature
                )

                with gr.Row():
                    extract_btn = gr.Button("🚀 Extract All", variant="primary", size="lg")
                    clear_btn = gr.Button("🗑️ Clear", size="lg")

            # Section 2: Results Overview
            with gr.Group():
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

            # Section 3: Visual Comparison
            with gr.Group():
                comparison_view = gr.HTML(value="")

            # Event handlers
            def sync_process_documents(files, selected_extractors):
                """Synchronous wrapper for async processing."""
                result = asyncio.run(self.process_documents(files, selected_extractors))

                # Get list of filenames for dropdown
                filenames = list(self.results.keys()) if self.results else []
                first_filename = filenames[0] if filenames else None

                # Generate initial comparison view
                comparison = ""
                if first_filename:
                    comparison = self.generate_comparison_view_tabbed(first_filename)

                # Return results + show controls
                return (
                    result[0],  # results_table
                    gr.update(visible=True, choices=filenames, value=first_filename),  # document_selector
                    gr.update(visible=True),  # controls_row
                    gr.update(visible=True),  # download_row
                    comparison  # comparison_view
                )

            def update_comparison_view(filename, view_mode):
                """Update comparison view based on selected document and view mode."""
                if not filename:
                    return ""

                if view_mode == "Side-by-Side":
                    return self.generate_comparison_view_sidebyside(filename)
                else:
                    return self.generate_comparison_view_tabbed(filename)

            def download_zip():
                """Generate and return ZIP file."""
                zip_path = self.get_download_zip()
                return gr.update(value=zip_path, visible=True) if zip_path else None

            def download_report():
                """Generate and return HTML report."""
                report_path = self.get_comparison_report()
                return gr.update(value=report_path, visible=True) if report_path else None

            extract_btn.click(
                fn=sync_process_documents,
                inputs=[file_upload, extractor_choices],
                outputs=[results_table, document_selector, controls_row, download_row, comparison_view],
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
                    None,  # ground_truth_upload
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
                    ground_truth_upload,
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


def create_ui(extractors: dict = None) -> gr.Blocks:
    """
    Create and configure the Benchmarkdown UI.

    Args:
        extractors: Dictionary mapping extractor names to their instances
                   e.g., {"Docling": docling_extractor, "AWS Textract": textract_extractor}

    Returns:
        Configured Gradio Blocks interface
    """
    ui = BenchmarkUI()

    if extractors:
        for name, extractor_config in extractors.items():
            if isinstance(extractor_config, dict):
                ui.register_extractor(
                    name,
                    extractor_config["instance"],
                    extractor_config.get("cost_per_page")
                )
            else:
                ui.register_extractor(name, extractor_config)

    return ui.create_interface()
