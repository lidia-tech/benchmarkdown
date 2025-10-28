"""
Dynamic configuration UI generation for extractor plugins.

This module provides utilities to generate Gradio UI components dynamically
from extractor plugin metadata, eliminating the need for hardcoded config sections.
"""

import gradio as gr
from typing import Dict, List, Tuple, Any
from benchmarkdown.extractors import ExtractorRegistry, ExtractorMetadata
from benchmarkdown.config_ui import create_gradio_component_from_field


class DynamicConfigUI:
    """Manages dynamic generation of configuration UI for extractor plugins."""

    def __init__(self, registry: ExtractorRegistry):
        """
        Initialize the dynamic config UI manager.

        Args:
            registry: ExtractorRegistry instance with discovered extractors
        """
        self.registry = registry
        self.config_areas = {}  # engine_name -> gr.Column
        self.component_lists = {}  # engine_name -> list of gr.Components
        self.component_field_maps = {}  # engine_name -> list of field names

    def generate_engine_choices(self) -> List[str]:
        """
        Generate list of available engine display names for dropdown.

        Returns:
            List of engine display names
        """
        available = self.registry.get_available_extractors()
        return [meta.display_name for meta in available.values()]

    def engine_name_from_display(self, display_name: str) -> str:
        """
        Convert display name to engine name.

        Args:
            display_name: Human-readable engine name (e.g., "Docling (Local)")

        Returns:
            Engine identifier (e.g., "docling")
        """
        for name, meta in self.registry.get_all_extractors().items():
            if meta.display_name == display_name:
                return name
        return None

    def generate_config_ui_for_extractor(
        self,
        metadata: ExtractorMetadata
    ) -> Tuple[gr.Column, List[gr.components.Component], List[str]]:
        """
        Generate configuration UI for a single extractor.

        Args:
            metadata: ExtractorMetadata for the extractor

        Returns:
            Tuple of (config_area, components_list, field_names_list)
        """
        with gr.Column(visible=False) as config_area:
            components = []
            field_names = []

            # Basic fields section
            with gr.Group():
                gr.Markdown("#### Basic Options")
                for field_name in metadata.basic_fields:
                    if field_name not in metadata.config_class.model_fields:
                        continue

                    field_info = metadata.config_class.model_fields[field_name]
                    field_type = field_info.annotation

                    component, _ = create_gradio_component_from_field(
                        field_name, field_info, field_type
                    )
                    components.append(component)
                    field_names.append(field_name)

            # Advanced fields section
            if metadata.advanced_fields:
                with gr.Accordion("Advanced Options", open=False):
                    for field_name in metadata.advanced_fields:
                        if field_name not in metadata.config_class.model_fields:
                            continue

                        field_info = metadata.config_class.model_fields[field_name]
                        field_type = field_info.annotation

                        component, _ = create_gradio_component_from_field(
                            field_name, field_info, field_type
                        )
                        components.append(component)
                        field_names.append(field_name)

        return config_area, components, field_names

    def generate_all_config_uis(self) -> Dict[str, Any]:
        """
        Generate configuration UIs for all available extractors.

        IMPORTANT: This must be called from within a gr.Blocks() context!

        Returns:
            Dictionary with keys:
            - config_areas: Dict[engine_name, gr.Column]
            - component_lists: Dict[engine_name, List[gr.Component]]
            - field_maps: Dict[engine_name, List[str]]
        """
        available = self.registry.get_available_extractors()

        for engine_name, metadata in available.items():
            config_area, components, field_names = self.generate_config_ui_for_extractor(metadata)

            self.config_areas[engine_name] = config_area
            self.component_lists[engine_name] = components
            self.component_field_maps[engine_name] = field_names

        return {
            "config_areas": self.config_areas,
            "component_lists": self.component_lists,
            "field_maps": self.component_field_maps,
        }

    def build_config_dict_from_values(
        self,
        engine_name: str,
        config_values: List[Any]
    ) -> Dict[str, Any]:
        """
        Build configuration dictionary from UI values.

        Args:
            engine_name: Engine identifier
            config_values: List of values from UI components

        Returns:
            Dictionary mapping field names to values
        """
        field_names = self.component_field_maps.get(engine_name, [])

        if len(config_values) != len(field_names):
            raise ValueError(
                f"Expected {len(field_names)} values for {engine_name}, "
                f"got {len(config_values)}"
            )

        return dict(zip(field_names, config_values))

    def get_config_area_updates(
        self,
        selected_engine_display: str
    ) -> List[gr.update]:
        """
        Generate gr.update() objects to show the correct config area.

        Args:
            selected_engine_display: Display name of selected engine

        Returns:
            List of gr.update() objects, one per config area, in consistent order
        """
        selected_engine = self.engine_name_from_display(selected_engine_display)
        updates = []

        # Return updates in a consistent order (sorted by engine name)
        for engine_name in sorted(self.config_areas.keys()):
            visible = (engine_name == selected_engine)
            updates.append(gr.update(visible=visible))

        return updates

    def get_component_count_by_engine(self, engine_name: str) -> int:
        """
        Get the number of UI components for an engine.

        Args:
            engine_name: Engine identifier

        Returns:
            Number of components
        """
        return len(self.component_lists.get(engine_name, []))

    def get_all_config_areas(self) -> List[gr.Column]:
        """
        Get all config area components in consistent order.

        Returns:
            List of config area gr.Column objects
        """
        return [self.config_areas[name] for name in sorted(self.config_areas.keys())]

    def get_all_components_for_engine(self, engine_name: str) -> List[gr.components.Component]:
        """
        Get all UI components for a specific engine.

        Args:
            engine_name: Engine identifier

        Returns:
            List of Gradio components
        """
        return self.component_lists.get(engine_name, [])

    def get_default_values_for_engine(self, engine_display_name: str) -> List[gr.update]:
        """
        Get default values for all fields of an engine.

        Args:
            engine_display_name: Display name of the engine

        Returns:
            List of gr.update() objects with default values for all components
        """
        engine_name = self.engine_name_from_display(engine_display_name)
        if not engine_name:
            return []

        field_names = self.component_field_maps.get(engine_name, [])
        extractor_meta = self.registry.get_extractor(engine_name)
        if not extractor_meta:
            return []

        config_class = extractor_meta.config_class
        updates = []

        for field_name in field_names:
            if field_name not in config_class.model_fields:
                updates.append(gr.update())
                continue

            field_info = config_class.model_fields[field_name]
            default_value = field_info.default

            # Handle list defaults - convert to comma-separated string for UI
            if isinstance(default_value, list):
                default_value = ", ".join(str(v) for v in default_value)

            updates.append(gr.update(value=default_value))

        return updates

    def get_profile_values_for_engine(
        self,
        engine_display_name: str,
        config_data: Dict[str, Any]
    ) -> List[gr.update]:
        """
        Get profile values for all fields of an engine, falling back to defaults.

        Args:
            engine_display_name: Display name of the engine
            config_data: Dictionary with saved profile values

        Returns:
            List of gr.update() objects with profile values for all components
        """
        engine_name = self.engine_name_from_display(engine_display_name)
        if not engine_name:
            return []

        field_names = self.component_field_maps.get(engine_name, [])
        extractor_meta = self.registry.get_extractor(engine_name)
        if not extractor_meta:
            return []

        config_class = extractor_meta.config_class
        updates = []

        def normalize_list_value(value):
            """Convert list values to comma-separated strings for UI display."""
            if isinstance(value, list):
                return ", ".join(str(v) for v in value)
            elif isinstance(value, str) and value.startswith("[") and value.endswith("]"):
                try:
                    import ast
                    parsed = ast.literal_eval(value)
                    if isinstance(parsed, list):
                        return ", ".join(str(v) for v in parsed)
                except:
                    pass
            return value

        for field_name in field_names:
            if field_name not in config_class.model_fields:
                updates.append(gr.update())
                continue

            field_info = config_class.model_fields[field_name]

            # Try to get value from config_data
            if field_name in config_data:
                value = normalize_list_value(config_data[field_name])
                updates.append(gr.update(value=value))
            else:
                # Fall back to default
                default_value = field_info.default
                default_value = normalize_list_value(default_value)
                updates.append(gr.update(value=default_value))

        return updates

    def extract_engine_values_from_all_values(
        self,
        engine_display_name: str,
        all_config_values: List[Any]
    ) -> Tuple[List[Any], Dict[str, Any]]:
        """
        Extract values for a specific engine from the flattened list of all component values.

        Args:
            engine_display_name: Display name of the engine
            all_config_values: Flattened list of ALL component values from ALL engines

        Returns:
            Tuple of (engine_values_list, config_dict)
        """
        engine_name = self.engine_name_from_display(engine_display_name)
        if not engine_name:
            return [], {}

        # Calculate the starting index for this engine's values
        start_idx = 0
        for eng_name in sorted(self.component_lists.keys()):
            if eng_name == engine_name:
                break
            start_idx += len(self.component_lists[eng_name])

        # Extract this engine's values
        num_components = len(self.component_lists.get(engine_name, []))
        engine_values = all_config_values[start_idx:start_idx + num_components]

        # Build config dictionary
        field_names = self.component_field_maps.get(engine_name, [])
        config_dict = dict(zip(field_names, engine_values))

        return engine_values, config_dict
