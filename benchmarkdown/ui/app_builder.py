"""
Main app builder for Benchmarkdown - Redesigned UI with intuitive two-column workflow.

Layout:
- Left column (35%): Task List - always visible, primary focus
- Right column (65%): Task Editor - appears on Add/Edit
- Results view: Full-width, replaces both columns

This module now uses DYNAMIC UI GENERATION from the plugin registry.
No hardcoded extractor-specific code!
"""

import asyncio
import gradio as gr
from benchmarkdown.ui.core import BenchmarkUI
from benchmarkdown.ui.queue import load_queue_from_disk, save_queue_to_disk, generate_task_list_html
from benchmarkdown.ui.results import generate_comparison_view_tabbed, generate_comparison_view_sidebyside
from benchmarkdown.ui.dynamic_config import DynamicConfigUI
from benchmarkdown.ui.validation import ValidationUI
from benchmarkdown.config_ui import build_config_from_ui_values
from benchmarkdown.profile_manager import ProfileManager
from benchmarkdown.metrics import MetricRegistry


def create_app(registry):
    """
    Create the redesigned Gradio interface with full dynamic plugin support.

    Args:
        registry: ExtractorRegistry instance containing discovered plugins

    Returns:
        Gradio Blocks app instance
    """
    if registry is None:
        raise ValueError("Registry parameter is required for dynamic UI generation")

    # Initialize components
    ui = BenchmarkUI()
    profile_manager = ProfileManager()
    dynamic_config = DynamicConfigUI(registry)

    # Initialize metrics and validation
    metric_registry = MetricRegistry()
    metric_registry.discover_metrics()
    validation_ui = ValidationUI(metric_registry=metric_registry)

    # State for extractor queue - list of dicts with keys: engine, config_name, extractor, cost
    extractor_queue = []

    # Load queue on app creation
    load_queue_from_disk(extractor_queue, ui)

    # State for editing - None or index of task being edited
    editing_task_index = [None]  # Use list to make it mutable in closures

    with gr.Blocks(
        title="Benchmarkdown - Document Extraction Comparison",
        head="""
        <style>
        #hidden-delete-controls {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            overflow: hidden !important;
        }
        </style>
        <script>
        function deleteTask(taskNumber) {
            // Find the hidden input by elem_id
            const hiddenInput = document.querySelector('#hidden-task-index input[type="number"]');
            const hiddenButton = document.querySelector('#hidden-delete-trigger');

            if (hiddenInput && hiddenButton) {
                // Set the value and trigger the input event
                hiddenInput.value = taskNumber;
                hiddenInput.dispatchEvent(new Event('input', { bubbles: true }));

                // Small delay to ensure Gradio processes the input change
                setTimeout(() => {
                    hiddenButton.click();
                }, 100);
            } else {
                console.error('Could not find hidden components for task deletion', {
                    inputFound: !!hiddenInput,
                    buttonFound: !!hiddenButton
                });
            }
        }
        </script>
        """
    ) as demo:
        gr.Markdown("# 📄 Benchmarkdown - Document Extraction Comparison")

        # ============================================================
        # MAIN VIEW: Task List and Editor (always visible)
        # ============================================================
        gr.Markdown("## 📋 Extraction Tasks")

        with gr.Row():
            # LEFT COLUMN: Task List (always visible)
            with gr.Column(scale=1) as task_list_column:
                task_list_display = gr.HTML(
                    value=generate_task_list_html(extractor_queue)
                )

                # Hidden components for JavaScript communication (visible but styled as hidden)
                with gr.Row(visible=True, elem_id="hidden-delete-controls") as hidden_controls:
                    hidden_task_index = gr.Number(
                        label="",
                        value=0,
                        elem_id="hidden-task-index",
                        container=False,
                        show_label=False,
                        scale=0,
                        min_width=1
                    )
                    hidden_delete_trigger = gr.Button(
                        "",
                        elem_id="hidden-delete-trigger",
                        size="sm",
                        scale=0,
                        min_width=1
                    )

                # All action buttons below the task list in workflow order
                with gr.Row():
                    add_task_btn = gr.Button("➕ Add Task", variant="primary", size="sm")
                    clear_all_btn = gr.Button("🗑️ Clear All", size="sm", variant="stop", visible=bool(extractor_queue))

            # RIGHT COLUMN: Task Editor (hidden by default)
            with gr.Column(scale=2, visible=False) as task_editor_column:
                gr.Markdown("## ⚙️ Task Editor")

                editor_status = gr.Markdown("*Select an extractor engine and profile*")

                # Step 1: Select Engine (Dynamically generated from registry!)
                with gr.Group():
                    gr.Markdown("### 1. Select Extractor Engine")

                    engine_selector = gr.Dropdown(
                        choices=dynamic_config.generate_engine_choices(),
                        label="Extractor Engine",
                        value=None,
                        interactive=True,
                        info="Engines discovered dynamically from plugins"
                    )

                # Step 2: Select Profile (hidden until engine selected)
                with gr.Group(visible=False) as profile_group:
                    gr.Markdown("### 2. Select Profile")

                    with gr.Row():
                        profile_selector = gr.Dropdown(
                            label="Saved Profiles",
                            choices=[],
                            value=None,
                            interactive=True,
                            info="Select a profile to load its settings, or create a new one",
                            scale=3
                        )
                        refresh_profiles_btn = gr.Button("🔄", size="sm", scale=0, min_width=50)

                    with gr.Row():
                        edit_profile_btn = gr.Button("✏️ Edit Profile", size="sm")
                        new_profile_btn = gr.Button("✨ New Profile", size="sm", variant="primary")
                        delete_profile_btn = gr.Button("🗑️ Delete Profile", size="sm")

                    profile_status = gr.Markdown("", visible=False)

                # Step 3: Configuration Editor (hidden until Edit or New clicked)
                with gr.Column(visible=False) as config_editor:
                    gr.Markdown("### 3. Configure Settings")

                    config_name_input = gr.Textbox(
                        label="Profile Name",
                        placeholder="e.g., 'Fast Mode', 'High Quality', etc.",
                        value="",
                        interactive=True
                    )

                    # ========== DYNAMIC CONFIG UI GENERATION ==========
                    # All config UIs generated dynamically from plugin registry!
                    # This replaces 197 lines of hardcoded Docling/Textract UI
                    
                    config_ui_data = dynamic_config.generate_all_config_uis()

                    # Store references for event handlers
                    config_areas = config_ui_data['config_areas']
                    component_lists = config_ui_data['component_lists']
                    field_maps = config_ui_data['field_maps']
                    nested_groups = config_ui_data['nested_groups']
                    parent_components = config_ui_data['parent_components']
                    conditional_groups = config_ui_data['conditional_groups']
                    conditional_parent_components = config_ui_data['conditional_parent_components']

                    # All config areas are now generated and ready!
                    # No hardcoded engine-specific code needed.

                    # ========== SETUP CONDITIONAL FIELD HANDLERS ==========
                    # Set up event handlers for conditional fields (show/hide based on parent value)
                    for engine_name, parent_components_dict in conditional_parent_components.items():
                        for parent_field, parent_component in parent_components_dict.items():
                            # Get the conditional sections for this parent field
                            if engine_name in conditional_groups and parent_field in conditional_groups[engine_name]:
                                cond_sections_dict = conditional_groups[engine_name][parent_field]
                                # Flatten all components from all conditional sections
                                cond_components_flat = []
                                for key in sorted(cond_sections_dict.keys()):
                                    cond_components_flat.extend(cond_sections_dict[key])

                                # Create handler function for this parent field
                                def make_conditional_handler(eng_name, parent_fld):
                                    def handler(parent_value):
                                        # Get the metadata to find display name
                                        metadata = registry.get_extractor(eng_name)
                                        if not metadata:
                                            return [gr.update() for _ in cond_components_flat]

                                        # Get updates from dynamic_config
                                        updates = dynamic_config.get_conditional_group_updates(
                                            metadata.display_name,
                                            parent_fld,
                                            parent_value
                                        )
                                        return updates
                                    return handler

                                # Bind the handler to the parent component
                                handler_fn = make_conditional_handler(engine_name, parent_field)
                                parent_component.change(
                                    fn=handler_fn,
                                    inputs=[parent_component],
                                    outputs=cond_components_flat
                                )

                    # ========== SETUP NESTED CONFIG HANDLERS ==========
                    # Set up event handlers for nested configs (e.g., Docling OCR engine selection)
                    for engine_name, nested_parent_components_dict in parent_components.items():
                        for parent_field, parent_component in nested_parent_components_dict.items():
                            # Get the nested sections for this parent field
                            if engine_name in nested_groups and parent_field in nested_groups[engine_name]:
                                nested_sections_dict = nested_groups[engine_name][parent_field]
                                # Flatten all components from all nested sections
                                nested_components_flat = []
                                for key in sorted(nested_sections_dict.keys()):
                                    nested_components_flat.extend(nested_sections_dict[key])

                                # Create handler function for this parent field
                                def make_nested_handler(eng_name, parent_fld):
                                    def handler(parent_value):
                                        # Get the metadata to find display name
                                        metadata = registry.get_extractor(eng_name)
                                        if not metadata:
                                            return [gr.update() for _ in nested_components_flat]

                                        # Get updates from dynamic_config
                                        updates = dynamic_config.get_nested_group_updates(
                                            metadata.display_name,
                                            parent_fld,
                                            parent_value
                                        )
                                        return updates
                                    return handler

                                # Bind the handler to the parent component
                                handler_fn = make_nested_handler(engine_name, parent_field)
                                parent_component.change(
                                    fn=handler_fn,
                                    inputs=[parent_component],
                                    outputs=nested_components_flat
                                )

                    # Configuration editor action buttons
                    with gr.Row():
                        save_profile_btn = gr.Button("💾 Save Profile", variant="primary", size="sm")
                        cancel_config_btn = gr.Button("✖️ Cancel", size="sm")

                # Save Task button (always visible at bottom of editor)
                gr.Markdown("---")
                save_task_btn = gr.Button("✅ Add Task to Queue", variant="primary", size="lg")
                cancel_editor_btn = gr.Button("✖️ Cancel", size="lg")

        # ============================================================
        # UPLOAD AND EXTRACTION SECTION (always visible)
        # ============================================================
        gr.Markdown("---")
        gr.Markdown("## 📤 Upload Documents")
        gr.Markdown("Upload the documents you want to extract with the configured tasks.")

        file_upload = gr.File(
            label="Select Documents",
            file_count="multiple",
            file_types=[".pdf", ".docx", ".doc", ".txt"]
        )

        run_extraction_btn = gr.Button(
            "▶️ Run Extraction",
            variant="primary",
            size="lg"
        )

        extraction_status = gr.Markdown("", visible=False)

        # ============================================================
        # EXTRACTION RESULTS SECTION (appears after extraction)
        # ============================================================
        gr.Markdown("---")
        with gr.Column(visible=False) as extraction_results_section:
            gr.Markdown("## 📊 Extraction Results")

            results_table = gr.HTML(
                value="<p style='color: #666;'>Results will appear here after extraction completes.</p>"
            )

            # Download buttons
            with gr.Row():
                download_zip_btn = gr.Button("📦 Download All Markdown", size="sm")
                download_report_btn = gr.Button("📊 Download Report", size="sm")

            download_zip_file = gr.File(label="ZIP Download", visible=False)
            download_report_file = gr.File(label="Report Download", visible=False)

            # Markdown preview section in collapsible accordion
            with gr.Accordion("📄 View Extracted Markdown", open=False, visible=False) as markdown_preview_accordion:
                # Results controls
                with gr.Row() as results_controls:
                    document_selector = gr.Dropdown(
                        label="Select Document to View",
                        choices=[],
                        interactive=True
                    )
                    view_mode = gr.Radio(
                        choices=["Tabbed", "Side-by-Side"],
                        value="Tabbed",
                        label="View Mode"
                    )

                # Comparison view
                comparison_view = gr.HTML(value="")

        # ============================================================
        # VALIDATION SECTION (appears after extraction)
        # ============================================================
        gr.Markdown("---")
        with gr.Column(visible=False) as validation_section:
            gr.Markdown("## 🎯 Validation (Compare Against Ground Truth)")
            gr.Markdown("""
            Upload ground truth markdown files to validate extraction results using metrics like word count similarity,
            character count similarity, and more.
            """)

            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 1. Upload Ground Truth")
                    gt_document_selector = gr.Dropdown(
                        label="Select Document",
                        choices=[],
                        interactive=True
                    )
                    gt_file_upload = gr.File(
                        label="Upload Ground Truth Markdown",
                        file_types=[".md", ".txt"],
                        type="filepath"
                    )
                    gt_upload_status = gr.Markdown("")

                    # Persistent list of uploaded ground truth files
                    gr.Markdown("**Uploaded Ground Truth Files:**")
                    gt_uploaded_list = gr.HTML(
                        value="<p style='color: var(--body-text-color-subdued, #666); font-size: 0.9em; font-style: italic;'>No ground truth files uploaded yet.</p>"
                    )

                with gr.Column(scale=1):
                    gr.Markdown("### 2. Select What to Validate")
                    val_document_selector = gr.CheckboxGroup(
                        label="Documents",
                        choices=[],
                        interactive=True
                    )
                    val_extractor_selector = gr.CheckboxGroup(
                        label="Extractors",
                        choices=[],
                        interactive=True
                    )
                    val_metric_selector = gr.CheckboxGroup(
                        label="Metrics",
                        choices=[],
                        value=[],  # Will be set based on available metrics
                        interactive=True
                    )

            with gr.Row():
                run_validation_btn = gr.Button("▶️ Run Validation", variant="primary", size="lg")
                clear_validation_btn = gr.Button("🗑️ Clear Results", size="sm")

            validation_status = gr.Markdown("")

        # ============================================================
        # VALIDATION RESULTS SECTION (appears after validation)
        # ============================================================
        gr.Markdown("---")
        with gr.Column(visible=False) as validation_results_section:
            gr.Markdown("## 📊 Validation Results")
            validation_results_view = gr.HTML(
                value="<p style='color: var(--body-text-color-subdued, #666);'>Validation results will appear here.</p>"
            )

        # ============================================================
        # Event Handlers
        # ============================================================

        def get_task_choices():
            """Get task choices for dropdown."""
            return [f"{i+1}. {task['engine']} - {task['config_name']}" for i, task in enumerate(extractor_queue)]

        # State for current loaded profile
        current_profile_data = [None]  # Will hold loaded profile config

        def show_task_editor(is_new=True, task_index=None):
            """Show the task editor, optionally loading an existing task."""
            editing_task_index[0] = task_index

            if is_new:
                status = "*Select an extractor engine and profile*"
                return (
                    gr.update(visible=True),  # task_editor_column
                    status,  # editor_status
                    gr.update(value=None),  # engine_selector
                    gr.update(visible=False),  # profile_group
                    gr.update(visible=False),  # config_editor
                )
            else:
                # Load existing task for editing - open config editor with task data
                task = extractor_queue[task_index]
                status = f"*Editing task: {task['config_name']}*"

                # Prepare config values for UI
                updates = [
                    gr.update(visible=True),  # task_editor_column
                    status,  # editor_status
                    gr.update(value=task['engine']),  # engine_selector
                    gr.update(visible=True),  # profile_group
                    gr.update(visible=True),  # config_editor (open for editing)
                    gr.update(value=task['config_name']),  # config_name_input
                ]

                # Show/hide config areas based on engine
                if task['engine'] == "Docling":
                    updates.extend([
                        gr.update(visible=True),  # docling_config_area
                        gr.update(visible=False),  # textract_config_area
                    ])

                    # Load config values into components
                    config_dict = task['config_dict']
                    all_fields = DOCLING_BASIC_FIELDS + DOCLING_ADVANCED_FIELDS
                    for field_name in all_fields:
                        if field_name in config_dict:
                            updates.append(gr.update(value=config_dict[field_name]))
                        else:
                            updates.append(gr.update())

                    # Store in current profile data
                    current_profile_data[0] = config_dict
                else:
                    updates.extend([
                        gr.update(visible=False),  # docling_config_area
                        gr.update(visible=True),  # textract_config_area
                    ])
                    # Add empty updates for docling components
                    updates.extend([gr.update()] * max(len(comps) for comps in component_lists.values()))

                return tuple(updates)

        def hide_task_editor():
            """Hide the task editor and reset state."""
            editing_task_index[0] = None
            current_profile_data[0] = None
            return gr.update(visible=False)

        def open_new_task():
            """Open editor for new task."""
            return show_task_editor(is_new=True)

        def profile_selected_handler(engine, selected_profile):
            """Auto-load profile when selected from dropdown."""
            if not selected_profile or not engine:
                current_profile_data[0] = None
                return gr.update(value="Select a profile or click 'New Profile'", visible=True)

            try:
                profile = profile_manager.load_profile(selected_profile)

                if profile["engine"] != engine:
                    return gr.update(value=f"❌ Profile is for {profile['engine']}, but {engine} is selected", visible=True)

                # Store loaded profile data
                current_profile_data[0] = profile["config_data"]

                return gr.update(value=f"✅ Loaded profile: **{selected_profile}** - Ready to add to queue or click 'Edit Profile' to modify", visible=True)

            except Exception as e:
                current_profile_data[0] = None
                return gr.update(value=f"❌ Error loading profile: {e}", visible=True)

        def normalize_list_value(value):
            """Convert list values to comma-separated strings for UI display.

            Handles:
            - Actual lists: ["en", "it"] → "en, it"
            - String representations: "['en', 'it']" → "en, it"
            - Already converted: "en, it" → "en, it"
            """
            if isinstance(value, list):
                return ", ".join(str(v) for v in value)
            elif isinstance(value, str) and value.startswith("[") and value.endswith("]"):
                # Old format: string representation of a Python list
                try:
                    import ast
                    parsed = ast.literal_eval(value)
                    if isinstance(parsed, list):
                        return ", ".join(str(v) for v in parsed)
                except:
                    pass
            return value

        def edit_profile_handler(engine_display, selected_profile):
            """Open config editor to edit the selected profile (works for ANY engine!)."""
            if not selected_profile:
                # Return updates to hide editor
                updates = [
                    gr.update(visible=False),  # config_editor
                    gr.update(value=""),  # config_name_input
                ]
                # Hide all config areas
                updates.extend([gr.update(visible=False) for _ in config_areas])
                # Clear all component values
                updates.extend([gr.update() for _ in all_config_components])
                return updates

            try:
                profile = profile_manager.load_profile(selected_profile)

                if profile["engine"] != engine_display:
                    # Engine mismatch - hide editor
                    updates = [
                        gr.update(visible=False),  # config_editor
                        gr.update(value=""),  # config_name_input
                    ]
                    updates.extend([gr.update(visible=False) for _ in config_areas])
                    updates.extend([gr.update() for _ in all_config_components])
                    return updates

                config_data = profile["config_data"]
                current_profile_data[0] = config_data

                # Open config editor with profile data
                updates = [
                    gr.update(visible=True),  # config_editor
                    gr.update(value=selected_profile),  # config_name_input
                ]

                # Show appropriate config area (hide others)
                updates.extend(dynamic_config.get_config_area_updates(engine_display))

                # Load profile values for the selected engine
                # For other engines, return empty updates
                engine_name = dynamic_config.engine_name_from_display(engine_display)

                for eng_name in sorted(component_lists.keys()):
                    if eng_name == engine_name:
                        # Load profile values for this engine
                        updates.extend(dynamic_config.get_profile_values_for_engine(engine_display, config_data))
                    else:
                        # Empty updates for other engines' components
                        updates.extend([gr.update() for _ in component_lists[eng_name]])

                return updates

            except Exception as e:
                # Error loading profile - hide editor
                updates = [
                    gr.update(visible=False),  # config_editor
                    gr.update(value=""),  # config_name_input
                ]
                updates.extend([gr.update(visible=False) for _ in config_areas])
                updates.extend([gr.update() for _ in all_config_components])
                return updates

        def new_profile_handler(engine_display):
            """Open config editor for creating a new profile (works for ANY engine!)."""
            if not engine_display:
                # Return updates to hide editor and clear everything
                updates = [
                    gr.update(visible=False),  # config_editor
                    gr.update(value=""),  # config_name_input
                ]
                # Hide all config areas
                updates.extend([gr.update(visible=False) for _ in config_areas])
                # Clear all component values
                updates.extend([gr.update() for _ in all_config_components])
                return updates

            current_profile_data[0] = None  # Clear current profile

            # Open config editor with empty/default values
            updates = [
                gr.update(visible=True),  # config_editor
                gr.update(value=""),  # config_name_input (empty for new)
            ]

            # Show appropriate config area (hide others)
            updates.extend(dynamic_config.get_config_area_updates(engine_display))

            # Get default values for the selected engine's components
            # For other engines, return empty updates
            engine_name = dynamic_config.engine_name_from_display(engine_display)

            for eng_name in sorted(component_lists.keys()):
                if eng_name == engine_name:
                    # Load default values for this engine
                    updates.extend(dynamic_config.get_default_values_for_engine(engine_display))
                else:
                    # Empty updates for other engines' components
                    updates.extend([gr.update() for _ in component_lists[eng_name]])

            return updates

        def cancel_config_handler():
            """Close config editor without saving."""
            return gr.update(visible=False)  # Hide config_editor

        def save_task(engine_display, selected_profile):
            """Add current task (from loaded profile) to queue (works for ANY engine!)."""
            if not engine_display:
                return (
                    gr.update(value=generate_task_list_html(extractor_queue)),
                    gr.update(visible=False),  # hide editor
                    "❌ Please select an extractor engine",
                    gr.update(visible=bool(extractor_queue))
                )

            # Use currently loaded profile data or ask user to select
            if current_profile_data[0] is None:
                return (
                    gr.update(value=generate_task_list_html(extractor_queue)),
                    gr.update(visible=True),  # keep editor open
                    "❌ Please select a profile or create a new one",
                    gr.update(visible=bool(extractor_queue))
                )

            if not selected_profile:
                return (
                    gr.update(value=generate_task_list_html(extractor_queue)),
                    gr.update(visible=True),  # keep editor open
                    "❌ Please select a profile",
                    gr.update(visible=bool(extractor_queue))
                )

            try:
                # Get engine name from display name
                engine_name = dynamic_config.engine_name_from_display(engine_display)
                if not engine_name:
                    return (
                        gr.update(value=generate_task_list_html(extractor_queue)),
                        gr.update(visible=True),
                        f"❌ Unknown engine: {engine_display}",
                        gr.update(visible=bool(extractor_queue))
                    )

                # Get extractor metadata from registry
                extractor_meta = registry.get_extractor(engine_name)
                if not extractor_meta:
                    return (
                        gr.update(value=generate_task_list_html(extractor_queue)),
                        gr.update(visible=True),
                        f"❌ Extractor not found: {engine_name}",
                        gr.update(visible=bool(extractor_queue))
                    )

                # Build config from current profile data
                config = build_config_from_ui_values(extractor_meta.config_class, current_profile_data[0])

                # Create extractor instance
                extractor = registry.create_extractor_instance(engine_name, config=config)
                full_name = f"{engine_display} ({selected_profile})"

                task_data = {
                    'engine': engine_display,
                    'config_name': selected_profile,
                    'extractor': extractor,
                    'cost': None,
                    'config_dict': current_profile_data[0]
                }

                # Add or update task
                if editing_task_index[0] is not None:
                    # Update existing task
                    old_name = extractor_queue[editing_task_index[0]]['config_name']
                    extractor_queue[editing_task_index[0]] = task_data
                    # Update UI registry
                    old_full_name = f"{engine_display} ({old_name})"
                    if old_full_name in ui.extractors:
                        del ui.extractors[old_full_name]
                    ui.register_extractor(full_name, extractor)
                    message = f"✓ Updated task: {selected_profile}"
                else:
                    # Add new task
                    extractor_queue.append(task_data)
                    ui.register_extractor(full_name, extractor)
                    message = f"✓ Added task: {selected_profile}"

                # Save queue to disk
                save_queue_to_disk(extractor_queue)

                editing_task_index[0] = None
                current_profile_data[0] = None

                # Show Clear All button if we have tasks
                return (
                    gr.update(value=generate_task_list_html(extractor_queue)),
                    gr.update(visible=False),  # hide editor
                    message,
                    gr.update(visible=True)  # show clear_all_btn
                )

            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"Error saving task: {error_details}")
                return (
                    gr.update(value=generate_task_list_html(extractor_queue)),
                    gr.update(visible=True),
                    f"❌ Error: {e}",
                    gr.update(visible=bool(extractor_queue))
                )

        def delete_task_handler(task_number):
            """Delete a task from the queue by its number."""
            if task_number is None or not extractor_queue:
                return (
                    gr.update(value=generate_task_list_html(extractor_queue)),
                    gr.update(visible=bool(extractor_queue))
                )

            try:
                task_index = int(task_number) - 1  # Convert to 0-based index

                if 0 <= task_index < len(extractor_queue):
                    task = extractor_queue[task_index]
                    full_name = f"{task['engine']} ({task['config_name']})"

                    # Remove from queue and UI registry
                    extractor_queue.pop(task_index)
                    if full_name in ui.extractors:
                        del ui.extractors[full_name]

                    # Save queue to disk
                    save_queue_to_disk(extractor_queue)

                    return (
                        gr.update(value=generate_task_list_html(extractor_queue)),
                        gr.update(visible=bool(extractor_queue))  # Hide if queue is now empty
                    )
            except (ValueError, IndexError):
                pass

            return (
                gr.update(value=generate_task_list_html(extractor_queue)),
                gr.update(visible=bool(extractor_queue))
            )

        def clear_all_tasks_handler():
            """Clear all tasks from the queue."""
            # Clear the queue
            extractor_queue.clear()
            # Clear UI registry
            ui.extractors.clear()

            # Save queue to disk
            save_queue_to_disk(extractor_queue)

            return (
                gr.update(value=generate_task_list_html(extractor_queue)),
                gr.update(visible=False)  # Hide delete controls
            )

        def edit_task_handler(selected_task):
            """Open editor to edit an existing task based on dropdown selection."""
            if not selected_task or not extractor_queue:
                # Return defaults if error
                return tuple([gr.update()] * (7 + max(len(comps) for comps in component_lists.values())))

            try:
                # Extract index from dropdown value like "1. Docling - Fast Mode"
                task_index = int(selected_task.split('.')[0]) - 1

                if 0 <= task_index < len(extractor_queue):
                    return show_task_editor(is_new=False, task_index=task_index)
            except (ValueError, IndexError):
                pass

            # Return defaults if error
            return tuple([gr.update()] * (7 + max(len(comps) for comps in component_lists.values())))

        def toggle_profile_group(engine):
            """Show profile group when engine is selected."""
            if engine:
                # Refresh profiles for selected engine
                profiles = profile_manager.list_profiles(engine=engine)
                profile_names = [p["profile_name"] for p in profiles]
                return gr.update(visible=True), gr.update(choices=profile_names, value=None)
            return gr.update(visible=False), gr.update(choices=[], value=None)

        def show_config_area(engine_display):
            """Show appropriate config area dynamically (works for ANY engine!)."""
            if not engine_display:
                # Hide all config areas
                updates = [gr.update(visible=False) for _ in config_areas]
                updates.append(gr.update(visible=False))  # profile_status
                return updates

            # Get updates for all config areas
            updates = dynamic_config.get_config_area_updates(engine_display)
            updates.append(gr.update(visible=False))  # profile_status
            return updates

        def refresh_profile_list(engine):
            """Refresh the list of available profiles for the selected engine."""
            if not engine:
                return gr.update(choices=[])

            profiles = profile_manager.list_profiles(engine=engine)
            profile_names = [p["profile_name"] for p in profiles]
            return gr.update(choices=profile_names, value=None)

        def load_profile_handler(engine, selected_profile):
            """Load a profile and populate configuration UI."""
            if not selected_profile:
                return [gr.update(visible=True, value="❌ Please select a profile to load")] + [gr.update()] * max(len(comps) for comps in component_lists.values()) + [gr.update()]

            try:
                profile = profile_manager.load_profile(selected_profile)

                # Verify engine matches
                if profile["engine"] != engine:
                    return [gr.update(visible=True, value=f"❌ Profile is for {profile['engine']}, but {engine} is selected")] + [gr.update()] * max(len(comps) for comps in component_lists.values()) + [gr.update()]

                # Update config name
                config_name = profile["profile_name"]

                # Prepare updates for all config components
                updates = [gr.update(visible=True, value=f"✓ Loaded profile: {config_name}")]

                if engine == "Docling":
                    config_data = profile["config_data"]

                    # Load basic fields
                    for field_name in DOCLING_BASIC_FIELDS:
                        if field_name in config_data:
                            updates.append(gr.update(value=config_data[field_name]))
                        else:
                            updates.append(gr.update())

                    # Load OCR configs (nested)
                    for field_name in EASYOCR_BASIC_FIELDS + EASYOCR_ADVANCED_FIELDS:
                        if "easyocr_config" in config_data and field_name in config_data["easyocr_config"]:
                            value = config_data["easyocr_config"][field_name]
                            # Convert lists to comma-separated strings for UI
                            if isinstance(value, list):
                                value = ", ".join(str(v) for v in value)
                            updates.append(gr.update(value=value))
                        else:
                            # Use defaults from model
                            default = EasyOcrConfig.model_fields[field_name].default
                            if isinstance(default, list):
                                default = ", ".join(str(v) for v in default)
                            updates.append(gr.update(value=default))

                    for field_name in TESSERACT_BASIC_FIELDS + TESSERACT_ADVANCED_FIELDS:
                        if "tesseract_config" in config_data and field_name in config_data["tesseract_config"]:
                            value = normalize_list_value(config_data["tesseract_config"][field_name])
                            updates.append(gr.update(value=value))
                        else:
                            default = TesseractOcrConfig.model_fields[field_name].default
                            default = normalize_list_value(default)
                            updates.append(gr.update(value=default))

                    for field_name in TESSERACT_CLI_BASIC_FIELDS + TESSERACT_CLI_ADVANCED_FIELDS:
                        if "tesseract_cli_config" in config_data and field_name in config_data["tesseract_cli_config"]:
                            value = normalize_list_value(config_data["tesseract_cli_config"][field_name])
                            updates.append(gr.update(value=value))
                        else:
                            default = TesseractCliOcrConfig.model_fields[field_name].default
                            default = normalize_list_value(default)
                            updates.append(gr.update(value=default))

                    for field_name in OCR_MAC_BASIC_FIELDS + OCR_MAC_ADVANCED_FIELDS:
                        if "ocr_mac_config" in config_data and field_name in config_data["ocr_mac_config"]:
                            value = normalize_list_value(config_data["ocr_mac_config"][field_name])
                            updates.append(gr.update(value=value))
                        else:
                            default = OcrMacConfig.model_fields[field_name].default
                            default = normalize_list_value(default)
                            updates.append(gr.update(value=default))

                    for field_name in RAPIDOCR_BASIC_FIELDS + RAPIDOCR_ADVANCED_FIELDS:
                        if "rapidocr_config" in config_data and field_name in config_data["rapidocr_config"]:
                            value = normalize_list_value(config_data["rapidocr_config"][field_name])
                            updates.append(gr.update(value=value))
                        else:
                            default = RapidOcrConfig.model_fields[field_name].default
                            default = normalize_list_value(default)
                            updates.append(gr.update(value=default))

                    # Load advanced fields
                    for field_name in DOCLING_ADVANCED_FIELDS:
                        if field_name in config_data:
                            updates.append(gr.update(value=config_data[field_name]))
                        else:
                            updates.append(gr.update())
                else:
                    updates.extend([gr.update()] * max(len(comps) for comps in component_lists.values()))

                # Update config name field
                updates.append(gr.update(value=config_name))

                return updates

            except FileNotFoundError:
                return [gr.update(visible=True, value=f"❌ Profile '{selected_profile}' not found")] + [gr.update()] * max(len(comps) for comps in component_lists.values()) + [gr.update()]
            except Exception as e:
                return [gr.update(visible=True, value=f"❌ Error loading profile: {e}")] + [gr.update()] * max(len(comps) for comps in component_lists.values()) + [gr.update()]

        def save_profile_handler(engine_display, config_name, *config_values):
            """Save current configuration as a profile (works for ANY engine!)."""
            if not config_name:
                return (
                    gr.update(visible=True),  # Keep editor open
                    gr.update(value="❌ Please enter a profile name", visible=True),
                    gr.update(),  # profile_selector
                )

            try:
                # Extract values for the selected engine from the flattened list
                _, config_dict = dynamic_config.extract_engine_values_from_all_values(
                    engine_display,
                    list(config_values)
                )

                # Save profile
                profile_manager.save_profile(
                    engine=engine_display,
                    profile_name=config_name,
                    config_data=config_dict
                )

                # Update current profile data
                current_profile_data[0] = config_dict

                # Refresh profile list
                profiles = profile_manager.list_profiles(engine=engine_display)
                profile_names = [p["profile_name"] for p in profiles]

                return (
                    gr.update(visible=False),  # Close config_editor
                    gr.update(value=f"✅ Saved profile: **{config_name}** - Ready to add to queue", visible=True),  # profile_status
                    gr.update(choices=profile_names, value=config_name)  # profile_selector with new profile selected
                )

            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"Error saving profile: {error_details}")
                return (
                    gr.update(visible=True),  # Keep editor open
                    gr.update(value=f"❌ Error saving profile: {e}", visible=True),
                    gr.update()
                )

        def delete_profile_handler(engine, selected_profile):
            """Delete a profile."""
            if not selected_profile:
                return gr.update(visible=True, value="❌ Please select a profile to delete"), gr.update()

            try:
                success = profile_manager.delete_profile(selected_profile)

                if success:
                    # Refresh profile list
                    profiles = profile_manager.list_profiles(engine=engine)
                    profile_names = [p["profile_name"] for p in profiles]

                    return (
                        gr.update(visible=True, value=f"✓ Deleted profile: {selected_profile}"),
                        gr.update(choices=profile_names, value=None)
                    )
                else:
                    return (
                        gr.update(visible=True, value=f"❌ Profile '{selected_profile}' not found"),
                        gr.update()
                    )

            except Exception as e:
                return gr.update(visible=True, value=f"❌ Error deleting profile: {e}"), gr.update()

        def run_extraction_handler(files, progress=gr.Progress()):
            """Process documents with all queued extractors."""
            if not files:
                return (
                    gr.update(visible=False),  # extraction_results_section
                    "<p style='color: red;'>❌ No files uploaded.</p>",  # results_table
                    gr.update(visible=False),  # markdown_preview_accordion
                    "",  # comparison_view
                    gr.update(choices=[], value=None),  # document_selector
                    gr.update(visible=False),  # validation_section
                    gr.update(choices=[]),  # gt_document_selector
                    gr.update(choices=[]),  # val_document_selector
                    gr.update(choices=[]),  # val_extractor_selector
                    gr.update(choices=[]),  # val_metric_selector
                    gr.update(value="❌ No files uploaded.", visible=True),  # extraction_status
                )

            # Get all extractor names from queue
            extractor_names = [f"{task['engine']} ({task['config_name']})" for task in extractor_queue]

            # Show progress
            num_files = len(files) if isinstance(files, list) else 1
            num_extractors = len(extractor_names)
            progress(0, desc=f"🚀 Starting extraction for {num_files} document(s) with {num_extractors} extractor(s)...")

            # Process documents
            result = asyncio.run(ui.process_documents(files, extractor_names))

            progress(0.9, desc="✅ Extraction complete, generating results...")

            # Get filenames for dropdown
            filenames = list(ui.results.keys()) if ui.results else []
            first_filename = filenames[0] if filenames else None

            # Generate comparison view
            comparison = ""
            if first_filename:
                comparison = generate_comparison_view_tabbed(ui.results, first_filename)

            # Get unique extractor names from results
            extractor_set = set()
            for doc_results in ui.results.values():
                extractor_set.update(doc_results.keys())
            extractor_list = sorted(list(extractor_set))

            # Get available metrics
            metric_choices = [m[0] for m in validation_ui.get_available_metrics()]

            return (
                gr.update(visible=True),  # extraction_results_section
                result[0],  # results_table
                gr.update(visible=True),  # markdown_preview_accordion
                comparison,  # comparison_view
                gr.update(choices=filenames, value=first_filename),  # document_selector
                gr.update(visible=True),  # validation_section
                gr.update(choices=filenames, value=first_filename if filenames else None),  # gt_document_selector
                gr.update(choices=filenames, value=filenames),  # val_document_selector
                gr.update(choices=extractor_list, value=extractor_list),  # val_extractor_selector
                gr.update(choices=metric_choices, value=metric_choices),  # val_metric_selector
                gr.update(value=f"✅ Extraction complete! Processed {num_files} document(s) with {num_extractors} extractor(s).", visible=True),  # extraction_status
            )

        def update_comparison(filename, view_mode_val):
            """Update comparison view."""
            if not filename:
                return ""
            if view_mode_val == "Side-by-Side":
                return generate_comparison_view_sidebyside(ui.results, filename)
            else:
                return generate_comparison_view_tabbed(ui.results, filename)

        # ============================================================
        # Validation Event Handlers
        # ============================================================

        def generate_gt_uploaded_list_html():
            """Generate HTML list of uploaded ground truth files."""
            if not validation_ui.ground_truths:
                return "<p style='color: var(--body-text-color-subdued, #666); font-size: 0.9em; font-style: italic;'>No ground truth files uploaded yet.</p>"

            html = ["<ul style='list-style: none; padding: 0; margin: 0; font-size: 0.9em;'>"]
            for doc_name in sorted(validation_ui.ground_truths.keys()):
                gt_text = validation_ui.ground_truths[doc_name]
                word_count = len(gt_text.split())
                char_count = len(gt_text)
                html.append(f"<li style='padding: 4px 0; color: var(--body-text-color);'>")
                html.append(f"✅ <strong>{doc_name}</strong>")
                html.append(f" <span style='color: var(--body-text-color-subdued, #666);'>({word_count} words, {char_count} chars)</span>")
                html.append("</li>")
            html.append("</ul>")
            return "".join(html)

        def upload_ground_truth_handler(file_path, document_name):
            """Handle ground truth file upload."""
            if not file_path:
                # Don't show error - file control is empty because we cleared it
                return "", gr.update(), generate_gt_uploaded_list_html()
            if not document_name:
                return "⚠️ Please select a document", gr.update(), generate_gt_uploaded_list_html()

            status = validation_ui.upload_ground_truth(file_path, document_name)
            # Clear the file upload control so user can upload another file
            # Also update the list of uploaded GTs
            return status, gr.update(value=None), generate_gt_uploaded_list_html()

        def run_validation_handler(selected_docs, selected_extractors, selected_metrics):
            """Handle validation execution."""
            # Run validation
            status = asyncio.run(validation_ui.run_validation(
                ui_results=ui.results,
                selected_documents=selected_docs,
                selected_extractors=selected_extractors,
                selected_metrics=selected_metrics
            ))

            # Generate HTML results
            html = validation_ui.generate_validation_results_html()

            # Show results section
            return status, html, gr.update(visible=True)

        def clear_validation_handler():
            """Handle clearing validation results."""
            status = validation_ui.clear_validation_results()
            html = validation_ui.generate_validation_results_html()
            # Hide results section
            return status, html, gr.update(visible=False)

        # ============================================================
        # Wire up events
        # ============================================================

        # Page Load Event - refresh display on page load
        def reload_page():
            """Reload queue from disk and update display."""
            # Clear current queue and reload from disk to ensure consistency
            extractor_queue.clear()
            ui.extractors.clear()
            load_queue_from_disk(extractor_queue, ui)

            return (
                gr.update(value=generate_task_list_html(extractor_queue)),
                gr.update(visible=bool(extractor_queue))
            )

        def ocr_engine_change_handler(ocr_engine_value):
            """Handle OCR engine selection - show/hide appropriate OCR config sections."""
            # Map enum values to visibility
            visibility_map = {
                "easyocr": [True, False, False, False, False],
                "tesseract": [False, True, False, False, False],
                "tesseract_cli": [False, False, True, False, False],
                "ocr_mac": [False, False, False, True, False],
                "rapid_ocr": [False, False, False, False, True],
            }

            # Get visibility for selected engine (default to EasyOCR)
            visibilities = visibility_map.get(ocr_engine_value, [True, False, False, False, False])

            return [
                gr.update(visible=visibilities[0]),  # easyocr_group
                gr.update(visible=visibilities[1]),  # tesseract_group
                gr.update(visible=visibilities[2]),  # tesseract_cli_group
                gr.update(visible=visibilities[3]),  # ocr_mac_group
                gr.update(visible=visibilities[4]),  # rapidocr_group
            ]

        demo.load(
            fn=reload_page,
            outputs=[task_list_display, clear_all_btn]
        )

        # Task List Events
        add_task_btn.click(
            fn=open_new_task,
            outputs=[task_editor_column, editor_status, engine_selector, profile_group, config_editor]
        )

        # Task Editor Events
        def engine_change_handler(engine):
            """Handle engine selection change - show profile group and hide config editor."""
            profile_group_update, profile_selector_update = toggle_profile_group(engine)
            return (
                profile_group_update,     # profile_group
                profile_selector_update,  # profile_selector
                gr.update(visible=False), # config_editor (hide settings)
                gr.update(visible=False), # profile_status (hide status message)
            )

        engine_selector.change(
            fn=engine_change_handler,
            inputs=[engine_selector],
            outputs=[profile_group, profile_selector, config_editor, profile_status]
        )

        profile_selector.change(
            fn=profile_selected_handler,
            inputs=[engine_selector, profile_selector],
            outputs=[profile_status]
        )

        # TODO: Wire up OCR engine dropdown for Docling config
        # This needs to be reimplemented with dynamic config system
        # if ocr_engine_dropdown is not None:
        #     ocr_engine_dropdown.change(
        #         fn=ocr_engine_change_handler,
        #         inputs=[ocr_engine_dropdown],
        #         outputs=[easyocr_group, tesseract_group, tesseract_cli_group, ocr_mac_group, rapidocr_group]
        #     )


