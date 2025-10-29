# UI Refactoring Guide: Complete Dynamic Integration

##  Current Status
- ✅ Plugin infrastructure: Complete
- ✅ Dynamic UI module: Created and tested
- ✅ Proof-of-concept: Working (examples/dynamic_ui_demo.py)
- ⏳ Main UI integration: In progress

This guide provides step-by-step instructions for completing the app_builder.py refactoring.

## File to Refactor
**Target**: `benchmarkdown/ui/app_builder.py` (1534 lines)
**Backup**: `benchmarkdown/ui/app_builder.py.backup` (created)

## Phase 1: Update Imports (Lines 10-43)

### Current (Hardcoded):
```python
from benchmarkdown.extractors.docling import Extractor as DoclingExtractor
from benchmarkdown.extractors.docling import Config as DoclingConfig
from benchmarkdown.extractors.docling.config import (
    EasyOcrConfig,
    # ... more imports
)
from benchmarkdown.config_ui import (
    create_gradio_component_from_field,
    build_config_from_ui_values,
)
# Field constants now imported from extractor modules
```

### Replace With:
```python
from benchmarkdown.ui.dynamic_config import DynamicConfigUI
from benchmarkdown.config_ui import build_config_from_ui_values
```

**Lines to delete**: 15-42 (28 import lines)
**Lines to add**: 2 imports
**Net change**: -26 lines

## Phase 2: Update Function Signature (Lines 46-63)

### Current:
```python
def create_app(registry=None, has_docling=False, has_textract=False):
    # Support both new registry-based and old boolean-based approaches
    if registry is not None:
        available = registry.get_available_extractors()
        has_docling = 'docling' in available
        has_textract = 'textract' in available

    ui = BenchmarkUI()
    profile_manager = ProfileManager()
```

### Replace With:
```python
def create_app(registry):
    """Create the Gradio interface with dynamic plugin support."""
    if registry is None:
        raise ValueError("Registry parameter is required")

    ui = BenchmarkUI()
    profile_manager = ProfileManager()
    dynamic_config = DynamicConfigUI(registry)
```

**Lines to delete**: 46-63 (18 lines)
**Lines to add**: 9 lines
**Net change**: -9 lines

## Phase 3: Update Engine Selector (Lines 161-172)

### Current:
```python
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
```

### Replace With:
```python
engine_selector = gr.Dropdown(
    choices=dynamic_config.generate_engine_choices(),
    label="Extractor Engine",
    value=None,
    interactive=True
)
```

**Lines to delete**: 161-172 (12 lines)
**Lines to add**: 6 lines
**Net change**: -6 lines

## Phase 4: Replace Config UI Generation (Lines 177-373)

This is the **biggest change**: 196 lines of hardcoded UI → ~10 lines of dynamic generation

### Current Structure:
```python
# Lines 177-376: Hardcoded Docling config
with gr.Column(visible=False) as docling_config_area:
    docling_components = []

    # Basic fields (15 lines)
    for field_name in DOCLING_BASIC_FIELDS:
        # ... create component

    # 5 OCR engine sections (150+ lines)
    with gr.Group(visible=True) as easyocr_group:
        # EasyOCR fields...
    with gr.Group(visible=False) as tesseract_group:
        # Tesseract fields...
    # ... 3 more OCR engines

    # Advanced fields (20 lines)
    for field_name in DOCLING_ADVANCED_FIELDS:
        # ... create component

# Lines 377-389: Hardcoded Textract config
with gr.Column(visible=False) as textract_config_area:
    # Similar structure...
```

### Replace With:
```python
# Dynamically generate ALL config UIs
config_ui_data = dynamic_config.generate_all_config_uis()

# Store references for event handlers
config_areas = config_ui_data['config_areas']  # Dict[engine_name, gr.Column]
component_lists = config_ui_data['component_lists']  # Dict[engine_name, List[Component]]
field_maps = config_ui_data['field_maps']  # Dict[engine_name, List[str]]
```

**Lines to delete**: 177-389 (213 lines!)
**Lines to add**: 7 lines
**Net change**: -206 lines  🎉

## Phase 5: Refactor Event Handlers

### 5a. `show_config_area` (Lines 1010-1016)

**Current**:
```python
def show_config_area(engine):
    """Show appropriate config area and hide profile status."""
    if engine == "Docling":
        return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)
    elif engine == "AWS Textract":
        return gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)
    return gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)
```

**Replace with**:
```python
def show_config_area(engine_display):
    """Show appropriate config area dynamically."""
    updates = dynamic_config.get_config_area_updates(engine_display)
    updates.append(gr.update(visible=False))  # hide profile_status
    return updates
```

### 5b. `save_profile_handler` (Lines 1125-1260)

This is complex - currently 135 lines with if/elif for each engine.

