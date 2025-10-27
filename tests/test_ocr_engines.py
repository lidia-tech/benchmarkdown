"""
Test OCR engine selection with different configurations.

This test demonstrates how to use different OCR engines with Docling.
"""

import asyncio
from pathlib import Path
from benchmarkdown.config import (
    DoclingConfig,
    OcrEngineEnum,
    EasyOcrConfig,
    TesseractOcrConfig,
    TesseractCliOcrConfig,
    RapidOcrConfig
)
from benchmarkdown.docling import DoclingExtractor


async def test_easyocr_engine():
    """Test extraction with EasyOCR engine."""
    print("✅ Testing EasyOCR engine...")

    # Configure EasyOCR
    easyocr_config = EasyOcrConfig(
        lang=["en"],
        use_gpu=False,
        force_full_page_ocr=True,
        confidence_threshold=0.5
    )

    # Create DoclingConfig with EasyOCR
    config = DoclingConfig(
        do_ocr=True,
        ocr_engine=OcrEngineEnum.EASYOCR,
        easyocr_config=easyocr_config,
        do_table_structure=True,
        num_threads=4
    )

    # Verify config
    assert config.ocr_engine == OcrEngineEnum.EASYOCR
    assert config.easyocr_config.lang == ["en"]
    assert config.easyocr_config.force_full_page_ocr == True

    # Create extractor
    extractor = DoclingExtractor(config=config)

    # Verify to_docling_options creates correct OCR options
    format_options = config.to_docling_options()
    assert format_options is not None

    print("   EasyOCR configuration created successfully")
    print(f"   Language: {config.easyocr_config.lang}")
    print(f"   GPU: {config.easyocr_config.use_gpu}")
    print(f"   Full page OCR: {config.easyocr_config.force_full_page_ocr}")


async def test_tesseract_engine():
    """Test extraction with Tesseract engine."""
    print("\n✅ Testing Tesseract OCR engine...")

    # Configure Tesseract
    tesseract_config = TesseractOcrConfig(
        lang=["eng"],
        force_full_page_ocr=False,
        bitmap_area_threshold=0.05,
        path=None  # Auto-detect
    )

    # Create DoclingConfig with Tesseract
    config = DoclingConfig(
        do_ocr=True,
        ocr_engine=OcrEngineEnum.TESSERACT,
        tesseract_config=tesseract_config,
        do_table_structure=True,
        num_threads=4
    )

    # Verify config
    assert config.ocr_engine == OcrEngineEnum.TESSERACT
    assert config.tesseract_config.lang == ["eng"]
    assert config.tesseract_config.path is None

    # Create extractor
    extractor = DoclingExtractor(config=config)

    # Verify to_docling_options creates correct OCR options
    format_options = config.to_docling_options()
    assert format_options is not None

    print("   Tesseract configuration created successfully")
    print(f"   Language: {config.tesseract_config.lang}")
    print(f"   Path: {config.tesseract_config.path or 'auto-detect'}")
    print(f"   Full page OCR: {config.tesseract_config.force_full_page_ocr}")


async def test_tesseract_cli_engine():
    """Test extraction with Tesseract CLI engine."""
    print("\n✅ Testing Tesseract CLI engine...")

    # Configure Tesseract CLI
    tesseract_cli_config = TesseractCliOcrConfig(
        lang=["eng"],
        force_full_page_ocr=True,
        tesseract_cmd=None,  # Auto-detect
        path=None  # Auto-detect
    )

    # Create DoclingConfig with Tesseract CLI
    config = DoclingConfig(
        do_ocr=True,
        ocr_engine=OcrEngineEnum.TESSERACT_CLI,
        tesseract_cli_config=tesseract_cli_config,
        do_table_structure=True,
        num_threads=4
    )

    # Verify config
    assert config.ocr_engine == OcrEngineEnum.TESSERACT_CLI
    assert config.tesseract_cli_config.lang == ["eng"]
    assert config.tesseract_cli_config.force_full_page_ocr == True

    # Create extractor
    extractor = DoclingExtractor(config=config)

    # Verify to_docling_options creates correct OCR options
    format_options = config.to_docling_options()
    assert format_options is not None

    print("   Tesseract CLI configuration created successfully")
    print(f"   Language: {config.tesseract_cli_config.lang}")
    print(f"   Full page OCR: {config.tesseract_cli_config.force_full_page_ocr}")
    print(f"   Tesseract command: {config.tesseract_cli_config.tesseract_cmd or 'auto-detect'}")


