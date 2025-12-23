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

        # Storage for ground truth texts (gt_id -> gt_text)
        # gt_id is the uploaded filename (e.g., "ground_truth_v1.txt")
        self.ground_truths: Dict[str, str] = {}

        # Storage for validation results (document_name -> extractor_name -> metric_name -> result)
        self.validation_results: Dict[str, Dict[str, Dict[str, Any]]] = {}

        # Track which metrics were selected in the last validation run
        self.last_selected_metrics: List[str] = []

    def get_available_metrics(self) -> List[tuple]:
        """Get list of available metrics for UI selection.

        Returns:
            List of (metric_name, display_name) tuples
        """
        metrics = []
        for name, metadata in self.metric_registry.get_available_metrics().items():
            metrics.append((name, metadata.display_name))
        return metrics

    def upload_ground_truth(self, file_path: str) -> str:
        """Upload and store ground truth markdown.

        Args:
            file_path: Path to the ground truth markdown file

        Returns:
            Status message
        """
        try:
            # Extract filename from path
            from pathlib import Path
            gt_filename = Path(file_path).name

            with open(file_path, 'r', encoding='utf-8') as f:
                gt_text = f.read()

            self.ground_truths[gt_filename] = gt_text
            word_count = len(gt_text.split())
            char_count = len(gt_text)

            return f"✅ Ground truth '{gt_filename}' uploaded ({word_count} words, {char_count} characters)"
        except Exception as e:
            return f"❌ Failed to load ground truth: {str(e)}"

    async def run_validation(
        self,
        ui_results: Dict[str, Dict[str, Any]],
        selected_ground_truth: str,
        selected_documents: List[str],
        selected_extractors: List[str],
        selected_metrics: List[str]
    ) -> str:
        """Run validation for selected documents, extractors, and metrics.

        Args:
            ui_results: The results dict from BenchmarkUI (filename -> extractor_name -> result)
            selected_ground_truth: The ground truth filename to use for validation
            selected_documents: List of document names to validate
            selected_extractors: List of extractor names to validate
            selected_metrics: List of metric names to apply

        Returns:
            Status message
        """
        if not selected_ground_truth:
            return "⚠️ Please select a ground truth file"
        if not selected_documents:
            return "⚠️ Please select at least one document"
        if not selected_extractors:
            return "⚠️ Please select at least one extractor"
        if not selected_metrics:
            return "⚠️ Please select at least one metric"

        # Check that the selected ground truth exists
        if selected_ground_truth not in self.ground_truths:
            return f"⚠️ Ground truth '{selected_ground_truth}' not found"

        # Store selected metrics for use in results display
        self.last_selected_metrics = selected_metrics.copy()

        # Run metrics for each combination
        total_computations = len(selected_documents) * len(selected_extractors) * len(selected_metrics)
        computed = 0

        # Get the ground truth text once (it's the same for all documents being validated)
        gt_text = self.ground_truths[selected_ground_truth]

        for doc_name in selected_documents:
            if doc_name not in ui_results:
                continue

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
                        continue

                    result = await metric.compute(gt_text, extracted_text)

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

        # For each document
        for doc_name in sorted(self.validation_results.keys()):
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
