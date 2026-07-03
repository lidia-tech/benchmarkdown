"""Pytest configuration for the benchmarkdown test suite.

Two tiers gate tests that reach beyond a plain, offline unit run:

- ``@pytest.mark.integration`` — tests that need live API credentials, a running
  app, or a browser. They are *deselected* by default via the
  ``addopts = "-m 'not integration'"`` setting in ``pyproject.toml``. Run them
  with ``uv run pytest -m integration`` (the CLI ``-m`` replaces the default
  filter) or everything with ``uv run pytest -m ""``.

- ``@pytest.mark.live`` — tests that hit real, billable external services
  (e.g. a real extraction call to a cloud API). They are *collected* but
  *skipped* unless the custom ``--live`` flag is passed. ``live`` is stricter
  than ``integration``; a live integration test typically needs both:
  ``uv run pytest -m integration --live``.
"""

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--live",
        action="store_true",
        default=False,
        help="run @pytest.mark.live tests that hit real, billable external services",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: tests that require live API credentials, a running app, or a "
        "browser (deselected by default; run with -m integration)",
    )
    config.addinivalue_line(
        "markers",
        "live: tests that hit real, billable external services (skipped unless --live)",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--live"):
        return
    skip_live = pytest.mark.skip(reason="need --live option to run")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)
