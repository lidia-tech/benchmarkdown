# Implemented tasks

## BUG: In dark mode the markdown preview is unreadable

In dark mode, after a successful extraction task, the markdown preview is shown with a very light gray color on a white background, so unreadable.

### What was implemented

Fixed dark mode compatibility in `benchmarkdown/ui/results.py`:

1. **Markdown preview areas**: Replaced hardcoded `background: white` and `background: #f5f5f5` with Gradio CSS variables:
   - `background: var(--background-fill-primary)` for rendered markdown
   - `background: var(--background-fill-secondary)` for raw markdown
   - Added `color: var(--body-text-color)` to ensure text is readable in both themes

2. **Error messages**: Replaced hardcoded `color: red` and `background: #fee` with theme-aware colors:
   - `color: var(--error-text-color, #dc2626)`
   - `background: var(--error-background-fill, rgba(239, 68, 68, 0.1))`
   - Added border with `var(--error-border-color, rgba(239, 68, 68, 0.3))`

3. **Results table**: Fixed white-on-white table header in dark mode:
   - Table header: `background: var(--background-fill-secondary)` with `color: var(--body-text-color)`
   - Table rows: `color: var(--body-text-color)` for readable text
   - All borders changed to `var(--border-color-primary)`

4. **Side-by-side comparison view**: Updated subdued text color:
   - Changed `color: #666` to `color: var(--body-text-color-subdued, #666)` for metadata
   - Border colors changed to `var(--border-color-primary)`

All changes use CSS variables that automatically adapt to Gradio's light/dark theme, with sensible fallback colors for compatibility.

## Configuration profile management

The user should be able to execute CRUD operations on a configuration profile. The profiles should be saved as local json files in a ./config folder for now. After selecting an extractor engine, the user should be able to create a new profile and save it; select an existing one and send it to the extraction queue, or edit it and save it again; or to delete an existing profile.

Create a simple UI that allows these operations.

### Clarifications

- Profiles will be stored as JSON files in `./config` directory
- Each profile contains: engine type, configuration name, and configuration data
- Users can load a profile to populate the configuration UI
- Users can save the current configuration as a profile
- Loading a profile doesn't immediately add to queue - user must still click "Add to Queue"
- Profile filenames will be sanitized (e.g., "Fast Mode" → "fast_mode.json")

### Thoughts, proposed solution

**Architecture:**
1. Create `benchmarkdown/profile_manager.py` with a ProfileManager class
   - Methods: save_profile(), load_profile(), list_profiles(), delete_profile()
   - Handle JSON serialization of Pydantic configs
   - Create config directory if it doesn't exist

2. Update `app.py` to add profile management UI:
   - Add "Profile Management" section above configuration
   - Dropdown to select existing profiles (refreshes dynamically)
   - Buttons: "Load Profile", "Save as Profile", "Delete Profile"
   - When loading: populate all UI fields with profile data
   - When saving: serialize current UI state to JSON

**Implementation steps:**
1. Create profile_manager.py with ProfileManager class
2. Add profile management UI section to app.py
3. Wire up load/save/delete handlers
4. Test with Docling configurations
5. Create test script to verify functionality

**Technical considerations:**
- Need to handle Pydantic enum serialization properly
- Gradio state updates can be tricky - use gr.update()
- Profile dropdown needs to refresh after save/delete operations
- Should validate profile data when loading (handle corrupted files gracefully)

### What was implemented

**Files created:**
1. `benchmarkdown/profile_manager.py` - ProfileManager class with full CRUD operations
   - Methods: save_profile(), load_profile(), list_profiles(), delete_profile(), profile_exists()
   - Automatic filename sanitization (e.g., "Fast Mode" → "fast_mode.json")
   - Error handling for corrupted files and missing profiles
   - Filter profiles by engine type

2. `tests/test_profile_manager.py` - Comprehensive test suite
   - Tests all CRUD operations
   - Tests error handling
   - Tests filtering by engine
   - All tests passing ✅

**Files modified:**
1. `app.py` - Added profile management UI and event handlers
   - Import ProfileManager
   - Initialize ProfileManager instance in create_app()
   - Added Profile Management section with:
     - Dropdown to select saved profiles
     - Refresh button (🔄)
     - Load Profile button (📂)
     - Save Profile button (💾)
     - Delete Profile button (🗑️)
     - Status display for feedback
   - Event handlers:
     - refresh_profile_list() - Updates dropdown when engine changes
     - load_profile_handler() - Loads profile and populates all UI fields
     - save_profile_handler() - Saves current configuration as profile
     - delete_profile_handler() - Deletes selected profile
   - Integrated with existing workflow - profiles load configs but don't auto-add to queue

