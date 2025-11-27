# Version-Aware Workflow System

## Overview

The workflow status system now tracks **version consistency** across all pipeline stages. When any asset is regenerated to a new version, ALL downstream assets must be updated to match that version for the stage to be marked complete.

## Core Concept: Expected Version

**Expected Version** = The highest version number found across all assets in a stage.

Once any single asset reaches v2, ALL assets in that stage must reach v2 for completion.

## Version Propagation Chain

```
Text v2 → Audio v2 → Page Video v2 → Final Slideshow v2
```

### Example Scenario

**Initial State (All v1):**
```
✅ Rewrite for Kids (22/22) [v1]
✅ Generate Audio (22/22) [v1]
✅ Create Page Videos (22/22) [v1]
✅ Create Final Slideshow (2/2) [v1]
```

**After regenerating page_0002 text to v2:**
```
⚠️ Rewrite for Kids (2/22) [needs v2]
  ✅ page_0002/final_text_en_v2.txt (v2)
  ✅ page_0002/final_text_hi_v2.txt (v2)
  ❌ page_0001/final_text_en (has v1, needs v2)
  ❌ page_0001/final_text_hi (has v1, needs v2)
  ... (20 more pages need v2)

⚠️ Generate Audio (0/22) [needs v2]
  ❌ All audio files (have v1, need v2)

⚠️ Create Page Videos (0/22) [needs v2]
  ❌ All page videos (have v1, need v2)

⚠️ Create Final Slideshow (0/2) [needs v2]
  ❌ Both slideshows (have v1, need v2)
```

## Stage-by-Stage Logic

### 1. Extract Content
- No versioning (one-time extraction)
- Complete when all pages extracted

### 2. Plan Story
- No versioning (one-time planning)
- Complete when story file + all clean_text files exist

### 3. Rewrite for Kids
- **Versioned:** `final_text_en_vN.txt`, `final_text_hi_vN.txt`
- **Expected Version:** Max version across all text files
- **Complete When:** ALL pages have text at expected version

**Status Display:**
```
⚠️ ✏️ Rewrite for Kids (4/22) [needs v2]
```
Means: 2 pages at v2 (4 files), 20 pages need upgrade to v2

### 4. Generate Audio
- **Versioned:** `final_text_en_vN.mp3`, `final_text_hi_vN.mp3`
- **Expected Version:** Inherited from Rewrite stage
- **Complete When:** ALL audio files match text version

**Status Display:**
```
⚠️ 🎙️ Generate Audio (0/22) [needs v2]
```
Means: No audio at v2 yet, all need regeneration

### 5. Create Page Videos (NEW STAGE)
- **Versioned:** `page_video_en_vN.mp4`, `page_video_hi_vN.mp4`
- **Expected Version:** Inherited from Audio stage
- **Complete When:** ALL page videos combine image + audio at expected version

**Status Display:**
```
⚠️ 🎬 Create Page Videos (0/22) [needs v2]
```
Means: No page videos at v2, all need regeneration

### 6. Create Final Slideshow
- **Versioned:** `english_slideshow_vN.mp4`, `hindi_slideshow_vN.mp4`
- **Expected Version:** Inherited from Page Videos stage
- **Complete When:** Both slideshows built from page videos at expected version

**Status Display:**
```
⚠️ 🎞️ Create Final Slideshow (0/2) [needs v2]
```
Means: Slideshows need rebuild from v2 page videos

## File Naming Conventions

### Text Files
```
page_0001/
  final_text_en_v1.txt
  final_text_en_v2.txt
  final_text_en_v3.txt  ← Latest
  final_text_hi_v1.txt
  final_text_hi_v2.txt
  final_text_hi_v3.txt  ← Latest
```

### Audio Files
```
page_0001/
  final_text_en_v1.mp3
  final_text_en_v2.mp3  ← Latest
  final_text_hi_v1.mp3
  final_text_hi_v2.mp3  ← Latest
```

### Page Videos (NEW)
```
page_0001/
  page_video_en_v1.mp4
  page_video_en_v2.mp4  ← Latest
  page_video_hi_v1.mp4
  page_video_hi_v2.mp4  ← Latest
```

### Final Slideshows
```
extracted/download/
  english_slideshow_v1.mp4
  english_slideshow_v2.mp4  ← Latest
  hindi_slideshow_v1.mp4
  hindi_slideshow_v2.mp4    ← Latest
```

## Status Messages Explained

### Complete Stage
```
✅ ✏️ Rewrite for Kids (22/22) [v2]
```
- ✅ = All files present
- (22/22) = 22 out of 22 files complete
- [v2] = All at version 2

### Incomplete Stage
```
⚠️ 🎙️ Generate Audio (4/22) [needs v2]
```
- ⚠️ = Incomplete
- (4/22) = Only 4 out of 22 files at expected version
- [needs v2] = Remaining files need upgrade to v2

