from typing import Tuple
from .metric import HeadingF1Metric

METRIC_NAME = "heading_f1"
METRIC_DISPLAY_NAME = "Heading Structure F1"
METRIC_DESCRIPTION = "F1 similarity score between document heading structures."
METRIC_CATEGORY = "basic"

Metric = HeadingF1Metric


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