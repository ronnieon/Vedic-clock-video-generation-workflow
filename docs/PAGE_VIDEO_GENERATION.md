# Page Video Generation Feature

## Overview

Added **version-aware page video generation** that combines `image_to_use.png` with audio files to create individual page videos. Videos are tracked with version numbers matching the audio version.

## Location

**UI Section:** Under each page in "📑 View Extracted Pages" → "🎬 Page Videos"

## How It Works

### Prerequisites
1. **image_to_use.png** must exist in page directory
2. **Audio files** (EN and/or HI) must be generated

### Version Matching
- Page video version **matches audio version**
- If audio is v2, video will be v2
- If audio is v1, video will be v1

### File Naming
```
page_0001/
  page_video_en_v1.mp4
  page_video_en_v2.mp4  ← Latest
  page_video_hi_v1.mp4
  page_video_hi_v2.mp4  ← Latest
```

## UI Display

### Button States

**No Video Exists:**
```
🎬 Generate EN Video (v2)
```

**Video Exists But Outdated:**
```
🎬 Generate EN Video v2 (current: v1)
```

**Video Up-to-Date:**
```
🎬 EN Video v2 ✅
```

### Layout

```
┌─────────────────────────────────────────────────────┐
│ 🎬 Page Videos                                      │
├──────────────────────┬──────────────────────────────┤
│ EN Video             │ HI Video                     │
├──────────────────────┼──────────────────────────────┤
│ 🎬 Generate EN Video │ 🎬 Generate HI Video v2      │
│    v2 (current: v1)  │    (current: v1)             │
│ [Button]             │ [Button]                     │
│                      │                              │
│ 📹 EN Video (v1)     │ 📹 HI Video (v1)             │
│ [Video Player]       │ [Video Player]               │
└──────────────────────┴──────────────────────────────┘
```

## Generation Process

### Step-by-Step

1. **Click Generate Button**
   - Shows spinner: "Creating EN video v2..."

2. **Load Audio**
   - Reads latest audio file
   - Gets duration from audio

3. **Create Image Clip**
   - Loads `image_to_use.png`
   - Sets duration to match audio

4. **Combine**
   - Merges image + audio
   - Encodes as MP4 (H.264 video, AAC audio)

5. **Save**
   - Writes to `page_video_en_v2.mp4`
   - Logs operation

6. **Display**
   - Shows success message
   - Reloads page to show video player

### Technical Details

**Video Settings:**
- **FPS:** 24
- **Video Codec:** libx264 (H.264)
- **Audio Codec:** AAC
- **Duration:** Matches audio length exactly

**Libraries Used:**
- `moviepy.editor.ImageClip` - Static image
- `moviepy.editor.AudioFileClip` - Audio track
- `PIL.Image` - Image loading

## Version Tracking

### Automatic Version Detection

The system automatically:
1. Finds max audio version (EN and HI)
2. Sets expected video version to match
3. Checks if current video version matches expected
4. Shows appropriate button label

### Example Scenarios

**Scenario 1: First Video**
```
Audio: v1 exists
Video: None
Button: "🎬 Generate EN Video (v1)"
```

**Scenario 2: Audio Updated**
```
Audio: v2 exists
Video: v1 exists
Button: "🎬 Generate EN Video v2 (current: v1)"
Status: ⚠️ Outdated
```

**Scenario 3: Up-to-Date**
```
Audio: v2 exists
Video: v2 exists
Button: "🎬 EN Video v2 ✅"
Status: ✅ Complete
```

## Integration with Workflow Status

### Sidebar Tracking

The "🎬 Create Page Videos" stage in the sidebar now:

1. **Checks expected version** from audio stage
2. **Counts videos at expected version**
3. **Shows progress** (e.g., "4/22 [needs v2]")
4. **Lists missing/outdated videos**

### Example Status Display

```
⚠️ 🎬 Create Page Videos (2/22) [needs v2]
  ✅ View 2 complete file(s)
    ✅ page_0001/page_video_en_v2.mp4 (v2)
    ✅ page_0001/page_video_hi_v2.mp4 (v2)
  ❌ View 20 missing/outdated file(s)
    ❌ page_0002/page_video_en.mp4 (has v1, needs v2)
    ❌ page_0002/page_video_hi.mp4 (has v1, needs v2)
    ...
```

## Audio Generation Updates

### Also Version-Aware

Audio generation has been updated to use versioning:

**Button Labels:**
- First time: `🎙️ Generate Audio (v1)`
- After text update: `🎙️ Generate Audio v2 (current: v1)`
- Create new: `🎙️ Create New Audio (v3)`

