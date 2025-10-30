"""Test ground truth upload list functionality."""

import tempfile
from pathlib import Path
from benchmarkdown.ui.validation import ValidationUI


def test_gt_upload_list():
    """Test that uploaded GT files are tracked correctly."""
    print("\n" + "="*60)
    print("Test: Ground Truth Upload List")
    print("="*60)

    validation_ui = ValidationUI()

    # Initially empty
    assert len(validation_ui.ground_truths) == 0
    print("\n✅ Initially empty")

    # Upload first GT
    gt_text_1 = "First ground truth document with some content here."
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(gt_text_1)
        gt_file_1 = f.name

    status = validation_ui.upload_ground_truth(gt_file_1, "doc1.pdf")
    Path(gt_file_1).unlink()

    assert "doc1.pdf" in validation_ui.ground_truths
    assert len(validation_ui.ground_truths) == 1
    print(f"\n{status}")
    print("✅ First GT uploaded")

    # Upload second GT
    gt_text_2 = "Second ground truth document with different content and more words to test counting."
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(gt_text_2)
        gt_file_2 = f.name

    status = validation_ui.upload_ground_truth(gt_file_2, "doc2.pdf")
    Path(gt_file_2).unlink()

    assert "doc2.pdf" in validation_ui.ground_truths
    assert len(validation_ui.ground_truths) == 2
    print(f"\n{status}")
    print("✅ Second GT uploaded")

    # Upload third GT
    gt_text_3 = "Third document."
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(gt_text_3)
        gt_file_3 = f.name

    status = validation_ui.upload_ground_truth(gt_file_3, "doc3.pdf")
    Path(gt_file_3).unlink()

    assert "doc3.pdf" in validation_ui.ground_truths
    assert len(validation_ui.ground_truths) == 3
    print(f"\n{status}")
    print("✅ Third GT uploaded")

    # Verify all are tracked
    print(f"\n✅ All {len(validation_ui.ground_truths)} GT files tracked:")
    for doc_name, gt_text in sorted(validation_ui.ground_truths.items()):
        word_count = len(gt_text.split())
        char_count = len(gt_text)
        print(f"   - {doc_name}: {word_count} words, {char_count} chars")

    print("\n" + "="*60)
    print("✅ All tests passed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_gt_upload_list()