**Current structure**:
```python
def save_profile_handler(engine, config_name, *config_values):
    if engine == "Docling":
        # Calculate indices (20 lines)
        basic_len = len(DOCLING_BASIC_FIELDS)
        easyocr_len = len(EASYOCR_BASIC_FIELDS + EASYOCR_ADVANCED_FIELDS)
        # ... more calculations

        # Extract values (50 lines)
        idx = 0
        basic_values = config_values[idx:idx+basic_len]
        # ... more slicing

        # Build config_data (40 lines)
        config_data = {}
        for field, value in zip(DOCLING_BASIC_FIELDS, basic_values):
            config_data[field] = value
        # ... nested OCR configs

    elif engine == "AWS Textract":
        # Similar structure for Textract (25 lines)
```

**Replace with**:
```python
def save_profile_handler(engine_display, config_name, *config_values):
    if not config_name:
        return (gr.update(visible=False),
                gr.update(value="❌ Please enter a profile name", visible=True),
                gr.update())

    try:
        engine_name = dynamic_config.engine_name_from_display(engine_display)

        # Get components for this engine
        engine_components = dynamic_config.get_all_components_for_engine(engine_name)

        # Extract only the values for this engine from *config_values
        # (config_values contains ALL engines' components, we need just this one)
        start_idx = 0
        for eng in sorted(config_areas.keys()):
            if eng == engine_name:
                break
            start_idx += len(component_lists[eng])

        end_idx = start_idx + len(engine_components)
        engine_values = config_values[start_idx:end_idx]

        # Build config dict - works for ANY engine!
        config_dict = dynamic_config.build_config_dict_from_values(
            engine_name,
            list(engine_values)
        )

        # Save profile
        profile_manager.save_profile(
            engine=engine_display,
            profile_name=config_name,
            config_data=config_dict
        )

        # Refresh profile list
        profiles = profile_manager.list_profiles(engine=engine_display)
        profile_names = [p["profile_name"] for p in profiles]

        return (
            gr.update(visible=False),
            gr.update(value=f"✅ Saved: {config_name}", visible=True),
            gr.update(choices=profile_names, value=config_name)
        )

    except Exception as e:
        return (
            gr.update(visible=False),
            gr.update(value=f"❌ Error: {e}", visible=True),
            gr.update()
        )
```

## Phase 6: Update Event Handler Wiring

### Current (Lines 1400+):
```python
# Hardcoded list of all Docling components
all_docling_inputs = [engine_selector, config_name_input] + docling_components

# Hardcoded list of all Textract components
all_textract_inputs = [engine_selector, config_name_input] + textract_components

# Different handlers for different engines
save_profile_btn.click(
    fn=save_profile_handler,
    inputs=all_docling_inputs if engine == "Docling" else all_textract_inputs,
    outputs=[...]
)
```

### Replace With:
```python
# Collect ALL components from ALL engines in consistent order
all_config_components = []
for engine_name in sorted(component_lists.keys()):
    all_config_components.extend(component_lists[engine_name])

# Single handler works for all engines!
save_profile_btn.click(
    fn=save_profile_handler,
    inputs=[engine_selector, config_name_input] + all_config_components,
    outputs=[config_editor, profile_status, profile_selector]
)
```

## Summary of Changes

| Section | Current Lines | New Lines | Net Change |
|---------|--------------|-----------|------------|
| Imports | 33 | 2 | -31 |
| Function signature | 18 | 9 | -9 |
| Engine selector | 12 | 6 | -6 |
| Config UI generation | 213 | 7 | -206 |
| Event handlers | ~300 | ~100 | -200 |
| **Total** | **~576** | **~124** | **~-452 lines** |

## Expected Outcome

After refactoring:
- ❌ **Before**: 1534 lines, hardcoded for 2 engines
- ✅ **After**: ~1082 lines, works for infinite engines
- 🎉 **Reduction**: 452 lines removed
- ✨ **Benefit**: Adding new extractors requires ZERO UI changes

## Testing Checklist

After refactoring, test:
1. ✅ App launches without errors
2. ✅ Engine selector shows available engines
3. ✅ Selecting engine shows correct config UI
4. ✅ Can create and save profile
5. ✅ Can load existing profile
6. ✅ Can add task to queue
7. ✅ Can run extraction
8. ✅ Existing saved profiles still work
9. ✅ Queue persistence works
10. ✅ Results display correctly

## Estimated Time

- Phase 1 (Imports): 10 minutes
- Phase 2 (Signature): 5 minutes
- Phase 3 (Engine selector): 5 minutes
- Phase 4 (Config UI): 30 minutes
- Phase 5 (Event handlers): 2 hours
- Phase 6 (Wiring): 1 hour
- Testing & debugging: 1 hour

**Total: 4-5 hours**

## Quick Start

```bash
# 1. Backup current file (already done)
cp benchmarkdown/ui/app_builder.py benchmarkdown/ui/app_builder.py.backup

# 2. Start refactoring (use this guide)
# Edit benchmarkdown/ui/app_builder.py

# 3. Test frequently
uv run python app.py

# 4. If issues, restore backup
cp benchmarkdown/ui/app_builder.py.backup benchmarkdown/ui/app_builder.py
```

## Reference Implementation

See `examples/dynamic_ui_demo.py` for working example of:
- Dynamic engine selector
- Dynamic config UI generation
- Generic event handlers
- Profile save/load

This is the pattern to follow for app_builder.py!
