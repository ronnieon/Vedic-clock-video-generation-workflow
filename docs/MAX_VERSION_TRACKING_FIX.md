# Maximum Version Tracking Fix

## Problem

When audio was generated at v3 (ahead of text at v2), the sidebar showed:
```
⚠️ 🎙️ Generate Audio (0/22) [needs v2]
```

This was incorrect because:
- Audio v3 existed for page_0002
- System expected v2 (from text)
- Should have expected v3 (the actual maximum)

## Root Cause

Each stage was only looking at the **previous stage** to determine expected version:

```python
# OLD (WRONG)
status['audio_generated']['expected_version'] = status['rewritten']['expected_version']
```

This meant:
- Text stage: max text version = v2
- Audio stage: inherited v2 from text
- Ignored that audio v3 existed

## Solution

Each stage now finds the **absolute maximum version** across ALL relevant assets:

### Text/Rewrite Stage
```python
# NEW (CORRECT)
for page_dir in page_dirs:
    en_text_version = get_latest_version_number(page_dir, 'en_text')
    hi_text_version = get_latest_version_number(page_dir, 'hi_text')
    en_audio_version = get_latest_version_number(page_dir, 'en_audio')
    hi_audio_version = get_latest_version_number(page_dir, 'hi_audio')
    
    # Max considers BOTH text and audio
    status['rewritten']['max_version'] = max(
        status['rewritten']['max_version'], 
        en_text_version, hi_text_version,
        en_audio_version, hi_audio_version
    )

status['rewritten']['expected_version'] = status['rewritten']['max_version']
```

### Audio Stage
```python
# NEW (CORRECT)
for page_dir in page_dirs:
    en_audio_version = get_latest_version_number(page_dir, 'en_audio')
    hi_audio_version = get_latest_version_number(page_dir, 'hi_audio')
    en_text_version = get_latest_version_number(page_dir, 'en_text')
    hi_text_version = get_latest_version_number(page_dir, 'hi_text')
    
    # Max across ALL assets (text + audio)
    status['audio_generated']['max_version'] = max(
        status['audio_generated']['max_version'], 
        en_audio_version, hi_audio_version,
        en_text_version, hi_text_version
    )

status['audio_generated']['expected_version'] = status['audio_generated']['max_version']
```

### Page Videos Stage
```python
# NEW (CORRECT)
for page_dir in page_dirs:
    # Check text and audio versions
    en_text_version = get_latest_version_number(page_dir, 'en_text')
    hi_text_version = get_latest_version_number(page_dir, 'hi_text')
    en_audio_version = get_latest_version_number(page_dir, 'en_audio')
    hi_audio_version = get_latest_version_number(page_dir, 'hi_audio')
    
    # Check video versions
    for i in range(1, 20):
        if (page_dir / f'page_video_en_v{i}.mp4').exists():
            status['page_videos']['max_version'] = max(status['page_videos']['max_version'], i)
        if (page_dir / f'page_video_hi_v{i}.mp4').exists():
            status['page_videos']['max_version'] = max(status['page_videos']['max_version'], i)
    
    # Max across ALL assets
    status['page_videos']['max_version'] = max(
        status['page_videos']['max_version'],
        en_text_version, hi_text_version,
        en_audio_version, hi_audio_version
    )

status['page_videos']['expected_version'] = status['page_videos']['max_version']
```

### Slideshow Stage
```python
# NEW (CORRECT)
# Find max slideshow version
for i in range(1, 20):
    if (extraction_dir / f'english_slideshow_v{i}.mp4').exists():
        status['slideshow_created']['max_version'] = max(status['slideshow_created']['max_version'], i)
    if (extraction_dir / f'hindi_slideshow_v{i}.mp4').exists():
        status['slideshow_created']['max_version'] = max(status['slideshow_created']['max_version'], i)

# Expected version is max across slideshows AND all previous stages
status['slideshow_created']['expected_version'] = max(
    status['slideshow_created']['max_version'],
    status['page_videos']['expected_version']
)
```

## New Behavior

### Scenario: Audio Ahead of Text

**Files:**
- page_0002: text v2, audio v3
- All other pages: text v1, audio v1

**Old Display (WRONG):**
```
⚠️ ✏️ Rewrite for Kids (2/22) [needs v2]
⚠️ 🎙️ Generate Audio (0/22) [needs v2]
```

