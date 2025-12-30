"""Validation UI components for comparing extraction results against ground truth.

This module provides UI components and logic for:
- Uploading ground truth markdown
- Selecting results to validate
- Applying metrics
- Displaying comparison results
"""

import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path

from benchmarkdown.metrics import MetricRegistry
from benchmarkdown.pdf_metadata import PDFMetadataManager


class ValidationUI:
    """Manages validation of extraction results against ground truth."""

    def __init__(self, metric_registry: Optional[MetricRegistry] = None):
        """Initialize validation UI.

        Args:
            metric_registry: MetricRegistry instance (will create if not provided)
        """
        self.metric_registry = metric_registry or MetricRegistry()
        if metric_registry is None:
            self.metric_registry.discover_metrics()

        # Storage for uploaded ground truth files (gt_filename -> gt_text)
        self.uploaded_ground_truths: Dict[str, str] = {}

        # Storage for ground truth associations (document_filename -> gt_filename)
        self.ground_truth_associations: Dict[str, str] = {}

        # Storage for validation results (document_name -> extractor_name -> metric_name -> result)
        self.validation_results: Dict[str, Dict[str, Dict[str, Any]]] = {}

        # Track which metrics were selected in the last validation run
        self.last_selected_metrics: List[str] = []

        # Track which documents were validated in the last validation run
        self.last_validated_documents: List[str] = []

    def get_available_metrics(self) -> List[tuple]:
        """Get list of available metrics for UI selection.

        Returns:
            List of (metric_name, display_name) tuples
        """
        metrics = []
        for name, metadata in self.metric_registry.get_available_metrics().items():
            metrics.append((name, metadata.display_name))
        return metrics

    def upload_ground_truth_files(self, file_paths: List[str]) -> str:
        """Upload and store ground truth markdown files.

        Args:
            file_paths: List of paths to ground truth markdown files

        Returns:
            Status message
        """
        if not file_paths:
            return ""

        try:
            uploaded_count = 0
            for file_path in file_paths:
                gt_filename = Path(file_path).name

                with open(file_path, 'r', encoding='utf-8') as f:
                    gt_text = f.read()

                self.uploaded_ground_truths[gt_filename] = gt_text
                uploaded_count += 1

            return f"✅ Uploaded {uploaded_count} ground truth file(s)"
        except Exception as e:
            return f"❌ Failed to load ground truth: {str(e)}"

    def set_association(self, document_name: str, gt_filename: str):
        """Associate a document with a ground truth file (in-memory only).

        Args:
            document_name: The document filename
            gt_filename: The ground truth filename to associate
        """
        if gt_filename and gt_filename != "None":
            self.ground_truth_associations[document_name] = gt_filename
        elif document_name in self.ground_truth_associations:
            del self.ground_truth_associations[document_name]

    def _match_filename(self, pdf_filename: str, gt_filename: str) -> bool:
        """Check if PDF and GT filenames match (ignoring extensions).

        Args:
            pdf_filename: PDF filename (e.g., "document.pdf")
            gt_filename: Ground truth filename (e.g., "document.md" or "document.txt")

        Returns:
            True if basenames match
        """
        pdf_base = Path(pdf_filename).stem
        gt_base = Path(gt_filename).stem
        return pdf_base == gt_base

    def auto_associate_by_filename(self, ui_results: Dict[str, Dict[str, Any]]) -> int:
        """Automatically associate PDFs with ground truth files by matching filenames.

        Args:
            ui_results: Results dict from BenchmarkUI (filename -> extractor_name -> result)

        Returns:
            Number of successful associations
        """
        if not ui_results or not self.uploaded_ground_truths:
            return 0

        associations_made = 0
        self.ground_truth_associations.clear()

        for doc_name in ui_results.keys():
            # Try to find matching ground truth file
            for gt_filename in self.uploaded_ground_truths.keys():
                if self._match_filename(doc_name, gt_filename):
                    self.ground_truth_associations[doc_name] = gt_filename
                    associations_made += 1
                    break

        return associations_made

    def generate_association_status_html(
        self,
        ui_results: Dict[str, Dict[str, Any]]
    ) -> str:
        """Generate HTML showing association status for each PDF.

        Args:
            ui_results: Results dict from BenchmarkUI (filename -> extractor_name -> result)

        Returns:
            HTML string with association status for each PDF
        """
        if not ui_results:
            return (
                "<p style='color: var(--body-text-color-subdued, #666);'>"
                "No documents processed yet. Process documents first."
                "</p>"
            )

        if not self.uploaded_ground_truths:
            return (
                "<p style='color: var(--body-text-color-subdued, #666);'>"
                "No ground truth files uploaded yet. Upload ground truth files first."
                "</p>"
            )

        html = ["<div style='font-family: monospace;'>"]
        html.append("<p><strong>Association Status (by filename matching):</strong></p>")

        associated_count = 0
        missing_count = 0

        for doc_name in sorted(ui_results.keys()):
            # Check if there's an association
            gt_filename = self.ground_truth_associations.get(doc_name)

            html.append(
                f"<div style='margin: 10px 0; padding: 10px; "
                f"border: 1px solid var(--border-color-primary); "
                f"border-radius: 5px; background: var(--background-fill-secondary);'>"
            )
            html.append(f"<div style='display: flex; justify-content: space-between; align-items: center;'>")
            html.append(f"<strong>📄 {doc_name}</strong>")

            if gt_filename:
                html.append(
                    f"<span style='color: #27ae60; font-weight: bold;'>✓ Associated</span>"
                )
                html.append("</div>")
                html.append(
                    f"<div style='margin-top: 5px; font-size: 0.9em; "
                    f"color: var(--body-text-color-subdued);'>"
                    f"→ Ground truth: <strong>{gt_filename}</strong></div>"
                )
                associated_count += 1
            else:
                html.append(
                    f"<span style='color: #e74c3c; font-weight: bold;'>✗ No Match</span>"
                )
                html.append("</div>")
                html.append(
                    f"<div style='margin-top: 5px; font-size: 0.9em; "
                    f"color: var(--body-text-color-subdued);'>"
                    f"No ground truth file with matching name found</div>"
                )
                missing_count += 1

            html.append("</div>")

        # Summary
        html.append("<div style='margin-top: 15px; padding: 10px; background: var(--background-fill-primary); border-radius: 5px;'>")
        html.append(f"<strong>Summary:</strong> {associated_count} associated, {missing_count} missing")
        html.append("</div>")

        html.append("</div>")
        return "".join(html)

    def save_associations_to_pdf(
        self,
        ui_results: Dict[str, Dict[str, Any]],
        pdf_directory: str
    ) -> str:
        """Save ground truth associations to PDF metadata.

        Args:
            ui_results: Results dict from BenchmarkUI
            pdf_directory: Directory containing the PDF files

        Returns:
            Status message
        """
        if not self.ground_truth_associations:
            return "⚠️ No associations to save"

        saved_count = 0
        failed_count = 0
        errors = []

        for doc_name, gt_filename in self.ground_truth_associations.items():
            pdf_path = Path(pdf_directory) / doc_name

            if not pdf_path.exists():
                errors.append(f"PDF not found: {doc_name}")
                failed_count += 1
                continue

            success = PDFMetadataManager.set_ground_truth_association(
                str(pdf_path),
                gt_filename
            )

            if success:
                saved_count += 1
            else:
                failed_count += 1
                errors.append(f"Failed to write metadata: {doc_name}")

        if saved_count > 0 and failed_count == 0:
            return f"✅ Saved {saved_count} association(s) to PDF metadata"
        elif saved_count > 0:
            error_msg = "; ".join(errors[:3])
            return f"⚠️ Saved {saved_count}, failed {failed_count}. Errors: {error_msg}"
        else:
            error_msg = "; ".join(errors[:3])
            return f"❌ Failed to save associations. Errors: {error_msg}"

    async def run_validation(
        self,
        ui_results: Dict[str, Dict[str, Any]],
        selected_documents: List[str],
        selected_extractors: List[str],
        selected_metrics: List[str]
    ) -> str:
        """Run validation for selected documents, extractors, and metrics.

        Args:
            ui_results: The results dict from BenchmarkUI (filename -> extractor_name -> result)
            selected_documents: List of document names to validate
            selected_extractors: List of extractor names to validate
            selected_metrics: List of metric names to apply

        Returns:
            Status message
        """
        if not selected_documents:
            return "⚠️ Please select at least one document"
        if not selected_extractors:
            return "⚠️ Please select at least one extractor"
        if not selected_metrics:
            return "⚠️ Please select at least one metric"

        # Check that all selected documents have ground truth associations
        missing_associations = []
        for doc in selected_documents:
            # Check if any extraction result has ground_truth_filename
            has_association = False
            if doc in ui_results:
                for extractor_results in ui_results[doc].values():
                    if hasattr(extractor_results, 'ground_truth_filename') and extractor_results.ground_truth_filename:
                        has_association = True
                        break

            # Fallback to in-memory associations
            if not has_association and doc not in self.ground_truth_associations:
                missing_associations.append(doc)

        if missing_associations:
            return f"⚠️ Missing ground truth association for: {', '.join(missing_associations)}"

        # Store selected metrics and documents for use in results display
        self.last_selected_metrics = selected_metrics.copy()
        self.last_validated_documents = selected_documents.copy()

        # Run metrics for each combination
        total_computations = len(selected_documents) * len(selected_extractors) * len(selected_metrics)
        computed = 0

        for doc_name in selected_documents:
            if doc_name not in ui_results:
                print(f"  ⚠️ Skipping {doc_name}: not in ui_results")
                continue

            # Get the ground truth filename from ExtractionResult (preferred) or fallback to in-memory
            gt_filename = None
            for extractor_results in ui_results[doc_name].values():
                if hasattr(extractor_results, 'ground_truth_filename') and extractor_results.ground_truth_filename:
                    gt_filename = extractor_results.ground_truth_filename
                    break

            if not gt_filename:
                gt_filename = self.ground_truth_associations.get(doc_name)

            if not gt_filename:
                print(f"  ⚠️ Skipping {doc_name}: no ground truth association")
                continue

            print(f"  📄 {doc_name} -> GT file: {gt_filename}")

            if gt_filename not in self.uploaded_ground_truths:
                print(f"    ⚠️ GT file '{gt_filename}' not found in uploaded_ground_truths!")
                continue

            gt_text = self.uploaded_ground_truths[gt_filename]
            gt_char_count = len(gt_text)
            gt_word_count = len(gt_text.split())
            print(f"    ✓ GT text loaded: {gt_char_count} chars, {gt_word_count} words")

            for extractor_name in selected_extractors:
                if extractor_name not in ui_results[doc_name]:
                    continue

                extraction_result = ui_results[doc_name][extractor_name]
                if extraction_result.error:
                    continue

                extracted_text = extraction_result.markdown

                # Initialize nested dicts if needed
                if doc_name not in self.validation_results:
                    self.validation_results[doc_name] = {}
                if extractor_name not in self.validation_results[doc_name]:
                    self.validation_results[doc_name][extractor_name] = {}

                for metric_name in selected_metrics:
                    metric = self.metric_registry.create_metric_instance(metric_name)
                    if metric is None:
                        print(f"      ⚠️ Could not create metric: {metric_name}")
                        continue

                    result = await metric.compute(gt_text, extracted_text)
                    print(f"      ✓ {metric_name}: {result.value} ({result.formatted_value})")

                    self.validation_results[doc_name][extractor_name][metric_name] = result
                    computed += 1

        return f"✅ Computed {computed} metrics across {len(selected_documents)} documents and {len(selected_extractors)} extractors"

    def generate_validation_results_html(self) -> str:
        """Generate HTML display of validation results.

        Returns:
            HTML string with formatted validation results
        """
        METRIC_ORDER = [
            "char_count_diff",
            "word_count_diff",
            "heading_f1",
            "structure_similarity",
        ]

        def metric_sort_key(name: str) -> tuple[int, str]:
            try:
                return (METRIC_ORDER.index(name), "")
            except ValueError:
                return (len(METRIC_ORDER), name)

        if not self.validation_results:
            return (
                "<p style='color: var(--body-text-color-subdued, #666);'>"
                "No validation results yet. Upload ground truth and run validation."
                "</p>"
            )

        html = ["<div style='font-family: monospace;'>"]

        # Determine which documents to display
        # Only show documents from the last validation run if available
        if self.last_validated_documents:
            documents_to_show = [doc for doc in self.last_validated_documents if doc in self.validation_results]
        else:
            # Fallback to showing all documents (for backwards compatibility)
            documents_to_show = list(self.validation_results.keys())

        # For each document
        for doc_name in sorted(documents_to_show):
            html.append(f"<h3>📋 {doc_name}</h3>")
            html.append(
                "<table style='width: 100%; border-collapse: collapse; margin-bottom: 20px;'>"
            )

            # Use only the metrics that were selected in the last validation run
            # This ensures the table only shows chosen metrics, not all computed metrics
            if self.last_selected_metrics:
                # Filter to only show metrics that were selected AND actually computed
                all_metrics = set()
                for extractor_results in self.validation_results[doc_name].values():
                    all_metrics.update(extractor_results.keys())
                # Intersect with selected metrics
                display_metrics = [m for m in self.last_selected_metrics if m in all_metrics]
            else:
                # Fallback: show all computed metrics (for backwards compatibility)
                all_metrics = set()
                for extractor_results in self.validation_results[doc_name].values():
                    all_metrics.update(extractor_results.keys())
                display_metrics = list(all_metrics)

            # Compute ordered metric list ONCE
            ordered_metrics = sorted(display_metrics, key=metric_sort_key)

            # ---------------- Header row ----------------
            html.append(
                "<tr style='background: var(--background-fill-secondary); "
                "border-bottom: 2px solid var(--border-color-primary); "
                "color: var(--body-text-color);'>"
            )
            html.append("<th style='padding: 8px; text-align: left;'>Extractor</th>")

            for metric_name in ordered_metrics:
                html.append(
                    f"<th style='padding: 8px; text-align: center;'>"
                    f"{metric_name.replace('_', ' ').title()}"
                    "</th>"
                )

            html.append("</tr>")

            # ---------------- Data rows ----------------
            for extractor_name in sorted(self.validation_results[doc_name].keys()):
                extractor_results = self.validation_results[doc_name][extractor_name]

                html.append(
                    "<tr style='border-bottom: 1px solid var(--border-color-primary); "
                    "color: var(--body-text-color);'>"
                )
                html.append(f"<td style='padding: 8px;'>{extractor_name}</td>")

                for metric_name in ordered_metrics:
                    if metric_name in extractor_results:
                        result = extractor_results[metric_name]
                        formatted = (
                            result.formatted_value
                            if result.formatted_value
                            else str(result.value)
                        )

                        similarity = result.value
                        if similarity >= 0.95:
                            color = "#27ae60"
                        elif similarity >= 0.85:
                            color = "#f39c12"
                        else:
                            color = "#e74c3c"

                        html.append(
                            f"<td style='padding: 8px; text-align: center; "
                            f"color: {color}; font-weight: bold;'>"
                            f"{formatted}</td>"
                        )
                    else:
                        html.append(
                            "<td style='padding: 8px; text-align: center; "
                            "color: var(--body-text-color-subdued, #999);'>—</td>"
                        )

                html.append("</tr>")

                # ---------------- Description row ----------------
                html.append(
                    "<tr style='border-bottom: 1px solid var(--border-color-primary); "
                    "color: var(--body-text-color-subdued, #666);'>"
                )
                html.append("<td style='padding: 8px; font-size: 0.85em;'></td>")

                for metric_name in ordered_metrics:
                    if metric_name in extractor_results:
                        result = extractor_results[metric_name]
                        html.append(
                            f"<td style='padding: 8px; font-size: 0.85em; "
                            f"text-align: center;'>{result.description}</td>"
                        )
                    else:
                        html.append("<td style='padding: 8px;'></td>")

                html.append("</tr>")

            html.append("</table>")

        html.append("</div>")
        return "".join(html)

    def clear_validation_results(self) -> str:
        """Clear all validation results.

        Returns:
            Status message
        """
        self.validation_results.clear()
        return "✅ Validation results cleared"


__all__ = ['ValidationUI']
