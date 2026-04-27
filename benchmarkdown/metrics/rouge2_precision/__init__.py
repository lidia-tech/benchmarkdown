from typing import Tuple
from benchmarkdown.metrics.rouge2.metric import Rouge2PrecisionMetric

METRIC_NAME = "rouge2_precision"
METRIC_DISPLAY_NAME = "ROUGE-2 Precision"
METRIC_DESCRIPTION = "Bigram overlap precision — measures content cleanliness (what fraction of extracted content matches ground truth)"
METRIC_CATEGORY = "content"

Metric = Rouge2PrecisionMetric


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
