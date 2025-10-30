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

        # Storage for ground truth texts (document_name -> gt_text)
        self.ground_truths: Dict[str, str] = {}

        # Storage for validation results (document_name -> extractor_name -> metric_name -> result)
        self.validation_results: Dict[str, Dict[str, Dict[str, Any]]] = {}

    def get_available_metrics(self) -> List[tuple]:
        """Get list of available metrics for UI selection.

        Returns:
            List of (metric_name, display_name) tuples
        """
        metrics = []
        for name, metadata in self.metric_registry.get_available_metrics().items():
            metrics.append((name, metadata.display_name))
        return metrics

    def upload_ground_truth(self, file_path: str, document_name: str) -> str:
        """Upload and store ground truth markdown.

        Args:
            file_path: Path to the ground truth markdown file
            document_name: Name of the document this GT corresponds to

        Returns:
            Status message
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                gt_text = f.read()

            self.ground_truths[document_name] = gt_text
            word_count = len(gt_text.split())
            char_count = len(gt_text)

            return f"✅ Ground truth loaded for '{document_name}' ({word_count} words, {char_count} characters)"
        except Exception as e:
            return f"❌ Failed to load ground truth: {str(e)}"

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

        # Check that all selected documents have ground truth
        missing_gt = [doc for doc in selected_documents if doc not in self.ground_truths]
        if missing_gt:
            return f"⚠️ Missing ground truth for: {', '.join(missing_gt)}"

        # Run metrics for each combination
        total_computations = len(selected_documents) * len(selected_extractors) * len(selected_metrics)
        computed = 0

        for doc_name in selected_documents:
            if doc_name not in ui_results:
                continue

            gt_text = self.ground_truths[doc_name]

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

                    # For text_stats, we need to compute both word and char variants
                    if metric_name == "text_stats":
                        # Import the factory functions
                        from benchmarkdown.metrics.text_stats import (
                            create_word_count_metric,
                            create_char_count_metric
                        )

                        word_metric = create_word_count_metric()
                        char_metric = create_char_count_metric()

                        word_result = await word_metric.compute(gt_text, extracted_text)
                        char_result = await char_metric.compute(gt_text, extracted_text)

                        self.validation_results[doc_name][extractor_name]['word_count_diff'] = word_result
                        self.validation_results[doc_name][extractor_name]['char_count_diff'] = char_result
                        computed += 2
                    else:
                        result = await metric.compute(gt_text, extracted_text)
                        self.validation_results[doc_name][extractor_name][metric_name] = result
                        computed += 1

        return f"✅ Computed {computed} metrics across {len(selected_documents)} documents and {len(selected_extractors)} extractors"

    def generate_validation_results_html(self) -> str:
        """Generate HTML display of validation results.

        Returns:
            HTML string with formatted validation results
        """
        if not self.validation_results:
            return "<p style='color: var(--body-text-color-subdued, #666);'>No validation results yet. Upload ground truth and run validation.</p>"

        html = ["<div style='font-family: monospace;'>"]

        # For each document
        for doc_name in sorted(self.validation_results.keys()):
            html.append(f"<h3>📋 {doc_name}</h3>")

            # Create a table for this document
            html.append("<table style='width: 100%; border-collapse: collapse; margin-bottom: 20px;'>")

            # Get all unique metrics across all extractors for this document
            all_metrics = set()
            for extractor_results in self.validation_results[doc_name].values():
                all_metrics.update(extractor_results.keys())

            # Table header
            html.append("<tr style='background: var(--background-fill-secondary); border-bottom: 2px solid var(--border-color-primary); color: var(--body-text-color);'>")
            html.append("<th style='padding: 8px; text-align: left;'>Extractor</th>")

            for metric_name in sorted(all_metrics):
                html.append(f"<th style='padding: 8px; text-align: center;'>{metric_name.replace('_', ' ').title()}</th>")

            html.append("</tr>")

            # For each extractor
            for extractor_name in sorted(self.validation_results[doc_name].keys()):
                extractor_results = self.validation_results[doc_name][extractor_name]

                html.append("<tr style='border-bottom: 1px solid var(--border-color-primary); color: var(--body-text-color);'>")
                html.append(f"<td style='padding: 8px;'>{extractor_name}</td>")

                for metric_name in sorted(all_metrics):
                    if metric_name in extractor_results:
                        result = extractor_results[metric_name]
                        formatted = result.formatted_value if result.formatted_value else str(result.value)

                        # Color code based on percentage (for diff metrics, lower is better)
                        if '%' in formatted:
                            try:
                                pct_value = float(formatted.rstrip('%'))
                                if pct_value < 5:
                                    color = '#27ae60'  # Green
                                elif pct_value < 15:
                                    color = '#f39c12'  # Orange
                                else:
                                    color = '#e74c3c'  # Red
                            except:
                                color = 'var(--body-text-color)'
                        else:
                            color = 'var(--body-text-color)'

                        html.append(f"<td style='padding: 8px; text-align: center; color: {color}; font-weight: bold;'>{formatted}</td>")
                    else:
                        html.append("<td style='padding: 8px; text-align: center; color: var(--body-text-color-subdued, #999);'>—</td>")

                html.append("</tr>")

                # Add a detail row with descriptions
                html.append("<tr style='border-bottom: 1px solid var(--border-color-primary); color: var(--body-text-color-subdued, #666);'>")
                html.append("<td style='padding: 8px; font-size: 0.85em;'></td>")

                for metric_name in sorted(all_metrics):
                    if metric_name in extractor_results:
                        result = extractor_results[metric_name]
                        html.append(f"<td style='padding: 8px; font-size: 0.85em; text-align: center;'>{result.description}</td>")
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
