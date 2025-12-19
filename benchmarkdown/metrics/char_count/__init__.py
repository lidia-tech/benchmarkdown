from typing import Tuple
from .metric import CharCountMetric

METRIC_NAME = "char_count_diff"
METRIC_DISPLAY_NAME = "Character Count Similarity"
METRIC_DESCRIPTION = "Normalized similarity between character counts of extracted text and ground truth"
METRIC_CATEGORY = "basic"

Metric = CharCountMetric


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