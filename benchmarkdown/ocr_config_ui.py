"""
Helper functions for OCR configuration UI generation and management.
"""

from typing import Dict, Any, List, Tuple
import gradio as gr
from benchmarkdown.config import (
    EasyOcrConfig,
    TesseractOcrConfig,
    TesseractCliOcrConfig,
    OcrMacConfig,
    RapidOcrConfig,
    OcrEngineEnum
)
from benchmarkdown.config_ui import (
    create_gradio_component_from_field,
    EASYOCR_BASIC_FIELDS,
    EASYOCR_ADVANCED_FIELDS,
    TESSERACT_BASIC_FIELDS,
    TESSERACT_ADVANCED_FIELDS,
    TESSERACT_CLI_BASIC_FIELDS,
    TESSERACT_CLI_ADVANCED_FIELDS,
    OCR_MAC_BASIC_FIELDS,
    OCR_MAC_ADVANCED_FIELDS,
    RAPIDOCR_BASIC_FIELDS,
    RAPIDOCR_ADVANCED_FIELDS
)


def create_ocr_config_ui() -> Tuple[List[gr.components.Component], Dict[str, List[gr.components.Component]], List[gr.Group]]:
    """
    Create OCR configuration UI with conditional sections for each engine.

    Returns:
        Tuple of:
        - List of all OCR components (for event handler inputs/outputs)
        - Dict mapping engine name to its components
        - List of Group components for visibility control
    """
    all_components = []
    engine_components = {}
    groups = []

    # EasyOCR Configuration
    with gr.Group(visible=True) as easyocr_group:
        gr.Markdown("#### EasyOCR Settings")
        easyocr_components = []

        with gr.Group():
            gr.Markdown("**Basic Options**")
            for field_name in EASYOCR_BASIC_FIELDS:
                if field_name not in EasyOcrConfig.model_fields:
                    continue
                field_info = EasyOcrConfig.model_fields[field_name]
                field_type = field_info.annotation
                component, _ = create_gradio_component_from_field(
                    field_name, field_info, field_type
                )
                easyocr_components.append(component)
                all_components.append(component)

        with gr.Accordion("Advanced Options", open=False):
            for field_name in EASYOCR_ADVANCED_FIELDS:
                if field_name not in EasyOcrConfig.model_fields:
                    continue
                field_info = EasyOcrConfig.model_fields[field_name]
                field_type = field_info.annotation
                component, _ = create_gradio_component_from_field(
                    field_name, field_info, field_type
                )
                easyocr_components.append(component)
                all_components.append(component)

        engine_components["easyocr"] = easyocr_components
        groups.append(easyocr_group)

    # Tesseract Configuration
    with gr.Group(visible=False) as tesseract_group:
        gr.Markdown("#### Tesseract OCR Settings")
        tesseract_components = []

        with gr.Group():
            gr.Markdown("**Basic Options**")
            for field_name in TESSERACT_BASIC_FIELDS:
                if field_name not in TesseractOcrConfig.model_fields:
                    continue
                field_info = TesseractOcrConfig.model_fields[field_name]
                field_type = field_info.annotation
                component, _ = create_gradio_component_from_field(
                    field_name, field_info, field_type
                )
                tesseract_components.append(component)
                all_components.append(component)

        with gr.Accordion("Advanced Options", open=False):
            for field_name in TESSERACT_ADVANCED_FIELDS:
                if field_name not in TesseractOcrConfig.model_fields:
                    continue
                field_info = TesseractOcrConfig.model_fields[field_name]
                field_type = field_info.annotation
                component, _ = create_gradio_component_from_field(
                    field_name, field_info, field_type
                )
                tesseract_components.append(component)
                all_components.append(component)

        engine_components["tesseract"] = tesseract_components
        groups.append(tesseract_group)

    # Tesseract CLI Configuration
    with gr.Group(visible=False) as tesseract_cli_group:
        gr.Markdown("#### Tesseract CLI Settings")
        tesseract_cli_components = []

        with gr.Group():
            gr.Markdown("**Basic Options**")
            for field_name in TESSERACT_CLI_BASIC_FIELDS:
                if field_name not in TesseractCliOcrConfig.model_fields:
                    continue
                field_info = TesseractCliOcrConfig.model_fields[field_name]
                field_type = field_info.annotation
                component, _ = create_gradio_component_from_field(
                    field_name, field_info, field_type
                )
                tesseract_cli_components.append(component)
                all_components.append(component)

        with gr.Accordion("Advanced Options", open=False):
            for field_name in TESSERACT_CLI_ADVANCED_FIELDS:
                if field_name not in TesseractCliOcrConfig.model_fields:
                    continue
                field_info = TesseractCliOcrConfig.model_fields[field_name]
                field_type = field_info.annotation
                component, _ = create_gradio_component_from_field(
                    field_name, field_info, field_type
                )
                tesseract_cli_components.append(component)
                all_components.append(component)

        engine_components["tesseract_cli"] = tesseract_cli_components
        groups.append(tesseract_cli_group)

    # OcrMac Configuration
    with gr.Group(visible=False) as ocr_mac_group:
        gr.Markdown("#### macOS OCR Settings")
        ocr_mac_components = []

        with gr.Group():
            gr.Markdown("**Basic Options**")
            for field_name in OCR_MAC_BASIC_FIELDS:
                if field_name not in OcrMacConfig.model_fields:
                    continue
                field_info = OcrMacConfig.model_fields[field_name]
                field_type = field_info.annotation
                component, _ = create_gradio_component_from_field(
                    field_name, field_info, field_type
                )
                ocr_mac_components.append(component)
                all_components.append(component)

        with gr.Accordion("Advanced Options", open=False):
            for field_name in OCR_MAC_ADVANCED_FIELDS:
                if field_name not in OcrMacConfig.model_fields:
                    continue
                field_info = OcrMacConfig.model_fields[field_name]
                field_type = field_info.annotation
                component, _ = create_gradio_component_from_field(
                    field_name, field_info, field_type
                )
                ocr_mac_components.append(component)
                all_components.append(component)

        engine_components["ocr_mac"] = ocr_mac_components
        groups.append(ocr_mac_group)

    # RapidOCR Configuration
    with gr.Group(visible=False) as rapidocr_group:
        gr.Markdown("#### RapidOCR Settings")
        rapidocr_components = []

        with gr.Group():
            gr.Markdown("**Basic Options**")
            for field_name in RAPIDOCR_BASIC_FIELDS:
                if field_name not in RapidOcrConfig.model_fields:
                    continue
                field_info = RapidOcrConfig.model_fields[field_name]
                field_type = field_info.annotation
                component, _ = create_gradio_component_from_field(
                    field_name, field_info, field_type
                )
                rapidocr_components.append(component)
                all_components.append(component)

        with gr.Accordion("Advanced Options", open=False):
            for field_name in RAPIDOCR_ADVANCED_FIELDS:
                if field_name not in RapidOcrConfig.model_fields:
                    continue
                field_info = RapidOcrConfig.model_fields[field_name]
                field_type = field_info.annotation
                component, _ = create_gradio_component_from_field(
                    field_name, field_info, field_type
                )
                rapidocr_components.append(component)
                all_components.append(component)

        engine_components["rapidocr"] = rapidocr_components
        groups.append(rapidocr_group)

    return all_components, engine_components, groups