# Helper to get all config components in order
        def get_all_config_components_flat():
            all_comps = []
            for eng in sorted(config_areas.keys()):
                all_comps.extend(component_lists[eng])
            return all_comps
        
        all_config_components = get_all_config_components_flat()
        all_config_areas_list = [config_areas[eng] for eng in sorted(config_areas.keys())]

        refresh_profiles_btn.click(
            fn=refresh_profile_list,
            inputs=[engine_selector],
            outputs=[profile_selector]
        )

        edit_profile_btn.click(
            fn=edit_profile_handler,
            inputs=[engine_selector, profile_selector],
            outputs=[config_editor, config_name_input] + all_config_areas_list + all_config_components
        )

        new_profile_btn.click(
            fn=new_profile_handler,
            inputs=[engine_selector],
            outputs=[config_editor, config_name_input] + all_config_areas_list + all_config_components
        )

        save_profile_btn.click(
            fn=save_profile_handler,
            inputs=[engine_selector, config_name_input] + all_config_components,
            outputs=[config_editor, profile_status, profile_selector]
        )

        cancel_config_btn.click(
            fn=cancel_config_handler,
            outputs=[config_editor]
        )

        delete_profile_btn.click(
            fn=delete_profile_handler,
            inputs=[engine_selector, profile_selector],
            outputs=[profile_status, profile_selector]
        )

        save_task_btn.click(
            fn=save_task,
            inputs=[engine_selector, profile_selector],
            outputs=[task_list_display, task_editor_column, editor_status, clear_all_btn]
        )

        cancel_editor_btn.click(
            fn=hide_task_editor,
            outputs=[task_editor_column]
        )

        hidden_delete_trigger.click(
            fn=delete_task_handler,
            inputs=[hidden_task_index],
            outputs=[task_list_display, clear_all_btn]
        )

        clear_all_btn.click(
            fn=clear_all_tasks_handler,
            outputs=[task_list_display, clear_all_btn]
        )

        # Extraction Events
        run_extraction_btn.click(
            fn=run_extraction_handler,
            inputs=[file_upload],
            outputs=[
                extraction_results_section,
                results_table,
                markdown_preview_accordion,
                comparison_view,
                document_selector,
                validation_section,
                gt_document_selector,
                val_document_selector,
                val_extractor_selector,
                val_metric_selector,
                extraction_status
            ]
        )

        document_selector.change(
            fn=update_comparison,
            inputs=[document_selector, view_mode],
            outputs=[comparison_view]
        )

        # Validation Events
        gt_file_upload.change(
            fn=upload_ground_truth_handler,
            inputs=[gt_file_upload, gt_document_selector],
            outputs=[gt_upload_status, gt_file_upload, gt_uploaded_list]
        )

        run_validation_btn.click(
            fn=run_validation_handler,
            inputs=[val_document_selector, val_extractor_selector, val_metric_selector],
            outputs=[validation_status, validation_results_view, validation_results_section]
        )

        clear_validation_btn.click(
            fn=clear_validation_handler,
            outputs=[validation_status, validation_results_view, validation_results_section]
        )

        view_mode.change(
            fn=update_comparison,
            inputs=[document_selector, view_mode],
            outputs=[comparison_view]
        )

        download_zip_btn.click(
            fn=lambda: gr.update(value=ui.get_download_zip(), visible=True) if ui.get_download_zip() else None,
            outputs=[download_zip_file]
        )

        download_report_btn.click(
            fn=lambda: gr.update(value=ui.get_comparison_report(), visible=True) if ui.get_comparison_report() else None,
            outputs=[download_report_file]
        )

    return demo


if __name__ == "__main__":
    print("\n🚀 Starting Benchmarkdown UI (Redesigned)...")
    demo = create_app()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )
