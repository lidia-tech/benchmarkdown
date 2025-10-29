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
    print("✅ Test 1: TensorLake environment variables")

    # Set environment variable
    os.environ['TENSORLAKE_MAX_TIMEOUT'] = '600'

    try:
        from benchmarkdown.extractors.tensorlake.config import TensorLakeConfig

        config = TensorLakeConfig()
        print(f"   ✓ max_timeout from env var: {config.max_timeout} (expected: 600)")
        assert config.max_timeout == 600, f"Expected 600, got {config.max_timeout}"

        # Clean up
        del os.environ['TENSORLAKE_MAX_TIMEOUT']

        # Test default value
        config_default = TensorLakeConfig()
        print(f"   ✓ max_timeout default: {config_default.max_timeout} (expected: 300)")
        assert config_default.max_timeout == 300, f"Expected 300, got {config_default.max_timeout}"

        return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_llamaparse_env_vars():
    """Test LlamaParse environment variable configuration."""
    print("\n✅ Test 2: LlamaParse environment variables")

    # Set environment variables
    os.environ['LLAMAPARSE_NUM_WORKERS'] = '8'
    os.environ['LLAMAPARSE_MAX_TIMEOUT'] = '3000'
    os.environ['LLAMAPARSE_VERBOSE'] = 'true'
    os.environ['LLAMAPARSE_SHOW_PROGRESS'] = 'false'
    os.environ['LLAMAPARSE_IGNORE_ERRORS'] = '1'

    try:
        from benchmarkdown.extractors.llamaparse.config import LlamaParseConfig

        config = LlamaParseConfig()
        print(f"   ✓ num_workers from env var: {config.num_workers} (expected: 8)")
        assert config.num_workers == 8, f"Expected 8, got {config.num_workers}"

        print(f"   ✓ max_timeout from env var: {config.max_timeout} (expected: 3000)")
        assert config.max_timeout == 3000, f"Expected 3000, got {config.max_timeout}"

        print(f"   ✓ verbose from env var: {config.verbose} (expected: True)")
        assert config.verbose == True, f"Expected True, got {config.verbose}"

        print(f"   ✓ show_progress from env var: {config.show_progress} (expected: False)")
        assert config.show_progress == False, f"Expected False, got {config.show_progress}"

        print(f"   ✓ ignore_errors from env var: {config.ignore_errors} (expected: True)")
        assert config.ignore_errors == True, f"Expected True, got {config.ignore_errors}"

        # Clean up
        for key in ['LLAMAPARSE_NUM_WORKERS', 'LLAMAPARSE_MAX_TIMEOUT', 'LLAMAPARSE_VERBOSE',
                    'LLAMAPARSE_SHOW_PROGRESS', 'LLAMAPARSE_IGNORE_ERRORS']:
            if key in os.environ:
                del os.environ[key]

        # Test defaults
        config_default = LlamaParseConfig()
        print(f"   ✓ num_workers default: {config_default.num_workers} (expected: 4)")
        assert config_default.num_workers == 4, f"Expected 4, got {config_default.num_workers}"

        print(f"   ✓ max_timeout default: {config_default.max_timeout} (expected: 2000)")
        assert config_default.max_timeout == 2000, f"Expected 2000, got {config_default.max_timeout}"

        return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_docling_env_vars():
    """Test Docling environment variable configuration."""
    print("\n✅ Test 3: Docling environment variables")

    # Set environment variables
    os.environ['DOCLING_NUM_THREADS'] = '16'
    os.environ['DOCLING_DOCUMENT_TIMEOUT'] = '600.0'

    try:
        from benchmarkdown.extractors.docling.config import DoclingConfig

        config = DoclingConfig()
        print(f"   ✓ num_threads from env var: {config.num_threads} (expected: 16)")
        assert config.num_threads == 16, f"Expected 16, got {config.num_threads}"

        print(f"   ✓ document_timeout from env var: {config.document_timeout} (expected: 600.0)")
        assert config.document_timeout == 600.0, f"Expected 600.0, got {config.document_timeout}"

        # Clean up
        del os.environ['DOCLING_NUM_THREADS']
        del os.environ['DOCLING_DOCUMENT_TIMEOUT']

        # Test defaults
        import multiprocessing
        config_default = DoclingConfig()
        expected_threads = multiprocessing.cpu_count()
        print(f"   ✓ num_threads default: {config_default.num_threads} (expected: {expected_threads})")
        assert config_default.num_threads == expected_threads, f"Expected {expected_threads}, got {config_default.num_threads}"

        print(f"   ✓ document_timeout default: {config_default.document_timeout} (expected: None)")
        assert config_default.document_timeout is None, f"Expected None, got {config_default.document_timeout}"

        return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_env_var_precedence():
    """Test that environment variables take precedence over defaults."""
    print("\n✅ Test 4: Environment variable precedence")

    try:
        # TensorLake: env var should override default
        os.environ['TENSORLAKE_MAX_TIMEOUT'] = '450'
        from benchmarkdown.extractors.tensorlake.config import TensorLakeConfig
        config = TensorLakeConfig()
        print(f"   ✓ TensorLake max_timeout: {config.max_timeout} (env var overrides default)")
        assert config.max_timeout == 450
        del os.environ['TENSORLAKE_MAX_TIMEOUT']

        # LlamaParse: explicit value in constructor should override env var
        os.environ['LLAMAPARSE_NUM_WORKERS'] = '10'
        from benchmarkdown.extractors.llamaparse.config import LlamaParseConfig

        # First, verify env var is used when no explicit value
        config_env = LlamaParseConfig()
        print(f"   ✓ LlamaParse num_workers from env: {config_env.num_workers} (expected: 10)")
        assert config_env.num_workers == 10

        # Then verify explicit value overrides env var
        config_explicit = LlamaParseConfig(num_workers=6)
        print(f"   ✓ LlamaParse num_workers explicit: {config_explicit.num_workers} (overrides env var)")
        assert config_explicit.num_workers == 6

        del os.environ['LLAMAPARSE_NUM_WORKERS']

        return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("Environment Variable Configuration Test")
    print("=" * 70)

    tests = [
        test_tensorlake_env_vars,
        test_llamaparse_env_vars,
        test_docling_env_vars,
        test_env_var_precedence,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("\n" + "=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Test Results: {passed}/{total} passed")

    if passed == total:
        print("✅ All tests passed!")
    else:
        print(f"❌ {total - passed} test(s) failed")
    print("=" * 70)

    return 0 if passed == total else 1


if __name__ == "__main__":
    exit(main())
