# PDF to Slideshow Pipeline Dashboard

A comprehensive Streamlit application for converting PDFs into multilingual (English & Hindi) video slideshows with voiceovers.

## 🎯 Features

Complete end-to-end pipeline:
1. **📄 Extract Content** - Extract text and images from PDF
2. **📖 Plan Story** - Clean and organize extracted text using AI
3. **✏️ Rewrite for Kids** - Create kid-friendly versions in English and Hindi
4. **🎙️ Generate Audio** - Create voiceovers using ElevenLabs
5. **🎬 Create Slideshow** - Build final MP4 slideshow videos

## 📁 Project Structure

```
VEDIC CLOCK WORKFLOW/
├── app.py                          # Main Streamlit dashboard
├── components/                     # UI components
│   ├── __init__.py
│   ├── pipeline_stages.py          # All 5 pipeline stage components
│   └── content_viewer.py           # Content viewing components
├── utils/                          # Utility functions
│   ├── __init__.py
│   └── workflow.py                 # Workflow status management
├── extract_pdfs.py                 # PDF extraction logic
├── clean_and_concatenate.py        # Story planning & cleaning
├── rewrite_for_kids.py             # AI rewriting for kids
├── generate_voiceovers.py          # Audio generation
├── make_slideshows.py              # Video slideshow creation
├── requirements.txt                # Python dependencies
└── extracted/                      # Output directory (auto-created)
    └── {pdf_name}/
        ├── page_0001/
        │   ├── text.txt            # Raw extracted text
        │   ├── clean_text.txt      # Cleaned text
        │   ├── final_text_en.txt   # Kid-friendly English
        │   ├── final_text_hi.txt   # Kid-friendly Hindi
        │   ├── final_text_en.mp3   # English audio
        │   ├── final_text_hi.mp3   # Hindi audio
        │   ├── image_001.png       # Extracted images
        │   └── image_to_use.png    # Selected image for slideshow
        ├── page_0002/
        ├── ...
        ├── whole_story_cleaned.txt # Complete cleaned story
        ├── english_slideshow.mp4   # Final English video
        └── hindi_slideshow.mp4     # Final Hindi video
```

## 📚 Documentation & PDFs

All architectural, workflow, and enhancement notes have been moved into the `docs/` folder to declutter the root directory. Key files include:
- `VERSIONING_SYSTEM.md` / `VERSION_DISCOVERY.md` / `VERSION_AWARE_WORKFLOW.md` – Versioning concepts and evolution
- `QUEUE_MODE.md` / `QUEUE_MODE_LOCATIONS.md` – Queue processing behavior and placement rules
- `S3_SYNC.md` / `S3_SYNC_BEHAVIOR.md` – Object storage sync strategy
- `IMAGE_EDITING_VERSIONING.md` / `IMAGE_TO_VIDEO.md` / `PAGE_VIDEO_GENERATION.md` – Media generation & editing flows
- `LOGGING.md` / `STATUS_TRACKING.md` – Operational observability
- `BATCH_VIDEO_ENHANCEMENTS.md` / `COMPREHENSIVE_FAST_FORWARD.md` / `FAST_FORWARD_VERSIONING.md` / `MAX_VERSION_TRACKING_FIX.md` – Fast-forward and batch processing notes
- Other focused enhancement and prompt design docs (`ENHANCED_PROMPTS.md`, `ENHANCED_PROMPTS_UX.md`, etc.)

Add new internal documentation by placing a Markdown file in `docs/` and referencing it here if broadly useful. Keep names descriptive and prefer grouping related concepts (e.g., versioning, queueing, media) for easier discovery.

Original source PDFs should be placed in the `pdfs/` folder (legacy format: 1 PDF page = 1 content unit) or the newer `pdfs_updated/` folder (updated format: 2 consecutive PDF pages = 1 logical scene). After processing, structured outputs go into `extracted/{pdf_name}/`. Keeping originals in their respective input folders preserves a clean audit trail and allows re-runs without mixing inputs and generated artifacts.

### Updated PDF Format (`pdfs_updated/`) – Paired Page Scenes

There is now an explicit `--pdf_format` switch in `extract_pdfs.py` controlling how pages map to output units:

