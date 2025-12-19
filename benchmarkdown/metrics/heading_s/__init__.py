from typing import Tuple
from .metric import StructureSimilarityMetric

METRIC_NAME = "structure_similarity"
METRIC_DISPLAY_NAME = "Structure Similarity"
METRIC_DESCRIPTION = (
    "Graph-based structural similarity between markdown documents "
    "based on table-of-contents alignment."
)
METRIC_CATEGORY = "basic"

Metric = StructureSimilarityMetric


def is_available() -> Tuple[bool, str]:
    return True, ""


__all__ = [
    "Metric",
    "METRIC_NAME",
    "METRIC_DISPLAY_NAME",
    "METRIC_DESCRIPTION",
    "METRIC_CATEGORY",
    "is_available",
]