def get_ocr_engine_group_updates(selected_engine: str) -> List[gr.update]:
    """
    Get visibility updates for OCR engine groups based on selected engine.

    Args:
        selected_engine: The OCR engine value (e.g., "easyocr", "tesseract", etc.)

    Returns:
        List of gr.update() for [easyocr_group, tesseract_group, tesseract_cli_group, ocr_mac_group, rapidocr_group]
    """
    engines = ["easyocr", "tesseract", "tesseract_cli", "ocr_mac", "rapid_ocr"]
    return [gr.update(visible=(selected_engine == engine)) for engine in engines]


def serialize_ocr_configs(
    ocr_engine: str,
    easyocr_values: List[Any],
    tesseract_values: List[Any],
    tesseract_cli_values: List[Any],
    ocr_mac_values: List[Any],
    rapidocr_values: List[Any]
) -> Dict[str, Any]:
    """
    Serialize OCR configuration values into nested config dictionaries.

    Returns:
        Dict with keys like "easyocr_config", "tesseract_config", etc.
    """
    result = {}

    # EasyOCR
    if easyocr_values:
        easyocr_fields = EASYOCR_BASIC_FIELDS + EASYOCR_ADVANCED_FIELDS
        result["easyocr_config"] = {
            field: value for field, value in zip(easyocr_fields, easyocr_values)
        }

    # Tesseract
    if tesseract_values:
        tesseract_fields = TESSERACT_BASIC_FIELDS + TESSERACT_ADVANCED_FIELDS
        result["tesseract_config"] = {
            field: value for field, value in zip(tesseract_fields, tesseract_values)
        }

    # Tesseract CLI
    if tesseract_cli_values:
        tesseract_cli_fields = TESSERACT_CLI_BASIC_FIELDS + TESSERACT_CLI_ADVANCED_FIELDS
        result["tesseract_cli_config"] = {
            field: value for field, value in zip(tesseract_cli_fields, tesseract_cli_values)
        }

    # OcrMac
    if ocr_mac_values:
        ocr_mac_fields = OCR_MAC_BASIC_FIELDS + OCR_MAC_ADVANCED_FIELDS
        result["ocr_mac_config"] = {
            field: value for field, value in zip(ocr_mac_fields, ocr_mac_values)
        }

    # RapidOCR
    if rapidocr_values:
        rapidocr_fields = RAPIDOCR_BASIC_FIELDS + RAPIDOCR_ADVANCED_FIELDS
        result["rapidocr_config"] = {
            field: value for field, value in zip(rapidocr_fields, rapidocr_values)
        }

    return result


