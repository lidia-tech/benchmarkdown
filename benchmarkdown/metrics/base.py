"""Base protocol and data structures for evaluation metrics.

This module defines the core protocol that all metrics must implement,
following the same plugin architecture pattern as extractors.
"""

from dataclasses import dataclass
from typing import Protocol, Optional, Dict, Any


@dataclass
class MetricResult:
    """Result of a metric computation.

    Attributes:
        value: The computed metric value (could be float, int, or other types)
        description: Human-readable description of the result
        details: Optional dictionary with additional information
        formatted_value: Optional pre-formatted string representation
    """
    value: Any
    description: str
    details: Optional[Dict[str, Any]] = None
    formatted_value: Optional[str] = None

    def __str__(self) -> str:
        """String representation of the metric result."""
        if self.formatted_value:
            return self.formatted_value
        return f"{self.value}"


class Metric(Protocol):
    """Protocol for evaluation metrics.

    All metrics must implement this protocol to be discoverable and usable
    by the metrics registry and UI.
    """

    async def compute(self, ground_truth: str, extracted: str) -> MetricResult:
        """Compute the metric comparing extracted text to ground truth.

        Args:
            ground_truth: The reference/ground truth markdown text
            extracted: The extracted markdown text to evaluate

        Returns:
            MetricResult containing the computed value and metadata
        """
        ...


__all__ = ['Metric', 'MetricResult']
