#!/usr/bin/env python3
"""
Benchmarkdown - Redesigned UI with intuitive two-column workflow.

Layout:
- Left column (35%): Task List - always visible, primary focus
- Right column (65%): Task Editor - appears on Add/Edit
- Results view: Full-width, replaces both columns
"""

import os
import json
import asyncio
import gradio as gr
from benchmarkdown.ui import BenchmarkUI
from benchmarkdown.docling import DoclingExtractor
from benchmarkdown.config import DoclingConfig
from benchmarkdown.config_ui import (
    create_gradio_component_from_field,
    build_config_from_ui_values,
    DOCLING_BASIC_FIELDS,
    DOCLING_ADVANCED_FIELDS
)
from benchmarkdown.profile_manager import ProfileManager

# Check available extractors
has_docling = False
has_textract = False

try:
    from benchmarkdown.docling import DoclingExtractor
    has_docling = True
    print("✓ Docling extractor available")
except ImportError as e:
    print(f"⚠️  Docling not available: {e}")

try:
    from benchmarkdown.textract import TextractExtractor
    from textractor.data.constants import TextractFeatures
    s3_bucket = os.environ.get("TEXTRACT_S3_BUCKET", "your-bucket-name")
    if s3_bucket != "your-bucket-name":
        has_textract = True
        print("✓ AWS Textract extractor available")
    else:
        print("⚠️  AWS Textract not configured (set TEXTRACT_S3_BUCKET)")
except ImportError:
    print("⚠️  AWS Textract not available")

if not has_docling and not has_textract:
    print("\n❌ No extractors available! Install with: uv sync --group docling")
    exit(1)


