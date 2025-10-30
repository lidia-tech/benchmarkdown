"""Test validation workflow end-to-end."""

import asyncio
import tempfile
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from benchmarkdown.ui.validation import ValidationUI
from benchmarkdown.metrics import MetricRegistry


@dataclass
class MockExtractionResult:
    """Mock extraction result for testing."""
    markdown: str
    error: Optional[str] = None
    timing: float = 0.0


async def test_validation_ui_basic():
    """Test basic validation UI functionality."""
    print("\n" + "="*60)
    print("Test 1: Validation UI Basic Setup")
    print("="*60)

    # Create validation UI
    registry = MetricRegistry()
    registry.discover_metrics()
    validation_ui = ValidationUI(metric_registry=registry)

    # Check available metrics
    metrics = validation_ui.get_available_metrics()
    print(f"\n✅ Available metrics: {metrics}")
    assert len(metrics) > 0, "Should have at least one metric"

    print("\n✅ Validation UI initialized correctly")


async def test_ground_truth_upload():
    """Test ground truth upload."""
    print("\n" + "="*60)
    print("Test 2: Ground Truth Upload")
    print("="*60)

    validation_ui = ValidationUI()

    # Create a temp file with ground truth
    gt_text = "This is the ground truth markdown text with exactly ten words here."

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(gt_text)
        gt_file = f.name

    try:
        # Upload ground truth
        doc_name = "test_doc.pdf"
        status = validation_ui.upload_ground_truth(gt_file, doc_name)
        print(f"\n{status}")

        assert "✅" in status, "Upload should succeed"
        assert doc_name in validation_ui.ground_truths, "GT should be stored"
        assert validation_ui.ground_truths[doc_name] == gt_text, "GT text should match"

        print("\n✅ Ground truth upload works correctly")

    finally:
        Path(gt_file).unlink()


async def test_validation_execution():
    """Test running validation with metrics."""
    print("\n" + "="*60)
    print("Test 3: Validation Execution")
    print("="*60)

    validation_ui = ValidationUI()

    # Setup ground truth
    gt_text = "This is the ground truth text with ten words total."
    doc_name = "test_doc.pdf"

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(gt_text)
        gt_file = f.name

    validation_ui.upload_ground_truth(gt_file, doc_name)
    Path(gt_file).unlink()

    # Setup mock extraction results
    ui_results = {
        doc_name: {
            "Docling": MockExtractionResult(
                markdown="This is extracted text with seven words.",
                error=None
            ),
            "AWS Textract": MockExtractionResult(
                markdown="This is another extraction with different word count here.",
                error=None
            ),
        }
    }

    # Run validation
    status = await validation_ui.run_validation(
        ui_results=ui_results,
        selected_documents=[doc_name],
        selected_extractors=["Docling", "AWS Textract"],
        selected_metrics=["text_stats"]
    )

    print(f"\n{status}")
    assert "✅" in status, "Validation should succeed"

    # Check results were stored
    assert doc_name in validation_ui.validation_results, "Results should be stored for document"
    assert "Docling" in validation_ui.validation_results[doc_name], "Results should be stored for Docling"
    assert "AWS Textract" in validation_ui.validation_results[doc_name], "Results should be stored for Textract"

    # Check that word_count_diff and char_count_diff were computed
    docling_results = validation_ui.validation_results[doc_name]["Docling"]
    assert "word_count_diff" in docling_results, "Should have word count metric"
    assert "char_count_diff" in docling_results, "Should have char count metric"

    print(f"\nDocling word count diff: {docling_results['word_count_diff'].formatted_value}")
    print(f"Docling char count diff: {docling_results['char_count_diff'].formatted_value}")

    print("\n✅ Validation execution works correctly")


async def test_validation_html_generation():
    """Test HTML results generation."""
    print("\n" + "="*60)
    print("Test 4: HTML Results Generation")
    print("="*60)

    validation_ui = ValidationUI()

    # Setup and run validation
    gt_text = "This is the ground truth text."
    doc_name = "test_doc.pdf"

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(gt_text)
        gt_file = f.name

    validation_ui.upload_ground_truth(gt_file, doc_name)
    Path(gt_file).unlink()

    ui_results = {
        doc_name: {
            "Docling": MockExtractionResult(markdown="This is extracted text."),
            "AWS Textract": MockExtractionResult(markdown="Different extracted text here."),
        }
    }

    await validation_ui.run_validation(
        ui_results=ui_results,
        selected_documents=[doc_name],
        selected_extractors=["Docling", "AWS Textract"],
        selected_metrics=["text_stats"]
    )

    # Generate HTML
    html = validation_ui.generate_validation_results_html()

    print(f"\nGenerated HTML ({len(html)} chars)")
    assert len(html) > 0, "Should generate HTML"
    assert doc_name in html, "Should include document name"
    assert "Docling" in html, "Should include Docling"
    assert "AWS Textract" in html, "Should include Textract"
    assert "word_count_diff" in html or "Word Count Diff" in html, "Should include word count metric"

    print("\n✅ HTML generation works correctly")


