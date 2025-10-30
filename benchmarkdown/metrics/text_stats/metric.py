"""Text statistics metrics implementation.

Computes basic text statistics comparing extracted text to ground truth:
- Word count difference (percentage)
- Character count difference (percentage)
"""

import asyncio
from typing import Optional

from benchmarkdown.metrics.base import MetricResult


class TextStatsMetric:
    """Metric that compares basic text statistics (word count, character count).

    This is a simple baseline metric that measures the percentage difference
    in word count and character count between ground truth and extracted text.
    """

    def __init__(self, metric_type: str = "word_count"):
        """Initialize the text stats metric.

        Args:
            metric_type: Either "word_count" or "char_count"
        """
        if metric_type not in ["word_count", "char_count"]:
            raise ValueError(f"Invalid metric_type: {metric_type}. Must be 'word_count' or 'char_count'")
        self.metric_type = metric_type

    async def compute(self, ground_truth: str, extracted: str) -> MetricResult:
        """Compute the text statistics metric.

        Args:
            ground_truth: The reference/ground truth markdown text
            extracted: The extracted markdown text to evaluate

        Returns:
            MetricResult containing the percentage difference
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._compute_sync, ground_truth, extracted)

    def _compute_sync(self, ground_truth: str, extracted: str) -> MetricResult:
        """Synchronous computation of text statistics."""
        if self.metric_type == "word_count":
            return self._compute_word_count_diff(ground_truth, extracted)
        else:
            return self._compute_char_count_diff(ground_truth, extracted)

    def _compute_word_count_diff(self, ground_truth: str, extracted: str) -> MetricResult:
        """Compute word count difference percentage."""
        gt_words = len(ground_truth.split())
        ext_words = len(extracted.split())

        if gt_words == 0:
            percentage_diff = 100.0 if ext_words > 0 else 0.0
            description = "Ground truth is empty"
        else:
            percentage_diff = abs(ext_words - gt_words) / gt_words * 100.0
            description = f"Word count difference: {abs(ext_words - gt_words)} words"

        details = {
            "ground_truth_word_count": gt_words,
            "extracted_word_count": ext_words,
            "absolute_difference": abs(ext_words - gt_words),
            "relative_difference": (ext_words - gt_words) / gt_words * 100.0 if gt_words > 0 else 0.0
        }

        formatted_value = f"{percentage_diff:.2f}%"

        return MetricResult(
            value=percentage_diff,
            description=description,
            details=details,
            formatted_value=formatted_value
        )

    def _compute_char_count_diff(self, ground_truth: str, extracted: str) -> MetricResult:
        """Compute character count difference percentage."""
        gt_chars = len(ground_truth)
        ext_chars = len(extracted)

        if gt_chars == 0:
            percentage_diff = 100.0 if ext_chars > 0 else 0.0
            description = "Ground truth is empty"
        else:
            percentage_diff = abs(ext_chars - gt_chars) / gt_chars * 100.0
            description = f"Character count difference: {abs(ext_chars - gt_chars)} characters"

        details = {
            "ground_truth_char_count": gt_chars,
            "extracted_char_count": ext_chars,
            "absolute_difference": abs(ext_chars - gt_chars),
            "relative_difference": (ext_chars - gt_chars) / gt_chars * 100.0 if gt_chars > 0 else 0.0
        }

        formatted_value = f"{percentage_diff:.2f}%"

        return MetricResult(
            value=percentage_diff,
            description=description,
            details=details,
            formatted_value=formatted_value
        )


__all__ = ['TextStatsMetric']