def create_app():
    """Create the redesigned Gradio interface."""
    ui = BenchmarkUI()
    profile_manager = ProfileManager()

    # State for extractor queue - list of dicts with keys: engine, config_name, extractor, cost
    extractor_queue = []

    # Queue persistence file
    QUEUE_FILE = ".task_queue.json"

    # Load existing queue from disk if it exists
    def load_queue_from_disk():
        """Load task queue from disk."""
        if os.path.exists(QUEUE_FILE):
            try:
                with open(QUEUE_FILE, 'r') as f:
                    saved_queue = json.load(f)
                    for task_data in saved_queue:
                        # Recreate extractor from config
                        engine = task_data['engine']
                        config_name = task_data['config_name']
                        config_dict = task_data['config_dict']

                        if engine == "Docling":
                            config = build_config_from_ui_values(DoclingConfig, config_dict)
                            extractor = DoclingExtractor(config=config)
                            full_name = f"Docling ({config_name})"

                            task = {
                                'engine': engine,
                                'config_name': config_name,
                                'extractor': extractor,
                                'cost': None,
                                'config_dict': config_dict
                            }
                            extractor_queue.append(task)
                            ui.extractors[full_name] = extractor
                print(f"✓ Loaded {len(extractor_queue)} tasks from disk")
            except Exception as e:
                print(f"⚠️  Failed to load queue: {e}")

    def save_queue_to_disk():
        """Save task queue to disk (without extractor objects)."""
        try:
            saved_queue = []
            for task in extractor_queue:
                saved_queue.append({
                    'engine': task['engine'],
                    'config_name': task['config_name'],
                    'cost': task['cost'],
                    'config_dict': task['config_dict']
                })
            with open(QUEUE_FILE, 'w') as f:
                json.dump(saved_queue, f, indent=2)
        except Exception as e:
            print(f"⚠️  Failed to save queue: {e}")

    # Load queue on app creation
    load_queue_from_disk()

    # State for editing - None or index of task being edited
    editing_task_index = [None]  # Use list to make it mutable in closures

    def generate_task_list_html():
        """Generate HTML for the task list display with inline delete buttons."""
        if not extractor_queue:
            return "<p style='opacity: 0.6; padding: 20px; text-align: center;'>No tasks configured yet.<br>Click 'Add Task' to begin.</p>"

        html = "<div class='task-list-container' style='font-family: system-ui, sans-serif;'>"
        for i, task in enumerate(extractor_queue):
            html += f"""
            <div class='task-card' style='border: 1px solid rgba(128, 128, 128, 0.3); padding: 12px; margin: 8px 0; border-radius: 6px; background: rgba(128, 128, 128, 0.1); display: flex; align-items: center;'>
                <div style='background: #4CAF50; color: white; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; margin-right: 12px; font-weight: bold; flex-shrink: 0;'>
                    {i+1}
                </div>
                <div style='flex-grow: 1;'>
                    <strong style='font-size: 1.1em; color: var(--body-text-color, inherit);'>{task['engine']}</strong>
                    <br>
                    <span style='opacity: 0.7; font-size: 0.9em;'>{task['config_name']}</span>
                </div>
                <button
                    onclick='deleteTask({i+1})'
                    style='background: #f44336; color: white; border: none; border-radius: 4px; padding: 6px 12px; cursor: pointer; font-size: 0.9em; margin-left: 8px; flex-shrink: 0;'
                    onmouseover='this.style.background="#d32f2f"'
                    onmouseout='this.style.background="#f44336"'
                    title='Delete this task'
                >
                    🗑️ Delete
                </button>
            </div>
            """
        html += "</div>"
        return html

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
        # MAIN VIEW: Two-column layout (Task List | Task Editor)
        # ============================================================
        with gr.Row() as main_view:
            # LEFT COLUMN: Task List (always visible)
            with gr.Column(scale=1) as task_list_column:
                gr.Markdown("## 📋 Extraction Tasks")

                with gr.Row():
                    add_task_btn = gr.Button("➕ Add Task", variant="primary", size="sm")
                    launch_btn = gr.Button("🚀 Launch Extraction", variant="secondary", size="sm")

                task_list_display = gr.HTML(
                    value=generate_task_list_html()
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

                # Clear All button - shown when tasks exist
                with gr.Row(visible=bool(extractor_queue)) as delete_controls:
                    clear_all_btn = gr.Button("🗑️ Clear All", size="sm", variant="stop", min_width=120)

            # RIGHT COLUMN: Task Editor (hidden by default)
            with gr.Column(scale=2, visible=False) as task_editor_column:
                gr.Markdown("## ⚙️ Task Editor")

                editor_status = gr.Markdown("*Select an extractor engine and profile*")

                # Step 1: Select Engine
                with gr.Group():
                    gr.Markdown("### 1. Select Extractor Engine")

                    extractor_engines = []
                    if has_docling:
                        extractor_engines.append("Docling")
                    if has_textract:
                        extractor_engines.append("AWS Textract")

                    engine_selector = gr.Dropdown(
                        choices=extractor_engines,
                        label="Extractor Engine",
                        value=None,
                        interactive=True
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

                    # Docling configuration options
                    with gr.Column(visible=False) as docling_config_area:
                        docling_components = []

                        with gr.Group():
                            gr.Markdown("#### Basic Options")
                            for field_name in DOCLING_BASIC_FIELDS:
                                if field_name not in DoclingConfig.model_fields:
                                    continue
                                field_info = DoclingConfig.model_fields[field_name]
                                field_type = field_info.annotation
                                component, _ = create_gradio_component_from_field(
                                    field_name, field_info, field_type
                                )
                                docling_components.append(component)

                        with gr.Accordion("Advanced Options", open=False):
                            for field_name in DOCLING_ADVANCED_FIELDS:
                                if field_name not in DoclingConfig.model_fields:
                                    continue
                                field_info = DoclingConfig.model_fields[field_name]
                                field_type = field_info.annotation
                                component, _ = create_gradio_component_from_field(
                                    field_name, field_info, field_type
                                )
                                docling_components.append(component)

                    # Textract configuration options (placeholder)
                    with gr.Column(visible=False) as textract_config_area:
                        gr.Markdown("*AWS Textract configuration options coming soon*")

                    # Configuration editor action buttons
                    with gr.Row():
                        save_profile_btn = gr.Button("💾 Save Profile", variant="primary", size="sm")
                        cancel_config_btn = gr.Button("✖️ Cancel", size="sm")

                # Save Task button (always visible at bottom of editor)
                gr.Markdown("---")
                save_task_btn = gr.Button("✅ Add Task to Queue", variant="primary", size="lg")
                cancel_editor_btn = gr.Button("✖️ Cancel", size="lg")

        # ============================================================
        # RESULTS VIEW: Full-width (hidden by default)
        # ============================================================
        with gr.Column(visible=False) as results_view:
            with gr.Row():
                back_to_tasks_btn = gr.Button("← Back to Tasks", size="sm")

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

            gr.Markdown("---")
            gr.Markdown("## 📊 Extraction Results")

            results_table = gr.HTML(
                value="<p style='color: #666;'>Results will appear here after extraction completes.</p>"
            )

            # Results controls (hidden initially)
            with gr.Row(visible=False) as results_controls:
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

            # Download buttons
            with gr.Row(visible=False) as download_row:
                download_zip_btn = gr.Button("📦 Download All (ZIP)", size="sm")
                download_report_btn = gr.Button("📊 Generate Report (HTML)", size="sm")

            download_zip_file = gr.File(label="ZIP Download", visible=False)
            download_report_file = gr.File(label="Report Download", visible=False)

            # Comparison view
            comparison_view = gr.HTML(value="")

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
                    updates.extend([gr.update()] * len(docling_components))

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

        def edit_profile_handler(engine, selected_profile):
            """Open config editor to edit the selected profile."""
            if not selected_profile:
                return [gr.update(visible=False)] + [gr.update()] * (2 + len(docling_components))

            try:
                profile = profile_manager.load_profile(selected_profile)

                if profile["engine"] != engine:
                    return [gr.update(visible=False)] + [gr.update()] * (2 + len(docling_components))

                config_data = profile["config_data"]
                current_profile_data[0] = config_data

                # Open config editor with profile data
                updates = [
                    gr.update(visible=True),  # config_editor
                    gr.update(value=selected_profile),  # config_name_input
                ]

                # Show appropriate config area and load values
                if engine == "Docling":
                    updates.extend([
                        gr.update(visible=True),  # docling_config_area
                        gr.update(visible=False),  # textract_config_area
                    ])

                    all_fields = DOCLING_BASIC_FIELDS + DOCLING_ADVANCED_FIELDS
                    for field_name in all_fields:
                        if field_name in config_data:
                            updates.append(gr.update(value=config_data[field_name]))
                        else:
                            updates.append(gr.update())
                else:
                    updates.extend([
                        gr.update(visible=False),  # docling_config_area
                        gr.update(visible=True),  # textract_config_area
                    ])
                    updates.extend([gr.update()] * len(docling_components))

                return updates

            except Exception as e:
                return [gr.update(visible=False)] + [gr.update()] * (2 + len(docling_components))

        def new_profile_handler(engine):
            """Open config editor for creating a new profile."""
            if not engine:
                return [gr.update(visible=False)] + [gr.update()] * (2 + len(docling_components))

            current_profile_data[0] = None  # Clear current profile

            # Open config editor with empty/default values
            updates = [
                gr.update(visible=True),  # config_editor
                gr.update(value=""),  # config_name_input (empty for new)
            ]

            # Show appropriate config area with defaults
            if engine == "Docling":
                updates.extend([
                    gr.update(visible=True),  # docling_config_area
                    gr.update(visible=False),  # textract_config_area
                ])

                # Load default values for all fields
                all_fields = DOCLING_BASIC_FIELDS + DOCLING_ADVANCED_FIELDS
                for field_name in all_fields:
                    if field_name in DoclingConfig.model_fields:
                        default_value = DoclingConfig.model_fields[field_name].default
                        updates.append(gr.update(value=default_value))
                    else:
                        updates.append(gr.update())
            else:
                updates.extend([
                    gr.update(visible=False),  # docling_config_area
                    gr.update(visible=True),  # textract_config_area
                ])
                updates.extend([gr.update()] * len(docling_components))

            return updates

        def cancel_config_handler():
            """Close config editor without saving."""
            return gr.update(visible=False)  # Hide config_editor

        def save_task(engine, selected_profile):
            """Add current task (from loaded profile) to queue."""
            if not engine:
                return (
                    gr.update(value=generate_task_list_html()),
                    gr.update(visible=False),  # hide editor
                    "❌ Please select an extractor engine",
                    gr.update(visible=bool(extractor_queue))
                )

            # Use currently loaded profile data or ask user to select
            if current_profile_data[0] is None:
                return (
                    gr.update(value=generate_task_list_html()),
                    gr.update(visible=True),  # keep editor open
                    "❌ Please select a profile or create a new one",
                    gr.update(visible=bool(extractor_queue))
                )

            if not selected_profile:
                return (
                    gr.update(value=generate_task_list_html()),
                    gr.update(visible=True),  # keep editor open
                    "❌ Please select a profile",
                    gr.update(visible=bool(extractor_queue))
                )

            if engine == "Docling":
                # Build config from current profile data
                config = build_config_from_ui_values(DoclingConfig, current_profile_data[0])

                # Create extractor
                extractor = DoclingExtractor(config=config)
                full_name = f"Docling ({selected_profile})"

                task_data = {
                    'engine': 'Docling',
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
                    old_full_name = f"Docling ({old_name})"
                    if old_full_name in ui.extractors:
                        del ui.extractors[old_full_name]
                    ui.register_extractor(full_name, extractor, cost_per_page=None)
                    message = f"✓ Updated task: {selected_profile}"
                else:
                    # Add new task
                    extractor_queue.append(task_data)
                    ui.register_extractor(full_name, extractor, cost_per_page=None)
                    message = f"✓ Added task: {selected_profile}"

                # Save queue to disk
                save_queue_to_disk()

                editing_task_index[0] = None
                current_profile_data[0] = None

                # Show delete controls if we have tasks
                return (
                    gr.update(value=generate_task_list_html()),
                    gr.update(visible=False),  # hide editor
                    message,
                    gr.update(visible=True)  # show delete_controls
                )

            elif engine == "AWS Textract":
                return (
                    gr.update(value=generate_task_list_html()),
                    gr.update(visible=True),
                    "⚠️  Textract configuration not yet implemented",
                    gr.update(visible=bool(extractor_queue))
                )

            return (
                gr.update(value=generate_task_list_html()),
                gr.update(visible=True),
                "❌ Unknown engine",
                gr.update(visible=bool(extractor_queue))
            )

        def delete_task_handler(task_number):
            """Delete a task from the queue by its number."""
            if task_number is None or not extractor_queue:
                return (
                    gr.update(value=generate_task_list_html()),
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
                    save_queue_to_disk()

                    return (
                        gr.update(value=generate_task_list_html()),
                        gr.update(visible=bool(extractor_queue))  # Hide if queue is now empty
                    )
            except (ValueError, IndexError):
                pass

            return (
                gr.update(value=generate_task_list_html()),
                gr.update(visible=bool(extractor_queue))
            )

        def clear_all_tasks_handler():
            """Clear all tasks from the queue."""
            # Clear the queue
            extractor_queue.clear()
            # Clear UI registry
            ui.extractors.clear()

            # Save queue to disk
            save_queue_to_disk()

            return (
                gr.update(value=generate_task_list_html()),
                gr.update(visible=False)  # Hide delete controls
            )

        def edit_task_handler(selected_task):
            """Open editor to edit an existing task based on dropdown selection."""
            if not selected_task or not extractor_queue:
                # Return defaults if error
                return tuple([gr.update()] * (7 + len(docling_components)))

            try:
                # Extract index from dropdown value like "1. Docling - Fast Mode"
                task_index = int(selected_task.split('.')[0]) - 1

                if 0 <= task_index < len(extractor_queue):
                    return show_task_editor(is_new=False, task_index=task_index)
            except (ValueError, IndexError):
                pass

            # Return defaults if error
            return tuple([gr.update()] * (7 + len(docling_components)))

        def toggle_profile_group(engine):
            """Show profile group when engine is selected."""
            if engine:
                # Refresh profiles for selected engine
                profiles = profile_manager.list_profiles(engine=engine)
                profile_names = [p["profile_name"] for p in profiles]
                return gr.update(visible=True), gr.update(choices=profile_names, value=None)
            return gr.update(visible=False), gr.update(choices=[], value=None)

        def show_config_area(engine):
            """Show appropriate config area and hide profile status."""
            if engine == "Docling":
                return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)
            elif engine == "AWS Textract":
                return gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)
            return gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

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
                return [gr.update(visible=True, value="❌ Please select a profile to load")] + [gr.update()] * len(docling_components) + [gr.update()]

            try:
                profile = profile_manager.load_profile(selected_profile)

                # Verify engine matches
                if profile["engine"] != engine:
                    return [gr.update(visible=True, value=f"❌ Profile is for {profile['engine']}, but {engine} is selected")] + [gr.update()] * len(docling_components) + [gr.update()]

                # Update config name
                config_name = profile["profile_name"]

                # Prepare updates for all config components
                updates = [gr.update(visible=True, value=f"✓ Loaded profile: {config_name}")]

                if engine == "Docling":
                    config_data = profile["config_data"]
                    all_fields = DOCLING_BASIC_FIELDS + DOCLING_ADVANCED_FIELDS

                    # Update each component with the loaded value
                    for field_name in all_fields:
                        if field_name in config_data:
                            updates.append(gr.update(value=config_data[field_name]))
                        else:
                            updates.append(gr.update())
                else:
                    updates.extend([gr.update()] * len(docling_components))

                # Update config name field
                updates.append(gr.update(value=config_name))

                return updates

            except FileNotFoundError:
                return [gr.update(visible=True, value=f"❌ Profile '{selected_profile}' not found")] + [gr.update()] * len(docling_components) + [gr.update()]
            except Exception as e:
                return [gr.update(visible=True, value=f"❌ Error loading profile: {e}")] + [gr.update()] * len(docling_components) + [gr.update()]

        def save_profile_handler(engine, config_name, *config_values):
            """Save current configuration as a profile and close config editor."""
            if not config_name:
                return (
                    gr.update(visible=False),  # Don't close editor yet, show error in status
                    gr.update(value="❌ Please enter a profile name", visible=True),
                    gr.update(),  # profile_selector
                )

            try:
                if engine == "Docling":
                    all_fields = DOCLING_BASIC_FIELDS + DOCLING_ADVANCED_FIELDS
                    config_data = {field: value for field, value in zip(all_fields, config_values)}

                    # Save profile
                    filepath = profile_manager.save_profile(
                        engine=engine,
                        profile_name=config_name,
                        config_data=config_data
                    )

                    # Update current profile data
                    current_profile_data[0] = config_data

                    # Refresh profile list
                    profiles = profile_manager.list_profiles(engine=engine)
                    profile_names = [p["profile_name"] for p in profiles]

                    return (
                        gr.update(visible=False),  # Close config_editor
                        gr.update(value=f"✅ Saved profile: **{config_name}** - Ready to add to queue", visible=True),  # profile_status
                        gr.update(choices=profile_names, value=config_name)  # profile_selector with new profile selected
                    )
                else:
                    return (
                        gr.update(visible=True),  # Keep editor open
                        gr.update(value="⚠️  Profile saving not yet implemented for this engine", visible=True),
                        gr.update()
                    )

            except Exception as e:
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

        def show_results_view():
            """Switch to results view."""
            if not extractor_queue:
                return (
                    gr.update(visible=True),  # main_view stays visible
                    gr.update(visible=False),  # results_view hidden
                    "<p style='color: red;'>❌ No tasks configured. Please add at least one extraction task.</p>"
                )

            return (
                gr.update(visible=False),  # main_view hidden
                gr.update(visible=True),  # results_view visible
                "<p>Upload documents and click 'Run Extraction' to begin.</p>"
            )

        def back_to_tasks_handler():
            """Switch back to task management view."""
            return (
                gr.update(visible=True),  # main_view
                gr.update(visible=False),  # results_view
            )

        def run_extraction_handler(files):
            """Process documents with all queued extractors."""
            if not files:
                return (
                    "<p style='color: red;'>❌ No files uploaded.</p>",
                    gr.update(visible=False),  # results_controls
                    gr.update(visible=False),  # download_row
                    "",  # comparison_view
                    gr.update(choices=[], value=None)  # document_selector
                )

            # Get all extractor names from queue
            extractor_names = [f"{task['engine']} ({task['config_name']})" for task in extractor_queue]

            # Process documents
            result = asyncio.run(ui.process_documents(files, extractor_names))

            # Get filenames for dropdown
            filenames = list(ui.results.keys()) if ui.results else []
            first_filename = filenames[0] if filenames else None

            # Generate comparison view
            comparison = ""
            if first_filename:
                comparison = ui.generate_comparison_view_tabbed(first_filename)

            return (
                result[0],  # results_table
                gr.update(visible=True),  # results_controls
                gr.update(visible=True),  # download_row
                comparison,  # comparison_view
                gr.update(choices=filenames, value=first_filename)  # document_selector
            )

        def update_comparison(filename, view_mode_val):
            """Update comparison view."""
            if not filename:
                return ""
            if view_mode_val == "Side-by-Side":
                return ui.generate_comparison_view_sidebyside(filename)
            else:
                return ui.generate_comparison_view_tabbed(filename)

        # ============================================================
        # Wire up events
        # ============================================================

        # Page Load Event - refresh display on page load
        def reload_page():
            """Reload queue from disk and update display."""
            # Clear current queue and reload from disk to ensure consistency
            extractor_queue.clear()
            ui.extractors.clear()
            load_queue_from_disk()

            return (
                gr.update(value=generate_task_list_html()),
                gr.update(visible=bool(extractor_queue))
            )

        demo.load(
            fn=reload_page,
            outputs=[task_list_display, delete_controls]
        )

        # Task List Events
        add_task_btn.click(
            fn=open_new_task,
            outputs=[task_editor_column, editor_status, engine_selector, profile_group, config_editor]
        )

        launch_btn.click(
            fn=show_results_view,
            outputs=[main_view, results_view, results_table]
        )

        # Task Editor Events
        engine_selector.change(
            fn=lambda engine: (
                *toggle_profile_group(engine),
            ),
            inputs=[engine_selector],
            outputs=[profile_group, profile_selector]
        )

        profile_selector.change(
            fn=profile_selected_handler,
            inputs=[engine_selector, profile_selector],
            outputs=[profile_status]
        )

        refresh_profiles_btn.click(
            fn=refresh_profile_list,
            inputs=[engine_selector],
            outputs=[profile_selector]
        )

        edit_profile_btn.click(
            fn=edit_profile_handler,
            inputs=[engine_selector, profile_selector],
            outputs=[config_editor, config_name_input, docling_config_area, textract_config_area] + docling_components
        )

        new_profile_btn.click(
            fn=new_profile_handler,
            inputs=[engine_selector],
            outputs=[config_editor, config_name_input, docling_config_area, textract_config_area] + docling_components
        )

        save_profile_btn.click(
            fn=save_profile_handler,
            inputs=[engine_selector, config_name_input] + docling_components,
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
            outputs=[task_list_display, task_editor_column, editor_status, delete_controls]
        )

        cancel_editor_btn.click(
            fn=hide_task_editor,
            outputs=[task_editor_column]
        )

        hidden_delete_trigger.click(
            fn=delete_task_handler,
            inputs=[hidden_task_index],
            outputs=[task_list_display, delete_controls]
        )

        clear_all_btn.click(
            fn=clear_all_tasks_handler,
            outputs=[task_list_display, delete_controls]
        )

        # Results View Events
        back_to_tasks_btn.click(
            fn=back_to_tasks_handler,
            outputs=[main_view, results_view]
        )

        run_extraction_btn.click(
            fn=run_extraction_handler,
            inputs=[file_upload],
            outputs=[results_table, results_controls, download_row, comparison_view, document_selector]
        )

        document_selector.change(
            fn=update_comparison,
            inputs=[document_selector, view_mode],
            outputs=[comparison_view]
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
