#!/usr/bin/env python3
"""
Rewrite per-page cleaned text into kid-friendly narration (EN + HI) using Gemini 2.5 Flash.

- Walks each PDF folder under a root (default: ./extracted)
- For each page_XXXX/ subfolder, reads clean_text.txt
- Calls Gemini to generate:
  - English kid-friendly narration -> final_text_en.txt
  - Simple colloquial Hindi narration -> final_text_hi.txt

Usage examples:
  python rewrite_for_kids.py --root_dir extracted --model gemini-2.5-flash
  python rewrite_for_kids.py --root_dir extracted --only download --force

Requirements:
  - GEMINI_API_KEY must be set in your environment (from AI Studio: https://aistudio.google.com/app/apikey)
  - pip install -r requirements.txt
"""
from __future__ import annotations

import argparse
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from tqdm import tqdm

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except Exception:
    GENAI_AVAILABLE = False
    genai = None

# LEGACY FORMAT DISABLED - Only using scene-based format
# PAGE_DIR_PREFIX = "page_"
SCENE_DIR_PREFIX = "scene_"
INPUT_FILENAME = "clean_text.txt"
OUT_EN_FILENAME = "final_text_en.txt"
OUT_HI_FILENAME = "final_text_hi.txt"


@dataclass
class PageItem:
    index: int
    path: Path
    input_path: Path
    out_en_path: Path
    out_hi_path: Path


def list_pdf_dirs(root: Path) -> List[Path]:
    items: List[Path] = []
    for p in sorted(root.iterdir()):
        if p.is_dir():
            # LEGACY FORMAT DISABLED - Only check for scene_ dirs
            # has_page = any(child.is_dir() and child.name.startswith(PAGE_DIR_PREFIX) for child in p.iterdir())
            has_scene = any(child.is_dir() and child.name.startswith(SCENE_DIR_PREFIX) for child in p.iterdir())
            if has_scene:
                items.append(p)
    return items


def list_pages(pdf_dir: Path) -> List[PageItem]:
    pages: List[PageItem] = []
    for child in sorted(pdf_dir.iterdir()):
        # LEGACY FORMAT DISABLED - Only handle scene_ dirs
        # if child.is_dir() and child.name.startswith(PAGE_DIR_PREFIX):
        #     num_str = child.name[len(PAGE_DIR_PREFIX):]
        if child.is_dir() and child.name.startswith(SCENE_DIR_PREFIX):
            num_str = child.name[len(SCENE_DIR_PREFIX):]
            try:
                idx = int(num_str)
            except ValueError:
                idx = 0
            input_path = child / INPUT_FILENAME
            out_en_path = child / OUT_EN_FILENAME
            out_hi_path = child / OUT_HI_FILENAME
            pages.append(PageItem(index=idx, path=child, input_path=input_path, out_en_path=out_en_path, out_hi_path=out_hi_path))
    pages.sort(key=lambda x: (x.index, x.path.name))
    return pages


def _ensure_gemini_ready() -> None:
    if not GENAI_AVAILABLE:
        raise RuntimeError("google-generativeai package not installed. Please `pip install -r requirements.txt`.")
    import google.generativeai as genai
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set in environment.")
    genai.configure(api_key=api_key)


