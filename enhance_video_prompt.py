"""
Enhance Video Prompts for Kid-Friendly Story Books
===================================================
Generate contextually-aware, simple video prompts optimized for children's storybooks.
"""

import os
import time
from pathlib import Path
from typing import Optional
import google.generativeai as genai


def enhance_video_prompt(
    caption: str,
    page_text: Optional[str] = None,
    whole_story: Optional[str] = None,
    previous_pages: Optional[str] = None
) -> str:
    """
    Enhance a video prompt using current page + story summary for context.
    
    Uses whole story summary for understanding context, but creates GENERIC
    prompts without character names (video model doesn't recognize them).
    
    Args:
        caption: Original AI-generated image caption
        page_text: Current page text (used for audio) - PRIMARY SOURCE
        whole_story: Whole story for context (summary created)
        previous_pages: Not used (kept for API compatibility)
    
    Returns:
        Generic, visually exciting video prompt optimized for kids' storybooks
    """
    try:
        # Configure Gemini
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # STEP 1: Create story summary (if whole_story provided)
        story_summary = None
        if whole_story:
            summary_prompt = f"""Provide a 2-sentence summary of this story focusing on the GENRE, SETTING, and MOOD (not characters):

{whole_story[:1000]}

Return ONLY 2 sentences describing the type of story, setting, and emotional tone."""
            
            summary_response = model.generate_content(summary_prompt)
            if summary_response and summary_response.text:
                story_summary = summary_response.text.strip()
        
        # STEP 2: Create enhanced prompt with strict guidelines
        system_instruction = """You are an expert at creating GENERIC, VISUALLY EXCITING video motion prompts for children's storybook illustrations.

CRITICAL RULES:
1. DO NOT use character names or specific names - video models don't recognize them
2. Use GENERIC descriptions: "the hero", "the friend", "the creature", "figures", etc.
3. Make it VISUALLY EXCITING and ATMOSPHERIC
4. Focus on MOVEMENT, LIGHTING, and ENVIRONMENT

GUIDELINES FOR VIDEO PROMPTS:
1. Keep it SIMPLE - minimal movement only (2-3 actions max)
2. Focus on VISUAL RICHNESS and ATMOSPHERE
3. Movements should be GENTLE and SLOW
4. Avoid complex actions or physical contact between figures
5. If multiple figures: they may slowly and dramatically move/gesture towards each other but NEVER touch
6. Examples of GOOD prompts:
   - "glowing magical aura surrounds figures, gentle wind sways enchanted forest"
   - "brave figure slowly raises hand, warm golden light bathes the scene"
   - "creatures slowly circle each other dramatically, storm clouds gather overhead"
   - "soft moonlight filters through trees, mysterious shadows shift gently"
7. Examples of BAD prompts (too specific):
   - "Harry raises his wand" ❌ (uses name)
   - "The dragon Smaug breathes fire" ❌ (uses name)
   
USE GENERIC TERMS ONLY."""

        # Build input
        input_parts = [system_instruction, "\n\n"]
        
        if story_summary:
            input_parts.append(f"**STORY CONTEXT (for mood/setting reference only):**\n{story_summary}\n\n")
        
        input_parts.append(f"**IMAGE CAPTION:**\n{caption}\n\n")
        
        if page_text:
            input_parts.append(f"**CURRENT PAGE TEXT:**\n{page_text}\n\n")
        else:
            input_parts.append("**CURRENT PAGE TEXT:** Not available.\n\n")
        
        input_parts.append("""**TASK:**
1. Check if the caption matches the page text
2. Identify the key visual elements and action on this page
3. Create a GENERIC, VISUALLY EXCITING video motion prompt (1 sentence, max 20 words)
4. Use ONLY generic terms (no character names!)
5. Focus on: movement, lighting, atmosphere, environment
6. Make it dramatic and visually rich while keeping movements simple

**CRITICAL**: Replace any names with generic descriptions:
- Character names → "the hero", "the friend", "the young one", "the figure"
- Place names → "the kingdom", "the forest", "the mountain", "the castle"
- Creature names → "the creature", "the beast", "the dragon", "the guardian"

**OUTPUT FORMAT:**
Return ONLY the enhanced video motion prompt as a single sentence. No names. No explanation.""")
        
        # Generate enhanced prompt
        response = model.generate_content(''.join(input_parts))
        
        if response and response.text:
            enhanced_prompt = response.text.strip()
            # Clean up any markdown or extra formatting
            enhanced_prompt = enhanced_prompt.replace('**', '').replace('*', '')
            # Remove quotes if present
            if enhanced_prompt.startswith('"') and enhanced_prompt.endswith('"'):
                enhanced_prompt = enhanced_prompt[1:-1]
            if enhanced_prompt.startswith("'") and enhanced_prompt.endswith("'"):
                enhanced_prompt = enhanced_prompt[1:-1]
            return enhanced_prompt
        else:
            # Fallback to simple prompt
            return "Gentle atmosphere with subtle movement and soft lighting"
                
    except Exception as e:
        print(f"Error enhancing prompt: {str(e)}")
        # Return a safe fallback
        return "Gentle camera movement with soft lighting and minimal motion"


def batch_enhance_prompts(
    page_dirs: list[Path],
    pdf_stem: str
) -> dict[str, str]:
    """
    Enhance prompts for multiple pages using whole story summary + each page's text.
    
    Creates GENERIC, visually exciting prompts without character names.
    
    Args:
        page_dirs: List of page directories
        pdf_stem: PDF stem name for finding story files
    
    Returns:
        Dict mapping page_dir.name to enhanced prompt
    """
    from utils.versioning import get_latest_version_path
    from utils.workflow import get_extraction_dir
    
    results = {}
    
    # Load whole story for context summary
    extraction_dir = get_extraction_dir(pdf_stem)
    whole_story_file = extraction_dir / 'whole_story_cleaned.txt'
    whole_story = None
    if whole_story_file.exists():
        whole_story = whole_story_file.read_text(encoding='utf-8', errors='ignore')
    
    sorted_dirs = sorted(page_dirs, key=lambda p: p.name)
    api_call_count = 0
    
    for page_dir in sorted_dirs:
        # Get caption
        caption_file = page_dir / 'image_caption.txt'
        if not caption_file.exists():
            results[page_dir.name] = None
            continue
        
        caption = caption_file.read_text(encoding='utf-8').strip()
        
        # Get page text (try versioned first, then legacy)
        page_text = None
        en_text_path = get_latest_version_path(page_dir, 'en_text')
        if not en_text_path:
            en_text_path = page_dir / 'final_text_en.txt'
        
        if en_text_path and en_text_path.exists():
            page_text = en_text_path.read_text(encoding='utf-8', errors='ignore')
        
        # Add delay before API call if this isn't the first call
        if api_call_count > 0:
            print(api_call_count)
        
        # Enhance prompt using whole story summary + current page context
        # Creates generic prompts without character names
        enhanced_prompt = enhance_video_prompt(
            caption=caption,
            page_text=page_text,
            whole_story=whole_story,  # Used for summary/context
            previous_pages=None  # Not used
        )
        
        results[page_dir.name] = enhanced_prompt
        api_call_count += 1
    
    return results