async def test_validation_error_handling():
    """Test validation error handling."""
    print("\n" + "="*60)
    print("Test 5: Validation Error Handling")
    print("="*60)

    validation_ui = ValidationUI()

    # Try validation without ground truth
    status = await validation_ui.run_validation(
        ui_results={},
        selected_documents=["missing_doc.pdf"],
        selected_extractors=["Docling"],
        selected_metrics=["text_stats"]
    )

    print(f"\n{status}")
    assert "⚠️" in status and "Missing ground truth" in status, "Should warn about missing GT"

    # Try validation with no documents selected
    status = await validation_ui.run_validation(
        ui_results={},
        selected_documents=[],
        selected_extractors=["Docling"],
        selected_metrics=["text_stats"]
    )

    print(f"{status}")
    assert "⚠️" in status and "document" in status.lower(), "Should warn about no documents"

    # Try validation with no extractors selected
    status = await validation_ui.run_validation(
        ui_results={},
        selected_documents=["doc.pdf"],
        selected_extractors=[],
        selected_metrics=["text_stats"]
    )

    print(f"{status}")
    assert "⚠️" in status and "extractor" in status.lower(), "Should warn about no extractors"

    print("\n✅ Error handling works correctly")


async def test_multiple_documents():
    """Test validation with multiple documents."""
    print("\n" + "="*60)
    print("Test 6: Multiple Documents Validation")
    print("="*60)

    validation_ui = ValidationUI()

    # Setup ground truths for multiple documents
    documents = {
        "doc1.pdf": "First document ground truth text.",
        "doc2.pdf": "Second document has different content here.",
        "doc3.pdf": "Third document with even more text content."
    }

    for doc_name, gt_text in documents.items():
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(gt_text)
            gt_file = f.name
        validation_ui.upload_ground_truth(gt_file, doc_name)
        Path(gt_file).unlink()

    # Setup extraction results for all documents
    ui_results = {
        doc_name: {
            "Docling": MockExtractionResult(markdown=f"Extracted text for {doc_name}")
        }
        for doc_name in documents.keys()
    }

    # Run validation for all documents
    status = await validation_ui.run_validation(
        ui_results=ui_results,
        selected_documents=list(documents.keys()),
        selected_extractors=["Docling"],
        selected_metrics=["text_stats"]
    )

    print(f"\n{status}")
    assert "✅" in status, "Validation should succeed"

    # Verify results for all documents
    for doc_name in documents.keys():
        assert doc_name in validation_ui.validation_results, f"Should have results for {doc_name}"
        assert "Docling" in validation_ui.validation_results[doc_name], f"Should have Docling results for {doc_name}"

    # Generate HTML and check it includes all documents
    html = validation_ui.generate_validation_results_html()
    for doc_name in documents.keys():
        assert doc_name in html, f"HTML should include {doc_name}"

    print(f"\n✅ Multiple documents validation works correctly")


async def test_clear_results():
    """Test clearing validation results."""
    print("\n" + "="*60)
    print("Test 7: Clear Validation Results")
    print("="*60)

    validation_ui = ValidationUI()

    # Add some results
    validation_ui.validation_results = {
        "doc.pdf": {
            "Docling": {
                "word_count_diff": "test"
            }
        }
    }

    assert len(validation_ui.validation_results) > 0, "Should have results"

    # Clear results
    status = validation_ui.clear_validation_results()
    print(f"\n{status}")

    assert "✅" in status, "Clear should succeed"
    assert len(validation_ui.validation_results) == 0, "Results should be empty"

    print("\n✅ Clear results works correctly")


async def main():
    """Run all tests."""
    print("\n🧪 Testing Validation Workflow\n")

    try:
        await test_validation_ui_basic()
        await test_ground_truth_upload()
        await test_validation_execution()
        await test_validation_html_generation()
        await test_validation_error_handling()
        await test_multiple_documents()
        await test_clear_results()

        print("\n" + "="*60)
        print("✅ All validation workflow tests passed!")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())
