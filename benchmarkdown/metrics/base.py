"""Base protocol and data structures for evaluation metrics.

This module defines the core protocol that all metrics must implement,
following the same plugin architecture pattern as extractors.
"""

from dataclasses import dataclass
from typing import Protocol, Optional, Dict, Any


@dataclass
class MetricResult:
    """Result of a metric computation.

    All metrics must return a normalized similarity score in the range [0.0, 1.0]:
    - 1.0 = perfect match (best possible score)
    - 0.0 = worst possible match

    This normalization allows:
    - Consistent comparison across different metric types
    - Easy aggregation and averaging
    - Intuitive "higher is better" interpretation
    - Simple percentage visualization (multiply by 100)

    Attributes:
        value: Normalized similarity score in range [0.0, 1.0]
        description: Human-readable description of the result
        details: Optional dictionary with additional information
        formatted_value: Optional pre-formatted string representation (e.g., "85.5%")
    """
    value: float
    description: str
    details: Optional[Dict[str, Any]] = None
    formatted_value: Optional[str] = None

    def __post_init__(self):
        """Validate that value is in valid range."""
        if not isinstance(self.value, (int, float)):
            raise ValueError(f"MetricResult value must be numeric, got {type(self.value)}")
        if not 0.0 <= self.value <= 1.0:
            raise ValueError(f"MetricResult value must be in range [0.0, 1.0], got {self.value}")

    def __str__(self) -> str:
        """String representation of the metric result."""
        if self.formatted_value:
            return self.formatted_value
        return f"{self.value * 100:.1f}%"


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
