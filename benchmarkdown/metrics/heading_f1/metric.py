import asyncio
from difflib import SequenceMatcher
from benchmarkdown.metrics.base import MetricResult
from benchmarkdown.metrics.textstruct import toc_extract

def compute_header_f1(
    text1: str,
    text2: str,
    similarity_threshold: float = 0.8
) -> float:
    toc1 = toc_extract(text1)
    toc2 = toc_extract(text2)

    h1 = [h.strip().lower() for h in toc1[1]["header"]]
    h2 = [h.strip().lower() for h in toc2[1]["header"]]

    matched_1 = set()
    matched_2 = set()

    for i, a in enumerate(h1):
        for j, b in enumerate(h2):
            if SequenceMatcher(None, a, b).ratio() >= similarity_threshold:
                matched_1.add(i)
                matched_2.add(j)
                break

    tp = len(matched_1)
    fp = len(h2) - len(matched_2)
    fn = len(h1) - len(matched_1)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0

    return (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

class HeadingF1Metric:
    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold

    async def compute(self, ground_truth: str, extracted: str) -> MetricResult:
        f1 = compute_header_f1(
            ground_truth,
            extracted,
            self.similarity_threshold,
        )

        return MetricResult(
            value=f1,
            description=f"Heading structure F1 (threshold={self.similarity_threshold})",
            details={
                "f1": f1,
                "threshold": self.similarity_threshold,
            },
            formatted_value=f"{f1 * 100:.1f}%",
        )
