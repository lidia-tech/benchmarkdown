"""
Automatic UI generation from Pydantic configuration models.

This module provides utilities to generate Gradio UI components from Pydantic
models, enabling type-safe configuration interfaces.
"""

from typing import Any, Dict, List, Tuple, Type, Union, get_origin, get_args
from enum import Enum
import gradio as gr
from pydantic import BaseModel
from pydantic.fields import FieldInfo


def create_gradio_component_from_field(
    field_name: str,
    field_info: FieldInfo,
    field_type: Type
) -> Tuple[gr.components.Component, str]:
    """
    Create a Gradio component from a Pydantic field.

    Args:
        field_name: Name of the field
        field_info: Pydantic FieldInfo containing metadata
        field_type: Type of the field

    Returns:
        Tuple of (gradio_component, component_id)
    """
    # Get field metadata
    description = field_info.description or field_name
    default_value = field_info.default
    is_optional = False

    # Handle None defaults for Optional types
    if default_value is None:
        origin = get_origin(field_type)
        if origin is not None:  # Optional types
            is_optional = True
            args = get_args(field_type)
            if len(args) > 0:
                # Get the non-None type
                field_type = next((arg for arg in args if arg is not type(None)), args[0])
                # Try to get a sensible default for UI
                if field_type == float:
                    default_value = 0.0
                elif field_type == int:
                    default_value = 0
                elif field_type == str:
                    default_value = ""

    # Determine component type based on field type
    origin = get_origin(field_type)

    # Handle Enum types
    if isinstance(field_type, type) and issubclass(field_type, Enum):
        choices = [e.value for e in field_type]
        default = default_value.value if isinstance(default_value, Enum) else default_value
        component = gr.Dropdown(
            choices=choices,
            value=default,
            label=field_name.replace('_', ' ').title(),
            info=description
        )
        return component, field_name

    # Handle list types
    if origin is list:
        args = get_args(field_type)
        if args and isinstance(args[0], type) and issubclass(args[0], Enum):
            # List of enums - use CheckboxGroup
            choices = [e.value for e in args[0]]
            default = [v.value if isinstance(v, Enum) else v for v in default_value]
            component = gr.CheckboxGroup(
                choices=choices,
                value=default,
                label=field_name.replace('_', ' ').title(),
                info=description
            )
            return component, field_name
        elif args and args[0] == str:
            # List of strings - use Textbox with comma-separated values
            default_str = ", ".join(default_value) if isinstance(default_value, list) else ""
            component = gr.Textbox(
                value=default_str,
                label=field_name.replace('_', ' ').title(),
                info=f"{description} (comma-separated)",
                placeholder="e.g., en, fr, de"
            )
            return component, field_name

    # Handle primitive types
    if field_type == bool:
        component = gr.Checkbox(
            value=default_value,
            label=field_name.replace('_', ' ').title(),
            info=description
        )
        return component, field_name

    elif field_type == int:
        # Check for min/max constraints
        ge = getattr(field_info, 'ge', None)
        le = getattr(field_info, 'le', None)

        # For optional fields, use Number input; for required, use Slider
        if is_optional:
            info_text = f"{description} (Leave at 0 or empty for no limit)" if description else "Leave at 0 for no limit"
            component = gr.Number(
                value=default_value,
                label=field_name.replace('_', ' ').title(),
                info=info_text,
                minimum=ge if ge is not None else 0,
                maximum=le if le is not None else None
            )
        else:
            minimum = ge if ge is not None else 0
            maximum = le if le is not None else 100
            component = gr.Slider(
                minimum=minimum,
                maximum=maximum,
                value=default_value,
                step=1,
                label=field_name.replace('_', ' ').title(),
                info=description
            )
        return component, field_name

    elif field_type == float:
        # Check for min/max constraints
        ge = getattr(field_info, 'ge', None)
        le = getattr(field_info, 'le', None)

        # For optional fields, use Number input; for required, use Slider
        if is_optional:
            info_text = f"{description} (Leave at 0 or empty for no limit)" if description else "Leave at 0 for no limit"
            component = gr.Number(
                value=default_value if default_value is not None else 0.0,
                label=field_name.replace('_', ' ').title(),
                info=info_text,
                minimum=ge if ge is not None else 0.0,
                maximum=le if le is not None else None
            )
        else:
            minimum = ge if ge is not None else 0.0
            maximum = le if le is not None else 2.0
            component = gr.Slider(
                minimum=minimum,
                maximum=maximum,
                value=default_value if default_value is not None else 1.0,
                step=0.1,
                label=field_name.replace('_', ' ').title(),
                info=description
            )
        return component, field_name

    elif field_type == str or origin is None:
        component = gr.Textbox(
            value=default_value if default_value is not None else "",
            label=field_name.replace('_', ' ').title(),
            info=description
        )
        return component, field_name

    # Fallback to textbox
    component = gr.Textbox(
        value=str(default_value),
        label=field_name.replace('_', ' ').title(),
        info=description
    )
    return component, field_name


def create_config_ui(
    config_class: Type[BaseModel],
    basic_fields: List[str],
    advanced_fields: List[str],
    title: str = "Configuration"
) -> Tuple[List[gr.components.Component], Dict[str, str]]:
    """
    Create a two-tier UI (basic + advanced) from a Pydantic config class.

    Args:
        config_class: Pydantic BaseModel class
        basic_fields: List of field names to show in basic section
        advanced_fields: List of field names to show in advanced section
        title: Title for the configuration section

    Returns:
        Tuple of (list of components, dict mapping field names to component IDs)
    """
    components = []
    component_map = {}

    # Create basic section
    with gr.Group():
        gr.Markdown(f"### {title} - Basic Options")

        for field_name in basic_fields:
            if field_name not in config_class.model_fields:
                continue

            field_info = config_class.model_fields[field_name]
            field_type = field_info.annotation

            component, comp_id = create_gradio_component_from_field(
                field_name, field_info, field_type
            )
            components.append(component)
            component_map[field_name] = comp_id

    # Create advanced section (accordion)
    with gr.Accordion(f"{title} - Advanced Options", open=False):
        for field_name in advanced_fields:
            if field_name not in config_class.model_fields:
                continue

            field_info = config_class.model_fields[field_name]
            field_type = field_info.annotation

            component, comp_id = create_gradio_component_from_field(
                field_name, field_info, field_type
            )
            components.append(component)
            component_map[field_name] = comp_id

    return components, component_map


