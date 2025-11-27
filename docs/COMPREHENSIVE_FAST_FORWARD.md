# Comprehensive Fast Forward System

## Overview

All assets (Text, Audio, Video) now have:
1. **⚠️ Version status indicators** showing if behind or at latest
2. **⏩ Fast forward buttons** always visible for every asset
3. **Disabled state** when already at latest version
4. **Consistent behavior** across all pages and PDFs

## Complete Asset Coverage

### ✅ Text Assets
- **EN Text** (`final_text_en_vN.txt`)
- **HI Text** (`final_text_hi_vN.txt`)

### ✅ Audio Assets
- **EN Audio** (`final_text_en_vN.mp3`)
- **HI Audio** (`final_text_hi_vN.mp3`)

### ✅ Video Assets
- **EN Video** (`page_video_en_vN.mp4`)
- **HI Video** (`page_video_hi_vN.mp4`)

## UI Pattern (Consistent Across All Assets)

### When Behind Expected Version
```
📝 Kid-Friendly EN (v1) ⚠️ Needs v3
[Content display]
⏩ Fast Forward to v3 [ENABLED Button]
```

### When At Latest Version
```
📝 Kid-Friendly EN (v3) 🟢 Latest
[Content display]
⏩ At Latest (v3) [DISABLED Button]
```

## Button States

### Text Fast Forward
**Behind:**
```
⏩ Fast Forward to v3 [ENABLED]
```

**At Latest:**
```
⏩ At Latest (v3) [DISABLED, GRAYED OUT]
```

### Audio Fast Forward
**Behind:**
```
⏩ Fast Forward Audio to v3 [ENABLED]
```

**At Latest:**
```
⏩ Audio At Latest (v3) [DISABLED, GRAYED OUT]
```

### Video Fast Forward
**Behind:**
```
⏩ Fast Forward Video to v3 [ENABLED]
```

**At Latest:**
```
⏩ Video At Latest (v3) [DISABLED, GRAYED OUT]
```

## Complete Page Example

```
Page 0001 (Expected Version: v3)

┌─────────────────────────────────────────┐
│ 📝 Kid-Friendly EN (v1) ⚠️ Needs v3    │
│ [Text content...]                       │
│ ⏩ Fast Forward to v3 [ENABLED]        │
├─────────────────────────────────────────┤
│ 📝 Kid-Friendly HI (v1) ⚠️ Needs v3    │
│ [Text content...]                       │
│ ⏩ Fast Forward to v3 [ENABLED]        │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 🎵 EN Audio (v3) 🟢 Latest              │
│ [Audio player]                          │
│ ⏩ Audio At Latest (v3) [DISABLED]     │
├─────────────────────────────────────────┤
│ 🎵 HI Audio (v2) ⚠️ Needs v3           │
│ [Audio player]                          │
│ ⏩ Fast Forward Audio to v3 [ENABLED]  │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 📹 EN Video (v1) ⚠️ Needs v3           │
│ [Video player]                          │
│ ⏩ Fast Forward Video to v3 [ENABLED]  │
├─────────────────────────────────────────┤
│ 📹 HI Video (v1) ⚠️ Needs v3           │
│ [Video player]                          │
│ ⏩ Fast Forward Video to v3 [ENABLED]  │
└─────────────────────────────────────────┘
```

## Expected Version Calculation

**Includes ALL asset types:**
```python
def get_expected_version_for_page(page_dir: Path) -> int:
    """Calculate max across ALL assets."""
    en_text_v = get_latest_version_number(page_dir, 'en_text')
    hi_text_v = get_latest_version_number(page_dir, 'hi_text')
    en_audio_v = get_latest_version_number(page_dir, 'en_audio')
    hi_audio_v = get_latest_version_number(page_dir, 'hi_audio')
    en_video_v = get_latest_version_number(page_dir, 'en_video')
    hi_video_v = get_latest_version_number(page_dir, 'hi_video')
    
    return max(en_text_v, hi_text_v, en_audio_v, 
               hi_audio_v, en_video_v, hi_video_v)
```

## Video Support Added

### Video Version Detection
```python
def get_latest_version_number(page_dir: Path, content_type: str) -> int:
    # For videos, scan files directly
    if content_type in ['en_video', 'hi_video']:
        import re
        pattern = 'page_video_en_v*.mp4' if content_type == 'en_video' else 'page_video_hi_v*.mp4'
        videos = list(page_dir.glob(pattern))
        max_version = 0
        for vid in videos:
            match = re.search(r'_v(\d+)\.mp4$', vid.name)
            if match:
                max_version = max(max_version, int(match.group(1)))
        return max_version
```

### Video Fast Forward
```python
def fast_forward_version(page_dir: Path, content_type: str, target_version: int):
    # Supports: en_text, hi_text, en_audio, hi_audio, en_video, hi_video
    
    if content_type in ['en_video', 'hi_video']:
        base_name = 'page_video_en' if content_type == 'en_video' else 'page_video_hi'
        extension = '.mp4'
        
        # Copy video file (binary)
        content = latest_path.read_bytes()
        new_path.write_bytes(content)
```

## Workflow Benefits

### 1. Always Visible
- **Fast forward buttons** always present
- **No confusion** about whether feature is available
- **Clear status** via disabled/enabled state

### 2. Consistent Interface
- **Same pattern** for text, audio, video
- **Same button position** under each asset
- **Same behavior** across all pages

### 3. Prevents Errors
- **Can't fast forward** when already at latest (disabled)
- **Can't click** grayed out buttons
- **Clear indication** of current state

### 4. Complete Coverage
- **Every asset** has fast forward option
- **Every page** shows version status
- **Every PDF** tracked consistently

## User Journey

