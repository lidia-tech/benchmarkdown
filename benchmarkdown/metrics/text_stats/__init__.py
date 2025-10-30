"""Text statistics metrics plugin.

This plugin provides basic text statistics similarity metrics for evaluating extracted markdown:
- Word count similarity (normalized 0.0-1.0)
- Character count similarity (normalized 0.0-1.0)

All metrics return normalized scores where 1.0 is a perfect match and 0.0 is the worst.
"""

from typing import Tuple
from .metric import TextStatsMetric

# Standard exports required by MetricRegistry

# We actually have two metrics here, so we'll create a factory pattern
# The registry will discover this as a category, and we'll provide both metrics
METRIC_NAME = "text_stats"
METRIC_DISPLAY_NAME = "Text Statistics"
METRIC_DESCRIPTION = "Compares word count and character count similarity (normalized 0.0-1.0, higher is better)"
METRIC_CATEGORY = "basic"

# For now, expose as the base class - we'll handle the two variants in the UI
Metric = TextStatsMetric


def is_available() -> Tuple[bool, str]:
    """Check if this metric is available.

    Text statistics metrics have no external dependencies.

    Returns:
        Tuple of (is_available, reason_if_unavailable)
    """
    return True, ""


# Additional exports for metric variants
def create_word_count_metric():
    """Create a word count difference metric instance."""
    return TextStatsMetric(metric_type="word_count")


def create_char_count_metric():
    """Create a character count difference metric instance."""
    return TextStatsMetric(metric_type="char_count")


__all__ = [
    'Metric',
    'METRIC_NAME',
    'METRIC_DISPLAY_NAME',
    'METRIC_DESCRIPTION',
    'METRIC_CATEGORY',
    'is_available',
    'create_word_count_metric',
    'create_char_count_metric'
]
