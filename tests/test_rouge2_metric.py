"""Test ROUGE-2 bigram overlap metric."""

import asyncio
from benchmarkdown.metrics.rouge2.metric import Rouge2Metric, normalize_for_comparison


async def test_identical_text():
    """Identical text should score ~1.0."""
    print("\n" + "="*60)
    print("Test 1: Identical Text")
    print("="*60)

    metric = Rouge2Metric()
    text = "The quick brown fox jumps over the lazy dog near the river bank."
    result = await metric.compute(text, text)

    print(f"F1: {result.formatted_value}")
    print(f"Details: {result.details}")

    assert result.value == 1.0, f"Expected 1.0 for identical text, got {result.value}"
    assert result.details["recall"] == 1.0
    assert result.details["precision"] == 1.0
    print("\n✅ Identical text scores 1.0")


async def test_empty_extraction():
    """Empty extraction against non-empty ground truth should score 0."""
    print("\n" + "="*60)
    print("Test 2: Empty Extraction")
    print("="*60)

    metric = Rouge2Metric()
    result = await metric.compute("The quick brown fox jumps over the lazy dog.", "")

    print(f"F1: {result.formatted_value}")
    print(f"Details: {result.details}")

    assert result.value == 0.0, f"Expected 0.0 for empty extraction, got {result.value}"
    assert result.details["ext_bigrams"] == 0
    print("\n✅ Empty extraction scores 0.0")


async def test_both_empty():
    """Both texts empty should score 1.0 (perfect match)."""
    print("\n" + "="*60)
    print("Test 3: Both Empty")
    print("="*60)

    metric = Rouge2Metric()
    result = await metric.compute("", "")

    print(f"F1: {result.formatted_value}")
    print(f"Details: {result.details}")

    assert result.value == 1.0, f"Expected 1.0 for both empty, got {result.value}"
    assert result.details["ref_bigrams"] == 0
    assert result.details["ext_bigrams"] == 0
    print("\n✅ Both empty scores 1.0")


async def test_truncated_text():
    """Truncated extraction: high precision, low recall."""
    print("\n" + "="*60)
    print("Test 4: Truncated Text")
    print("="*60)

    metric = Rouge2Metric()
    ground_truth = "The quick brown fox jumps over the lazy dog near the river bank."
    extracted = "The quick brown fox"

    result = await metric.compute(ground_truth, extracted)

    print(f"F1: {result.formatted_value}")
    print(f"Recall: {result.details['recall']}")
    print(f"Precision: {result.details['precision']}")

    assert result.details["precision"] == 1.0, "Truncated clean text should have perfect precision"
    assert result.details["recall"] < 0.5, "Truncated text should have low recall"
    print("\n✅ Truncated text: high precision, low recall")


async def test_boilerplate_text():
    """Text with prepended boilerplate: high recall, lower precision."""
    print("\n" + "="*60)
    print("Test 5: Boilerplate Prepended")
    print("="*60)

    metric = Rouge2Metric()
    ground_truth = "The quick brown fox jumps over the lazy dog."
    extracted = "Cookie policy accept all terms and conditions. The quick brown fox jumps over the lazy dog."

    result = await metric.compute(ground_truth, extracted)

    print(f"F1: {result.formatted_value}")
    print(f"Recall: {result.details['recall']}")
    print(f"Precision: {result.details['precision']}")

    assert result.details["recall"] == 1.0, "All ground truth content present → recall should be 1.0"
    assert result.details["precision"] < 1.0, "Boilerplate should reduce precision"
    print("\n✅ Boilerplate: high recall, reduced precision")


async def test_markdown_formatting_ignored():
    """Markdown formatting differences should not affect score."""
    print("\n" + "="*60)
    print("Test 6: Markdown Formatting Ignored")
    print("="*60)

    metric = Rouge2Metric()
    plain = "This is a heading and some important text follows here."
    markdown = "# This is a heading\n\nAnd **some** *important* text follows here."

    result = await metric.compute(plain, markdown)

    print(f"F1: {result.formatted_value}")
    assert result.value > 0.9, f"Formatting differences shouldn't matter, got {result.value}"
    print("\n✅ Markdown formatting does not affect score")


async def test_fenced_code_blocks_stripped():
    """Fenced code blocks should be stripped from text."""
    print("\n" + "="*60)
    print("Test 7: Fenced Code Blocks Stripped")
    print("="*60)

    metric = Rouge2Metric()
    ground_truth = "Introduction paragraph about the contract terms and conditions."
    with_code = "Introduction paragraph about the contract terms and conditions.\n\n```python\ndef irrelevant_code(): pass\n```"

    result = await metric.compute(ground_truth, with_code)

    print(f"F1: {result.formatted_value}")
    assert result.value == 1.0, f"Fenced code block should be stripped, got {result.value}"
    print("\n✅ Fenced code blocks are stripped")


async def test_single_token():
    """Single token in both texts (zero bigrams) should return 1.0."""
    print("\n" + "="*60)
    print("Test 8: Single Token (Zero Bigrams)")
    print("="*60)

    metric = Rouge2Metric()
    result = await metric.compute("hello", "hello")

    print(f"F1: {result.formatted_value}")
    print(f"Details: {result.details}")

    assert result.value == 1.0, f"Expected 1.0 for identical single token, got {result.value}"
    assert result.details["ref_bigrams"] == 0
    assert result.details["ext_bigrams"] == 0
    print("\n✅ Single token handled correctly")


async def test_details_accuracy():
    """Details dict should report actual bigram counts, not sentinel values."""
    print("\n" + "="*60)
    print("Test 9: Details Accuracy")
    print("="*60)

    metric = Rouge2Metric()
    # "the quick brown" → bigrams: (the,quick), (quick,brown) → 2
    result = await metric.compute("the quick brown", "the quick brown fox jumps")

    print(f"Details: {result.details}")

    assert result.details["ref_bigrams"] == 2, f"Expected 2 ref bigrams, got {result.details['ref_bigrams']}"
    assert result.details["ext_bigrams"] == 4, f"Expected 4 ext bigrams, got {result.details['ext_bigrams']}"
    assert result.details["overlap"] == 2
    print("\n✅ Details report accurate bigram counts")


async def main():
    """Run all tests."""
    print("\n🧪 Testing ROUGE-2 Bigram Overlap Metric\n")

    try:
        await test_identical_text()
        await test_empty_extraction()
        await test_both_empty()
        await test_truncated_text()
        await test_boilerplate_text()
        await test_markdown_formatting_ignored()
        await test_fenced_code_blocks_stripped()
        await test_single_token()
        await test_details_accuracy()

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