**New Display (CORRECT):**
```
⚠️ ✏️ Rewrite for Kids (2/22) [needs v3]
  ✅ 2 complete files
    ✅ page_0002/final_text_en_v2.txt (v2)
    ✅ page_0002/final_text_hi_v2.txt (v2)
  ❌ 20 missing/outdated files
    ❌ page_0001/final_text_en (has v1, needs v3)
    ❌ page_0002/final_text_en (has v2, needs v3)
    ...

⚠️ 🎙️ Generate Audio (2/22) [needs v3]
  ✅ 2 complete files
    ✅ page_0002/final_text_en_v3.mp3 (v3)
    ✅ page_0002/final_text_hi_v3.mp3 (v3)
  ❌ 20 missing/outdated files
    ❌ page_0001/final_text_en.mp3 (has v1, needs v3)
    ...
```

## Key Principle

**The expected version is ALWAYS the highest version found across ALL assets in the pipeline.**

This ensures:
- ✅ No asset is ignored when calculating expected version
- ✅ If any asset is ahead, all others must catch up
- ✅ True representation of what needs updating
- ✅ Consistent version tracking across entire pipeline

## Example Workflow

### Step 1: Initial State (All v1)
```
✅ ✏️ Rewrite for Kids (22/22) [v1]
✅ 🎙️ Generate Audio (22/22) [v1]
✅ 🎬 Create Page Videos (22/22) [v1]
✅ 🎞️ Create Final Slideshow (2/2) [v1]
```

### Step 2: Regenerate Text for page_0002 → v2
```
⚠️ ✏️ Rewrite for Kids (2/22) [needs v2]
⚠️ 🎙️ Generate Audio (0/22) [needs v2]
⚠️ 🎬 Create Page Videos (0/22) [needs v2]
⚠️ 🎞️ Create Final Slideshow (0/2) [needs v2]
```

### Step 3: Generate Audio for page_0002 → v3 (accidentally ahead)
```
⚠️ ✏️ Rewrite for Kids (2/22) [needs v3]  ← Updated to v3!
  ❌ page_0002 text at v2, needs v3

⚠️ 🎙️ Generate Audio (2/22) [needs v3]
  ✅ page_0002 audio at v3

⚠️ 🎬 Create Page Videos (0/22) [needs v3]
⚠️ 🎞️ Create Final Slideshow (0/2) [needs v3]
```

### Step 4: Update page_0002 Text to v3
```
⚠️ ✏️ Rewrite for Kids (2/22) [needs v3]
  ✅ page_0002 text at v3

⚠️ 🎙️ Generate Audio (2/22) [needs v3]
  ✅ page_0002 audio at v3

⚠️ 🎬 Create Page Videos (0/22) [needs v3]
⚠️ 🎞️ Create Final Slideshow (0/2) [needs v3]
```

## Benefits

### 1. Accurate Status
- Shows true maximum version
- No hidden outdated assets
- Clear what needs updating

### 2. Handles Edge Cases
- Audio generated ahead of text
- Videos generated before audio updated
- Any asset can be ahead

### 3. Consistent Tracking
- All stages use same logic
- Expected version propagates correctly
- No confusion about versions

### 4. Flexible Workflow
- Can regenerate in any order
- System adapts to actual state
- Always shows correct status

## Technical Details

### Version Detection Functions

**get_latest_version_number()**
```python
def get_latest_version_number(page_dir: Path, content_type: str) -> int:
    """
    Get the version number of the latest version.
    Returns: Version number (1, 2, 3, etc.) or 0 if no versions exist
    """
    return get_version_count(page_dir, content_type)
```

**get_version_count()**
```python
def get_version_count(page_dir: Path, content_type: str) -> int:
    """Get the total number of versions for a content type."""
    return len(get_all_versions(page_dir, content_type))
```

### Content Types Checked

- **en_text**: English text versions
- **hi_text**: Hindi text versions
- **en_audio**: English audio versions
- **hi_audio**: Hindi audio versions
- **page_video_en**: English page videos (via file glob)
- **page_video_hi**: Hindi page videos (via file glob)
- **slideshow_en**: English slideshow (via file glob)
- **slideshow_hi**: Hindi slideshow (via file glob)

## Summary

The fix ensures that **expected version = max version across ALL assets**, not just the previous stage. This provides accurate status tracking regardless of which assets are ahead or behind, and clearly shows what needs updating to reach version consistency.
