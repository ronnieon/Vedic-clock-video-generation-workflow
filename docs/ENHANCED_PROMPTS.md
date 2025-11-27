# Enhanced Video Prompts System

## Overview
AI-powered prompt enhancement system that creates **GENERIC, VISUALLY EXCITING** video prompts without character names (video models don't recognize them). Uses whole story summary for context but focuses on current page content.

## Features

### 1. AI Prompt Enhancement
- **Two-Step Process**: First creates story summary (genre/mood/setting), then enhances prompt
- **Generic Terms Only**: NO character names - uses "the hero", "the creature", "figures" instead
- **Visually Exciting**: Focuses on dramatic movement, lighting, atmosphere, and environment
- **Story Context**: Uses whole story summary to understand genre and mood
- **Page-Specific**: Uses current page text for accurate scene description
- **Kid-Friendly Guidelines**:
  - Minimal, simple movements only
  - Focus on atmosphere and visual richness
  - Gentle, slow character gestures
  - No physical contact between characters
  - Maximum 2-3 simple movements per prompt
  - Maintains storybook illustration aesthetic

### 2. Enhancement Rules
**Good Movements:**
- Gentle breeze making leaves sway softly
- Characters slowly turning heads, expressing emotion
- Soft lighting changes creating depth and mood
- Camera slowly zooms in/out for emphasis
- Subtle background movement adding life

**Character Interactions:**
- Multiple characters may slowly and dramatically move/gesture towards each other
- **NEVER physically touching**
- Dramatic charging motions allowed, but always stopping before contact

### 3. Implementation

#### Per-Page Enhancement
Located in: `components/content_viewer.py`
- **"✨ AI Enhance"** button in video generation section
- Shows enhanced prompt immediately
- Checkbox to enable/disable enhanced prompt usage
- Saved as `enhanced_video_prompt.txt` in each page directory

#### Batch Enhancement
Located in: `components/pipeline_stages.py`
- **"✨ AI Enhance Prompts"** button in Videos tab
- Processes all pages with captions
- Builds progressive context from previous pages
- Shows expandable view of all enhanced prompts

### 4. Files Generated
```
extracted/{pdf_name}/page_XXXX/
├── image_caption.txt           # Original AI caption
└── enhanced_video_prompt.txt   # AI-enhanced prompt (complete, ready to use)
```

### 5. Usage Flow

**Option 1: Per-Page**
1. Generate caption for image
2. Click **"✨ AI Enhance"**
3. Review enhanced prompt
4. Enable **"🎨 Use enhanced prompt"** checkbox
5. Generate video

**Option 2: Batch**
1. Generate captions for all pages
2. Click **"✨ AI Enhance Prompts"** in Videos tab
3. Review enhanced prompts in expandable section
4. Enable **"🎨 Enhance prompts with AI-generated captions"**
5. Generate videos (will use enhanced prompts automatically)

### 6. Prompt Priority
When generating videos:
1. **Enhanced prompt** (if exists and checkbox enabled) - Used directly
2. **Caption + Motion prompt** (if caption exists and checkbox enabled)
3. **Motion prompt only** (default)

### 7. Technical Details

**Model**: `gemini-2.0-flash-exp`

**Two-Step Process**:
1. **Step 1 (Summary)**: Creates 2-sentence story summary (genre, setting, mood - NO characters)
2. **Step 2 (Enhancement)**: Creates generic prompt using summary + current page

**Context Provided**:
- Whole story summary (for genre/mood/setting understanding)
- Current page text (for scene-specific details)
- Image caption (possibly inaccurate)

**Critical Rules**:
- **NO character names** (video models don't recognize them)
- Use generic terms: "the hero", "the friend", "the creature", "figures"
- Replace place names: "the kingdom", "the forest", "the mountain"
- Focus on VISUAL elements: movement, lighting, atmosphere

**Output**: Single sentence, max 20 words, generic and visually exciting

### 8. API Integration
```python
from enhance_video_prompt import enhance_video_prompt

enhanced = enhance_video_prompt(
    caption="AI-generated caption",
    page_text="Current page story text",
    whole_story="Full story text for context summary",  # Used to create genre/mood summary
    previous_pages=None  # Not used
)
```

**Note**: Uses **2 Gemini API calls**:
1. First call creates story summary (genre/mood/setting)
2. Second call creates the enhanced prompt

## Examples

### Example 1: Character Names Removed
**Before (Raw Caption):**
"Harry and Hermione standing in the castle"

**Page Text:** "The young wizard and his friend explored the ancient halls."

**After (Enhanced - GENERIC):**
"Young figures slowly walk through grand stone halls, magical torchlight flickers warmly"
- ✅ No names ("Harry", "Hermione" removed)
- ✅ Generic terms ("young figures")
- ✅ Visually exciting (magical torchlight)

---

### Example 2: Visually Exciting
**Before (Raw Caption):**
"A dragon in a cave"

**Page Text:** "The mighty creature awakened from its slumber, fire glowing in its throat."

**After (Enhanced - GENERIC):**
"Powerful creature slowly raises massive head, fierce orange glow illuminates dark cavern"
- ✅ No name (generic "creature")
- ✅ Dramatic and visual
- ✅ Simple movements

---

### Example 3: Atmospheric
**Before (Raw Caption):**
"A forest scene"

**Page Text:** "The enchanted woods whispered secrets as moonlight filtered through ancient trees."

**After (Enhanced - GENERIC):**
"Mystical forest breathes softly, silver moonbeams dance through towering ancient trees"
- ✅ Generic location
- ✅ Atmospheric and rich
- ✅ Gentle movements
