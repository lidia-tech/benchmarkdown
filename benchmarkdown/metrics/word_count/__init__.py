from typing import Tuple
from .metric import WordCountMetric

METRIC_NAME = "word_count_diff"
METRIC_DISPLAY_NAME = "Word Count Similarity"
METRIC_DESCRIPTION = "Normalized similarity between word counts of extracted text and ground truth"
METRIC_CATEGORY = "basic"

Metric = WordCountMetric


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
