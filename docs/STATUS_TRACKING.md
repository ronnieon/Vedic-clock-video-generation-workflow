# Workflow Status Tracking

## Overview

The workflow status system now tracks **complete progress** for each stage, showing exactly which files are missing when a stage is incomplete.

## Status Display

### ✅ Complete
All required files for the stage are present.
```
✅ 📄 Extract Content (11/11)
✅ 📖 Plan Story (12/12)
```

### ⚠️ Incomplete
Some files are missing. Shows progress and a collapsible list of missing files.
```
⚠️ ✏️ Rewrite for Kids (15/22)
  🔍 View 7 missing file(s)
    ❌ extracted/download2/page_0004/final_text_en.txt
    ❌ extracted/download2/page_0004/final_text_hi.txt
    ...
```

### ⏳ Not Started
No files present yet.
```
⏳ 🎙️ Generate Audio
```

## Stage Requirements

### 📄 Extract Content
**Required:** All page directories extracted from PDF

**Files checked:**
- `extracted/{pdf_stem}/page_XXXX/` directories

**Complete when:** All pages extracted

---

### 📖 Plan Story
**Required:** Cleaned text for all pages + whole story file

**Files checked:**
- `extracted/{pdf_stem}/whole_story_cleaned.txt`
- `extracted/{pdf_stem}/page_XXXX/clean_text.txt` (for each page)

**Complete when:** Story file + all page clean_text files exist

**Total count:** Number of pages + 1

---

### ✏️ Rewrite for Kids
**Required:** English and Hindi rewritten text for all pages

**Files checked:**
- `extracted/{pdf_stem}/page_XXXX/final_text_en.txt`
- `extracted/{pdf_stem}/page_XXXX/final_text_hi.txt`

**Complete when:** Both EN and HI files exist for ALL pages

**Total count:** Number of pages × 2

---

### 🎙️ Generate Audio
**Required:** English and Hindi audio for all pages

**Files checked:**
- `extracted/{pdf_stem}/page_XXXX/final_text_en.mp3`
- `extracted/{pdf_stem}/page_XXXX/final_text_hi.mp3`

**Complete when:** Both EN and HI audio exist for ALL pages

**Total count:** Number of pages × 2

---

### 🎬 Create Slideshow
**Required:** English and Hindi slideshow videos

**Files checked:**
- `extracted/{pdf_stem}/english_slideshow.mp4`
- `extracted/{pdf_stem}/hindi_slideshow.mp4`

**Complete when:** Both slideshow files exist

**Total count:** 2

---

## Status Object Structure

```python
{
    'extracted': {
        'complete': True,      # All required files present
        'total': 11,          # Total files required
        'done': 11,           # Files present
        'missing': []         # List of missing file paths
    },
    'planned': {
        'complete': False,
        'total': 12,
        'done': 8,
        'missing': [
            'extracted/download2/page_0004/clean_text.txt',
            'extracted/download2/page_0005/clean_text.txt',
            'extracted/download2/page_0006/clean_text.txt',
            'extracted/download2/page_0007/clean_text.txt'
        ]
    },
    # ... other stages
}
```

## Benefits

### 1. **Accurate Progress**
No more false "complete" status when only one page is done.

### 2. **Clear Missing Files**
Instantly see exactly which files are missing for each stage.

### 3. **Better Debugging**
Click to expand and view the full path of missing files.

### 4. **Visual Progress**
Shows completion percentage (done/total) for each stage.

### 5. **Prevents Errors**
Users can see if they need to complete previous stages before proceeding.

## Examples

### Example 1: Fresh PDF
```
⏳ 📄 Extract Content
⏳ 📖 Plan Story
⏳ ✏️ Rewrite for Kids
⏳ 🎙️ Generate Audio
⏳ 🎬 Create Slideshow
```

### Example 2: Extraction Complete
```
✅ 📄 Extract Content (11/11)
⏳ 📖 Plan Story
⏳ ✏️ Rewrite for Kids
⏳ 🎙️ Generate Audio
⏳ 🎬 Create Slideshow
```

### Example 3: Partial Rewrite
```
✅ 📄 Extract Content (11/11)
✅ 📖 Plan Story (12/12)
⚠️ ✏️ Rewrite for Kids (8/22)
  🔍 View 14 missing file(s) [click to expand]
⏳ 🎙️ Generate Audio
⏳ 🎬 Create Slideshow
```

### Example 4: Partial Audio
```
✅ 📄 Extract Content (11/11)
✅ 📖 Plan Story (12/12)
✅ ✏️ Rewrite for Kids (22/22)
⚠️ 🎙️ Generate Audio (15/22)
  🔍 View 7 missing file(s) [click to expand]
    ❌ extracted/download2/page_0006/final_text_en.mp3
    ❌ extracted/download2/page_0006/final_text_hi.mp3
    ❌ extracted/download2/page_0009/final_text_en.mp3
    ❌ extracted/download2/page_0009/final_text_hi.mp3
    ❌ extracted/download2/page_0010/final_text_en.mp3
    ❌ extracted/download2/page_0010/final_text_hi.mp3
    ❌ extracted/download2/page_0011/final_text_en.mp3
⏳ 🎬 Create Slideshow
```

### Example 5: All Complete
```
✅ 📄 Extract Content (11/11)
✅ 📖 Plan Story (12/12)
✅ ✏️ Rewrite for Kids (22/22)
✅ 🎙️ Generate Audio (22/22)
✅ 🎬 Create Slideshow (2/2)
```

## Implementation

The status checking logic is in `utils/workflow.py`:

```python
def get_workflow_status(pdf_stem: str) -> Dict:
    """Returns detailed status for each stage."""
    # Returns dict with 'complete', 'total', 'done', 'missing' for each stage
```

The UI rendering is in `app.py`:

```python
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
        with st.expander(f"🔍 View {len(missing)} missing file(s)"):
            for file_path in missing:
                st.caption(f"❌ `{file_path}`")
```

## Migration Notes

### Old Status (Boolean)
```python
{
    'extracted': True,
    'planned': False,
    'rewritten': False,
    'audio_generated': False,
    'slideshow_created': False
}
```

### New Status (Detailed)
```python
{
    'extracted': {'complete': True, 'total': 11, 'done': 11, 'missing': []},
    'planned': {'complete': False, 'total': 12, 'done': 8, 'missing': [...]},
    'rewritten': {'complete': False, 'total': 22, 'done': 0, 'missing': [...]},
    'audio_generated': {'complete': False, 'total': 22, 'done': 0, 'missing': [...]},
    'slideshow_created': {'complete': False, 'total': 2, 'done': 0, 'missing': [...]}
}
```

**Breaking Change:** Any code that checks `if status['extracted']:` needs to be updated to `if status['extracted']['complete']:`.

However, since the status is only used in `app.py` for UI display, this change is isolated and safe.
