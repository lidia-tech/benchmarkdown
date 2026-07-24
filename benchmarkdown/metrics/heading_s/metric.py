from benchmarkdown.metrics.base import MetricResult
from benchmarkdown.metrics.s_score import toc_extract, proc


def compute_structure_similarity(
    text1: str,
    text2: str,
    fuzzy_threshold: float,
    difs: bool = True,
) -> tuple[float, dict]:
    """Compute structural similarity score between two markdown documents.

    Returns:
        (similarity_score, debug_info)
    """
    toc1, toc_dict1 = toc_extract(text1)
    toc2, toc_dict2 = toc_extract(text2)

    similarity, debug_info = proc(
        toc1,
        toc2,
        toc_dict1,
        toc_dict2,
        fuzzy_threshold,
        difs=difs,
    )
    return float(similarity), debug_info


class StructureSimilarityMetric:
    """Structural graph similarity metric based on ToC graphs.

    Uses the generalized Jaccard (Ruzicka) similarity over the documents' text
    bush matrices. With ``difs=True`` (default) the adjacency and hierarchy
    (level-gap) channels are fused, so both edge structure and heading-level
    differences count toward the score.
    """

    def __init__(
        self,
        fuzzy_threshold: float = 80.0,
        difs: bool = True,
    ):
        """
        Args:
            fuzzy_threshold: heading fuzzy match cutoff on the 0–100 rapidfuzz
                WRatio scale (default 80 ≈ 80% similar)
            difs: fuse adjacency + hierarchy channels (default True)
        """
        self.fuzzy_threshold = fuzzy_threshold
        self.difs = difs

    async def compute(self, ground_truth: str, extracted: str) -> MetricResult:
        similarity, debug_info = compute_structure_similarity(
            ground_truth,
            extracted,
            self.fuzzy_threshold,
            self.difs,
        )

        node_recall = debug_info.get("node_recall", 0.0)

        return MetricResult(
            value=similarity,
            description=(
                f"Structural graph similarity "
                f"(fuzzy_threshold={self.fuzzy_threshold}, difs={self.difs})"
            ),
            details={
                "similarity": similarity,
                "node_recall": node_recall,
                "fuzzy_threshold": self.fuzzy_threshold,
                "difs": self.difs,
                **debug_info,
            },
            formatted_value=f"{similarity * 100:.1f}%",
        )


__all__ = ["StructureSimilarityMetric"]
