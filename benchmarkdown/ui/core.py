"""
Core UI classes for benchmarking document-to-markdown extraction tools.
"""

import asyncio
import os
import time
import zipfile
from dataclasses import dataclass
from typing import Optional
import tempfile

import markdown


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

    def register_extractor(self, name: str, extractor):
        """Register an extractor implementation.

        Args:
            name: Display name for the extractor
            extractor: Instance implementing the MarkdownExtractor protocol
        """
        self.extractors[name] = {
            "instance": extractor
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
        markdown_text = ""
        warnings = []

        try:
            markdown_text = await extractor.extract_markdown(file_path)
        except Exception as e:
            error = str(e)
            warnings.append(f"Extraction failed: {str(e)}")

        execution_time = time.time() - start_time

        # Calculate metrics
        char_count = len(markdown_text)
        word_count = len(markdown_text.split())

        return ExtractionResult(
            extractor_name=extractor_name,
            filename=os.path.basename(file_path),
            markdown=markdown_text,
            execution_time=execution_time,
            character_count=char_count,
            word_count=word_count,
            error=error,
            warnings=warnings,
        )

    async def process_documents(
        self,
        files: list,
        selected_extractors: list[str],
        progress_callback=None,
    ):
        """Process multiple documents with selected extractors."""
        if not files:
            return ("<p style='color: red;'>❌ No files uploaded.</p>",)

        if not selected_extractors:
            return ("<p style='color: red;'>❌ No extractors selected.</p>",)

        self.results = {}

        # Calculate total operations for progress tracking
        num_files = len(files)
        num_extractors = len(selected_extractors)
        total_operations = num_files * num_extractors
        completed_operations = 0

        for file_idx, file_obj in enumerate(files, 1):
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
                completed_operations += 1

                # Report progress after each extractor completes
                if progress_callback:
                    progress_value = completed_operations / total_operations
                    progress_callback(
                        progress_value,
                        desc=f"Processing: {filename} ({file_idx}/{num_files}) - {completed_operations}/{total_operations} tasks complete"
                    )

        # Generate results table
        from .results import generate_results_table
        results_table = generate_results_table(self.results)

        return (results_table,)

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
                html += f"""
                <tr>
                    <td>{extractor_name}</td>
                    <td>{result.execution_time:.1f}s</td>
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
                    rendered_markdown = markdown.markdown(result.markdown, extensions=['extra', 'nl2br', 'sane_lists'])
                    html += f"<div class='markdown-preview'>{rendered_markdown}</div>"
                html += "</div>"

        html += "</body></html>"

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)

        return report_path
