# Context-Aware Rewriting System

## Overview

The rewriting system now includes **story context** and **previous pages continuity** when generating kid-friendly narration. This ensures each page flows naturally from the previous one, maintaining narrative coherence throughout the entire story.

## How It Works

### Three Levels of Context

When rewriting a page, the AI model receives:

1. **Current Page Text** - The clean text to rewrite
2. **Full Story Context** - The entire story (from `whole_story_cleaned.txt`) for overall understanding
3. **Previous Pages** - All previously rewritten pages for continuity

### Context Flow Example

```
Story: "Hanuman's Journey" (11 pages)

Page 1: No context (first page)
  → Generates: "Hanuman was born with divine powers..."

Page 2: Context includes Page 1
  → Generates: "He grew stronger each day. His powers amazed everyone."
  (Continues from Page 1's introduction)

Page 3: Context includes Pages 1-2
  → Generates: "One day, the gods called him. They had an important mission."
  (Natural progression from previous narrative)

...and so on for all pages
```

## What Gets Passed to the AI

### Prompt Structure

```
SYSTEM:
You are a helpful writing assistant for high-octane storybooks.
- Audience: children aged 15-25.
- Keep language simple, friendly, and high-octane engaging.
- Avoid difficult vocabulary.
- Preserve core meaning but simplify.
- Maintain coherence within the page.
- 2 short sentences max.
- Ensure narrative continuity from previous pages.

USER:
Rewrite the following text into two versions...

--- FULL STORY CONTEXT (for reference) ---
[Entire cleaned story from whole_story_cleaned.txt]

--- STORY SO FAR (previous pages narration) ---
[Page 1] Hanuman was born with divine powers...
[Page 2] He grew stronger each day. His powers amazed everyone.

--- CURRENT PAGE TEXT TO REWRITE ---
[Raw text from current page's clean_text.txt]

Return output exactly in this format:
[EN]
<english text>

[HI]
<hindi text>
```

## Benefits

### 1. **Narrative Continuity**

**Without Context:**
```
Page 1: "A hero was born."
Page 2: "Someone discovered their power."  ❌ Who is "someone"?
Page 3: "The journey began."              ❌ What journey?
```

**With Context:**
```
Page 1: "Hanuman was born with divine powers."
Page 2: "He discovered he could fly and lift mountains."  ✅ Clear reference
Page 3: "His journey to save Sita began."                ✅ Natural flow
```

### 2. **Pronoun Resolution**

**Without Context:**
- "He did this" - Who is "he"?
- "They went there" - Who are "they"?
- "It happened" - What is "it"?

**With Context:**
- Knows "he" = Hanuman (established in Page 1)
- Knows "they" = Hanuman and the army (from Page 3)
- Knows "it" = the golden arrow (from Page 5)

### 3. **Story Arc Awareness**

The AI understands:
- Beginning: Introduction, setup
- Middle: Rising action, challenges
- End: Climax, resolution

This helps maintain appropriate tone and pacing for each section.

## Implementation Details

### CLI Usage (`rewrite_for_kids.py`)

```bash
python rewrite_for_kids.py --root_dir extracted --only download15 --force
```

**Automatic Context Loading:**
1. Loads `whole_story_cleaned.txt` once at start
2. For each page in order:
   - Accumulates previous pages' rewritten text
   - Passes both contexts to `_call_gemini_dual()`
   - Adds current page to accumulator for next iteration

### UI Usage (Streamlit)

#### Batch Rewrite (All Pages)

```
Step 3: Rewrite for Kids
└── ✏️ Create New Versions for All Pages
```

**What Happens:**
1. Loads `whole_story_cleaned.txt`
2. Processes pages in order (page_0001, page_0002, ...)
3. Each page gets context from all previous pages
4. Creates versioned files with continuity

#### Individual Page Rewrite

```
View Content → [Specific Page]
└── ✏️ Create New Version (v2)
```

**What Happens:**
1. Loads `whole_story_cleaned.txt`
2. Finds all previous pages (lower page numbers)
3. Loads their **latest** rewritten text
4. Generates new version with full context

**Example:**
```
Rewriting Page 0005:
  - Whole Story: [entire story]
  - Previous: 
      [Page 1] ...v2 text...
      [Page 2] ...v3 text...
      [Page 3] ...v1 text...
      [Page 4] ...v2 text...
  - Current: [Page 5 raw text]
```

## Code Structure

### `rewrite_for_kids.py`

**Enhanced `_call_gemini_dual()`:**

