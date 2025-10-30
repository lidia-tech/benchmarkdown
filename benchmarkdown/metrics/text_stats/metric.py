"""Text statistics metrics implementation.

Computes basic text statistics similarity scores comparing extracted text to ground truth:
- Word count similarity (normalized 0.0-1.0, where 1.0 is perfect match)
- Character count similarity (normalized 0.0-1.0, where 1.0 is perfect match)

All scores are normalized using: similarity = max(0.0, 1.0 - abs_diff / gt_count)
"""

import asyncio
from typing import Optional

from benchmarkdown.metrics.base import MetricResult


class TextStatsMetric:
    """Metric that compares basic text statistics (word count, character count).

    Returns normalized similarity scores in range [0.0, 1.0]:
    - 1.0 = perfect match (identical counts)
    - 0.0 = worst match (very different counts)

    Similarity calculation: max(0.0, 1.0 - abs(extracted - gt) / gt)
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
        """Compute word count similarity score.

        Returns a normalized similarity score where:
        - 1.0 = perfect match (same word count)
        - 0.0 = worst match (very different word counts)
        """
        gt_words = len(ground_truth.split())
        ext_words = len(extracted.split())

        if gt_words == 0:
            # If ground truth is empty, only perfect if extracted is also empty
            similarity = 1.0 if ext_words == 0 else 0.0
            description = "Ground truth is empty"
        else:
            # Similarity = 1 - (absolute_difference / ground_truth_count)
            # Clamped to [0.0, 1.0]
            abs_diff = abs(ext_words - gt_words)
            similarity = max(0.0, 1.0 - (abs_diff / gt_words))
            description = f"Word count: {ext_words} / {gt_words} ({abs_diff} words difference)"

        details = {
            "ground_truth_word_count": gt_words,
            "extracted_word_count": ext_words,
            "absolute_difference": abs(ext_words - gt_words),
            "relative_difference_pct": (ext_words - gt_words) / gt_words * 100.0 if gt_words > 0 else 0.0,
            "similarity_score": similarity
        }

        formatted_value = f"{similarity * 100:.1f}%"

        return MetricResult(
            value=similarity,
            description=description,
            details=details,
            formatted_value=formatted_value
        )

    def _compute_char_count_diff(self, ground_truth: str, extracted: str) -> MetricResult:
        """Compute character count similarity score.

        Returns a normalized similarity score where:
        - 1.0 = perfect match (same character count)
        - 0.0 = worst match (very different character counts)
        """
        gt_chars = len(ground_truth)
        ext_chars = len(extracted)

        if gt_chars == 0:
            # If ground truth is empty, only perfect if extracted is also empty
            similarity = 1.0 if ext_chars == 0 else 0.0
            description = "Ground truth is empty"
        else:
            # Similarity = 1 - (absolute_difference / ground_truth_count)
            # Clamped to [0.0, 1.0]
            abs_diff = abs(ext_chars - gt_chars)
            similarity = max(0.0, 1.0 - (abs_diff / gt_chars))
            description = f"Character count: {ext_chars} / {gt_chars} ({abs_diff} chars difference)"

        details = {
            "ground_truth_char_count": gt_chars,
            "extracted_char_count": ext_chars,
            "absolute_difference": abs(ext_chars - gt_chars),
            "relative_difference_pct": (ext_chars - gt_chars) / gt_chars * 100.0 if gt_chars > 0 else 0.0,
            "similarity_score": similarity
        }

        formatted_value = f"{similarity * 100:.1f}%"

        return MetricResult(
            value=similarity,
            description=description,
            details=details,
            formatted_value=formatted_value
        )


__all__ = ['TextStatsMetric']
