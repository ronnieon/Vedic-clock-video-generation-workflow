# Image-to-Video Animation System

## Overview

Convert static images into animated videos with AI-powered motion using Replicate's **wan-video/wan-2.2-5b-fast** model. Each page's `image_to_use.png` can be animated with custom motion prompts, creating engaging video content with full version tracking.

## Features

### ✅ AI-Powered Animation
- Convert static images to animated videos
- Natural language motion prompts
- Customizable frame count, FPS, aspect ratio
- High-quality 720p output

### ✅ Version Control
- Track all video versions (`page_image_video_v1.mp4`, `v2.mp4`, etc.)
- Restore previous versions anytime
- Fast forward to sync across pages
- Complete history with timestamps

### ✅ Advanced Controls
- **Frames**: 81-121 (81 recommended for best results)
- **Aspect Ratio**: 16:9 or 9:16
- **FPS**: 5-30 (default 24)
- **Sample Shift**: 1-20 (controls motion smoothness)

## UI Layout

### Video Display & Generation

```
┌──────────────────────────────┬──────────────────────────────┐
│  🎥 Current Video (Left)     │  🎬 Generation (Right)       │
├──────────────────────────────┼──────────────────────────────┤
│  🎥 Image Video (v1) 🟢      │  🎬 Generate Video from      │
│  [Video Player]              │     Image [Expand]           │
│                              │                              │
│  ⏩ Fast Forward to v2       │  Using: image_to_use_v2.png  │
│  📚 View 1 version(s)        │                              │
│                              │  Motion Prompt:              │
│                              │  [Text Area]                 │
│                              │                              │
│                              │  ⚙️ Advanced Options         │
│                              │  🎬 Generate Video (v2)      │
└──────────────────────────────┴──────────────────────────────┘
```

## Workflow Example

### Scenario: Animate Story Page

**Step 1: View Current Image**
```
Page has image_to_use_v2.png
No video generated yet
```

**Step 2: Expand Video Generator**
```
Click: 🎬 Generate Video from Image
Shows: "Using latest image: image_to_use_v2.png"
```

**Step 3: Enter Motion Prompt**
```
Type: "camera slowly zooms in, character's eyes 
       glow with power, subtle wind effect on clothing"
```

**Step 4: Adjust Settings (Optional)**
```
Frames: 81 (recommended)
Aspect Ratio: 16:9
FPS: 24
Sample Shift: 5.0
```

**Step 5: Generate Video**
```
Click: 🎬 Generate Video (v1)
Status: "Generating video from image (this may take 1-2 minutes)..."
Progress: [Spinner]
```

**Step 6: Review Result**
```
✅ Created image video v1
🎥 Image Video (v1) 🟢 Latest
[Video plays automatically]
```

**Step 7: Iterate (Optional)**
```
Change prompt: "camera pans left to right, revealing more of the scene"
Generate: v2
Compare with v1 in version history
```

## Motion Prompt Examples

### Camera Movements

**Zoom:**
```
camera slowly zooms in, focusing on the character
camera zooms out, revealing the full landscape
```

**Pan:**
```
camera pans from left to right across the scene
gentle horizontal pan, following the character's gaze
camera pans up to reveal the sky
```

**Dolly:**
```
camera moves closer to the character
camera pulls back to show more context
```

### Character Animation

**Subtle Movement:**
```
character's eyes blink, slight head movement
character breathes naturally, clothing shifts slightly
hair and clothing move gently in the wind
```

**Action:**
```
character raises their hand, pointing forward
character turns their head to look around
character's cloak billows dramatically
```

### Atmospheric Effects

**Nature:**
```
clouds drift slowly across the sky
leaves rustle in a gentle breeze
water ripples and flows naturally
```

**Magic/Fantasy:**
```
magical aura pulses around the character
mystical energy swirls in the air
divine light radiates from the character
```

**Environment:**
```
dust particles float in the air
fog rolls across the ground
shadows shift with moving clouds
```

### Combined Prompts

```
camera slowly zooms in while the character's eyes glow with power, 
wind gently moves their clothing, magical energy swirls around them

camera pans right to left as the hero walks forward, 
their cloak billowing behind them, determination in their eyes

gentle camera drift revealing the landscape while clouds move 
overhead, birds fly in the distance, sunlight shifts across the scene
```

## File Structure

### Versioned Video Files

```
page_0001/
├── image_to_use_v1.png          # Source image v1
├── image_to_use_v2.png          # Source image v2 (edited)
├── page_image_video_v1.mp4      # Video from v1 image
├── page_image_video_v2.mp4      # Video from v2 image (different motion)
├── page_image_video_v3.mp4      # Another animation of v2 image
└── versions.json                # Metadata
```