### Scenario: Update One Page

**Initial State (All v1):**
```
Page 0001: Text v1, Audio v1, Video v1
Page 0002: Text v1, Audio v1, Video v1
```

**Step 1: Update page_0002 text to v2**
```
Page 0001: 
  - Text v1 ⚠️ Needs v2 → ⏩ Fast Forward [ENABLED]
  - Audio v1 ⚠️ Needs v2 → ⏩ Fast Forward [ENABLED]
  - Video v1 ⚠️ Needs v2 → ⏩ Fast Forward [ENABLED]

Page 0002:
  - Text v2 🟢 Latest → ⏩ At Latest [DISABLED]
  - Audio v1 ⚠️ Needs v2 → ⏩ Fast Forward [ENABLED]
  - Video v1 ⚠️ Needs v2 → ⏩ Fast Forward [ENABLED]
```

**Step 2: Fast forward page_0001 text**
```
Page 0001:
  - Text v2 🟢 Latest → ⏩ At Latest [DISABLED]
  - Audio v1 ⚠️ Needs v2 → ⏩ Fast Forward [ENABLED]
  - Video v1 ⚠️ Needs v2 → ⏩ Fast Forward [ENABLED]
```

**Step 3: Fast forward page_0001 audio & video**
```
Page 0001:
  - Text v2 🟢 Latest → ⏩ At Latest [DISABLED]
  - Audio v2 🟢 Latest → ⏩ At Latest [DISABLED]
  - Video v2 🟢 Latest → ⏩ At Latest [DISABLED]
```

**Final: All at v2, all buttons disabled**

## Button Behavior

### Streamlit Implementation
```python
# Always show button, disabled if at latest
is_at_latest = (current_version >= expected_version)
button_label = f"⏩ Fast Forward to v{expected_version}" if not is_at_latest else f"⏩ At Latest (v{expected_version})"

if st.button(button_label, key=f"ff_asset_{page_dir.name}", 
             use_container_width=True, disabled=is_at_latest):
    # Fast forward logic
    pass
```

### Visual States
**Enabled Button:**
- Full color
- Clickable cursor
- Shows target version

**Disabled Button:**
- Grayed out
- Not clickable
- Shows "At Latest"

## Version Status Indicators

### Behind (⚠️)
```
📝 Kid-Friendly EN (v1) ⚠️ Needs v3
🎵 EN Audio (v2) ⚠️ Needs v3
📹 EN Video (v1) ⚠️ Needs v3
```

### At Latest (🟢)
```
📝 Kid-Friendly EN (v3) 🟢 Latest
🎵 EN Audio (v3) 🟢 Latest
📹 EN Video (v3) 🟢 Latest
```

## Generation Button Changes

### Video Generation Buttons
**Also disabled when at latest:**

**Behind:**
```
🎬 Generate EN Video v3 [ENABLED]
```

**At Latest:**
```
🎬 EN Video v3 ✅ [DISABLED]
```

This prevents accidental regeneration when already up-to-date.

## Technical Implementation

### Files Modified

1. **`utils/versioning.py`**
   - Added video support to `fast_forward_version()`
   - Added video version detection to `get_latest_version_number()`
   - Supports: `.txt`, `.mp3`, `.mp4`

2. **`components/content_viewer.py`**
   - Updated `get_expected_version_for_page()` to include videos
   - Changed all fast forward buttons to always show (disabled when at latest)
   - Added consistent version status indicators
   - Updated video generation sections

### Code Pattern

**Every asset follows this pattern:**
```python
# 1. Get versions
current_version = get_latest_version_number(page_dir, content_type)
expected_version = get_expected_version_for_page(page_dir)

# 2. Show status
if current_version < expected_version:
    st.caption(f"📝 Asset (v{current_version}) ⚠️ Needs v{expected_version}")
else:
    st.caption(f"📝 Asset (v{current_version}) 🟢 Latest")

# 3. Display content
st.text_area(...) # or st.audio(...) or st.video(...)

# 4. Fast forward button (always show)
is_at_latest = (current_version >= expected_version)
button_label = f"⏩ Fast Forward to v{expected_version}" if not is_at_latest else f"⏩ At Latest (v{expected_version})"

if st.button(button_label, key=f"ff_{content_type}_{page_dir.name}", 
             use_container_width=True, disabled=is_at_latest):
    if fast_forward_version(page_dir, content_type, expected_version):
        st.success(f"✅ Fast forwarded to v{expected_version}")
        st.rerun()
```

## Logging

All fast forward actions logged:
```
22:04:15 | INFO | USER ACTION: FAST_FORWARD_EN_TEXT | PDF: download | Details: {'page': 'page_0001', 'from': 1, 'to': 3}
22:04:20 | INFO | USER ACTION: FAST_FORWARD_EN_AUDIO | PDF: download | Details: {'page': 'page_0001', 'from': 1, 'to': 3}
22:04:25 | INFO | USER ACTION: FAST_FORWARD_EN_VIDEO | PDF: download | Details: {'page': 'page_0001', 'from': 1, 'to': 3}
```

## Error States

### No File to Copy From
```
❌ Fast forward failed
```

### Already at Latest
```
Button is disabled, cannot click
```

## Summary

The comprehensive fast forward system now provides:

✅ **Complete Coverage** - All assets (text, audio, video)  
✅ **Always Visible** - Buttons always present  
✅ **Clear State** - Disabled when at latest  
✅ **Version Indicators** - ⚠️ needs update, 🟢 latest  
✅ **Consistent UI** - Same pattern everywhere  
✅ **Prevents Errors** - Can't fast forward when already current  
✅ **Full Logging** - All actions tracked  

Every asset on every page of every PDF now has clear version status and fast forward capability!