```
# Legacy: 1 PDF page = page_XXXX directory
python extract_pdfs.py --input_dir pdfs --pdf_format old

# Updated: 2 consecutive PDF pages = scene_XXXX directory
# (text from first page, image from second page)
python extract_pdfs.py --input_dir pdfs_updated --pdf_format updated
```

In updated mode the output structure becomes:
```
extracted/{pdf_name}/
   scene_0001/
      text.txt        # Extracted from page 1
      image.png       # Extracted/rendered from page 2
      image_to_use.png# Compatibility copy for downstream stages
      summary.json    # Metadata (page indices used)
   scene_0002/       # Pages 3+4
   ...
```
If the PDF has an odd number of pages, the final scene uses the last page for both text and image (fallback behavior).

Downstream pipeline stages auto-detect `scene_` directories; no additional configuration required. Existing `page_` directories remain untouched, enabling mixing or reprocessing without deletion.

You can combine `--pdf_format` with the existing `--layout_mode` (layout cropping logic applies only to legacy single-page extraction). For updated paired scenes, images are taken directly from the second page (first embedded image or a full-page render if none found).

## 🚀 Getting Started

### Prerequisites

1. **Python 3.9+**
2. **API Keys** (set as environment variables):
   - `OPENAI_API_KEY` or `GEMINI_API_KEY` - For text cleaning and rewriting
   - `ELEVENLABS_API_KEY` - For audio generation

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables (example using .envrc)
export OPENAI_API_KEY="your-openai-key"
export GEMINI_API_KEY="your-gemini-key"
export ELEVENLABS_API_KEY="your-elevenlabs-key"
```

### Usage

1. **Place PDF files** in the project root directory

2. **Run the dashboard**:
```bash
streamlit run app.py
```

3. **Follow the workflow**:
   - Select a PDF from the dropdown
   - Complete each stage in order (Extract → Plan → Rewrite → Audio → Slideshow)
   - Monitor progress in the sidebar
   - View content in the expandable sections

## ⚠️ Safety Features

- **Overwrite Protection**: Every action that modifies existing files shows a confirmation dialog with exact file paths
- **Stage Dependencies**: Each stage checks if prerequisites are completed
- **Error Handling**: Graceful error messages with helpful guidance
- **Unique Keys**: All UI elements are properly scoped to avoid conflicts between PDFs

## 🎨 UI Organization

### Main Dashboard
- **Header**: Title and PDF selection dropdown
- **Sidebar**: Real-time workflow status tracker
- **Pipeline Stages**: 5 tabs for each stage with clear buttons and progress indicators
- **Content Viewers**: Expandable sections for:
  - Final cleaned story
  - Generated slideshow videos
  - Per-page content (text, audio, images)

### Per-Page Actions
Within the "View Extracted Pages" section, you can:
- Rewrite individual pages
- Generate audio for individual pages
- View all text versions side-by-side
- Preview all images

## 🔧 Configuration

### Image Size
Default slideshow image size: `994 x 1935` pixels  
Modify in `components/pipeline_stages.py`:
```python
TARGET_SIZE = (994, 1935)  # width, height
```

### Voice IDs (ElevenLabs)
- English: `eyVoIoi3vo6sJoHOKgAc`
- Hindi: `trxRCYtDC6qFREKq6Ek2`

Modify in `components/pipeline_stages.py` and `components/content_viewer.py`

### AI Models
- Story Planning: `gpt-4o-mini` (OpenAI)
- Rewriting: `gemini-2.5-flash` (Google Gemini)

Modify in `components/pipeline_stages.py`

## 📊 Workflow Status

The sidebar shows real-time status for:
- ✅ Completed stages (green)
- ⏳ Pending stages (blue)

## 🐛 Troubleshooting

### "No PDF files found"
- Ensure PDF files are in the same directory as `app.py`

### API Key Errors
- Verify environment variables are set correctly
- Check API key validity and quotas

### Audio Generation Fails
- Check ELEVENLABS_API_KEY is set
- Verify ElevenLabs quota hasn't been exceeded
- Ensure final_text files exist (complete Step 3 first)

### Slideshow Creation Fails
- Ensure audio files exist (complete Step 4 first)
- Check disk space for video output
- Verify moviepy and ffmpeg are installed correctly

## 📝 Best Practices

1. **Complete stages in order** for best results
2. **Review cleaned text** before rewriting for kids
3. **Check audio quality** before generating slideshows
4. **Use meaningful PDF names** - they become folder names
