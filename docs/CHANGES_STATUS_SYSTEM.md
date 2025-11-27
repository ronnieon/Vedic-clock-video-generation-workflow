# Status System Update - Complete Progress Tracking

## Summary

Updated the workflow status system to show **accurate completion status** for all pipeline stages. Stages are now only marked as complete when **ALL** required files are present, not just when any files exist.

## Problem Solved

**Before:** Stage showed ✅ complete if even 1 file was present
```
✅ 🎙️ Generate Audio  
// But only 3 out of 22 audio files existed!
```

**After:** Stage shows accurate progress with missing file details
```
⚠️ 🎙️ Generate Audio (3/22)
  🔍 View 19 missing file(s) [expandable]
    ❌ extracted/download2/page_0004/final_text_en.mp3
    ❌ extracted/download2/page_0004/final_text_hi.mp3
    ...
```

## Changes Made

### 1. **`utils/workflow.py`** - Core Status Logic

#### Changed function signature:
```python
# OLD
def get_workflow_status(pdf_stem: str) -> Dict[str, bool]

# NEW  
def get_workflow_status(pdf_stem: str) -> Dict
```

#### Changed return structure:
```python
# OLD - Simple boolean
{
    'extracted': True,
    'planned': False,
    'rewritten': False,
    'audio_generated': False,
    'slideshow_created': False
}

# NEW - Detailed status
{
    'extracted': {
        'complete': True,
        'total': 11,
        'done': 11, 
        'missing': []
    },
    'planned': {
        'complete': False,
        'total': 12,
        'done': 8,
        'missing': [
            'extracted/download2/page_0004/clean_text.txt',
            ...
        ]
    },
    ...
}
```

#### Updated completion logic:
- **OLD:** Used `any()` - marked complete if ANY file exists
- **NEW:** Checks ALL required files - marked complete only if ALL exist

**Example for Audio Stage:**
```python
# OLD
status['audio_generated'] = any((p / 'final_text_en.mp3').exists() for p in page_dirs)
# ❌ Returns True even if only 1 audio file exists

# NEW
for page_dir in page_dirs:
    en_audio = page_dir / 'final_text_en.mp3'
    hi_audio = page_dir / 'final_text_hi.mp3'
    if en_audio.exists():
        status['audio_generated']['done'] += 1
    else:
        status['audio_generated']['missing'].append(str(en_audio))
    # ... same for hi_audio
status['audio_generated']['complete'] = (done == total)
# ✅ Returns True only if ALL audio files exist
```

### 2. **`app.py`** - Sidebar UI Display

Updated status rendering to show:
- ✅ **Complete**: `✅ Stage Name (done/total)` - green
- ⚠️ **Incomplete**: `⚠️ Stage Name (done/total)` - yellow with expandable missing files
- ⏳ **Not Started**: `⏳ Stage Name` - blue

```python
# NEW UI code
for stage_name, stage_status in stages:
    total = stage_status['total']
    done = stage_status['done']
    missing = stage_status['missing']
    complete = stage_status['complete']
    
    if total == 0:
        st.info(f"⏳ {stage_name}")
    elif complete:
        st.success(f"✅ {stage_name} ({done}/{total})")
    else:
        st.warning(f"⚠️ {stage_name} ({done}/{total})")
        if missing:
            with st.expander(f"🔍 View {len(missing)} missing file(s)", expanded=False):
                for file_path in missing:
                    st.caption(f"❌ `{file_path}`")
```

### 3. **Documentation Files Created**

- **`STATUS_TRACKING.md`** - Complete documentation of the new status system
- **`CHANGES_STATUS_SYSTEM.md`** - This file, summary of changes

## Stage Requirements Detail

| Stage | Files Required | Count Formula |
|-------|---------------|---------------|
| **Extract** | Page directories | `num_pages` |
| **Plan Story** | `whole_story_cleaned.txt` + `clean_text.txt` per page | `num_pages + 1` |
| **Rewrite** | `final_text_en.txt` + `final_text_hi.txt` per page | `num_pages × 2` |
| **Audio** | `final_text_en.mp3` + `final_text_hi.mp3` per page | `num_pages × 2` |
| **Slideshow** | `english_slideshow.mp4` + `hindi_slideshow.mp4` | `2` |

## Example Output

### Before Changes
```
✅ 📄 Extract Content
✅ 📖 Plan Story  
✅ ✏️ Rewrite for Kids     // WRONG - only 8/22 files exist
✅ 🎙️ Generate Audio       // WRONG - only 3/22 files exist
⏳ 🎬 Create Slideshow
```

### After Changes
```
✅ 📄 Extract Content (11/11)
✅ 📖 Plan Story (12/12)
⚠️ ✏️ Rewrite for Kids (8/22)
  🔍 View 14 missing file(s)
    ❌ extracted/download2/page_0005/final_text_en.txt
    ❌ extracted/download2/page_0005/final_text_hi.txt
    ❌ extracted/download2/page_0006/final_text_en.txt
    ... [11 more]
⚠️ 🎙️ Generate Audio (3/22)  
  🔍 View 19 missing file(s)
    ❌ extracted/download2/page_0004/final_text_en.mp3
    ❌ extracted/download2/page_0004/final_text_hi.mp3
    ... [17 more]
⏳ 🎬 Create Slideshow
```

## Benefits

### 1. **Accurate Progress**
Users can now see exactly how many files are complete vs total required.

### 2. **No False Positives**
Stages are only marked ✅ when 100% complete, not when partially done.

### 3. **Debugging Aid**
Instantly see which specific files are missing by clicking the expander.

### 4. **Better UX**
Visual feedback shows progress percentage for incomplete stages.

### 5. **Prevents Errors**
Users won't proceed to next stage thinking current one is done when it's not.

## Testing

To test the new status system:

1. **Start fresh PDF** - All stages show ⏳
2. **Extract** - Shows ✅ with page count
3. **Plan partially** - Delete some `clean_text.txt` files, shows ⚠️ with missing list
4. **Complete planning** - Shows ✅
5. **Rewrite some pages** - Shows ⚠️ with accurate count
6. **Generate some audio** - Shows ⚠️ with missing file list
7. **Complete all** - All stages show ✅

## Migration Impact

### Breaking Changes
The `get_workflow_status()` function return type changed from `Dict[str, bool]` to `Dict`.

### Affected Code
Only `app.py` uses this function, and it has been updated accordingly.

### Backward Compatibility
None required - this is an isolated change to the UI display logic.

## Future Improvements

Potential enhancements:
- Add progress bars for incomplete stages
- Color-code missing files by page
- Add "retry missing only" buttons
- Show estimated completion time
- Add stage dependency warnings

## Implementation Notes

- All file paths in missing lists are relative to `Path.cwd()` for readability
- Expanders are collapsed by default to keep sidebar clean
- Warning color (yellow) used for incomplete stages instead of info (blue)
- Success color (green) only used when 100% complete
- File counts shown as `(done/total)` format

## Related Files

- `utils/workflow.py` - Core status checking logic
- `app.py` - Sidebar UI rendering
- `STATUS_TRACKING.md` - Full documentation
- `CHANGES_STATUS_SYSTEM.md` - This summary
