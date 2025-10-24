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
