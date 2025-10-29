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
        self.nested_groups = {}  # engine_name -> {parent_field: {option_value: [components]}}
        self.parent_components = {}  # engine_name -> {parent_field: gr.Component}
        self.conditional_groups = {}  # engine_name -> {parent_field: {parent_value: [components]}}
        self.conditional_parent_components = {}  # engine_name -> {parent_field: gr.Component}

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
            nested_groups_for_engine = {}  # parent_field -> {option_value: gr.Group}
            parent_components_for_engine = {}  # parent_field -> gr.Component
            conditional_groups_for_engine = {}  # parent_field -> {parent_value: gr.Group}
            conditional_parent_components_for_engine = {}  # parent_field -> gr.Component

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

                    # Check if this field is a parent for nested configs
                    if metadata.nested_configs and field_name in metadata.nested_configs:
                        parent_components_for_engine[field_name] = component

                    # Check if this field is a parent for conditional fields
                    conditional_fields = getattr(metadata, 'conditional_fields', None)
                    if conditional_fields and field_name in conditional_fields:
                        conditional_parent_components_for_engine[field_name] = component

            # Generate nested config sections if present
            if metadata.nested_configs:
                for parent_field_name, nested_options in metadata.nested_configs.items():
                    if parent_field_name in parent_components_for_engine:
                        nested_groups_for_engine[parent_field_name] = {}

                        # Generate UI for each nested config option
                        for option_value, option_meta in nested_options.items():
                            config_class = option_meta["config_class"]
                            basic_fields = option_meta.get("basic_fields", [])
                            advanced_fields = option_meta.get("advanced_fields", [])
                            display_name = option_meta.get("display_name", option_value)

                            # Determine default visibility (show first option by default)
                            is_first = list(nested_options.keys())[0] == option_value

                            # Track all components in this nested section
                            nested_section_components = []

                            # Don't use gr.Group() - it shows borders even when hidden
                            section_label = gr.Markdown(f"##### {display_name}", visible=is_first)
                            nested_section_components.append(section_label)

                            # Basic nested fields
                            for field_name in basic_fields:
                                if field_name not in config_class.model_fields:
                                    continue

                                field_info = config_class.model_fields[field_name]
                                field_type = field_info.annotation

                                component, _ = create_gradio_component_from_field(
                                    field_name, field_info, field_type
                                )
                                component.visible = is_first  # Set initial visibility
                                components.append(component)
                                nested_section_components.append(component)
                                # Use nested field name format: config_field.field_name
                                field_names.append(f"{option_meta['config_field']}.{field_name}")

                            # Advanced nested fields
                            if advanced_fields:
                                with gr.Accordion(f"Advanced {display_name}", open=False, visible=is_first) as accordion:
                                    nested_section_components.append(accordion)
                                    for field_name in advanced_fields:
                                        if field_name not in config_class.model_fields:
                                            continue

                                        field_info = config_class.model_fields[field_name]
                                        field_type = field_info.annotation

                                        component, _ = create_gradio_component_from_field(
                                            field_name, field_info, field_type
                                        )
                                        component.visible = is_first  # Set initial visibility
                                        components.append(component)
                                        nested_section_components.append(component)
                                        field_names.append(f"{option_meta['config_field']}.{field_name}")

                            # Store list of components for this nested section
                            nested_groups_for_engine[parent_field_name][option_value] = nested_section_components

            # Generate conditional field sections if present
            conditional_fields = getattr(metadata, 'conditional_fields', None)
            if conditional_fields:
                for parent_field_name, parent_value_conditions in conditional_fields.items():
                    conditional_groups_for_engine[parent_field_name] = {}

                    for parent_value, dependent_field_names in parent_value_conditions.items():
                        # Track all components in this conditional section
                        conditional_section_components = []

                        # Don't use gr.Group() - it shows borders even when hidden
                        section_label = gr.Markdown(f"##### {parent_field_name.replace('_', ' ').title()} Options", visible=False)
                        conditional_section_components.append(section_label)

                        for field_name in dependent_field_names:
                            if field_name not in metadata.config_class.model_fields:
                                continue

                            field_info = metadata.config_class.model_fields[field_name]
                            field_type = field_info.annotation

                            component, _ = create_gradio_component_from_field(
                                field_name, field_info, field_type
                            )
                            component.visible = False  # Initially hidden
                            components.append(component)
                            conditional_section_components.append(component)
                            field_names.append(field_name)

                        # Store list of components for this conditional section
                        conditional_groups_for_engine[parent_field_name][parent_value] = conditional_section_components

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

                        # Check if this field is a parent for conditional fields
                        conditional_fields = getattr(metadata, 'conditional_fields', None)
                        if conditional_fields and field_name in conditional_fields:
                            conditional_parent_components_for_engine[field_name] = component

        return (
            config_area,
            components,
            field_names,
            nested_groups_for_engine,
            parent_components_for_engine,
            conditional_groups_for_engine,
            conditional_parent_components_for_engine
        )

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
            (config_area, components, field_names, nested_groups, parent_components,
             conditional_groups, conditional_parent_components) = self.generate_config_ui_for_extractor(metadata)

            self.config_areas[engine_name] = config_area
            self.component_lists[engine_name] = components
            self.component_field_maps[engine_name] = field_names
            self.nested_groups[engine_name] = nested_groups
            self.parent_components[engine_name] = parent_components
            self.conditional_groups[engine_name] = conditional_groups
            self.conditional_parent_components[engine_name] = conditional_parent_components

        return {
            "config_areas": self.config_areas,
            "component_lists": self.component_lists,
            "field_maps": self.component_field_maps,
            "nested_groups": self.nested_groups,
            "parent_components": self.parent_components,
            "conditional_groups": self.conditional_groups,
            "conditional_parent_components": self.conditional_parent_components,
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
        nested_configs = extractor_meta.nested_configs or {}
        updates = []

        for field_name in field_names:
            # Check if this is a nested field (e.g., "easyocr_config.lang")
            if '.' in field_name:
                parts = field_name.split('.')
                nested_config_name = parts[0]
                nested_field_name = parts[1]

                # Find the nested config class
                nested_config_class = None
                for parent_field, nested_options in nested_configs.items():
                    for option_value, option_meta in nested_options.items():
                        if option_meta.get('config_field') == nested_config_name:
                            nested_config_class = option_meta['config_class']
                            break
                    if nested_config_class:
                        break

                if nested_config_class and nested_field_name in nested_config_class.model_fields:
                    field_info = nested_config_class.model_fields[nested_field_name]
                    default_value = field_info.default
                else:
                    updates.append(gr.update())
                    continue
            else:
                # Top-level field
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
        nested_configs = extractor_meta.nested_configs or {}
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
            # Check if this is a nested field (e.g., "easyocr_config.lang")
            if '.' in field_name:
                parts = field_name.split('.')
                nested_config_name = parts[0]
                nested_field_name = parts[1]

                # Find the nested config class
                nested_config_class = None
                for parent_field, nested_options in nested_configs.items():
                    for option_value, option_meta in nested_options.items():
                        if option_meta.get('config_field') == nested_config_name:
                            nested_config_class = option_meta['config_class']
                            break
                    if nested_config_class:
                        break

                if not nested_config_class:
                    updates.append(gr.update())
                    continue

                # Try to get value from nested config_data
                if nested_config_name in config_data and isinstance(config_data[nested_config_name], dict):
                    nested_data = config_data[nested_config_name]
                    if nested_field_name in nested_data:
                        value = normalize_list_value(nested_data[nested_field_name])
                        updates.append(gr.update(value=value))
                        continue

                # Fall back to default from nested config class
                if nested_field_name in nested_config_class.model_fields:
                    field_info = nested_config_class.model_fields[nested_field_name]
                    default_value = normalize_list_value(field_info.default)
                    updates.append(gr.update(value=default_value))
                else:
                    updates.append(gr.update())
            else:
                # Top-level field
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

        # Handle nested field names (e.g., "easyocr_config.lang")
        config_dict = {}
        for field_name, value in zip(field_names, engine_values):
            if '.' in field_name:
                # Nested field
                parts = field_name.split('.')
                nested_config_name = parts[0]
                nested_field_name = parts[1]

                if nested_config_name not in config_dict:
                    config_dict[nested_config_name] = {}
                config_dict[nested_config_name][nested_field_name] = value
            else:
                # Top-level field
                config_dict[field_name] = value

        return engine_values, config_dict

    def get_nested_group_updates(
        self,
        engine_display_name: str,
        parent_field: str,
        selected_value: str
    ) -> List[gr.update]:
        """
        Generate gr.update() objects for nested section components based on parent field value.

        Args:
            engine_display_name: Display name of the engine
            parent_field: Name of the parent field (e.g., "ocr_engine")
            selected_value: Selected value of the parent field (e.g., "easyocr")

        Returns:
            List of gr.update() objects for all components in all nested sections
        """
        engine_name = self.engine_name_from_display(engine_display_name)
        if not engine_name or engine_name not in self.nested_groups:
            return []

        nested_groups = self.nested_groups[engine_name].get(parent_field, {})
        if not nested_groups:
            return []

        # Generate updates: show components in selected section, hide all others
        # Must return updates in sorted order to match outputs list
        updates = []
        for option_value in sorted(nested_groups.keys()):
            visible = (option_value == selected_value)
            section_components = nested_groups[option_value]
            # One update per component in this section
            for _ in section_components:
                updates.append(gr.update(visible=visible))

        return updates

    def get_parent_component(self, engine_display_name: str, parent_field: str):
        """
        Get the parent component for a nested config.

        Args:
            engine_display_name: Display name of the engine
            parent_field: Name of the parent field

        Returns:
            Parent component or None
        """
        engine_name = self.engine_name_from_display(engine_display_name)
        if not engine_name or engine_name not in self.parent_components:
            return None

        return self.parent_components[engine_name].get(parent_field)

    def get_conditional_group_updates(
        self,
        engine_display_name: str,
        parent_field: str,
        parent_value: Any
    ) -> List[gr.update]:
        """
        Generate gr.update() objects for conditional section components based on parent field value.

        Args:
            engine_display_name: Display name of the engine
            parent_field: Name of the parent field (e.g., "auto_mode")
            parent_value: Value of the parent field (e.g., True/False)

        Returns:
            List of gr.update() objects for all components in all conditional sections
        """
        engine_name = self.engine_name_from_display(engine_display_name)
        if not engine_name or engine_name not in self.conditional_groups:
            return []

        conditional_groups = self.conditional_groups[engine_name].get(parent_field, {})
        if not conditional_groups:
            return []

        # Generate updates: show components if parent value matches, hide otherwise
        # IMPORTANT: Iterate in sorted order to match outputs list order in app_builder.py
        updates = []
        for condition_value in sorted(conditional_groups.keys()):
            visible = (condition_value == parent_value)
            section_components = conditional_groups[condition_value]
            # One update per component in this section
            for _ in section_components:
                updates.append(gr.update(visible=visible))

        return updates

    def get_conditional_parent_component(self, engine_display_name: str, parent_field: str):
        """
        Get the parent component for a conditional field group.

        Args:
            engine_display_name: Display name of the engine
            parent_field: Name of the parent field

        Returns:
            Parent component or None
        """
        engine_name = self.engine_name_from_display(engine_display_name)
        if not engine_name or engine_name not in self.conditional_parent_components:
            return None

        return self.conditional_parent_components[engine_name].get(parent_field)

    def get_all_conditional_groups_for_engine(self, engine_display_name: str) -> Dict[str, Dict[Any, Any]]:
        """
        Get all conditional groups for a specific engine.

        Args:
            engine_display_name: Display name of the engine

        Returns:
            Dict mapping parent_field -> {parent_value: gr.Group}
        """
        engine_name = self.engine_name_from_display(engine_display_name)
        if not engine_name or engine_name not in self.conditional_groups:
            return {}

        return self.conditional_groups[engine_name]
