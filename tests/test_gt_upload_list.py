"""Test ground truth upload list functionality."""

import tempfile
from pathlib import Path
from benchmarkdown.ui.validation import ValidationUI


def _write_gt(dir_path: Path, name: str, text: str) -> str:
    """Write a ground truth file with a controlled name and return its path.

    ``upload_ground_truth`` keys stored ground truths by the file's basename,
    so the test controls the filename rather than relying on a random temp name.
    """
    gt_path = dir_path / name
    gt_path.write_text(text, encoding="utf-8")
    return str(gt_path)


def test_gt_upload_list():
    """Test that uploaded GT files are tracked correctly."""
    print("\n" + "="*60)
    print("Test: Ground Truth Upload List")
    print("="*60)

    validation_ui = ValidationUI()

    # Initially empty
    assert len(validation_ui.ground_truths) == 0
    print("\n✅ Initially empty")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # Upload first GT
        gt_file_1 = _write_gt(tmp_path, "doc1.md", "First ground truth document with some content here.")
        status = validation_ui.upload_ground_truth(gt_file_1)

        assert "doc1.md" in validation_ui.ground_truths
        assert len(validation_ui.ground_truths) == 1
        print(f"\n{status}")
        print("✅ First GT uploaded")

        # Upload second GT
        gt_file_2 = _write_gt(
            tmp_path, "doc2.md",
            "Second ground truth document with different content and more words to test counting.",
        )
        status = validation_ui.upload_ground_truth(gt_file_2)

        assert "doc2.md" in validation_ui.ground_truths
        assert len(validation_ui.ground_truths) == 2
        print(f"\n{status}")
        print("✅ Second GT uploaded")

        # Upload third GT
        gt_file_3 = _write_gt(tmp_path, "doc3.md", "Third document.")
        status = validation_ui.upload_ground_truth(gt_file_3)

        assert "doc3.md" in validation_ui.ground_truths
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
