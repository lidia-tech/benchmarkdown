# Implemented tasks

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
