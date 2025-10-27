"""
Task queue management functions for the Benchmarkdown UI.
"""

import json
import os


QUEUE_FILE = ".task_queue.json"


def load_queue_from_disk(extractor_queue: list, ui_instance):
    """Load task queue from disk.

    Args:
        extractor_queue: List to populate with loaded tasks
        ui_instance: BenchmarkUI instance to register extractors with
    """
    from benchmarkdown.docling import DoclingExtractor
    from benchmarkdown.config import DoclingConfig, TextractConfig
    from benchmarkdown.config_ui import build_config_from_ui_values

    if not os.path.exists(QUEUE_FILE):
        return

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
                    ui_instance.extractors[full_name] = extractor

                elif engine == "AWS Textract":
                    config = build_config_from_ui_values(TextractConfig, config_dict)
                    from benchmarkdown.textract import TextractExtractor
                    extractor = TextractExtractor(config=config)
                    full_name = f"AWS Textract ({config_name})"

                    task = {
                        'engine': engine,
                        'config_name': config_name,
                        'extractor': extractor,
                        'cost': task_data.get('cost', 0.05),
                        'config_dict': config_dict
                    }
                    extractor_queue.append(task)
                    ui_instance.extractors[full_name] = extractor

        print(f"✓ Loaded {len(extractor_queue)} tasks from disk")
    except Exception as e:
        print(f"⚠️  Failed to load queue: {e}")


def save_queue_to_disk(extractor_queue: list):
    """Save task queue to disk (without extractor objects).

    Args:
        extractor_queue: List of task dictionaries to save
    """
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


def generate_task_list_html(extractor_queue: list) -> str:
    """Generate HTML for the task list display with inline delete buttons.

    Args:
        extractor_queue: List of task dictionaries

    Returns:
        HTML string for task list
    """
    if not extractor_queue:
        return "<p style='opacity: 0.6; padding: 20px; text-align: center;'>No tasks configured yet.<br>Click 'Add Task' to begin.</p>"

    html = "<div class='task-list-container' style='font-family: system-ui, sans-serif;'>"
    for i, task in enumerate(extractor_queue):
        html += f"""
        <div class='task-card' style='border: 1px solid rgba(128, 128, 128, 0.3); padding: 12px; margin: 8px 0; border-radius: 6px; background: rgba(128, 128, 128, 0.1); display: flex; align-items: center;'>
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
