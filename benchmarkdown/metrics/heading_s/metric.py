import asyncio
from benchmarkdown.metrics.base import MetricResult
from benchmarkdown.metrics.textstruct import (
    toc_extract,
    toc_fuzzy_unify,
    disconnected_sparse_graph,
    disconnected_full_graph,
    connected_graph,
    mask_vector,
    graph_to_matrix,
    GED,
    GED_norm_factor,
    GED_sim,
)


def compute_structure_similarity(
    text1: str,
    text2: str,
    fuzzy_threshold: float,
    mask,
) -> tuple[float, float]:
    """Compute structural similarity score between two markdown documents.

    Returns:
        (similarity_score, node_recall)
    """
    toc1, toc_dict1 = toc_extract(text1)
    toc2, toc_dict2 = toc_extract(text2)

    try:
        toc1_index, toc2_index, total_nodes, node_recall = toc_fuzzy_unify(
            toc_dict1,
            toc_dict2,
            fuzzy_threshold,
        )

        graph1_sparse = disconnected_sparse_graph(toc1_index)
        graph2_sparse = disconnected_sparse_graph(toc2_index)

        graph1_full_d = disconnected_full_graph(graph1_sparse)
        graph2_full_d = disconnected_full_graph(graph2_sparse)

        graph1_full = connected_graph(graph1_full_d, toc1_index)
        graph2_full = connected_graph(graph2_full_d, toc2_index)

        vector1 = mask_vector(toc1_index, mask, total_nodes)
        vector2 = mask_vector(toc2_index, mask, total_nodes)

        matrix1 = graph_to_matrix(graph1_full, total_nodes)
        matrix2 = graph_to_matrix(graph2_full, total_nodes)

        ged_abs = GED(matrix1, matrix2)
        norm = GED_norm_factor(matrix1, matrix2)

        similarity = GED_sim(ged_abs, norm)

        return float(similarity), float(node_recall)

    except Exception:
        return 0.0, 0.0


class StructureSimilarityMetric:
    """Structural graph similarity metric based on ToC graphs."""

    def __init__(
        self,
        fuzzy_threshold: float = 0.8,
        mask: list[float] | None = None,
    ):
        """
        Args:
            fuzzy_threshold: heading fuzzy match threshold
            mask: weights for header levels (e.g. [1, 0.8, 0.6, ...])
        """
        self.fuzzy_threshold = fuzzy_threshold
        self.mask = mask or [1, 1, 1, 1]

    async def compute(self, ground_truth: str, extracted: str) -> MetricResult:
        similarity, node_recall = compute_structure_similarity(
            ground_truth,
            extracted,
            self.fuzzy_threshold,
            self.mask,
        )

        return MetricResult(
            value=similarity,
            description=(
                f"Structural graph similarity "
                f"(fuzzy_threshold={self.fuzzy_threshold})"
            ),
            details={
                "similarity": similarity,
                "node_recall": node_recall,
                "fuzzy_threshold": self.fuzzy_threshold,
                "mask": self.mask,
            },
            formatted_value=f"{similarity * 100:.1f}%",
        )


__all__ = ["StructureSimilarityMetric"]