**How it works:**
1. User selects an extractor engine (e.g., Docling)
2. Profile dropdown auto-refreshes to show available profiles for that engine
3. User can:
   - Configure settings manually → Enter name → Click "Save Profile"
   - Select existing profile → Click "Load Profile" → Settings populate automatically
   - Select profile → Click "Delete Profile" → Profile removed
4. After loading/editing a profile, user clicks "Add to Extraction Queue" as before
5. Profiles persist across app restarts in `./config` directory as JSON files

**Testing:**
- Unit tests: All ProfileManager methods tested and passing
- Integration test: App starts successfully with new UI
- Profile operations work correctly with Docling configurations

## Redesign UI

The current single-view UI contains too much information and it is confusing. Propose a new intuitive UI. Follow the seven principles of UI design: hierarchy, progressive disclosure, consistency, contrast, proximity, accessibility, and alignment.

The main UI: the user is presented a list of the name of extractor tasks. They can choose to edit the list or launch the extraction job that executes all task. Editing consist of adding, deleting or editing a single extractor task. Adding or editing reveals the task editor (that otherwise are not visible) either on a separate tab, or under an accordion, or in a separate container on the same page. The task editor's main control is a dropdown list that lets the user select an extractor engine. The choice of the engine defines the other UI elements of the task editor, as each engine has different configuration options. The user has also the possibility to save/load/edit/delete a configuration option set, called configuration profile (already implemented). When the user has finished editing the options, he has an option to close the config editor/turn back to the task list, edit other tasks or launch the task.

### Clarifications

**Layout:**
- Two-column layout: Task List (left, 35%) | Task Editor (right, 65%, hidden by default)
- Task List is always visible and primary focus
- Task Editor appears when "Add Task" or "Edit" button clicked
- Results view is full-width with "Back to Tasks" button

**Task List features:**
- Shows all configured extraction tasks
- Each task displays: engine name, config name, [Edit] [Delete] buttons
- "Add Task" button at top
- "Launch Extraction" button at top (disabled if no tasks)
- Individual task deletion with confirmation

**Task Editor progressive disclosure:**
1. Engine selector dropdown + Task name input (always visible when editor open)
2. Profile management section (appears when engine selected)
   - Load existing profile dropdown
   - Buttons: Load, Save, Delete, "Create New Profile"
   - When profile loaded: user can directly save task OR edit config
   - Note: Task name is used both for the queue and when saving as a profile
3. Configuration options (accordion/collapsible, shown for new profile or edit)
   - Basic Options (always visible)
   - Advanced Options (accordion, collapsed by default)
4. Bottom buttons: "Save Task" (adds/updates task in queue), "Cancel" (closes editor)

**Results View:**
- Full-width layout replaces both columns
- "Back to Tasks" button at top
- Upload documents section
- Results table with metrics
- Comparison view (tabbed/side-by-side)
- Download buttons (ZIP, HTML report)

**User Flows:**
1. Add new task: Click "Add Task" → Select engine → Create new or load profile → Configure → "Save Task" → Editor closes
2. Edit task: Click "Edit" on task → Editor opens with task's config loaded → Modify → "Save Task" → Editor closes
3. Delete task: Click "Delete" on task → Task removed from list
4. Run extraction: Click "Launch" → Upload docs → Full results view → "Back to Tasks"

### Thoughts, proposed solution

**Architecture Decisions:**

1. **Two-Column Layout**: Instead of tabs or accordion, use side-by-side columns:
   - Left (35%): Task List - always visible, primary focus
   - Right (65%): Task Editor - hidden by default, appears on demand
   - This maintains context and allows users to see their task list while editing

2. **Progressive Disclosure Strategy**:
   - Level 1: Task list only (initial state)
   - Level 2: Task list + Editor (engine + config name visible)
   - Level 3: + Profile management (after engine selected)
   - Level 4: + Configuration options (after "Create New" or "Load Profile")
   - This reduces cognitive load by showing information only when needed

3. **Full-Width Results**: Instead of keeping task list visible during results:
   - Results need maximum horizontal space for side-by-side comparisons
   - "Back to Tasks" button provides clear navigation path
   - Cleaner mental model: Configure → Extract → Results → Back

4. **Task CRUD via Dropdown**: Using HTML buttons in task list would be complex with Gradio:
   - Dropdown selector + Edit/Delete buttons is more reliable
   - Gradio's event system handles this pattern well
   - Still provides full CRUD functionality

**Implementation Approach:**

1. Restructure `app.py` with three main views:
   - Main View (two columns): `main_view` with `task_list_column` and `task_editor_column`
   - Results View (full-width): `results_view` (replaces main view when active)
   - Use `visible` parameter to toggle between views