```python
def _call_gemini_dual(
    model: str, 
    page_text: str, 
    whole_story: Optional[str] = None,
    previous_pages: Optional[str] = None,
    max_retries: int = 5, 
    retry_delay: float = 2.0
) -> Tuple[str, str]:
    """
    Generate EN/HI rewrites with story context.
    
    Args:
        model: Gemini model name
        page_text: Current page text to rewrite
        whole_story: Full story for overall understanding
        previous_pages: Previous pages for continuity
    
    Returns:
        (en_text, hi_text)
    """
```

**Enhanced `process_pdf_dir()`:**

```python
def process_pdf_dir(pdf_dir: Path, model: str, force: bool = False, skip_missing: bool = False) -> None:
    # Load whole story once
    whole_story_file = pdf_dir / "whole_story_cleaned.txt"
    whole_story = whole_story_file.read_text() if whole_story_file.exists() else None
    
    # Accumulate previous pages
    previous_pages_en = []
    previous_pages_hi = []
    
    for page in pages:
        # Build context
        prev_context = "\n\n".join(previous_pages_en) if previous_pages_en else None
        
        # Generate with context
        en_text, hi_text = _call_gemini_dual(
            model, 
            page_text,
            whole_story=whole_story,
            previous_pages=prev_context
        )
        
        # Add to accumulator
        previous_pages_en.append(f"[Page {page.index}] {en_text}")
        previous_pages_hi.append(f"[Page {page.index}] {hi_text}")
```

### UI Integration

**`components/pipeline_stages.py`:**

Batch rewrite with context:

```python
# Load whole story
whole_story_file = extraction_dir / 'whole_story_cleaned.txt'
whole_story = whole_story_file.read_text() if whole_story_file.exists() else None

# Accumulate previous pages
previous_pages_en = []

for page_dir in page_dirs:
    # Build context
    prev_context = "\n\n".join(previous_pages_en) if previous_pages_en else None
    
    # Generate with context
    en_text, hi_text = rewrite_text_for_kids(
        'gemini-2.5-flash', 
        text,
        whole_story=whole_story,
        previous_pages=prev_context
    )
    
    # Accumulate
    previous_pages_en.append(f"[Page {page_index}] {en_text}")
```

**`components/content_viewer.py`:**

Individual page rewrite with context:

```python
# Load whole story
whole_story = whole_story_file.read_text() if whole_story_file.exists() else None

# Build previous pages
previous_pages_en = []
for prev_page_dir in all_page_dirs:
    if prev_index < current_page_index:
        prev_en_path = get_latest_version_path(prev_page_dir, 'en_text')
        if prev_en_path and prev_en_path.exists():
            prev_en_text = prev_en_path.read_text()
            previous_pages_en.append(f"[Page {prev_index}] {prev_en_text}")

# Generate with context
en_text, hi_text = rewrite_text_for_kids(
    'gemini-2.5-flash', 
    text,
    whole_story=whole_story,
    previous_pages=prev_context
)
```

## Backward Compatibility

### Legacy Support

The system is **fully backward compatible**:

**Old Code (still works):**
```python
en_text, hi_text = rewrite_text_for_kids('gemini-2.5-flash', page_text)
```

**New Code (with context):**
```python
en_text, hi_text = rewrite_text_for_kids(
    'gemini-2.5-flash', 
    page_text,
    whole_story=whole_story,
    previous_pages=prev_context
)
```

If you don't pass context parameters, they default to `None` and the system works exactly as before.

## Version Control Integration

### How Versions Work with Context

**Scenario: Regenerating Page 5**

```
Existing versions:
  Page 1: v2
  Page 2: v3
  Page 3: v1
  Page 4: v2
  Page 5: v1 (regenerating → v2)

Context for Page 5 v2:
  - Whole Story: [entire story]
  - Previous Pages:
      [Page 1] <v2 text>   ← Latest version
      [Page 2] <v3 text>   ← Latest version
      [Page 3] <v1 text>   ← Latest version
      [Page 4] <v2 text>   ← Latest version
```

**Key Point:** Always uses **latest version** of previous pages for context, ensuring continuity with current state.

### When to Regenerate

**Regenerate downstream pages when:**

1. **Upstream page edited:**
   ```
   Edit Page 2 → Regenerate Pages 3, 4, 5, ...
   (So they incorporate the new Page 2 context)
   ```

2. **Story planning changed:**
   ```
   New whole_story_cleaned.txt → Regenerate all pages
   (To reflect updated overall narrative)
   ```

3. **Quality improvement:**
   ```
   Better prompt on Page 5 → Creates v2
   (Can compare v1 vs v2 with same context)
   ```

## Best Practices

### 1. **Process in Order**

Always rewrite pages **sequentially** (1, 2, 3, ...) for best continuity:

