import asyncio
from typing import Optional
from difflib import SequenceMatcher

from benchmarkdown.metrics.base import MetricResult
from textstruct import toc_extract  # adjust import — ensure toc_extract + header_score available


def compute_header_f1(text1: str, text2: str, similarity_threshold: float = 0.8) -> float:
    """Compute F1 between lists of headings in two texts using fuzzy matching."""
    toc1 = toc_extract(text1)
    heading1 = toc1[1]['header']

    toc2 = toc_extract(text2)
    heading2 = toc2[1]['header']

    heading1 = [h.strip().lower() for h in heading1]
    heading2 = [h.strip().lower() for h in heading2]

    matched_1 = set()
    matched_2 = set()

    for i, h1 in enumerate(heading1):
        for j, h2 in enumerate(heading2):
            sim = SequenceMatcher(None, h1, h2).ratio()
            if sim >= similarity_threshold:
                matched_1.add(i)
                matched_2.add(j)
                break

    tp = len(matched_1)
    fp = len(heading2) - len(matched_2)
    fn = len(heading1) - len(matched_1)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return f1


class HeaderSimilarityMetric:
    """Metric computing F1 similarity between document headings."""

    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold

    async def compute(self, ground_truth: str, extracted: str) -> MetricResult:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self._compute_sync,
            ground_truth,
            extracted
        )

    def _compute_sync(self, ground_truth: str, extracted: str) -> MetricResult:
        f1 = compute_header_f1(ground_truth, extracted, self.similarity_threshold)

        # description
        description = (
            f"Heading F1 similarity using threshold={self.similarity_threshold}"
        )

        # details
        details = {
            "similarity_threshold": self.similarity_threshold,
            "f1_score": f1
        }

        formatted_value = f"{f1 * 100:.1f}%"

        return MetricResult(
            value=f1,
            description=description,
            details=details,
            formatted_value=formatted_value
        )


__all__ = ["HeaderSimilarityMetric"]
