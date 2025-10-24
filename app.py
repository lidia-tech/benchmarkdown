#!/usr/bin/env python3
"""
Benchmarkdown - Redesigned UI with intuitive two-column workflow.

Layout:
- Left column (35%): Task List - always visible, primary focus
- Right column (65%): Task Editor - appears on Add/Edit
- Results view: Full-width, replaces both columns
"""

import os
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

    # State for editing - None or index of task being edited
    editing_task_index = [None]  # Use list to make it mutable in closures

    with gr.Blocks(title="Benchmarkdown - Document Extraction Comparison") as demo:
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
                    value="<p style='color: #666; padding: 20px; text-align: center;'>No tasks configured yet.<br>Click 'Add Task' to begin.</p>"
                )

                # Task controls
                with gr.Group(visible=False) as task_controls:
                    task_selector = gr.Dropdown(
                        label="Select Task",
                        choices=[],
                        interactive=True
                    )
                    with gr.Row():
                        edit_task_btn = gr.Button("✏️ Edit", size="sm", variant="secondary")
                        delete_task_btn = gr.Button("🗑️ Delete", size="sm", variant="stop")

            # RIGHT COLUMN: Task Editor (hidden by default)
            with gr.Column(scale=2, visible=False) as task_editor_column:
                gr.Markdown("## ⚙️ Task Editor")

                editor_status = gr.Markdown("*Configure a new extraction task*")

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

                    config_name_input = gr.Textbox(
                        label="Task Name",
                        placeholder="e.g., 'Fast Mode', 'High Quality', etc.",
                        info="Used to identify this task in the queue and when saving as a profile",
                        value=""
                    )

                # Step 2: Profile Management (hidden until engine selected)
                with gr.Group(visible=False) as profile_group:
                    gr.Markdown("### 2. Profile Management")

                    with gr.Row():
                        profile_selector = gr.Dropdown(
                            label="Load Existing Profile",
                            choices=[],
                            interactive=True,
                            scale=3
                        )
                        refresh_profiles_btn = gr.Button("🔄", size="sm", scale=0, min_width=50)

                    with gr.Row():
                        load_profile_btn = gr.Button("📂 Load Profile", size="sm")
                        save_profile_btn = gr.Button("💾 Save Profile", size="sm")
                        delete_profile_btn = gr.Button("🗑️ Delete Profile", size="sm")
                        create_new_btn = gr.Button("✨ Create New Profile", size="sm", variant="primary")

                    profile_status = gr.Textbox(
                        label="Profile Status",
                        value="",
                        interactive=False,
                        visible=False
                    )

                # Step 3: Configuration Options (hidden until needed)
                with gr.Column(visible=False) as docling_config_area:
                    gr.Markdown("### 3. Configuration Options")

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

                with gr.Column(visible=False) as textract_config_area:
                    gr.Markdown("### 3. Configuration Options")
                    gr.Markdown("*AWS Textract configuration options coming soon*")

                # Editor Action Buttons
                with gr.Row():
                    save_task_btn = gr.Button("💾 Save Task", variant="primary", size="lg")
                    cancel_btn = gr.Button("✖️ Cancel", size="lg")

        # ============================================================
        # RESULTS VIEW: Full-width (hidden by default)
        # ============================================================
        with gr.Column(visible=False) as results_view:
            with gr.Row():
                back_to_tasks_btn = gr.Button("← Back to Tasks", size="sm")

            gr.Markdown("## 🚀 Extraction Results")

            file_upload = gr.File(
                label="Upload Documents (PDF, DOCX, etc.)",
                file_count="multiple",
                file_types=[".pdf", ".docx", ".doc", ".txt"]
            )

            run_extraction_btn = gr.Button(
                "▶️ Run Extraction on Uploaded Documents",
                variant="primary",
                size="lg"
            )

            results_table = gr.HTML(
                value="<p>Upload documents and click 'Run Extraction' to begin.</p>"
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

        def generate_task_list_html():
            """Generate HTML for the task list display."""
            if not extractor_queue:
                return "<p style='color: #666; padding: 20px; text-align: center;'>No tasks configured yet.<br>Click 'Add Task' to begin.</p>"

            html = "<div style='font-family: system-ui, sans-serif;'>"
            for i, task in enumerate(extractor_queue):
                html += f"""
                <div style='border: 1px solid #ddd; padding: 12px; margin: 8px 0; border-radius: 6px; background: #f9f9f9;'>
                    <strong style='font-size: 1.1em;'>{task['engine']}</strong>
                    <br>
                    <span style='color: #666; font-size: 0.9em;'>{task['config_name']}</span>
                </div>
                """
            html += "</div>"
            return html

        def get_task_choices():
            """Get task choices for dropdown."""
            return [f"{i+1}. {task['engine']} - {task['config_name']}" for i, task in enumerate(extractor_queue)]

        def show_task_editor(is_new=True, task_index=None):
            """Show the task editor, optionally loading an existing task."""
            editing_task_index[0] = task_index

            if is_new:
                status = "*Configure a new extraction task*"
                return (
                    gr.update(visible=True),  # task_editor_column
                    status,  # editor_status
                    gr.update(value=None),  # engine_selector
                    gr.update(value=""),  # config_name_input
                    gr.update(visible=False),  # profile_group
                    gr.update(visible=False),  # docling_config_area
                    gr.update(visible=False),  # textract_config_area
                )
            else:
                # Load existing task for editing
                task = extractor_queue[task_index]
                status = f"*Editing task: {task['config_name']}*"

                # Prepare config values for UI
                updates = [
                    gr.update(visible=True),  # task_editor_column
                    status,  # editor_status
                    gr.update(value=task['engine']),  # engine_selector
                    gr.update(value=task['config_name']),  # config_name_input
                    gr.update(visible=True),  # profile_group (show for selected engine)
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
            return gr.update(visible=False)

        def open_new_task():
            """Open editor for new task."""
            return show_task_editor(is_new=True)

        def save_task(engine, config_name, *config_values):
            """Save current task (new or edited) to queue."""
            if not engine:
                return (
                    generate_task_list_html(),
                    gr.update(visible=False),  # hide editor
                    "❌ Please select an extractor engine",
                    gr.update(visible=bool(extractor_queue), choices=get_task_choices() if extractor_queue else [])
                )

            if not config_name:
                return (
                    generate_task_list_html(),
                    gr.update(visible=True),  # keep editor open
                    "❌ Please enter a task name",
                    gr.update(visible=bool(extractor_queue), choices=get_task_choices() if extractor_queue else [])
                )

            if engine == "Docling":
                # Build config
                all_fields = DOCLING_BASIC_FIELDS + DOCLING_ADVANCED_FIELDS
                ui_values = {field: value for field, value in zip(all_fields, config_values)}
                config = build_config_from_ui_values(DoclingConfig, ui_values)

                # Create extractor
                extractor = DoclingExtractor(config=config)
                full_name = f"Docling ({config_name})"

                task_data = {
                    'engine': 'Docling',
                    'config_name': config_name,
                    'extractor': extractor,
                    'cost': None,
                    'config_dict': ui_values
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
                    message = f"✓ Updated task: {config_name}"
                else:
                    # Add new task
                    extractor_queue.append(task_data)
                    ui.register_extractor(full_name, extractor, cost_per_page=None)
                    message = f"✓ Added task: {config_name}"

                editing_task_index[0] = None

                # Show task controls if we have tasks
                task_choices = get_task_choices()
                return (
                    generate_task_list_html(),
                    gr.update(visible=False),  # hide editor
                    message,
                    gr.update(visible=True, choices=task_choices, value=None)  # show task_controls with updated dropdown
                )

            elif engine == "AWS Textract":
                return (
                    generate_task_list_html(),
                    gr.update(visible=True),
                    "⚠️  Textract configuration not yet implemented",
                    gr.update(visible=bool(extractor_queue), choices=get_task_choices() if extractor_queue else [])
                )

            return (
                generate_task_list_html(),
                gr.update(visible=True),
                "❌ Unknown engine",
                gr.update(visible=bool(extractor_queue), choices=get_task_choices() if extractor_queue else [])
            )

        def delete_task_handler(selected_task):
            """Delete a task from the queue based on dropdown selection."""
            if not selected_task or not extractor_queue:
                return (
                    generate_task_list_html(),
                    gr.update(visible=bool(extractor_queue), choices=get_task_choices() if extractor_queue else [], value=None)
                )

            try:
                # Extract index from dropdown value like "1. Docling - Fast Mode"
                task_index = int(selected_task.split('.')[0]) - 1

                if 0 <= task_index < len(extractor_queue):
                    task = extractor_queue[task_index]
                    full_name = f"{task['engine']} ({task['config_name']})"

                    # Remove from queue and UI registry
                    extractor_queue.pop(task_index)
                    if full_name in ui.extractors:
                        del ui.extractors[full_name]

                    # Update task choices
                    task_choices = get_task_choices() if extractor_queue else []
                    return (
                        generate_task_list_html(),
                        gr.update(visible=bool(extractor_queue), choices=task_choices, value=None)
                    )
            except (ValueError, IndexError):
                pass

            return (
                generate_task_list_html(),
                gr.update(visible=bool(extractor_queue), choices=get_task_choices() if extractor_queue else [], value=None)
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
            """Save current configuration as a profile."""
            if not config_name:
                return gr.update(visible=True, value="❌ Please enter a task name to save as profile"), gr.update()

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

                    # Refresh profile list
                    profiles = profile_manager.list_profiles(engine=engine)
                    profile_names = [p["profile_name"] for p in profiles]

                    return (
                        gr.update(visible=True, value=f"✓ Saved profile: {config_name}"),
                        gr.update(choices=profile_names, value=config_name)
                    )
                else:
                    return (
                        gr.update(visible=True, value="⚠️  Profile saving not yet implemented for this engine"),
                        gr.update()
                    )

            except Exception as e:
                return gr.update(visible=True, value=f"❌ Error saving profile: {e}"), gr.update()

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

        # Task List Events
        add_task_btn.click(
            fn=open_new_task,
            outputs=[task_editor_column, editor_status, engine_selector, config_name_input,
                    profile_group, docling_config_area, textract_config_area]
        )

        launch_btn.click(
            fn=show_results_view,
            outputs=[main_view, results_view, results_table]
        )

        # Task Editor Events
        engine_selector.change(
            fn=lambda engine: (
                *toggle_profile_group(engine),
                *show_config_area(engine)
            ),
            inputs=[engine_selector],
            outputs=[profile_group, profile_selector, docling_config_area, textract_config_area, profile_status]
        )

        create_new_btn.click(
            fn=show_config_area,
            inputs=[engine_selector],
            outputs=[docling_config_area, textract_config_area, profile_status]
        )

        refresh_profiles_btn.click(
            fn=refresh_profile_list,
            inputs=[engine_selector],
            outputs=[profile_selector]
        )

        load_profile_btn.click(
            fn=load_profile_handler,
            inputs=[engine_selector, profile_selector],
            outputs=[profile_status] + docling_components + [config_name_input]
        )

        save_profile_btn.click(
            fn=save_profile_handler,
            inputs=[engine_selector, config_name_input] + docling_components,
            outputs=[profile_status, profile_selector]
        )

        delete_profile_btn.click(
            fn=delete_profile_handler,
            inputs=[engine_selector, profile_selector],
            outputs=[profile_status, profile_selector]
        )

        save_task_btn.click(
            fn=save_task,
            inputs=[engine_selector, config_name_input] + docling_components,
            outputs=[task_list_display, task_editor_column, editor_status, task_selector]
        )

        cancel_btn.click(
            fn=hide_task_editor,
            outputs=[task_editor_column]
        )

        edit_task_btn.click(
            fn=edit_task_handler,
            inputs=[task_selector],
            outputs=[task_editor_column, editor_status, engine_selector, config_name_input,
                    profile_group, docling_config_area, textract_config_area] + docling_components
        )

        delete_task_btn.click(
            fn=delete_task_handler,
            inputs=[task_selector],
            outputs=[task_list_display, task_selector]
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