async def test_rapidocr_engine():
    """Test extraction with RapidOCR engine."""
    print("\n✅ Testing RapidOCR engine...")

    # Configure RapidOCR
    rapidocr_config = RapidOcrConfig(
        lang=["en"],
        use_det=True,
        use_rec=True,
        use_cls=False,
        text_score=0.5,
        force_full_page_ocr=False,
        print_verbose=False
    )

    # Create DoclingConfig with RapidOCR
    config = DoclingConfig(
        do_ocr=True,
        ocr_engine=OcrEngineEnum.RAPID_OCR,
        rapidocr_config=rapidocr_config,
        do_table_structure=True,
        num_threads=4
    )

    # Verify config
    assert config.ocr_engine == OcrEngineEnum.RAPID_OCR
    assert config.rapidocr_config.use_det == True
    assert config.rapidocr_config.use_rec == True
    assert config.rapidocr_config.use_cls == False

    # Create extractor
    extractor = DoclingExtractor(config=config)

    # Verify to_docling_options creates correct OCR options
    format_options = config.to_docling_options()
    assert format_options is not None

    print("   RapidOCR configuration created successfully")
    print(f"   Language: {config.rapidocr_config.lang}")
    print(f"   Detection: {config.rapidocr_config.use_det}")
    print(f"   Recognition: {config.rapidocr_config.use_rec}")
    print(f"   Classification: {config.rapidocr_config.use_cls}")
    print(f"   Text score threshold: {config.rapidocr_config.text_score}")


async def test_config_serialization():
    """Test that configs can be serialized/deserialized."""
    print("\n✅ Testing config serialization...")

    # Create a config
    config = DoclingConfig(
        do_ocr=True,
        ocr_engine=OcrEngineEnum.EASYOCR,
        easyocr_config=EasyOcrConfig(
            lang=["en", "fr"],
            use_gpu=True,
            force_full_page_ocr=True
        ),
        num_threads=8
    )

    # Serialize to dict
    config_dict = config.model_dump()
    assert "ocr_engine" in config_dict
    assert "easyocr_config" in config_dict
    assert config_dict["easyocr_config"]["lang"] == ["en", "fr"]

    # Deserialize from dict
    config2 = DoclingConfig(**config_dict)
    assert config2.ocr_engine == OcrEngineEnum.EASYOCR
    assert config2.easyocr_config.lang == ["en", "fr"]
    assert config2.easyocr_config.use_gpu == True
    assert config2.num_threads == 8

    print("   Config serialization/deserialization successful")
    print(f"   OCR Engine: {config2.ocr_engine if isinstance(config2.ocr_engine, str) else config2.ocr_engine.value}")
    print(f"   EasyOCR Lang: {config2.easyocr_config.lang}")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("OCR Engine Configuration Tests")
    print("=" * 60)

    try:
        await test_easyocr_engine()
        await test_tesseract_engine()
        await test_tesseract_cli_engine()
        await test_rapidocr_engine()
        await test_config_serialization()

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        print("\nYou can now use different OCR engines with Docling by:")
        print("1. Creating an OCR-specific config (e.g., EasyOcrConfig)")
        print("2. Creating a DoclingConfig with the OCR engine and config")
        print("3. Passing the config to DoclingExtractor")
        print("\nExample:")
        print("```python")
        print("config = DoclingConfig(")
        print("    ocr_engine=OcrEngineEnum.TESSERACT,")
        print("    tesseract_config=TesseractOcrConfig(lang=['eng'], psm=3)")
        print(")")
        print("extractor = DoclingExtractor(config=config)")
        print("```")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())