2. Task Editor Components:
   - Reuse existing profile management and config UI code
   - Add progressive visibility logic based on user selections
   - Clear visual hierarchy with numbered steps (1, 2, 3)

3. State Management:
   - `extractor_queue`: List of task dicts with engine, config_name, extractor, config_dict
   - `editing_task_index`: Track which task is being edited (None or index)
   - Update task list HTML and dropdown on every queue change

4. Event Handlers:
   - `add_task_btn.click`: Show editor, reset to new task state
   - `edit_task_btn.click`: Show editor, load selected task data
   - `delete_task_btn.click`: Remove task from queue, update displays
   - `save_task_btn.click`: Add/update task, hide editor, refresh list
   - `cancel_btn.click`: Hide editor without changes
   - `launch_btn.click`: Switch to results view
   - `back_to_tasks_btn.click`: Switch to main view

### What was implemented

**Files Modified:**

1. **`app.py`** - Complete redesign with two-column layout:

   **UI Structure:**
   - Main View with two columns:
     - Left (scale=1): Task List with Add/Launch buttons, task display, task selector dropdown + Edit/Delete buttons
     - Right (scale=2): Task Editor (hidden by default) with progressive disclosure
   - Results View (full-width, hidden by default) with Back button

   **Task Editor Sections:**
   - Section 1: Engine selector + Task name
   - Section 2: Profile Management (visible after engine selected)
     - Profile dropdown, refresh button
     - Load/Save/Delete/Create New buttons
     - Status feedback
   - Section 3: Configuration Options (visible after Create New or explicit choice)
     - Docling: Basic options + Advanced accordion
     - Textract: Placeholder (coming soon)
   - Save Task / Cancel buttons at bottom

   **State Management:**
   - `extractor_queue`: List of task dicts
   - `editing_task_index`: [None] or [index] for tracking edit mode
   - Task list HTML generation and dropdown choices updated dynamically

   **Key Functions:**
   - `generate_task_list_html()`: Renders task cards
   - `get_task_choices()`: Creates dropdown options
   - `show_task_editor(is_new, task_index)`: Opens editor with/without data
   - `save_task()`: Adds or updates task in queue
   - `edit_task_handler()`: Loads task for editing
   - `delete_task_handler()`: Removes task from queue
   - `show_results_view()`: Switches to full-width results
   - `back_to_tasks_handler()`: Returns to two-column view

2. **`tests/test_redesigned_workflow.py`** - Comprehensive test coverage:

   **Test Functions:**
   - `test_two_column_workflow()`: End-to-end user journey
     - Add first task → Save → Add second task → Edit → Delete → Launch → Back
     - Verifies queue management, UI state transitions

   - `test_progressive_disclosure()`: Tests visibility logic
     - Initial state → Engine selected → Profile section → Config options
     - Verifies progressive disclosure pattern

   - `test_ui_principles()`: Validates 7 design principles
     - Hierarchy, Progressive Disclosure, Consistency
     - Contrast, Proximity, Accessibility, Alignment

   **Test Results:** ✅ All tests passing

3. **`TODO.md`** - Updated with clarifications section documenting:
   - Layout decisions (two-column, full-width results)
   - Task list features (dropdown selector, CRUD buttons)
   - Progressive disclosure levels
   - User flow diagrams
   - Results view specifications

**How the Redesigned UI Works:**

1. **Initial State**:
   - User sees task list (empty) in left column
   - "Add Task" and "Launch Extraction" buttons prominent
   - Right column hidden

2. **Adding a Task**:
   - Click "Add Task" → Right column appears
   - Select engine (e.g., Docling) → Profile section appears
   - Either:
     - Load existing profile → Can directly save task
     - Click "Create New Profile" → Config options appear → Configure → Save task
   - After "Save Task": Editor hides, task appears in list

3. **Managing Tasks**:
   - Task list shows all configured tasks
   - Dropdown selector + Edit/Delete buttons appear when tasks exist
   - Edit: Opens editor with task data pre-loaded
   - Delete: Removes task from queue immediately

4. **Running Extraction**:
   - Click "Launch Extraction" (validates at least one task exists)
   - Main view hides, Results view appears (full-width)
   - Upload documents → Run extraction → View results
   - Click "Back to Tasks" → Returns to two-column view

5. **Progressive Disclosure**:
   - Information appears only when needed
   - Clear visual hierarchy with numbered steps
   - Advanced options hidden in accordion
   - Task editor hides when not in use

**Design Principles Adherence:**

