# Queue Mode Locations

## ✅ All Queue Mode Options Available

Queue mode is now available in **three locations** for both image editing and video generation:

---

## 1. Per-Page Image Editing
**Location**: Individual page viewer → "👁️ View Content" section

**How to Access**:
1. Select a PDF
2. Scroll down to "👁️ View Content"
3. Click on a page to expand it
4. Find "✏️ Edit Image" expander
5. Enter your edit prompt
6. Select **"Queue for Later"** radio button
7. Click "📝 Queue Edit for v{N}"

**Output**: Creates `image_edit_prompt_for_v{N}.txt` in the page directory

---

## 2. Per-Page Video Generation
**Location**: Individual page viewer → "🎥 Image-to-Video Animation" section

**How to Access**:
1. Select a PDF
2. Scroll down to "👁️ View Content"
3. Click on a page to expand it
4. Find "🎥 Image-to-Video Animation" section
5. Expand "🎬 Generate Video from Image"
6. Enter your motion prompt
7. Select **"Queue for Later"** radio button
8. Click "📝 Queue Video for v{N}"

**Output**: Creates `image_to_video_prompt_for_v{N}.txt` in the page directory

---

## 3. Batch Video Generation
**Location**: "🎬 Videos" tab → "🎥 Batch Image-to-Video Generation" section

**How to Access**:
1. Select a PDF
2. Go to "🎬 Videos" tab
3. Find "🎥 Batch Image-to-Video Generation" section
4. Enter your motion prompt (applies to all pages)
5. Select **"Queue for Later"** radio button
6. Choose one of:
   - "📝 Queue Videos for All Pages" - queues all pages
   - "📝 Queue Only Missing Videos" - queues only pages without videos

**Output**: Creates `image_to_video_prompt_for_v{N}.txt` in each page directory

---

## Summary of Queue Mode Features

| Feature | Location | Scope | Output File |
|---------|----------|-------|-------------|
| **Image Editing** | Per-page viewer | Single page | `image_edit_prompt_for_v{N}.txt` |
| **Video from Image** | Per-page viewer | Single page | `image_to_video_prompt_for_v{N}.txt` |
| **Batch Video** | Videos tab | Multiple pages | `image_to_video_prompt_for_v{N}.txt` (per page) |

---

## How to Process Queued Tasks

Once you've queued tasks, run the background processor:

```bash
# Process all queued tasks once
python background_processor.py --once

# Process continuously (checks every 60 seconds)
python background_processor.py

# Process specific PDF only
python background_processor.py --pdf-stem download

# Custom interval (e.g., every 5 minutes)
python background_processor.py --interval 300
```

---

## Visual Guide

### Radio Button Options
Every queue-enabled section now has:
- ⚡ **Execute Now** - Process immediately via Replicate API
- 📝 **Queue for Later** - Save prompt for background processing

### Button Labels Change
- Execute Now mode: "🎬 Generate..." or "🎨 Generate..."
- Queue for Later mode: "📝 Queue..." 

---

## Notes

- Queue mode respects versioning - prompts target the next available version
- Batch operations queue one prompt file per page
- Background processor processes prompts in order
- Completed prompts are renamed to `.txt.completed`
- Failed prompts are renamed to `.txt.failed` with error message
- The dashboard automatically shows new versions once processed
