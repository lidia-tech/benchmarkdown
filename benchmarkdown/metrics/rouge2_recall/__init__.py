from typing import Tuple
from benchmarkdown.metrics.rouge2.metric import Rouge2RecallMetric

METRIC_NAME = "rouge2_recall"
METRIC_DISPLAY_NAME = "ROUGE-2 Recall"
METRIC_DESCRIPTION = "Bigram overlap recall — measures content completeness (what fraction of ground truth content was extracted)"
METRIC_CATEGORY = "content"

Metric = Rouge2RecallMetric


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
