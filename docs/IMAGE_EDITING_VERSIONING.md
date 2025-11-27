# Image Editing and Versioning System

## Overview

`image_to_use.png` for each page is now part of the versioning system with AI-powered editing capabilities using Replicate's **qwen-image-edit-plus** model.

## Features

### ✅ Image Versioning
- Track all versions of `image_to_use.png`
- Each edit creates a new version (v1, v2, v3, etc.)
- Preserve all previous versions
- Restore any version anytime

### ✅ AI Image Editing
- Edit images with natural language prompts
- Powered by Replicate's qwen-image-edit-plus
- High-quality edits preserving original context
- Fast processing with optimizations

### ✅ Fast Forward
- Copy current image to newer versions instantly
- Maintain version consistency across pages
- No regeneration needed

### ✅ Version History
- View all image versions with thumbnails
- See creation date and model used
- Restore previous versions with one click

## Setup

### 1. Install Requirements

```bash
pip install replicate requests
```

Or from requirements.txt:
```bash
pip install -r requirements.txt
```

### 2. Add API Token

Add to `.envrc`:
```bash
REPLICATE_API_TOKEN=your_token_here
```

Load environment:
```bash
direnv allow
# or
source .envrc
```

## UI Display

### Image Section Layout

```
┌──────────────────────────────┬──────────────────────────────┐
│  📷 Original Extract         │  🖼️ Image to Use (v2)       │
│                              │  ⚠️ Needs v3                 │
│  [Original image_001]        │                              │
│                              │  [Current versioned image]   │
│                              │                              │
│                              │  ✏️ Edit Image [Expand]     │
│                              │  ⏩ Fast Forward to v3       │
│                              │  📚 View 2 versions         │
└──────────────────────────────┴──────────────────────────────┘
```

### Version Status

**Behind:**
```
🖼️ Image to Use (v1) ⚠️ Needs v3
```

**At Latest:**
```
🖼️ Image to Use (v3) 🟢 Latest
```

**No Versions (Legacy):**
```
🖼️ Image to Use
```

## Image Editing Interface

### Expandable Editor

```
✏️ Edit Image [Click to expand]
├── Edit Instruction [Text Area]
│   Placeholder: "e.g., Make the background brighter,
│                 Remove text from image,
│                 Add more vibrant colors"
│
├── 🎨 Generate Edited Image (v3) [Button]
│   Disabled when prompt is empty
│
└── Status messages appear here
```

### Example Prompts

**Brightness/Color:**
```
Make the background brighter
Add more vibrant colors
Increase contrast and saturation
Make colors warmer
```

**Content Removal:**
```
Remove text from image
Remove watermark
Clear background elements
Remove people from scene
```

**Style Changes:**
```
Make it look more cartoon-like
Add a soft glow effect
Convert to black and white
Add vintage film grain
```

**Quality Enhancement:**
```
Enhance image quality
Sharpen details
Remove noise
Improve clarity
```

**Composition:**
```
Center the main subject
Add more space on the right
Crop to focus on the character
```

## Workflow Example

### Scenario: Improve Image for Kids' Story

**Step 1: View Current Image**
```
🖼️ Image to Use (v1) 🟢 Latest
[Image shows scene with dark background]
```

**Step 2: Expand Edit Interface**
```
Click: ✏️ Edit Image
```

**Step 3: Enter Edit Prompt**
```
Type: "Make the background much brighter and add 
       vibrant rainbow colors to make it more 
       appealing for children"
```

**Step 4: Generate Edit**
```
Click: 🎨 Generate Edited Image (v2)
Status: "Editing image with AI..." [Spinner]
```

**Step 5: Review Result**
```
✅ Created edited image v2
🖼️ Image to Use (v2) 🟢 Latest
[Brighter, more colorful image displayed]
```

**Step 6: View History**
```
Click: 📚 View 2 versions

v1 - 2024-10-24 20:00:00 - migrated
[Thumbnail of original]

v2 🟢 Latest - 2024-10-24 22:35:00 - qwen-image-edit-plus
[Thumbnail of edited version]
↩️ Restore v1 [Button]
```

## File Structure

### Versioned Image Files

```
page_0001/
├── image_001.png              # Original extract (untouched)
├── image_to_use_v1.png        # First version
├── image_to_use_v2.png        # Edited version
├── image_to_use_v3.png        # Another edit
└── versions.json              # Metadata
```

### versions.json

