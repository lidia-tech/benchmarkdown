"""
Test environment variable configuration for system-level settings.

This test verifies that system-level settings can be configured via
environment variables across all extractors.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_tensorlake_env_vars():
    """Test TensorLake environment variable configuration."""
    from benchmarkdown.extractors.tensorlake.config import TensorLakeConfig

    # api_key is the env-var-backed field on this config.
    os.environ['TENSORLAKE_API_KEY'] = 'test-key-from-env'
    try:
        config = TensorLakeConfig()
        assert config.api_key == 'test-key-from-env', f"Expected 'test-key-from-env', got {config.api_key}"
    finally:
        del os.environ['TENSORLAKE_API_KEY']

    # Default value is an empty string when the env var is unset.
    config_default = TensorLakeConfig()
    assert config_default.api_key == '', f"Expected '', got {config_default.api_key}"


def test_llamaparse_env_vars():
    """Test LlamaParse environment variable configuration."""
    from benchmarkdown.extractors.llamaparse.config import LlamaParseConfig

    env = {
        'LLAMAPARSE_NUM_WORKERS': '8',
        'LLAMAPARSE_MAX_TIMEOUT': '3000',
        'LLAMAPARSE_VERBOSE': 'true',
        'LLAMAPARSE_SHOW_PROGRESS': 'false',
        'LLAMAPARSE_IGNORE_ERRORS': '1',
    }
    os.environ.update(env)
    try:
        config = LlamaParseConfig()
        assert config.num_workers == 8, f"Expected 8, got {config.num_workers}"
        assert config.max_timeout == 3000, f"Expected 3000, got {config.max_timeout}"
        assert config.verbose is True, f"Expected True, got {config.verbose}"
        assert config.show_progress is False, f"Expected False, got {config.show_progress}"
        assert config.ignore_errors is True, f"Expected True, got {config.ignore_errors}"
    finally:
        for key in env:
            os.environ.pop(key, None)

    # Defaults
    config_default = LlamaParseConfig()
    assert config_default.num_workers == 4, f"Expected 4, got {config_default.num_workers}"
    assert config_default.max_timeout == 2000, f"Expected 2000, got {config_default.max_timeout}"


def test_docling_env_vars():
    """Test Docling environment variable configuration."""
    import multiprocessing
    from benchmarkdown.extractors.docling.config import DoclingConfig

    os.environ['DOCLING_NUM_THREADS'] = '16'
    os.environ['DOCLING_DOCUMENT_TIMEOUT'] = '600.0'
    try:
        config = DoclingConfig()
        assert config.num_threads == 16, f"Expected 16, got {config.num_threads}"
        assert config.document_timeout == 600.0, f"Expected 600.0, got {config.document_timeout}"
    finally:
        del os.environ['DOCLING_NUM_THREADS']
        del os.environ['DOCLING_DOCUMENT_TIMEOUT']

    # Defaults
    config_default = DoclingConfig()
    expected_threads = multiprocessing.cpu_count()
    assert config_default.num_threads == expected_threads, f"Expected {expected_threads}, got {config_default.num_threads}"
    assert config_default.document_timeout is None, f"Expected None, got {config_default.document_timeout}"


def test_env_var_precedence():
    """Test that environment variables and explicit values interact correctly."""
    from benchmarkdown.extractors.tensorlake.config import TensorLakeConfig
    from benchmarkdown.extractors.llamaparse.config import LlamaParseConfig

    # TensorLake: env var should be picked up.
    os.environ['TENSORLAKE_API_KEY'] = 'precedence-key'
    try:
        config = TensorLakeConfig()
        assert config.api_key == 'precedence-key'
    finally:
        del os.environ['TENSORLAKE_API_KEY']

    # LlamaParse: env var used when no explicit value; explicit value overrides env var.
    os.environ['LLAMAPARSE_NUM_WORKERS'] = '10'
    try:
        config_env = LlamaParseConfig()
        assert config_env.num_workers == 10

        config_explicit = LlamaParseConfig(num_workers=6)
        assert config_explicit.num_workers == 6
    finally:
        del os.environ['LLAMAPARSE_NUM_WORKERS']
