from typing import Tuple
from .metric import Rouge2Metric

METRIC_NAME = "rouge2"
METRIC_DISPLAY_NAME = "ROUGE-2 (Bigram Overlap)"
METRIC_DESCRIPTION = "Word bigram overlap (ROUGE-2 style) measuring content recall, precision, and F1 between extracted text and ground truth"
METRIC_CATEGORY = "content"

Metric = Rouge2Metric


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
