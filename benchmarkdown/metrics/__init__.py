"""Metrics registry and plugin discovery system.

This module provides automatic discovery of evaluation metrics following
the same plugin architecture pattern as extractors.
"""

import importlib
import pkgutil
from dataclasses import dataclass
from typing import Dict, List, Tuple, Type, Optional, Any
from pathlib import Path

from .base import Metric, MetricResult


@dataclass
class MetricMetadata:
    """Metadata about a registered metric."""
    name: str
    display_name: str
    description: str
    category: str
    metric_class: Type[Metric]
    is_available: bool
    unavailable_reason: str = ""


class MetricRegistry:
    """Registry for discovering and managing evaluation metrics.

    Automatically discovers metrics from the benchmarkdown/metrics/ directory.
    Each metric should be in its own subdirectory with:
    - __init__.py: Exports METRIC_NAME, METRIC_DISPLAY_NAME, METRIC_DESCRIPTION,
                   METRIC_CATEGORY, Metric (the implementation class), is_available()
    """

    def __init__(self):
        """Initialize the registry."""
        self._metrics: Dict[str, MetricMetadata] = {}

    def discover_metrics(self) -> None:
        """Discover all available metrics in the metrics directory."""
        metrics_path = Path(__file__).parent

        # Iterate through all subdirectories
        for finder, name, ispkg in pkgutil.iter_modules([str(metrics_path)]):
            if not ispkg or name.startswith('_'):
                continue

            try:
                # Import the metric module
                module = importlib.import_module(f'benchmarkdown.metrics.{name}')

                # Check for required exports
                required_attrs = ['METRIC_NAME', 'METRIC_DISPLAY_NAME', 'METRIC_DESCRIPTION',
                                  'METRIC_CATEGORY', 'Metric', 'is_available']
                missing_attrs = [attr for attr in required_attrs if not hasattr(module, attr)]

                if missing_attrs:
                    print(f"⚠️  Metric '{name}' missing required attributes: {missing_attrs}")
                    continue

                # Check if metric is available
                is_available_func = getattr(module, 'is_available')
                is_available, reason = is_available_func()

                # Register the metric
                metric_name = getattr(module, 'METRIC_NAME')
                self._metrics[metric_name] = MetricMetadata(
                    name=metric_name,
                    display_name=getattr(module, 'METRIC_DISPLAY_NAME'),
                    description=getattr(module, 'METRIC_DESCRIPTION'),
                    category=getattr(module, 'METRIC_CATEGORY'),
                    metric_class=getattr(module, 'Metric'),
                    is_available=is_available,
                    unavailable_reason=reason
                )

                status = "✅" if is_available else "⚠️"
                print(f"{status} Discovered metric: {metric_name} ({getattr(module, 'METRIC_DISPLAY_NAME')})")
                if not is_available:
                    print(f"   Reason: {reason}")

            except Exception as e:
                print(f"❌ Failed to load metric '{name}': {e}")
                import traceback
                traceback.print_exc()

    def get_available_metrics(self) -> Dict[str, MetricMetadata]:
        """Get all available (usable) metrics.

        Returns:
            Dictionary mapping metric names to their metadata
        """
        return {name: meta for name, meta in self._metrics.items() if meta.is_available}

    def get_all_metrics(self) -> Dict[str, MetricMetadata]:
        """Get all registered metrics, including unavailable ones.

        Returns:
            Dictionary mapping metric names to their metadata
        """
        return self._metrics.copy()

    def get_metric(self, name: str) -> Optional[MetricMetadata]:
        """Get metadata for a specific metric.

        Args:
            name: The metric name

        Returns:
            MetricMetadata if found, None otherwise
        """
        return self._metrics.get(name)

    def create_metric_instance(self, name: str, **kwargs) -> Optional[Metric]:
        """Create an instance of a metric.

        Args:
            name: The metric name
            **kwargs: Additional arguments to pass to the metric constructor

        Returns:
            An instance of the metric, or None if not found/unavailable
        """
        metadata = self.get_metric(name)
        if not metadata or not metadata.is_available:
            return None

        try:
            return metadata.metric_class(**kwargs)
        except Exception as e:
            print(f"❌ Failed to instantiate metric '{name}': {e}")
            return None

    def list_metrics_by_category(self) -> Dict[str, List[MetricMetadata]]:
        """Get metrics grouped by category.

        Returns:
            Dictionary mapping category names to lists of metric metadata
        """
        categories: Dict[str, List[MetricMetadata]] = {}
        for metadata in self.get_available_metrics().values():
            if metadata.category not in categories:
                categories[metadata.category] = []
            categories[metadata.category].append(metadata)
        return categories


__all__ = ['MetricRegistry', 'MetricMetadata', 'Metric', 'MetricResult']
