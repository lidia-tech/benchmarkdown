"""PDF metadata management for ground truth associations.

This module provides utilities to read and write ground truth file associations
directly into PDF metadata using PyMuPDF (fitz).
"""

import os
from typing import Optional
from pathlib import Path


class PDFMetadataManager:
    """Manages ground truth associations stored in PDF metadata."""

    GROUND_TRUTH_KEY = "GroundTruthFile"

    @staticmethod
    def set_ground_truth_association(pdf_path: str, ground_truth_filename: str) -> bool:
        """Store ground truth filename in PDF metadata.

        Args:
            pdf_path: Path to the PDF file
            ground_truth_filename: Name of the ground truth markdown file

        Returns:
            True if successful, False otherwise
        """
        if not pdf_path.lower().endswith('.pdf'):
            return False

        try:
            import fitz  # PyMuPDF

            doc = fitz.open(pdf_path)
            metadata = doc.metadata or {}
            metadata[PDFMetadataManager.GROUND_TRUTH_KEY] = ground_truth_filename
            doc.set_metadata(metadata)
            doc.save(pdf_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
            doc.close()
            return True

        except Exception as e:
            print(f"Warning: Could not set metadata for {pdf_path}: {e}")
            return False

    @staticmethod
    def get_ground_truth_association(pdf_path: str) -> Optional[str]:
        """Retrieve ground truth filename from PDF metadata.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Ground truth filename if found, None otherwise
        """
        if not pdf_path.lower().endswith('.pdf'):
            return None

        try:
            import fitz  # PyMuPDF

            doc = fitz.open(pdf_path)
            metadata = doc.metadata or {}
            ground_truth = metadata.get(PDFMetadataManager.GROUND_TRUTH_KEY)
            doc.close()
            return ground_truth

        except Exception as e:
            print(f"Warning: Could not read metadata from {pdf_path}: {e}")
            return None

    @staticmethod
    def clear_ground_truth_association(pdf_path: str) -> bool:
        """Remove ground truth association from PDF metadata.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            True if successful, False otherwise
        """
        if not pdf_path.lower().endswith('.pdf'):
            return False

        try:
            import fitz  # PyMuPDF

            doc = fitz.open(pdf_path)
            metadata = doc.metadata or {}

            if PDFMetadataManager.GROUND_TRUTH_KEY in metadata:
                del metadata[PDFMetadataManager.GROUND_TRUTH_KEY]
                doc.set_metadata(metadata)
                doc.save(pdf_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)

            doc.close()
            return True

        except Exception as e:
            print(f"Warning: Could not clear metadata for {pdf_path}: {e}")
            return False


__all__ = ['PDFMetadataManager']