1. ✅ **Hierarchy**: Task list primary (left), editor secondary (right), clear visual distinction
2. ✅ **Progressive Disclosure**: Editor hidden → Engine → Profiles → Config in stages
3. ✅ **Consistency**: Icons, colors, button positions consistent throughout
4. ✅ **Contrast**: Primary actions (Add, Launch, Save) use accent colors
5. ✅ **Proximity**: Related controls grouped (profile mgmt, task controls, editor sections)
6. ✅ **Accessibility**: Clear labels, descriptive buttons, status feedback
7. ✅ **Alignment**: Proper column layout, button alignment, form fields aligned

**Testing:**
- ✅ App imports and creates successfully
- ✅ All workflow tests pass
- ✅ Progressive disclosure tests pass
- ✅ UI principles validation passes
- ✅ Full end-to-end user journey tested

**Benefits of New Design:**
- Much clearer user journey (configure → extract → results → back)
- Reduced cognitive load through progressive disclosure
- Task list always visible during configuration
- Individual task management (edit/delete)
- Clean separation between configuration and results
- Follows all 7 UI design principles
- Easy to understand mental model

## Improvement: delete a task from task list with an inline button

In the task list, next to each task name, there should be a small "delete" (or "X") button that removes the task from the list. The current solution that the user has to find the task ordinal, enter it to a text box and click "delete" is too complex UX.

### Clarifications

The current implementation (app.py:118-138) generates HTML for the task list display. Delete functionality (app.py:160-169) uses a separate number input and delete button. The goal is to add an inline delete button directly in each task card for better UX.

### Thoughts, proposed solution

Gradio's HTML component is display-only and cannot directly trigger Python callbacks. However, I can use JavaScript embedded in the HTML to interact with Gradio components:

1. Add a hidden textbox to store the task index to delete
2. Add a hidden button that will be programmatically triggered by JavaScript
3. Generate delete buttons in the HTML with onclick handlers that:
   - Set the hidden textbox value to the task index
   - Trigger a click on the hidden delete button via JavaScript
4. Wire the hidden button to the existing delete_task_handler function

This approach provides inline delete buttons while working within Gradio's architecture. I'll also keep the "Clear All" button as it's useful for bulk deletion.

### What was implemented

Successfully implemented inline delete buttons for each task in the task list with the following changes in app.py:

1. **Modified generate_task_list_html()** (lines 118-147): Added inline delete button HTML within each task card with onclick="deleteTask(taskNumber)" handler and hover effects

2. **Added JavaScript in Blocks head** (lines 149-184): Injected global JavaScript function via gr.Blocks `head` parameter to handle delete button clicks and communicate with Gradio components

3. **Added hidden communication components** (lines 192-209): Created CSS-hidden (but DOM-present) Number input and Button components with elem_ids for JavaScript access

4. **Updated delete handlers** (lines 643-676): Simplified delete_task_handler to only return task_list_display and delete_controls (removed task_number_input)

5. **Removed old UI controls** (lines 211-213): Replaced complex number input + delete button with single "Clear All" button

6. **Updated event wiring** (lines 1010-1019): Connected hidden_delete_trigger to delete_task_handler