**File Naming:**
```
page_0001/
  final_text_en_v1.mp3
  final_text_en_v2.mp3  ← Latest
  final_text_hi_v1.mp3
  final_text_hi_v2.mp3  ← Latest
```

**Metadata Tracking:**
- Stored in `versions.json`
- Includes timestamp, model used
- Tracks which is latest

## Workflow Example

### Complete Page Update Flow

**Step 1: Update Text**
```
Action: Click "Create New Version (v2)" for text
Result: 
  - final_text_en_v2.txt created
  - final_text_hi_v2.txt created
```

**Step 2: Generate Audio**
```
Action: Click "🎙️ Generate Audio v2 (current: v1)"
Result:
  - final_text_en_v2.mp3 created
  - final_text_hi_v2.mp3 created
```

**Step 3: Generate Videos**
```
Action: Click "🎬 Generate EN Video v2 (current: v1)"
Result:
  - page_video_en_v2.mp4 created
  - Video player shows new video

Action: Click "🎬 Generate HI Video v2 (current: v1)"
Result:
  - page_video_hi_v2.mp4 created
  - Video player shows new video
```

**Step 4: Check Sidebar**
```
Status Updates:
  ✅ ✏️ Rewrite for Kids (2/22) [needs v2]
  ✅ 🎙️ Generate Audio (2/22) [needs v2]
  ✅ 🎬 Create Page Videos (2/22) [needs v2]
  ⚠️ 🎞️ Create Final Slideshow (0/2) [needs v2]
```

## Error Handling

### Missing Prerequisites

**No image_to_use.png:**
```
ℹ️ Need image_to_use.png and audio files to generate videos
```

**No audio:**
```
ℹ️ Generate EN audio first
```

### Generation Errors

If video generation fails:
```
❌ Video generation failed: [error message]
```

Common issues:
- Corrupted audio file
- Missing image file
- Insufficient disk space
- MoviePy encoding errors

## Performance

### Generation Time

Typical times per video:
- **Short audio (10s):** ~5 seconds
- **Medium audio (30s):** ~10 seconds
- **Long audio (60s):** ~15 seconds

### File Sizes

Approximate sizes:
- **10s video:** ~200 KB
- **30s video:** ~600 KB
- **60s video:** ~1.2 MB

## Benefits

### 1. Version Consistency
- Videos always match audio version
- No mismatched audio/video combinations
- Clear tracking of what needs updating

### 2. Individual Page Control
- Generate videos one page at a time
- Preview before creating full slideshow
- Easy to regenerate specific pages

### 3. Quality Control
- View each page video before combining
- Verify audio sync
- Check image quality

### 4. Incremental Progress
- Don't need to regenerate all videos
- Work on one page at a time
- System tracks completion

## Future Enhancements

Potential additions:
- Bulk "generate all page videos" button
- Video preview before generation
- Custom video settings (FPS, codec)
- Transition effects between pages
- Text overlays on videos
- Background music options

## Technical Notes

### MoviePy Integration

The system uses MoviePy for video generation:

```python
from moviepy.editor import ImageClip, AudioFileClip

# Load audio
audio_clip = AudioFileClip(str(audio_path))
duration = audio_clip.duration

# Create image clip
image_clip = ImageClip(str(image_path)).set_duration(duration)

# Combine
video_clip = image_clip.set_audio(audio_clip)

# Write
video_clip.write_videofile(
    str(output_path),
    fps=24,
    codec='libx264',
    audio_codec='aac',
    logger=None
)

# Cleanup
video_clip.close()
audio_clip.close()
```

### Version Detection

Videos are detected using regex pattern matching:

```python
import re

existing_videos = sorted(page_dir.glob('page_video_en_v*.mp4'))
current_version = 0

for vid in existing_videos:
    match = re.search(r'_v(\d+)\.mp4$', vid.name)
    if match:
        current_version = max(current_version, int(match.group(1)))
```

### Expected Version Calculation

```python
en_audio_version = get_version_count(page_dir, 'en_audio')
hi_audio_version = get_version_count(page_dir, 'hi_audio')
expected_video_version = max(en_audio_version, hi_audio_version)
```

## Summary

The page video generation feature provides:
- ✅ **Version-aware** video creation
- ✅ **Individual page** control
- ✅ **Automatic tracking** in sidebar
- ✅ **Clear status** indicators
- ✅ **Easy regeneration** when audio updates

Videos are created by combining `image_to_use.png` with the latest audio, and version numbers automatically match the audio version to maintain consistency throughout the pipeline.