def deserialize_ocr_configs(config_dict: Dict[str, Any]) -> Tuple[List[Any], ...]:
    """
    Deserialize OCR configuration dictionaries into component values.

    Returns:
        Tuple of (easyocr_values, tesseract_values, tesseract_cli_values, ocr_mac_values, rapidocr_values)
    """
    easyocr_values = []
    tesseract_values = []
    tesseract_cli_values = []
    ocr_mac_values = []
    rapidocr_values = []

    # EasyOCR
    if "easyocr_config" in config_dict:
        easyocr_config = config_dict["easyocr_config"]
        for field in EASYOCR_BASIC_FIELDS + EASYOCR_ADVANCED_FIELDS:
            easyocr_values.append(easyocr_config.get(field, EasyOcrConfig.model_fields[field].default))
    else:
        # Use defaults
        for field in EASYOCR_BASIC_FIELDS + EASYOCR_ADVANCED_FIELDS:
            easyocr_values.append(EasyOcrConfig.model_fields[field].default)

    # Tesseract
    if "tesseract_config" in config_dict:
        tesseract_config = config_dict["tesseract_config"]
        for field in TESSERACT_BASIC_FIELDS + TESSERACT_ADVANCED_FIELDS:
            tesseract_values.append(tesseract_config.get(field, TesseractOcrConfig.model_fields[field].default))
    else:
        for field in TESSERACT_BASIC_FIELDS + TESSERACT_ADVANCED_FIELDS:
            tesseract_values.append(TesseractOcrConfig.model_fields[field].default)

    # Tesseract CLI
    if "tesseract_cli_config" in config_dict:
        tesseract_cli_config = config_dict["tesseract_cli_config"]
        for field in TESSERACT_CLI_BASIC_FIELDS + TESSERACT_CLI_ADVANCED_FIELDS:
            tesseract_cli_values.append(tesseract_cli_config.get(field, TesseractCliOcrConfig.model_fields[field].default))
    else:
        for field in TESSERACT_CLI_BASIC_FIELDS + TESSERACT_CLI_ADVANCED_FIELDS:
            tesseract_cli_values.append(TesseractCliOcrConfig.model_fields[field].default)

    # OcrMac
    if "ocr_mac_config" in config_dict:
        ocr_mac_config = config_dict["ocr_mac_config"]
        for field in OCR_MAC_BASIC_FIELDS + OCR_MAC_ADVANCED_FIELDS:
            ocr_mac_values.append(ocr_mac_config.get(field, OcrMacConfig.model_fields[field].default))
    else:
        for field in OCR_MAC_BASIC_FIELDS + OCR_MAC_ADVANCED_FIELDS:
            ocr_mac_values.append(OcrMacConfig.model_fields[field].default)

    # RapidOCR
    if "rapidocr_config" in config_dict:
        rapidocr_config = config_dict["rapidocr_config"]
        for field in RAPIDOCR_BASIC_FIELDS + RAPIDOCR_ADVANCED_FIELDS:
            rapidocr_values.append(rapidocr_config.get(field, RapidOcrConfig.model_fields[field].default))
    else:
        for field in RAPIDOCR_BASIC_FIELDS + RAPIDOCR_ADVANCED_FIELDS:
            rapidocr_values.append(RapidOcrConfig.model_fields[field].default)

    return (easyocr_values, tesseract_values, tesseract_cli_values, ocr_mac_values, rapidocr_values)