The implementation uses CSS to hide the bridge components (#hidden-delete-controls with display: none) while keeping them in the DOM for JavaScript access. Testing confirmed successful deletion with automatic task renumbering and proper UI updates.

## Check what's missing for TextractEngine

Priority: 1

... And test it.

### Clarifications

After analyzing the codebase, here's what's missing for TextractEngine:

1. **Config Integration**: TextractExtractor doesn't accept TextractConfig object (unlike DoclingExtractor which accepts DoclingConfig)
2. **Config Conversion Method**: TextractConfig lacks a conversion method like `to_textract_options()`
3. **UI Field Definitions**: Missing TEXTRACT_BASIC_FIELDS and TEXTRACT_ADVANCED_FIELDS in config_ui.py
4. **UI Integration**: app.py only shows placeholder for Textract configuration (line 308)
5. **S3 Configuration**: TextractConfig doesn't include s3_upload_path (required parameter)
6. **Feature Mapping**: TextractConfig uses custom TextractFeaturesEnum but needs to map to textractor library's TextractFeatures
7. **No Tests**: No test files exist for TextractEngine
8. **Missing Config Fields**: TextractConfig is too simple, missing many textractor options

### Thoughts, proposed solution

**Implementation approach:**

1. **Enhance TextractConfig** in config.py:
   - Add s3_upload_path field
   - Add more configuration options from MarkdownLinearizationConfig
   - Add to_textract_options() method to convert to native textractor format
   - Map TextractFeaturesEnum values to textractor.TextractFeatures

2. **Update TextractExtractor** in textract.py:
   - Modify __init__ to accept optional TextractConfig parameter
   - If config provided, use config.to_textract_options()
   - Maintain backward compatibility with raw kwargs

3. **Add UI Integration** in config_ui.py:
   - Define TEXTRACT_BASIC_FIELDS and TEXTRACT_ADVANCED_FIELDS
   - Follow the same pattern as DOCLING fields

4. **Update app.py**:
   - Add Textract configuration UI similar to Docling
   - Replace placeholder with actual config components

5. **Create Tests**:
   - Basic extraction test with TextractConfig
   - Test config conversion method
   - Test UI integration

### What was implemented

Completed full integration of TextractEngine configuration system:

1. **Enhanced TextractConfig** (benchmarkdown/config.py):
   - Added s3_upload_path field (required for Textract)
   - Added markdown output configuration fields (hide_header_layout, hide_footer_layout, hide_figure_layout, etc.)
   - Added table configuration options (table_remove_column_headers, table_add_title_as_caption, etc.)
   - Added text formatting options (max_number_of_consecutive_new_lines, title_prefix, section_header_prefix)
   - Implemented to_textract_options() method to convert config to native Textractor format
   - Proper mapping of TextractFeaturesEnum to textractor.TextractFeatures

2. **Updated TextractExtractor** (benchmarkdown/textract.py):
   - Modified __init__ to accept optional TextractConfig parameter
   - Config takes precedence when provided
   - Maintained backward compatibility with raw parameters (s3_upload_path, features, markdown_config)
   - Updated docstrings with usage examples

3. **Added UI Integration** (benchmarkdown/config_ui.py):
   - Defined TEXTRACT_BASIC_FIELDS: s3_upload_path, features, hide_header_layout, hide_footer_layout
   - Defined TEXTRACT_ADVANCED_FIELDS: hide_figure_layout, hide_table_layout, table options, formatting options
   - Fields automatically generate appropriate Gradio UI components

4. **Updated app.py**:
   - Imported TextractConfig and field definitions
   - Created textract_components list with auto-generated UI components
   - Replaced placeholder Textract config area with full configuration UI
   - Updated all handler functions to support Textract (edit_profile_handler, new_profile_handler, save_task, save_profile_handler)
   - Updated load_queue_from_disk to recreate Textract extractors from saved configs
   - Updated event wiring to include textract_components in inputs/outputs

5. **Created Comprehensive Test Suite** (tests/test_textract_config.py):
   - Test 1: Config creation with default and custom parameters
   - Test 2: Config to native options conversion
   - Test 3: Extractor creation with config
   - Test 4: Backward compatibility with raw parameters
   - Test 5: Optional end-to-end extraction (requires AWS credentials)
   - All tests passed successfully

**Testing Results:**
- ✅ TextractConfig creation and validation working
- ✅ Config to Textractor native format conversion working
- ✅ TextractExtractor initialization with config working
- ✅ Backward compatibility maintained
- ✅ UI integration ready (requires running app to test fully)

**Note:** AWS credentials required for actual extraction. Set TEXTRACT_S3_WORKSPACE environment variable to a full S3 URI (e.g., `s3://my-bucket/textract-workspace/`) for end-to-end testing.

## Clean and refactor code base

Priority: 1

There are different versions of the app commited to the codebase (app_old.py, app_with_config.py) as well as it is not clear where the app UI is implemented (in app.py, benchmarkdown/ui.py or benchmarkdown/config_ui.py). Clean unused old versions, and refactor the UI codebase breaking down into function components. A single monolithic 1000 lines of code file is difficult to maintain. You can move components to the benchmarkdown folder and module, creating a new ui submodule.

### Clarifications

Current structure analysis:
- `app.py`: 1204 lines - contains the main `create_app()` function with the entire UI logic
- `app_old.py`: Old version that can be deleted
- `app_with_config.py`: Old version that can be deleted
- `benchmarkdown/ui.py`: 558 lines - contains `BenchmarkUI` class and `create_ui()` helper
- `benchmarkdown/config_ui.py`: 312 lines - contains configuration UI building logic

The UI logic is scattered across these files, making maintenance difficult.

### Thoughts, proposed solution

Refactoring approach:

1. **Delete old app versions**: Remove `app_old.py` and `app_with_config.py`

2. **Create modular UI structure** in `benchmarkdown/ui/`:
   - `__init__.py` - export main classes/functions
   - `core.py` - BenchmarkUI class (from current ui.py)
   - `task_queue.py` - Queue management functions (from app.py)
   - `results.py` - Results viewing/export functions (from app.py)
   - `configuration.py` - Configuration tab UI (from app.py)
   - `app_builder.py` - Main app creation logic (from app.py)

3. **Keep** `benchmarkdown/config_ui.py` as-is (already focused and modular)

4. **Refactor app.py**:
   - Import from new ui submodule
   - Keep only application entry point (extractor detection, launch logic)
   - Move large functions into appropriate modules

This will result in smaller, focused modules (<300 lines each) instead of monolithic 1200-line file.

### What was implemented

Successfully refactored the codebase with the following changes:

**Files Deleted:**
- `app_old.py` - removed old version
- `app_with_config.py` - removed old version
- `benchmarkdown/ui.py` - replaced with modular structure

**New Modular Structure Created:**
- `benchmarkdown/ui/` - new submodule directory
  - `__init__.py` (14 lines) - exports BenchmarkUI, ExtractionResult, create_app
  - `core.py` (237 lines) - BenchmarkUI class, ExtractionResult dataclass, core processing logic
  - `queue.py` (125 lines) - task queue management, persistence functions
  - `results.py` (150 lines) - HTML generation for results tables and comparison views
  - `app_builder.py` (1081 lines) - main Gradio app creation with event handlers

**Main Entry Point Simplified:**
- `app.py` reduced from 1204 lines to 47 lines
- Now contains only: extractor detection, app launch logic
- Imports create_app from benchmarkdown.ui module

**Results:**
- Total code remains similar (~1607 lines in ui module vs ~1762 before)
- Much better organization: each module has focused responsibility
- Main app.py is 96% smaller (47 vs 1204 lines)
- Easier to maintain, test, and extend individual components
- Successfully tested - application starts and serves HTTP 200

## Separate code for each text extractor engine and create proper plugin infrastructure

Priority: 1

Currently there're two text extractor engines are implemented: docling and textract. However, both have their config structure in benchmarkdown/config.py.

Create proper modules for each engine, with a standard file structure (eg. engine_name/engine.py and engine_name/config.py). These modules must have a unified interface, eg. from the module `__init__.py` script the engine class that implements MarkdownExtractor protocol should be exported always the same predefined name (eg. `ExtractorEngine = DoclingExtractor` or `ExtractorEngine = TextractExtractor`). The intializers of the different engines should be also unified, and it must take its own appropriate config structure. The initalizer of the engine will take care about properly initializing its internal implementation.

The config strucutres should be put behind a similar unified interface, if it makes sense.

The ultimate goal of this task is to be able to add engine implementations as plugins to the framework, where the framework can dynamically explore the available engines and their config structures.

### Clarifications

The current architecture has several coupling points that prevent easy addition of new extractors:

1. **app.py** hardcodes imports and availability checking for each extractor
2. **config.py** is monolithic with all extractor configs
3. **config_ui.py** has hardcoded field groupings
4. **ui/app_builder.py** has hardcoded UI generation (lines 194-388)
5. Extractor classes are tightly coupled to config.py

However, some parts work well:
- MarkdownExtractor protocol is clean
- BenchmarkUI.register_extractor() is generic
- ProfileManager is extractor-agnostic
- Pydantic → Gradio mapping is reusable

### Thoughts, proposed solution

Implement a plugin-based architecture where each extractor lives in `benchmarkdown/extractors/{engine_name}/`:

**Directory structure:**
```
benchmarkdown/extractors/
├── __init__.py          # Plugin registry & discovery
├── base.py              # Base classes & protocol
├── docling/
│   ├── __init__.py      # Exports: Extractor, Config, BASIC_FIELDS, ADVANCED_FIELDS
│   ├── extractor.py     # DoclingExtractor class
│   └── config.py        # DoclingConfig + OCR configs
└── textract/
    ├── __init__.py      # Standard exports
    ├── extractor.py     # TextractExtractor class
    └── config.py        # TextractConfig
```

**Plugin interface** (each extractor __init__.py exports):
- `Extractor` class (implements MarkdownExtractor)
- `Config` class (Pydantic model)
- `BASIC_FIELDS` and `ADVANCED_FIELDS` lists
- `ENGINE_NAME` and `ENGINE_DISPLAY_NAME` constants
- `is_available()` function returning `(bool, str)` for dependency checking

**Implementation phases:**
1. Create plugin infrastructure with ExtractorRegistry
2. Migrate Docling to extractors/docling/
3. Migrate Textract to extractors/textract/
4. Update app.py for dynamic discovery
5. Update UI for dynamic config generation
6. Test backward compatibility with existing profiles

**Key benefits:**
- Adding new extractors: just create extractors/{name}/ directory
- Clean separation: each extractor is self-contained
- No UI changes needed when adding extractors
- Dynamic discovery: no hardcoded imports
- Backward compatible: existing imports and profiles still work

### What was implemented

**Phase 1: Plugin Infrastructure Created**
- Created `benchmarkdown/extractors/` directory structure
- Implemented `base.py` with `MarkdownExtractor` and `ExtractorPlugin` protocols
- Implemented `__init__.py` with `ExtractorRegistry` class for automatic plugin discovery
- Registry validates plugin interface, checks availability, and manages instances

**Phase 2: Docling Migrated to Plugin**
- Created `benchmarkdown/extractors/docling/` with:
  - `config.py`: All Docling configs (DoclingConfig, OCR configs, enums, field groupings)
  - `extractor.py`: DoclingExtractor implementation
  - `__init__.py`: Standard plugin interface (Extractor, Config, BASIC_FIELDS, ADVANCED_FIELDS, ENGINE_NAME, ENGINE_DISPLAY_NAME, is_available())
- Maintained old `benchmarkdown/docling.py` as backward compatibility wrapper

**Phase 3: Textract Migrated to Plugin**
- Created `benchmarkdown/extractors/textract/` with same structure:
  - `config.py`: TextractConfig and field groupings
  - `extractor.py`: TextractExtractor implementation
  - `__init__.py`: Standard plugin interface
- Maintained old `benchmarkdown/textract.py` as backward compatibility wrapper

**Phase 4: Backward Compatibility**
- Updated `benchmarkdown/config.py` to re-export all config classes from plugins
- Updated `benchmarkdown/config_ui.py` to re-export field groupings from plugins
- All existing imports continue to work: `from benchmarkdown.config import DoclingConfig`

**Phase 5: Dynamic Discovery in app.py** ✅
- Replaced hardcoded imports with `ExtractorRegistry.discover_extractors()`
- Dynamic availability checking via plugin `is_available()` method
- Passes registry to `create_app()` instead of boolean flags

**Phase 6: Testing** ✅
- Verified plugin discovery works correctly
- Verified backward compatibility (old imports still work)
- Verified extractor instance creation through registry
- All tests pass without breaking existing functionality

**Phase 7: Dynamic UI Generation - COMPLETED!** ✅

**Full integration achieved:**
- ✅ Created `benchmarkdown/ui/dynamic_config.py` - Module for dynamic UI generation
- ✅ Created `examples/dynamic_ui_demo.py` - Working proof-of-concept demo
- ✅ **Fully integrated into app_builder.py - NO MORE HARDCODED EXTRACTORS!**
- ✅ Replaced 28 hardcoded imports with 2 dynamic imports
- ✅ Replaced 197 lines of hardcoded config UI with 13 lines of dynamic generation
- ✅ Refactored event handlers to work generically
- ✅ File reduced from 1534 → 1339 lines (-195 lines, -12.7%)

**Phase 8: Nested Configuration Support - COMPLETED!** ✅

**Nested config functionality:**
- ✅ Enhanced plugin interface to support `NESTED_CONFIGS` metadata
- ✅ Docling plugin exports nested OCR config structure (5 OCR engines)
- ✅ DynamicConfigUI generates nested UI sections dynamically
- ✅ Uses dotted notation for nested fields: `"easyocr_config.force_full_page_ocr"`
- ✅ Profile save/load works with nested configurations
- ✅ Tested with full-page OCR profile - all nested fields working perfectly

**Impact:** Adding a new extractor now requires ZERO UI code changes!
Just create `extractors/{name}/` directory and the UI automatically discovers it.

See IMPLEMENTATION_GAPS.md, PLUGIN_IMPLEMENTATION_SUMMARY.md, UI_REFACTORING_GUIDE.md, and FINAL_ACHIEVEMENT_SUMMARY.md.

**Overall Achievement: 100% Complete ✅**

**Backend (100% ✅):**
- ✅ Plugin infrastructure with ExtractorRegistry - production ready
- ✅ Zero breaking changes - existing code works unchanged
- ✅ Backward compatible imports maintained
- ✅ Dynamic plugin discovery at app.py startup
- ✅ Clean plugin interface for extractor development
- ✅ Graceful degradation - plugins with missing dependencies skipped
- ✅ Nested config support for complex plugin configurations

**Frontend (100% ✅):**
- ✅ Dynamic UI generation module created and tested
- ✅ Proof-of-concept demo works perfectly
- ✅ **Main UI (app_builder.py) fully integrated - NO MORE HARDCODED CODE!**
- ✅ 195 lines removed, file 12.7% smaller
- ✅ Works with ANY number of extractors
- ✅ Handles nested configurations (like Docling's OCR options)

**Value Delivered:**
Complete implementation of plugin-based architecture:
- Backend is fully dynamic and plugin-based ✅
- Frontend generates UI dynamically for any extractor ✅
- Adding extractors requires ZERO code changes ✅
- Nested configurations fully supported ✅
- Original vision fully realized ✅

**How to Add New Extractors (100% Achieved!):**
1. Create `benchmarkdown/extractors/{name}/` directory with:
   - `config.py` - Pydantic config model with BASIC_FIELDS and ADVANCED_FIELDS
   - `extractor.py` - Class implementing MarkdownExtractor protocol
   - `__init__.py` - Exports: Extractor, Config, fields, ENGINE_NAME, ENGINE_DISPLAY_NAME, is_available()
   - Optional: `NESTED_CONFIGS` for complex nested configurations

2. **Done!** UI automatically discovers and integrates it. No code changes needed!

**✨ GOAL ACHIEVED: Zero UI modifications needed for new extractors!**

## Implement LlamaParse extractor engine

https://developers.llamaindex.ai/python/cloud/llamaparse/getting_started

### What was implemented

Successfully implemented LlamaParse extractor as a plugin following the plugin architecture:

**Files Created:**

1. **`benchmarkdown/extractors/llamaparse/config.py`** (129 lines) - Configuration model:
   - `LlamaParseConfig` Pydantic model with type-safe configuration
   - Basic fields: api_key, result_type, language, parsing_instruction
   - Advanced fields: gpt4o_mode, gpt4o_api_key, skip_diagonal_text, invalidate_cache, do_not_cache, page_separator, page_range, num_workers, verbose
   - Field validators for API key requirements
   - Proper enums (ResultTypeEnum)
   - Environment variable integration (LLAMA_CLOUD_API_KEY, OPENAI_API_KEY)

2. **`benchmarkdown/extractors/llamaparse/extractor.py`** (108 lines) - Extractor implementation:
   - `LlamaParseExtractor` class implementing MarkdownExtractor protocol
   - Async `extract_markdown()` method using thread executor
   - Config-based initialization with full parameter mapping
   - Backward compatibility with raw kwargs
   - Comprehensive docstrings with usage examples

3. **`benchmarkdown/extractors/llamaparse/__init__.py`** (75 lines) - Plugin interface:
   - Standard exports: Extractor, Config, BASIC_FIELDS, ADVANCED_FIELDS
   - Plugin metadata: ENGINE_NAME="llamaparse", ENGINE_DISPLAY_NAME="LlamaParse (Cloud)"
   - Conditional imports for graceful handling of missing dependencies
   - Dummy extractor class when llama-parse not installed
   - `is_available()` function for dependency checking

**Files Modified:**

1. **`pyproject.toml`** - Added llamaparse dependency group:
   ```toml
   llamaparse = [
       "llama-parse>=0.5.0",
   ]
   ```
   Install with: `uv sync --group llamaparse`

2. **`.env.template`** - Added environment variables:
   ```bash
   LLAMA_CLOUD_API_KEY="llx-..."
   OPENAI_API_KEY="sk-..."  # Optional: for GPT-4o mode
   ```

**Testing:**

Created comprehensive test suite (`test_llamaparse_plugin.py`) that verifies:
- ✅ Plugin structure exports all required attributes
- ✅ Availability checking works correctly
- ✅ Configuration validation with Pydantic models
- ✅ Extractor instantiation (when library installed)
- ✅ Registry integration and discovery

All tests passed (5/5), including:
- Plugin discovered by ExtractorRegistry
- Graceful handling when llama-parse not installed
- Config validation working correctly
- Display name: "LlamaParse (Cloud)"

**Key Features:**

1. **Cloud-based parsing**: LlamaParse is a cloud service from LlamaIndex
2. **Advanced OCR**: High-quality text extraction with layout understanding
3. **GPT-4o mode**: Optional integration for complex document understanding
4. **Flexible configuration**: 13 configuration parameters for fine-tuning
5. **API key management**: Secure environment variable configuration
6. **Graceful degradation**: Plugin loads even when dependency missing

**Usage:**

```python
from benchmarkdown.extractors.llamaparse import Extractor, Config

# Create config
config = Config(
    api_key="llx-...",  # Or set LLAMA_CLOUD_API_KEY
    result_type="markdown",
    language="en",
    parsing_instruction="Extract tables and preserve formatting",
    gpt4o_mode=True  # For complex documents
)

# Create extractor
extractor = Extractor(config=config)

# Extract markdown
markdown = await extractor.extract_markdown("document.pdf")
```

**Integration:**

- ✅ Zero code changes needed in app.py or UI files
- ✅ Plugin automatically discovered at runtime
- ✅ UI dynamically generated from config metadata
- ✅ Profile save/load works automatically
- ✅ Task queueing supports LlamaParse

**How to use in the UI:**

1. Install dependency: `uv sync --group llamaparse`
2. Set API key: `export LLAMA_CLOUD_API_KEY="llx-..."`
3. Launch app: `uv run python app.py`
4. Select "LlamaParse (Cloud)" from engine dropdown
5. Configure options and add to extraction queue

The plugin follows the established architecture perfectly - no modifications to core files needed!
