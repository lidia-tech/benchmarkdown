"""Test basic metrics functionality."""

import asyncio
from benchmarkdown.metrics import MetricRegistry
from benchmarkdown.metrics.text_stats import create_word_count_metric, create_char_count_metric


async def test_metric_registry():
    """Test metric registry discovery."""
    print("\n" + "="*60)
    print("Test 1: Metric Registry Discovery")
    print("="*60)

    registry = MetricRegistry()
    registry.discover_metrics()

    print(f"\n✅ Discovered {len(registry.get_all_metrics())} total metrics")
    print(f"✅ Available {len(registry.get_available_metrics())} metrics")

    for name, metadata in registry.get_all_metrics().items():
        status = "✅" if metadata.is_available else "❌"
        print(f"{status} {metadata.display_name} ({name})")
        print(f"   Category: {metadata.category}")
        print(f"   Description: {metadata.description}")


async def test_word_count_metric():
    """Test word count metric."""
    print("\n" + "="*60)
    print("Test 2: Word Count Metric")
    print("="*60)

    metric = create_word_count_metric()

    ground_truth = "This is a test document with ten words in it."
    extracted = "This is a test with five words."

    result = await metric.compute(ground_truth, extracted)

    print(f"\nGround Truth: {len(ground_truth.split())} words")
    print(f"Extracted: {len(extracted.split())} words")
    print(f"Result: {result.formatted_value}")
    print(f"Description: {result.description}")
    print(f"Details: {result.details}")

    # GT has 10 words, extracted has 7 words, diff is 3
    # Similarity = 1.0 - 3/10 = 0.7 (70%)
    assert 0.0 <= result.value <= 1.0, "Similarity should be in range [0.0, 1.0]"
    assert result.value == 0.7, f"Expected 0.7 (70% similarity), got {result.value}"
    print("\n✅ Word count metric works correctly")


async def test_char_count_metric():
    """Test character count metric."""
    print("\n" + "="*60)
    print("Test 3: Character Count Metric")
    print("="*60)

    metric = create_char_count_metric()

    ground_truth = "This is a test document."
    extracted = "This is a test."

    result = await metric.compute(ground_truth, extracted)

    print(f"\nGround Truth: {len(ground_truth)} characters")
    print(f"Extracted: {len(extracted)} characters")
    print(f"Result: {result.formatted_value}")
    print(f"Description: {result.description}")
    print(f"Details: {result.details}")

    # GT has 24 chars, extracted has 15 chars, diff is 9
    # Similarity = 1.0 - 9/24 = 0.625 (62.5%)
    assert 0.0 <= result.value <= 1.0, "Similarity should be in range [0.0, 1.0]"
    assert result.value == 0.625, f"Expected 0.625 (62.5% similarity), got {result.value}"
    print("\n✅ Character count metric works correctly")


async def test_perfect_match():
    """Test metrics with identical texts."""
    print("\n" + "="*60)
    print("Test 4: Perfect Match (100% similarity)")
    print("="*60)

    text = "This is exactly the same text."

    word_metric = create_word_count_metric()
    char_metric = create_char_count_metric()

    word_result = await word_metric.compute(text, text)
    char_result = await char_metric.compute(text, text)

    print(f"\nWord count similarity: {word_result.formatted_value}")
    print(f"Character count similarity: {char_result.formatted_value}")

    assert word_result.value == 1.0, "Word count should be 1.0 (100%) for identical texts"
    assert char_result.value == 1.0, "Char count should be 1.0 (100%) for identical texts"

    print("\n✅ Perfect match detection works correctly")


async def test_empty_ground_truth():
    """Test handling of empty ground truth."""
    print("\n" + "="*60)
    print("Test 5: Empty Ground Truth")
    print("="*60)

    word_metric = create_word_count_metric()

    ground_truth = ""
    extracted = "Some extracted text here."

    result = await word_metric.compute(ground_truth, extracted)

    print(f"\nGround Truth: empty")
    print(f"Extracted: {len(extracted.split())} words")
    print(f"Result: {result.formatted_value}")
    print(f"Description: {result.description}")

    # Empty GT with non-empty extracted = 0.0 similarity (0%)
    assert result.value == 0.0, f"Expected 0.0 (0% similarity), got {result.value}"
    print("\n✅ Empty ground truth handled correctly")


async def main():
    """Run all tests."""
    print("\n🧪 Testing Metrics Framework\n")

    try:
        await test_metric_registry()
        await test_word_count_metric()
        await test_char_count_metric()
        await test_perfect_match()
        await test_empty_ground_truth()

        print("\n" + "="*60)
        print("✅ All tests passed!")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())
