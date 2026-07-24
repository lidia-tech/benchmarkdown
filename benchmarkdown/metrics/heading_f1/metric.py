from benchmarkdown.metrics.base import MetricResult
from benchmarkdown.metrics.s_score import toc_extract, heading_similarity


def compute_header_f1(
    text1: str,
    text2: str,
    similarity_threshold: float = 80.0,
) -> float:
    """Heading F1 between two documents using fuzzy heading matching.

    Uses the shared `heading_similarity` (rapidfuzz WRatio, 0–100), the same
    matcher the structural metric uses, so both metrics agree on what counts
    as a heading match.

    Args:
        similarity_threshold: match cutoff on the 0–100 scale (default 80).
            Headings match when their similarity is strictly greater than this
            cutoff (same comparison the structural metric's unifier uses).
    """
    toc1 = toc_extract(text1)
    toc2 = toc_extract(text2)

    h1 = [h.strip().lower() for h in toc1[1]["header"]]
    h2 = [h.strip().lower() for h in toc2[1]["header"]]

    matched_1 = set()
    matched_2 = set()

    for i, a in enumerate(h1):
        for j, b in enumerate(h2):
            if heading_similarity(a, b) > similarity_threshold:
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
    def __init__(self, similarity_threshold: float = 80.0):
        """
        Args:
            similarity_threshold: heading match cutoff on the 0–100 scale
                (default 80), consistent with `heading_s`.
        """
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