def build_config_from_ui_values(
    config_class: Type[BaseModel],
    values: Dict[str, Any]
) -> BaseModel:
    """
    Build a config instance from UI values.

    Args:
        config_class: Pydantic BaseModel class
        values: Dictionary of field names to values

    Returns:
        Instance of config_class
    """
    from pydantic import BaseModel as PydanticBaseModel

    # Clean up the values dict - handle None for optional fields
    clean_values = {}
    for field_name, value in values.items():
        if field_name in config_class.model_fields:
            field_info = config_class.model_fields[field_name]
            field_type = field_info.annotation
            origin = get_origin(field_type)

            # Handle list[str] fields (comma-separated strings)
            if origin is list:
                args = get_args(field_type)
                if args and args[0] == str:
                    if isinstance(value, str):
                        # Parse comma-separated string into list
                        clean_values[field_name] = [s.strip() for s in value.split(",") if s.strip()]
                    elif isinstance(value, list):
                        clean_values[field_name] = value
                    else:
                        clean_values[field_name] = []
                    continue

            # Check if this is an Optional type
            is_optional = origin is not None

            # Handle empty/None values for optional fields
            if value == "" or value is None:
                if is_optional:
                    clean_values[field_name] = None
                else:
                    clean_values[field_name] = value
            # Handle 0 for optional numeric fields (treat as None)
            elif value == 0 and is_optional:
                # Check if it's a numeric type
                args = get_args(field_type)
                if args:
                    non_none_type = next((arg for arg in args if arg is not type(None)), None)
                    if non_none_type in (int, float):
                        # For optional numeric fields, 0 means "not set" (None)
                        clean_values[field_name] = None
                    else:
                        clean_values[field_name] = value
                else:
                    clean_values[field_name] = value
            # Handle nested BaseModel fields (like OCR configs)
            elif isinstance(value, dict):
                # Check if this field is a BaseModel type
                args = get_args(field_type) if origin else []
                nested_type = None
                if origin is Union:
                    # For Optional[SomeModel], get the non-None type
                    nested_type = next((arg for arg in args if arg is not type(None) and isinstance(arg, type) and issubclass(arg, PydanticBaseModel)), None)
                elif isinstance(field_type, type) and issubclass(field_type, PydanticBaseModel):
                    nested_type = field_type

                if nested_type:
                    # Recursively clean the nested dict before creating the instance
                    clean_values[field_name] = build_config_from_ui_values(nested_type, value)
                else:
                    clean_values[field_name] = value
            else:
                clean_values[field_name] = value

    return config_class(**clean_values)


# Define field groupings for DoclingConfig
DOCLING_BASIC_FIELDS = [
    "do_ocr",
    "ocr_engine",
    "do_table_structure",
    "table_structure_mode",
    "num_threads",
]

DOCLING_ADVANCED_FIELDS = [
    "force_backend_text",
    "do_cell_matching",
    "do_code_enrichment",
    "do_formula_enrichment",
    "do_picture_classification",
    "do_picture_description",
    "generate_page_images",
    "generate_picture_images",
    "images_scale",
    "accelerator_device",
    "document_timeout",
]

# Define field groupings for each OCR engine configuration
EASYOCR_BASIC_FIELDS = [
    "lang",
    "use_gpu",
    "force_full_page_ocr",
]

EASYOCR_ADVANCED_FIELDS = [
    "confidence_threshold",
    "bitmap_area_threshold",
    "model_storage_directory",
]

TESSERACT_BASIC_FIELDS = [
    "lang",
    "force_full_page_ocr",
]

TESSERACT_ADVANCED_FIELDS = [
    "bitmap_area_threshold",
    "path",
]

TESSERACT_CLI_BASIC_FIELDS = [
    "lang",
    "force_full_page_ocr",
]

TESSERACT_CLI_ADVANCED_FIELDS = [
    "bitmap_area_threshold",
    "tesseract_cmd",
    "path",
]

OCR_MAC_BASIC_FIELDS = [
    "lang",
    "force_full_page_ocr",
]

OCR_MAC_ADVANCED_FIELDS = [
    "bitmap_area_threshold",
]

RAPIDOCR_BASIC_FIELDS = [
    "lang",
    "force_full_page_ocr",
    "use_det",
    "use_rec",
]

RAPIDOCR_ADVANCED_FIELDS = [
    "use_cls",
    "text_score",
    "bitmap_area_threshold",
    "print_verbose",
]

# Define field groupings for TextractConfig
TEXTRACT_BASIC_FIELDS = [
    # Note: s3_upload_path is read from TEXTRACT_S3_WORKSPACE environment variable
    "features",
    "hide_header_layout",
    "hide_footer_layout",
]

TEXTRACT_ADVANCED_FIELDS = [
    "hide_figure_layout",
    "hide_table_layout",
    "hide_key_value_layout",
    "hide_page_num_layout",
    "table_remove_column_headers",
    "table_add_title_as_caption",
    "table_add_footer_as_paragraph",
    "max_number_of_consecutive_new_lines",
    "title_prefix",
    "section_header_prefix",
]