def _call_gemini_dual(
    model: str, 
    page_text: str, 
    whole_story: Optional[str] = None,
    previous_pages: Optional[str] = None,
    max_retries: int = 5, 
    retry_delay: float = 2.0
) -> Tuple[str, str]:
    """
    Ask Gemini to produce both English and Hindi versions in a single call.
    
    Args:
        model: Gemini model name
        page_text: Current page text to rewrite
        whole_story: Optional full story context for overall understanding
        previous_pages: Optional text from all previous pages for continuity
        max_retries: Number of retry attempts
        retry_delay: Delay between retries
    
    Returns:
        (en_text, hi_text)
    """
    _ensure_gemini_ready()
    import google.generativeai as genai
    last_err: Optional[Exception] = None
    system = (
        "You are a helpful writing assistant for high-octane storybooks.\n"
        "- Audience: children aged 15-25.\n"
        "- Keep language simple, friendly, and high-octane engaging.\n"
        "- Avoid difficult vocabulary.\n"
        "- Preserve core meaning but simplify.\n"
        "- Maintain coherence within the page.\n"
        "- 2 short sentences max.\n"
        "- Ensure narrative continuity from previous pages.\n"
        "- Use respectful pronouns for deities and gods (e.g., 'He/Him/His' capitalized, 'They/Them/Their' capitalized).\n"
        "- In Hindi, use respectful forms like 'वे', 'उन्होंने', 'उनका' for deities.\n"
    )
    
    # Build context section
    context_section = ""
    if whole_story:
        context_section += f"\n--- FULL STORY CONTEXT (for reference) ---\n{whole_story}\n\n"
    
    if previous_pages:
        context_section += f"--- STORY SO FAR (previous pages narration) ---\n{previous_pages}\n\n"
    
    user = (
        "Rewrite the following text into two versions for a simple high-octane storybook (age 15-25):\n"
        "1) English (simple narration). 2 short sentences max.\n"
        "2) Simple colloquial Hindi in Devanagari script (हिन्दी), easy words and 2 short sentences max.\n\n"
        "IMPORTANT: Maintain narrative flow and continuity from the previous pages.\n"
        "Use the story context to understand the overall plot, and the previous pages to continue smoothly.\n\n"
        "TEXTUAL CONTROLS FOR SPEECH (use these to enhance audio narration):\n"
        "- Timed Pauses: Use new line for pauses (up to 3)."
        "- Emphasis: Use ALL CAPS for strong vocal emphasis. Example: This is URGENT!\n"
        "- Hesitation: Use ellipsis (...) for pauses and uncertainty. Example: I'm not sure... maybe later?\n"
        "- Pacing: Use punctuation (comma, period, em-dash —) naturally for flow.\n"
        "- Sentence Length: Vary sentence length—short for impact, longer for flow.\n\n"
        f"{context_section}"
        "Return output exactly in this format (no extra commentary):\n"
        "[EN]\n<english text>\n\n[HI]\n<hindi text>\n\n"
        f"--- CURRENT PAGE TEXT TO REWRITE ---\n{page_text}"
    )
    for attempt in range(1, max_retries + 1):
        try:
            # Configure safety settings using the correct format
            # Use list of dicts with 'category' and 'threshold' keys
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            # Simplify the prompt format - don't use SYSTEM/USER labels
            # Just provide the instructions directly
            combined_prompt = f"{system}\n\n{user}"
            
            model_obj = genai.GenerativeModel(model)
            resp = model_obj.generate_content(
                combined_prompt,
                safety_settings=safety_settings,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                }
            )
            
            # Check if prompt was blocked
            if hasattr(resp, 'prompt_feedback'):
                feedback = resp.prompt_feedback
                if hasattr(feedback, 'block_reason') and feedback.block_reason:
                    # Log the specific reason and try to provide helpful info
                    block_reason = feedback.block_reason
                    safety_ratings = getattr(feedback, 'safety_ratings', [])
                    error_msg = f"Prompt blocked: {block_reason}"
                    if safety_ratings:
                        error_msg += f", ratings: {safety_ratings}"
                    raise RuntimeError(error_msg)
            
            # Try to get text, handle blocking gracefully
            try:
                full = resp.text.strip()
            except (ValueError, AttributeError) as e:
                # Response was blocked after generation
                if hasattr(resp, 'candidates') and resp.candidates:
                    candidate = resp.candidates[0]
                    finish_reason = getattr(candidate, 'finish_reason', 'UNKNOWN')
                    safety_ratings = getattr(candidate, 'safety_ratings', [])
                    
                    # Provide helpful debug info
                    error_msg = f"Response blocked: finish_reason={finish_reason}"
                    if safety_ratings:
                        error_msg += f"\nSafety ratings: {safety_ratings}"
                    else:
                        error_msg += "\nNo safety ratings available (likely prompt-level block)"
                    
                    # If it's a safety block, suggest next steps
                    if finish_reason == 1:  # SAFETY
                        error_msg += f"\n\nPage text that triggered block:\n{page_text[:200]}..."
                    
                    raise RuntimeError(error_msg)
                raise RuntimeError(f"Unable to access response text: {str(e)}")
            
            if not full:
                raise RuntimeError("Empty response from Gemini")
            # Parse blocks
            en_text = ""
            hi_text = ""
            # Normalize line endings
            lines = full.replace("\r\n", "\n").split("\n")
            current = None
            buf: List[str] = []
            def flush():
                nonlocal en_text, hi_text, buf, current
                text = "\n".join(buf).strip()
                if current == "EN":
                    en_text = text
                elif current == "HI":
                    hi_text = text
                buf = []
            for ln in lines:
                tag = ln.strip()
                if tag == "[EN]":
                    if current is not None:
                        flush()
                    current = "EN"
                    buf = []
                elif tag == "[HI]":
                    if current is not None:
                        flush()
                    current = "HI"
                    buf = []
                else:
                    buf.append(ln)
            if current is not None:
                flush()
            if not en_text or not hi_text:
                # Fallback: if tags missing, split halfway heuristically (rare)
                half = len(full) // 2
                en_text = en_text or full[:half].strip()
                hi_text = hi_text or full[half:].strip()
            return en_text.strip(), hi_text.strip()
        except Exception as e:
            last_err = e
            time.sleep(retry_delay * attempt)
    raise RuntimeError(f"Gemini request failed after {max_retries} retries: {last_err}")