### versions.json

```json
{
  "image": {
    "latest": "image_to_use_v2.png",
    "versions": [...]
  },
  "image_video": {
    "latest": "page_image_video_v3.mp4",
    "versions": [
      {
        "file": "page_image_video_v1.mp4",
        "created": "2024-10-25T00:00:00",
        "model": "wan-video/wan-2.2-5b-fast"
      },
      {
        "file": "page_image_video_v2.mp4",
        "created": "2024-10-25T00:15:00",
        "model": "wan-video/wan-2.2-5b-fast"
      },
      {
        "file": "page_image_video_v3.mp4",
        "created": "2024-10-25T00:30:00",
        "model": "wan-video/wan-2.2-5b-fast"
      }
    ]
  }
}
```

## Version Management

### Fast Forward

**Scenario:** Page 0002 has video at v3, page 0001 at v1

**Display:**
```
Page 0001:
  🎥 Image Video (v1) ⚠️ Needs v3
  ⏩ Fast Forward Video to v3 [ENABLED]
```

**Action:**
```
Click: ⏩ Fast Forward Video to v3
Result:
  - Copies v1 → v2
  - Copies v1 → v3
  - Updates metadata
  - Instant (no API call)
```

**After:**
```
Page 0001:
  🎥 Image Video (v3) 🟢 Latest
  ⏩ Video At Latest (v3) [DISABLED]
```

### Version History

```
Click: 📚 View 3 versions

┌─────────────────────────────────────────┐
│ v1 - 2024-10-25 00:00:00                │
│ wan-video/wan-2.2-5b-fast               │
│ [Video Player]                          │
│ ↩️ Restore v1                           │
├─────────────────────────────────────────┤
│ v2 - 2024-10-25 00:15:00                │
│ wan-video/wan-2.2-5b-fast               │
│ [Video Player]                          │
│ ↩️ Restore v2                           │
├─────────────────────────────────────────┤
│ v3 🟢 Latest - 2024-10-25 00:30:00      │
│ wan-video/wan-2.2-5b-fast               │
│ [Video Player]                          │
│ [No restore - already latest]           │
└─────────────────────────────────────────┘
```

### Restore Version

```
Click: ↩️ Restore v2
Result:
  - v2 becomes latest
  - v3 still exists (not deleted)
  - Can switch back to v3 anytime
```

## API Details

### Replicate Model: wan-video/wan-2.2-5b-fast

**Model:** `wan-video/wan-2.2-5b-fast`

**Input Parameters:**
- `image`: Input image file
- `prompt`: Motion/animation description
- `num_frames`: 81-121 (81 recommended)
- `aspect_ratio`: "16:9" or "9:16"
- `resolution`: "720p" (default)
- `frames_per_second`: 5-30 (24 default)
- `sample_shift`: 1-20 (5 default, controls smoothness)
- `go_fast`: Enable optimizations (default: true)
- `seed`: Optional for reproducibility
- `negative_prompt`: What to avoid
- `optimize_prompt`: Translate to Chinese

**Output:**
- Single MP4 video file
- Duration based on frames/FPS
- High quality 720p

### API Usage

```python
from generate_image_videos import generate_video_from_image

success = generate_video_from_image(
    image_path=current_image,
    prompt="camera slowly zooms in, subtle movements",
    output_path=new_version_path,
    num_frames=81,
    aspect_ratio="16:9",
    frames_per_second=24
)
```

## Advanced Options Explained

### Number of Frames

- **81 frames**: Best quality/speed balance ⭐ Recommended
- **90-100 frames**: Slightly longer animation
- **121 frames**: Maximum length, slower generation

**Pricing Note:** Billed based on video duration at 16 FPS

### Aspect Ratio

- **16:9**: Standard widescreen (832x480px at 720p)
- **9:16**: Vertical/mobile (480x832px at 720p)

Choose based on your final output format.

### Frames Per Second

- **24 FPS**: Cinematic feel ⭐ Recommended
- **16 FPS**: Slightly choppy, lower cost
- **30 FPS**: Smooth, higher cost

Higher FPS = smoother motion but longer duration = higher cost.

### Sample Shift

- **1-5**: Subtle, gentle motion
- **5-10**: Moderate movement ⭐ Default
- **10-20**: Dramatic, intense motion

Controls how much the video diverges from the static image.

## Cost Considerations

### Replicate Pricing

- Billed per second of generated video
- Duration = (num_frames / 16 FPS) for pricing
- Example: 81 frames = ~5 seconds at 16 FPS
- Typical cost: $0.05-0.15 per video

