#!/usr/bin/env python3
"""
Demonstration of Dynamic UI Generation for Extractor Plugins.

This example shows how to create a configuration UI that works with ANY
extractor plugin without hardcoded engine-specific code.

Run with: uv run python examples/dynamic_ui_demo.py
"""

import os
from dotenv import load_dotenv
load_dotenv()

import gradio as gr
from benchmarkdown.extractors import get_global_registry
from benchmarkdown.ui.dynamic_config import DynamicConfigUI
from benchmarkdown.profile_manager import ProfileManager

# Get the plugin registry
print("🔍 Discovering plugins...")
registry = get_global_registry()

# Initialize dynamic config UI
dynamic_config = DynamicConfigUI(registry)
profile_manager = ProfileManager()

# Create the Gradio app
with gr.Blocks(title="Dynamic UI Demo") as demo:
    gr.Markdown("# 🎯 Dynamic Extractor Configuration Demo")
    gr.Markdown("""
    This demo shows how the plugin system enables **truly dynamic UI generation**.
    No hardcoded engine-specific code needed!
    """)

    with gr.Row():
        # Engine selector - dynamically generated from registry
        engine_selector = gr.Dropdown(
            choices=dynamic_config.generate_engine_choices(),
            label="Select Extractor Engine",
            info="Dynamically populated from plugin registry"
        )

    # Profile management
    with gr.Row():
        profile_name = gr.Textbox(
            label="Profile Name",
            placeholder="e.g., 'Fast Mode'"
        )
        save_btn = gr.Button("💾 Save Profile", variant="primary")
        load_btn = gr.Button("📂 Load Profile")

    # Status display
    status = gr.Markdown("*Select an engine to configure*")

    # Dynamically generate ALL config UIs
    print("🎨 Generating config UIs for all plugins...")
    config_ui_data = dynamic_config.generate_all_config_uis()

    # Get all config areas in consistent order
    all_config_areas = dynamic_config.get_all_config_areas()

    # Show stats
    gr.Markdown(f"""
    ### 📊 Dynamic UI Stats:
    - **Engines discovered**: {len(registry.get_all_extractors())}
    - **Available engines**: {len(registry.get_available_extractors())}
    - **Config UIs generated**: {len(config_ui_data['config_areas'])}
    - **Total components**: {sum(len(comps) for comps in config_ui_data['component_lists'].values())}

    **✨ Zero hardcoded engine names in this UI!**
    """)

    # Event handler: Show config area for selected engine
    def show_config_for_engine(engine_display_name):
        if not engine_display_name:
            return ([gr.update(visible=False) for _ in all_config_areas] +
                    [gr.update(value="*Select an engine to configure*")])

        engine_name = dynamic_config.engine_name_from_display(engine_display_name)
        updates = []

        # Update visibility for all config areas
        for config_engine in sorted(config_ui_data['config_areas'].keys()):
            updates.append(gr.update(visible=(config_engine == engine_name)))

        updates.append(gr.update(value=f"✅ Loaded config UI for **{engine_display_name}**"))
        return updates

    # Event handler: Save profile (generic for any engine!)
    def save_profile_generic(engine_display_name, prof_name, *config_values):
        if not engine_display_name or not prof_name:
            return gr.update(value="❌ Please select engine and enter profile name")

        try:
            engine_name = dynamic_config.engine_name_from_display(engine_display_name)

            # Build config dict from UI values - works for ANY engine!
            config_dict = dynamic_config.build_config_dict_from_values(
                engine_name,
                list(config_values)
            )

            # Save profile
            profile_manager.save_profile(
                engine=engine_display_name,
                profile_name=prof_name,
                config_data=config_dict
            )

            return gr.update(value=f"✅ Saved profile '{prof_name}' for {engine_display_name}")

        except Exception as e:
            return gr.update(value=f"❌ Error: {e}")

    # Wire up events
    engine_selector.change(
        fn=show_config_for_engine,
        inputs=[engine_selector],
        outputs=all_config_areas + [status]
    )

    # Get all components for save handler
    all_components_flat = []
    for engine_name in sorted(config_ui_data['component_lists'].keys()):
        all_components_flat.extend(config_ui_data['component_lists'][engine_name])

    save_btn.click(
        fn=save_profile_generic,
        inputs=[engine_selector, profile_name] + all_components_flat,
        outputs=[status]
    )

if __name__ == "__main__":
    print("\n🚀 Starting dynamic UI demo...")
    print("✨ This UI works with ANY number of extractors!")
    print("🔧 Add a new extractor plugin and it will automatically appear!\n")

    demo.launch(
        server_name="0.0.0.0",
        server_port=7861,
        share=False
    )