def process_pdf_dir(pdf_dir: Path, model: str, force: bool = False, skip_missing: bool = False) -> None:
    pages = list_pages(pdf_dir)
    if not pages:
        print(f"No pages found in {pdf_dir}")
        return
    
    # Load whole story context if available
    whole_story_file = pdf_dir / "whole_story_cleaned.txt"
    whole_story = None
    if whole_story_file.exists():
        whole_story = whole_story_file.read_text(encoding="utf-8", errors="ignore")
    
    # Accumulate previous pages for continuity
    previous_pages_en = []
    previous_pages_hi = []
    
    for page in tqdm(pages, desc=f"Rewriting for kids in {pdf_dir.name}"):
        if not page.input_path.exists():
            if skip_missing:
                continue
            else:
                # If missing, try to fall back to raw text.txt
                raw_fallback = page.path / "text.txt"
                if not raw_fallback.exists():
                    print(f"  - Missing input for {page.path}")
                    continue
                src_text = raw_fallback.read_text(encoding="utf-8", errors="ignore")
        else:
            src_text = page.input_path.read_text(encoding="utf-8", errors="ignore")

        if (not force) and page.out_en_path.exists() and page.out_hi_path.exists():
            # Already done - load existing text for continuity
            existing_en = page.out_en_path.read_text(encoding="utf-8", errors="ignore")
            existing_hi = page.out_hi_path.read_text(encoding="utf-8", errors="ignore")
            previous_pages_en.append(f"[Page {page.index}] {existing_en}")
            previous_pages_hi.append(f"[Page {page.index}] {existing_hi}")
            continue

        # Build context from previous pages
        prev_context = None
        if previous_pages_en:
            prev_context = "\n\n".join(previous_pages_en)
        
        # Generate with context
        en_text, hi_text = _call_gemini_dual(
            model, 
            src_text,
            whole_story=whole_story,
            previous_pages=prev_context
        )
        
        page.out_en_path.write_text(en_text, encoding="utf-8")
        page.out_hi_path.write_text(hi_text, encoding="utf-8")
        
        # Add to previous pages for next iteration
        previous_pages_en.append(f"[Page {page.index}] {en_text}")
        previous_pages_hi.append(f"[Page {page.index}] {hi_text}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rewrite page texts into kid-friendly narration (EN+HI) using Gemini 2.5 Flash")
    parser.add_argument("--root_dir", type=Path, default=Path.cwd() / "extracted", help="Root directory containing PDF output folders")
    parser.add_argument("--only", type=str, default="", help="Only process folders whose name contains this substring")
    parser.add_argument("--model", type=str, default=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"), help="Gemini model name to use")
    parser.add_argument("--force", action="store_true", help="Rewrite even if final_text files already exist")
    parser.add_argument("--skip_missing", action="store_true", help="Skip pages without clean_text.txt instead of falling back to text.txt")
    args = parser.parse_args(argv)

    root = args.root_dir.resolve()
    if not root.exists():
        print(f"Root directory does not exist: {root}")
        return 1

    if genai is None:
        print("google-generativeai package not installed. Please `pip install -r requirements.txt`.")
        return 1
    if not os.getenv("GEMINI_API_KEY"):
        print("GEMINI_API_KEY is not set in environment.")
        return 1

    pdf_dirs = list_pdf_dirs(root)
    if args.only:
        sub = args.only.lower()
        pdf_dirs = [d for d in pdf_dirs if sub in d.name.lower()]

    if not pdf_dirs:
        print(f"No PDF folders found under {root}")
        return 0

    print(f"Found {len(pdf_dirs)} folder(s) under {root}")
    for d in pdf_dirs:
        print(f"Processing folder: {d.name}")
        process_pdf_dir(d, model=args.model, force=args.force, skip_missing=args.skip_missing)

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