✅ **Correct:**
```bash
python rewrite_for_kids.py --root_dir extracted --force
```
Processes pages 1→2→3→... automatically

❌ **Avoid:**
Randomly rewriting individual pages out of order in UI, as context will be incomplete.

### 2. **Complete Story Planning First**

Run **Step 2: Plan Story** before **Step 3: Rewrite**:

```
Step 1: Extract Content ✅
Step 2: Plan Story ✅         ← Creates whole_story_cleaned.txt
Step 3: Rewrite for Kids ✅   ← Uses whole story context
```

### 3. **Batch Regeneration**

When upstream pages change, use batch rewrite:

```
UI: Step 3 → ✏️ Create New Versions for All Pages
```

This ensures all pages get updated context in one go.

### 4. **Version Comparison**

Compare versions to see impact of context:

```
Page 5:
  v1 (no context): "A battle happened."
  v2 (with context): "Hanuman fought the demon king to save Sita."
```

Much more specific and connected!

## Troubleshooting

### Issue: "Context too long"

**Symptom:** API error about token limit

**Cause:** Very long stories + many pages = huge context

**Solutions:**
1. Summarize whole story instead of full text
2. Limit previous pages to last 3-5 pages only
3. Use shorter `whole_story_cleaned.txt`

### Issue: "Inconsistent continuity"

**Symptom:** Page 5 doesn't match Page 4's ending

**Cause:** Pages rewritten out of order or with different versions

**Solution:** 
```bash
# Regenerate all pages in order
python rewrite_for_kids.py --root_dir extracted --only download15 --force
```

### Issue: "Page mentions wrong character"

**Symptom:** Page 7 talks about "Ram" but should be "Hanuman"

**Cause:** Whole story context has confusing information

**Solution:**
1. Review and improve `whole_story_cleaned.txt`
2. Make it clearer about main character
3. Regenerate rewrites

## Performance Considerations

### API Calls

Each page rewrite = 1 API call to Gemini

**With Context:**
- Input tokens: Higher (includes whole story + previous pages)
- Output tokens: Same (~50-100 tokens for 2 sentences)
- Cost: Slightly higher input cost, but much better quality

**Example:**
```
Without context:
  Input: 200 tokens (just current page)
  Output: 80 tokens
  
With context:
  Input: 2000 tokens (whole story + previous pages)
  Output: 80 tokens
  Cost: ~10x input, but story quality >>> 10x better
```

### Optimization Tips

1. **Batch processing:** More efficient than individual pages
2. **Cached context:** Whole story loaded once, reused for all pages
3. **Incremental accumulation:** Previous pages built up, not reloaded

## Examples

### Real Story: "Hanuman's Divine Power"

**Without Context (old system):**

```
Page 1: A baby was born with special powers.
Page 2: Someone could fly and lift heavy things.
Page 3: A journey started.
Page 4: There was a battle.
Page 5: Victory was achieved.
```

**Issues:** Generic, disconnected, unclear pronouns

**With Context (new system):**

```
Page 1: Hanuman was born with divine powers from Lord Shiva.
Page 2: Young Hanuman could fly to the sun and lift mountains effortlessly.
Page 3: Lord Ram called Hanuman to help rescue Sita from Ravana.
Page 4: Hanuman battled demons and found Sita in Lanka.
Page 5: He returned with news, bringing hope to Ram's army.
```

**Benefits:** Specific, connected, clear narrative flow

### Hindi Continuity Example

**Without Context:**

```
Page 1 (HI): एक बच्चा पैदा हुआ।
Page 2 (HI): किसी को शक्ति मिली।
```

**With Context:**

```
Page 1 (HI): हनुमान शिव के आशीर्वाद से पैदा हुए।
Page 2 (HI): हनुमान को उड़ने और पहाड़ उठाने की शक्ति मिली।
```

Much clearer "Hanuman" instead of vague "someone"!

## Summary

### Key Improvements

✅ **Narrative Continuity** - Each page flows from previous  
✅ **Pronoun Resolution** - Clear character references  
✅ **Story Arc Awareness** - Appropriate pacing and tone  
✅ **Context-Rich** - Full story understanding  
✅ **Backward Compatible** - Old code still works  
✅ **Version Tracking** - Latest context always used  

### When to Use

**Always use context for:**
- Multi-page stories (2+ pages)
- Stories with recurring characters
- Sequential narratives
- Books requiring consistency

**Context optional for:**
- Single-page content
- Standalone pages
- Independent scenes

### Result

Transform disconnected page rewrites into **coherent, engaging narratives** that maintain continuity throughout the entire story!