### Not Started
```
⏳ 🎬 Create Page Videos
```
- ⏳ = No files exist yet

## Expandable File Lists

### Complete Files
```
✅ View 4 complete file(s)
  ✅ extracted/download/page_0001/final_text_en_v2.mp3 (v2)
  ✅ extracted/download/page_0001/final_text_hi_v2.mp3 (v2)
  ✅ extracted/download/page_0002/final_text_en_v2.mp3 (v2)
  ✅ extracted/download/page_0002/final_text_hi_v2.mp3 (v2)
```

### Missing/Outdated Files
```
❌ View 18 missing/outdated file(s)
  ❌ extracted/download/page_0003/final_text_en.mp3 (has v1, needs v2)
  ❌ extracted/download/page_0003/final_text_hi.mp3 (has v1, needs v2)
  ❌ extracted/download/page_0004/final_text_en.mp3 (needs v2)
  ❌ extracted/download/page_0004/final_text_hi.mp3 (needs v2)
  ...
```

## Workflow Example

### Scenario: Improving One Page

**Step 1:** Regenerate text for page_0002
```
Action: Click "Create New Version (v2)" on page_0002
Result:
  - page_0002/final_text_en_v2.txt created
  - page_0002/final_text_hi_v2.txt created
  - Expected version for Rewrite stage → v2
```

**Step 2:** Check sidebar status
```
⚠️ ✏️ Rewrite for Kids (2/22) [needs v2]
  ✅ 2 complete files (page_0002 at v2)
  ❌ 20 missing/outdated files (other pages at v1)

⚠️ 🎙️ Generate Audio (0/22) [needs v2]
  ❌ 22 missing/outdated files (all at v1, need v2)
```

**Step 3:** Regenerate audio for page_0002
```
Action: Generate audio for page_0002
Result:
  - page_0002/final_text_en_v2.mp3 created
  - page_0002/final_text_hi_v2.mp3 created
```

**Step 4:** Check sidebar again
```
⚠️ 🎙️ Generate Audio (2/22) [needs v2]
  ✅ 2 complete files (page_0002 audio at v2)
  ❌ 20 missing/outdated files (other pages at v1)
```

**Step 5:** To complete the workflow
```
Option A: Regenerate all pages to v2
  - Rewrite all pages → v2
  - Generate all audio → v2
  - Create all page videos → v2
  - Create final slideshows → v2

Option B: Keep working incrementally
  - System tracks progress
  - Shows exactly what needs updating
  - Can complete pages one at a time
```

## Benefits

### 1. Version Consistency
- Ensures all assets in pipeline match
- Prevents mismatched audio/video combinations
- Clear indication when regeneration needed

### 2. Incremental Progress
- Can regenerate one page at a time
- System tracks partial completion
- Shows exactly what's done vs needed

### 3. Clear Status
- Version numbers in sidebar
- "has v1, needs v2" messages
- Easy to see what's outdated

### 4. Prevents Errors
- Won't mark stage complete with mixed versions
- Forces downstream regeneration
- Maintains quality consistency

## Implementation Details

### Version Detection
```python
# Find max version across all pages
max_version = 0
for page_dir in page_dirs:
    en_version = get_latest_version_number(page_dir, 'en_text')
    hi_version = get_latest_version_number(page_dir, 'hi_text')
    max_version = max(max_version, en_version, hi_version)

expected_version = max_version
```

### Completion Check
```python
# Check if file is at expected version
if file_exists and file_version == expected_version:
    status['done'] += 1
    status['present'].append(file_path)
elif file_exists:
    status['missing'].append(f"{file} (has v{file_version}, needs v{expected_version})")
else:
    status['missing'].append(f"{file} (needs v{expected_version})")
```

### Version Propagation
```python
# Each stage inherits expected version from previous
status['audio_generated']['expected_version'] = status['rewritten']['expected_version']
status['page_videos']['expected_version'] = status['audio_generated']['expected_version']
status['slideshow_created']['expected_version'] = status['page_videos']['expected_version']
```

## Migration from Old System

### Automatic Migration
- Existing files automatically converted to v1
- `versions.json` created for each page
- No manual intervention needed

### First Run After Update
```
Before: ✅ Rewrite for Kids (22/22)
After:  ✅ Rewrite for Kids (22/22) [v1]
```

All existing files marked as v1, system ready for v2 generation.

## Future Enhancements

Potential additions:
- Bulk "upgrade all to vN" button
- Version comparison viewer
- Automatic cascade regeneration
- Version branching (experimental vs production)
- Rollback entire PDF to specific version

## Summary

The version-aware workflow ensures **complete consistency** across the entire pipeline. When you regenerate any asset, the system clearly shows:
- What's at the new version
- What needs updating
- Exactly which files are outdated

This prevents mixed-version artifacts and maintains quality throughout the pipeline.
