import asyncio
from difflib import SequenceMatcher
from benchmarkdown.metrics.base import MetricResult

def normalized_similarity(gt: int, ext: int) -> float:
    if gt == 0:
        return 1.0 if ext == 0 else 0.0
    return max(0.0, 1.0 - abs(ext - gt) / gt)

class WordCountMetric:
    async def compute(self, ground_truth: str, extracted: str) -> MetricResult:
        gt_words = len(ground_truth.split())
        ext_words = len(extracted.split())
        score = normalized_similarity(gt_words, ext_words)

        return MetricResult(
            value=score,
            description=f"Word count similarity ({ext_words} / {gt_words})",
            details={
                "ground_truth": gt_words,
                "extracted": ext_words,
                "similarity": score,
            },
            formatted_value=f"{score * 100:.1f}%",
        )