```json
{
  "image": {
    "latest": "image_to_use_v3.png",
    "versions": [
      {
        "file": "image_to_use_v1.png",
        "created": "2024-10-24T20:00:00",
        "model": "migrated"
      },
      {
        "file": "image_to_use_v2.png",
        "created": "2024-10-24T22:35:00",
        "model": "qwen-image-edit-plus"
      },
      {
        "file": "image_to_use_v3.png",
        "created": "2024-10-24T22:40:00",
        "model": "qwen-image-edit-plus"
      }
    ]
  }
}
```

## Migration

### Automatic Legacy Migration

Existing `image_to_use.png` files are automatically migrated to `image_to_use_v1.png`:

**Before Migration:**
```
page_0001/
├── image_to_use.png
└── (no versions.json)
```

**After First View:**
```
page_0001/
├── image_to_use_v1.png        # Renamed from image_to_use.png
└── versions.json              # Created with v1 entry
```

No data loss - original file preserved as v1.

## Fast Forward

### When to Use

**Scenario:** Page 0002 has edited image at v3, but page 0001 is still at v1.

**Display:**
```
Page 0001:
  🖼️ Image to Use (v1) ⚠️ Needs v3
  ⏩ Fast Forward Image to v3 [ENABLED]
```

**Action:**
```
Click: ⏩ Fast Forward Image to v3
Result:
  - Copies v1 → v2
  - Copies v1 → v3
  - Updates metadata
  - Instant (no API call)
```

**After:**
```
Page 0001:
  🖼️ Image to Use (v3) 🟢 Latest
  ⏩ Image At Latest (v3) [DISABLED]
```

## Version History

### View All Versions

```
Click: 📚 View 3 versions

┌─────────────────────────────────────────┐
│ v1 - 2024-10-24 20:00:00 - migrated    │
│ [Thumbnail 200px]                       │
│ ↩️ Restore v1                           │
├─────────────────────────────────────────┤
│ v2 - 2024-10-24 22:35:00                │
│ qwen-image-edit-plus                    │
│ [Thumbnail 200px]                       │
│ ↩️ Restore v2                           │
├─────────────────────────────────────────┤
│ v3 🟢 Latest - 2024-10-24 22:40:00      │
│ qwen-image-edit-plus                    │
│ [Thumbnail 200px]                       │
│ [No restore button - already latest]   │
└─────────────────────────────────────────┘
```

### Restore Previous Version

```
Click: ↩️ Restore v2
Result:
  - v2 becomes latest
  - v3 still exists (not deleted)
  - Can switch back to v3 anytime
```

## API Details

### Replicate Model: qwen-image-edit-plus

**Model:** `qwen/qwen-image-edit-plus`

**Input Parameters:**
- `image`: Image file or URL
- `prompt`: Text instruction for editing
- `go_fast`: Enable optimizations (default: true)
- `aspect_ratio`: "match_input_image" (default)
- `output_format`: "png" (for quality)
- `output_quality`: 95 (high quality)
- `seed`: Optional for reproducibility

**Output:**
- Edited image as PNG
- Preserves original dimensions
- High-quality output

### API Usage

```python
from edit_images import edit_image_with_prompt

success = edit_image_with_prompt(
    image_path=current_image,
    prompt="Make the background brighter",
    output_path=new_version_path,
    output_format='png'
)
```

## Error Handling

### Common Issues

**1. API Token Missing**
```
❌ Error: REPLICATE_API_TOKEN not found in environment
```
**Fix:** Add token to `.envrc` and reload

**2. API Call Failed**
```
❌ Image editing failed
```
**Fix:** Check internet connection, API quota

**3. Invalid Image**
```
❌ Error: [error details]
```
**Fix:** Ensure source image exists and is valid PNG

## Costs

### Replicate Pricing

qwen-image-edit-plus runs on Replicate's platform:
- Pay per API call
- Typical cost: ~$0.01-0.05 per edit
- Fast processing with go_fast=true

**Cost Comparison:**
- Manual editing: Time-intensive
- API editing: Fast, consistent, affordable
- Fast forward: **FREE** (no API call)

## Benefits

### 1. Version Control
- Never lose an image edit
- Try different edits without risk
- Compare versions easily
- Restore anytime

### 2. AI-Powered
- Natural language instructions
- High-quality edits
- Fast processing
- Consistent results

### 3. Workflow Integration
- Part of overall versioning system
- Matches text/audio/video versions
- Fast forward support
- PDF-wide tracking