**Cost Optimization:**
- Use 81 frames (recommended)
- Use 24 FPS (standard)
- Use `go_fast=true` (default)
- Avoid regenerating unnecessarily

**Free Alternative:**
- Fast forward existing videos (no API call)

## Integration with Pipeline

### Complete Workflow

```
1. Extract PDF → image_001.png
2. Create image_to_use.png → v1 (migrated)
3. Rewrite text → text v2
4. Edit image → image v2
5. Generate image video → video v2
6. Generate audio → audio v2
7. Create final video (image video + audio) → final v2

All assets at v2 ✅
```

### Relationship with Other Videos

**Image Videos** (`page_image_video_v*.mp4`):
- Animated version of static image
- Motion from AI (wan-video)
- No audio included
- Standalone animation

**Page Videos** (`page_video_en_v*.mp4`, `page_video_hi_v*.mp4`):
- Static image + audio voiceover
- Created from image + text-to-speech
- Language-specific
- Current pipeline stage

**Final Slideshows**:
- Concatenation of all page videos
- Full story with audio
- Export-ready

## Logging

All operations are logged:

```
02:00:10 | INFO | USER ACTION: GENERATE_IMAGE_VIDEO | PDF: download | Details: {'page': 'page_0001', 'prompt': 'camera zooms in', 'new_version': 2}
02:01:45 | INFO | API CALL: Replicate | wan-video/wan-2.2-5b-fast | 15 chars | SUCCESS
02:01:45 | INFO | FILE OPERATION: gen_image_video_page_0001_v2 | SUCCESS
```

```
02:05:20 | INFO | USER ACTION: FAST_FORWARD_IMAGE_VIDEO | PDF: download | Details: {'page': 'page_0002', 'from': 1, 'to': 2}
```

## Best Practices

### 1. Prompt Crafting

**Good:**
```
"camera slowly zooms in, character's eyes glow"
```

**Better:**
```
"camera zooms in, eyes glow with divine power"
```

**Best:**
```
"gentle zoom focusing on character's glowing eyes, 
 subtle wind moves hair and clothing"
```

Clear, specific, detailed prompts work best.

### 2. Iterative Refinement

```
v1: "camera zooms in"
    → Too simple, not much motion

v2: "camera zooms in, character moves slightly"
    → Better, but still static

v3: "camera zooms in while character's eyes glow, 
     wind gently moves their hair and cloak"
    → Perfect! Dynamic and engaging
```

Build on what works.

### 3. Consistency Across Pages

For a cohesive story:
- Use similar camera movements
- Maintain consistent motion intensity
- Match pacing (frame count, FPS)

### 4. Version Management

- Keep meaningful versions only
- Use fast forward for consistency
- Restore when experimenting
- Review history before new generation

## Troubleshooting

### Common Issues

**1. Video Generation Fails**
```
Error: "Video generation failed"
```
**Fix:**
- Check `REPLICATE_API_TOKEN` in environment
- Verify image exists and is valid
- Try simpler prompt
- Check API quota

**2. Long Generation Time**
```
Status: "Generating... (1-2 minutes)"
```
**Normal:** 60-120 seconds per video
**Fix if stuck:** Check internet, API status

**3. Poor Quality Output**
```
Video looks choppy or unnatural
```
**Fix:**
- Use 81 frames (recommended)
- Reduce sample_shift (5-7)
- Simplify motion prompt
- Ensure source image is high quality

**4. Version Not Updating**
```
Still shows old version after generation
```
**Fix:** Refresh page or click Rerun

## Future Enhancements

### Planned

**1. Batch Generation**
```
Generate videos for all pages at once
Apply same prompt pattern to entire PDF
```

**2. Prompt Templates**
```
Quick buttons for common motions:
- Zoom In
- Pan Scene
- Character Focus
- Atmospheric
```

**3. Audio Integration**
```
Use image videos instead of static images
Combine with voiceover for richer experience
```

**4. Export Options**
```
Batch export all image videos
Create compilation videos
```

## Summary

Image-to-video animation provides:

✅ **AI-Powered Animation** - Static → animated with prompts  
✅ **Complete Versioning** - Track all video variations  
✅ **Fast Forward** - Quick version sync  
✅ **Version History** - View and restore any version  
✅ **Advanced Controls** - Fine-tune frames, FPS, motion  
✅ **Pipeline Integration** - Works with existing workflow  
✅ **High Quality** - 720p output, cinematic FPS  
✅ **Affordable** - ~$0.05-0.15 per video  

Perfect for bringing static story images to life with engaging motion!
