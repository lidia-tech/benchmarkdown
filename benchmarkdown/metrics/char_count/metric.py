import asyncio
from difflib import SequenceMatcher
from benchmarkdown.metrics.base import MetricResult

def normalized_similarity(gt: int, ext: int) -> float:
    if gt == 0:
        return 1.0 if ext == 0 else 0.0
    return max(0.0, 1.0 - abs(ext - gt) / gt)

class CharCountMetric:
    async def compute(self, ground_truth: str, extracted: str) -> MetricResult:
        gt_chars = len(ground_truth)
        ext_chars = len(extracted)
        score = normalized_similarity(gt_chars, ext_chars)

        return MetricResult(
            value=score,
            description=f"Character count similarity ({ext_chars} / {gt_chars})",
            details={
                "ground_truth": gt_chars,
                "extracted": ext_chars,
                "similarity": score,
            },
            formatted_value=f"{score * 100:.1f}%",
        )