### 4. Child-Friendly Content
- Brighten dark images
- Add vibrant colors
- Remove inappropriate elements
- Enhance appeal for kids

## Limitations

### 1. Image Format
- Primary support: PNG
- Input can be JPG/WebP
- Output always PNG (high quality)

### 2. Edit Scope
- Works best for style/color/content adjustments
- Not for complete image generation
- Maintains original composition
- Limited dramatic transformations

### 3. API Dependency
- Requires internet connection
- Needs valid API token
- Subject to API rate limits
- Costs per edit

## Best Practices

### 1. Descriptive Prompts
**Good:**
```
"Make the background 30% brighter while keeping 
 the character colors the same"
```

**Better:**
```
"Brighten background, keep character unchanged"
```

**Best:**
```
"Increase background brightness"
```

Clear, specific, concise prompts work best.

### 2. Iterative Editing
```
v1: Original
v2: "Brighten image"
v3: "Add more vibrant colors" (edit v2, not v1)
```

Build on previous edits for refinement.

### 3. Version Management
- Keep meaningful versions
- Use fast forward for consistency
- Restore when needed
- Review history before new edits

### 4. Prompt Types by Goal

**Enhancement:**
- "Improve image quality"
- "Enhance colors"
- "Sharpen details"

**Adjustment:**
- "Make brighter"
- "Adjust contrast"
- "Warm up colors"

**Removal:**
- "Remove text"
- "Clear background"
- "Delete watermark"

**Style:**
- "Make cartoon-like"
- "Add soft glow"
- "Vintage effect"

## Integration with Pipeline

### Complete Page Workflow

```
1. Extract PDF → image_001.png + text
2. Create image_to_use.png → v1 (migrated)
3. Rewrite text for kids → v2
4. Edit image for kids → image v2
5. Generate audio → audio v2
6. Create video → video v2

All assets at v2 ✅
```

### Cross-Page Consistency

**Scenario:** Edit page 0001 image to v2

**Result:**
```
Page 0001: Image v2 🟢 Latest
Page 0002: Image v1 ⚠️ Needs v2 → Fast Forward
Page 0003: Image v1 ⚠️ Needs v2 → Fast Forward
...
```

One-click fast forward maintains consistency.

## Logging

All image operations are logged:

```
22:35:10 | INFO | USER ACTION: EDIT_IMAGE | PDF: download | Details: {'page': 'page_0001', 'prompt': 'Make brighter', 'new_version': 2}
22:35:15 | INFO | API CALL: Replicate | qwen-image-edit-plus | 13 chars | SUCCESS
22:35:15 | INFO | FILE OPERATION: edit_image_page_0001_v2 | SUCCESS
```

```
22:40:20 | INFO | USER ACTION: FAST_FORWARD_IMAGE | PDF: download | Details: {'page': 'page_0002', 'from': 1, 'to': 2}
```

## Technical Implementation

### Module: edit_images.py

```python
def edit_image_with_prompt(
    image_path: Path,
    prompt: str,
    output_path: Path,
    output_format: str = 'png'
) -> bool:
    """Edit image with AI using text prompt."""
```

### Versioning: utils/versioning.py

```python
# Added image support
content_type = 'image'
base_name = 'image_to_use'
extension = '.png'
is_binary = True
```

### UI: components/content_viewer.py

```python
# Image editing interface
with st.expander("✏️ Edit Image"):
    prompt = st.text_area("Edit Instruction")
    if st.button("🎨 Generate Edited Image"):
        edit_image_with_prompt(...)
        create_new_version(page_dir, 'image', ...)
```

## Future Enhancements

### Planned

**1. Multiple Reference Images**
```python
edit_image_with_prompt(
    image_path,
    prompt,
    output_path,
    reference_images=[style_ref, pose_ref]
)
```

**2. Style Transfer**
```
"Apply the artistic style from uploaded image"
```

**3. Batch Editing**
```
Apply same prompt to all pages at once
```

**4. Preset Effects**
```
Quick buttons: Brighten | Enhance | Kid-Friendly
```

## Summary

Image editing and versioning provides:

✅ **AI-Powered Editing** - Natural language image edits  
✅ **Complete Versioning** - Track all image changes  
✅ **Fast Forward** - Quick version sync  
✅ **Version History** - View and restore any version  
✅ **Pipeline Integration** - Matches text/audio/video system  
✅ **Child-Friendly** - Optimize images for kids  
✅ **Cost-Effective** - Affordable API, free fast forward  

Perfect for iterative image improvement in your story creation pipeline!
