#!/usr/bin/env python3
"""
Clean and concatenate page texts for each extracted PDF folder using OpenAI.

- For every PDF folder under a root (default: ./extracted), iterate its page_XXXX/ subfolders
- For each page folder, read text.txt, send to OpenAI to clean, and write clean_text.txt next to it
- After all pages are cleaned, ask OpenAI to produce a clearly page-labeled whole story
- Save final whole story at the PDF folder level as whole_story_cleaned.txt

Usage examples:
  python clean_and_concatenate.py --only storyname
  python clean_and_concatenate.py --only storyname --model gpt-4o-mini
  python clean_and_concatenate.py --all  # Process ALL PDFs (use with caution)

Requirements:
  - OPENAI_API_KEY must be set in your environment
  - pip install -r requirements.txt
"""
from __future__ import annotations

import argparse
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from tqdm import tqdm

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except Exception as e:  # pragma: no cover
    OPENAI_AVAILABLE = False
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from openai import OpenAI

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except Exception:
    GENAI_AVAILABLE = False
    genai = None


# LEGACY FORMAT DISABLED - Only using updated scene-based format
# PAGE_DIR_PREFIX = "page_"  # legacy prefix
SCENE_DIR_PREFIX = "scene_"  # updated paired-page prefix
# DIR_PREFIXES = (PAGE_DIR_PREFIX, SCENE_DIR_PREFIX)
DIR_PREFIXES = (SCENE_DIR_PREFIX,)  # Only scene dirs now
PAGE_TEXT_FILENAME = "text.txt"
PAGE_CLEAN_FILENAME = "clean_text.txt"
WHOLE_STORY_FILENAME = "whole_story_cleaned.txt"
RAW_CONCAT_FILENAME = "whole_story_raw.txt"


@dataclass
class PageItem:
    index: int
    path: Path
    text_path: Path
    clean_path: Path


def list_pdf_dirs(root: Path) -> List[Path]:
    """Return immediate subdirectories of root that look like PDF extraction outputs."""
    items: List[Path] = []
    for p in sorted(root.iterdir()):
        if p.is_dir():
            # Heuristic: must contain at least one unit folder (page_XXXX or scene_XXXX)
            has_unit = any(
                child.is_dir() and any(child.name.startswith(pref) for pref in DIR_PREFIXES)
                for child in p.iterdir()
            )
            if has_unit:
                items.append(p)
    return items


def list_pages(pdf_dir: Path) -> List[PageItem]:
    pages: List[PageItem] = []
    for child in sorted(pdf_dir.iterdir()):
        if child.is_dir() and any(child.name.startswith(pref) for pref in DIR_PREFIXES):
            # Determine numeric part after prefix
            # LEGACY FORMAT DISABLED - Only handle scene_ dirs
            # if child.name.startswith(PAGE_DIR_PREFIX):
            #     num_str = child.name[len(PAGE_DIR_PREFIX):]
            # else:
            #     num_str = child.name[len(SCENE_DIR_PREFIX):]
            num_str = child.name[len(SCENE_DIR_PREFIX):]
            try:
                idx = int(num_str)
            except ValueError:
                idx = 0
            text_path = child / PAGE_TEXT_FILENAME
            clean_path = child / PAGE_CLEAN_FILENAME
            pages.append(PageItem(index=idx, path=child, text_path=text_path, clean_path=clean_path))
    # Sort by index then by name to be stable
    pages.sort(key=lambda x: (x.index, x.path.name))
    return pages


def _build_openai_client() -> "OpenAI":
    if not OPENAI_AVAILABLE:
        raise RuntimeError("openai package not installed. Please `pip install -r requirements.txt`." )
    from openai import OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in environment.")
    return OpenAI(api_key=api_key)


def _call_openai(client: "OpenAI", model: str, system_prompt: str, user_prompt: str, max_retries: int = 5, retry_delay: float = 2.0) -> str:
    """Call OpenAI responses API with simple text-in/text-out and retries."""
    last_err: Optional[Exception] = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )
            text = resp.choices[0].message.content or ""
            return text.strip()
        except Exception as e:  # pragma: no cover
            last_err = e
            # Exponential backoff
            time.sleep(retry_delay * attempt)
    raise RuntimeError(f"OpenAI request failed after {max_retries} retries: {last_err}")


def _ensure_gemini_ready() -> None:
    if not GENAI_AVAILABLE:
        raise RuntimeError("google-generativeai package not installed. Please `pip install -r requirements.txt`.")
    import google.generativeai as genai
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set in environment.")
    genai.configure(api_key=api_key)


def _call_gemini(model: str, system_prompt: str, user_prompt: str, max_retries: int = 5, retry_delay: float = 2.0) -> str:
    """Call Gemini with simple text-in/text-out and retries."""
    _ensure_gemini_ready()
    import google.generativeai as genai
    last_err: Optional[Exception] = None
    
    # Configure safety settings using the correct format
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    
    for attempt in range(1, max_retries + 1):
        try:
            gmodel = genai.GenerativeModel(model)
            # Combine system and user into ordered parts
            prompt_parts = [
                f"SYSTEM:\n{system_prompt}\n\n",
                f"USER:\n{user_prompt}",
            ]
            resp = gmodel.generate_content(prompt_parts, safety_settings=safety_settings)
            
            # Check if response was blocked
            if hasattr(resp, 'prompt_feedback') and resp.prompt_feedback.block_reason:
                raise RuntimeError(f"Content blocked by safety filters: {resp.prompt_feedback.block_reason}")
            
            # Try to get text, handle blocking gracefully
            try:
                text = resp.text
            except (ValueError, AttributeError) as e:
                # Response was blocked after generation
                if hasattr(resp, 'candidates') and resp.candidates:
                    candidate = resp.candidates[0]
                    if hasattr(candidate, 'finish_reason'):
                        raise RuntimeError(f"Response blocked: finish_reason={candidate.finish_reason}, safety_ratings={getattr(candidate, 'safety_ratings', 'N/A')}")
                raise RuntimeError(f"Unable to access response text: {str(e)}")
            
            return text.strip() if text else ""
        except Exception as e:  # pragma: no cover
            last_err = e
            time.sleep(retry_delay * attempt)
    raise RuntimeError(f"Gemini request failed after {max_retries} retries: {last_err}")


def clean_page_text(provider: str, client: Optional["OpenAI"], model: str, page_text: str) -> str:
    system = (
        "You clean up OCR'd or extracted page text.\n"
        "- Fix broken words, hyphenations, and spacing.\n"
        "- Preserve paragraphs and line breaks when meaningful.\n"
        "- Remove scanning artifacts and page headers/footers when obvious.\n"
        "- Do not add new content. Only correct formatting and minor typos.\n"
    )
    user = (
        "Clean the following page text and return only the cleaned text without any extra commentary.\n\n"
        f"TEXT:\n{page_text}"
    )
    if provider == "gemini":
        return _call_gemini(model, system, user)
    assert client is not None, "OpenAI client is required for OpenAI provider"
    return _call_openai(client, model, system, user)


def clean_whole_story(provider: str, client: Optional["OpenAI"], model: str, pages: List[Tuple[int, str]]) -> str:
    system = (
        "You compose a final, page-by-page cleaned version of a story.\n"
        "- Return the result clearly separated per page.\n"
        "- Prepend each section with 'Page NNNN:' using 1-based page numbers, zero-padded to 4 digits.\n"
        "- Do not add summaries or commentary; only the cleaned content.\n"
    )
    joined = []
    for idx, text in pages:
        joined.append(f"[PAGE {idx:04d}]\n{text}")
    user = (
        "Create a single, cohesive document from the per-page cleaned texts below.\n"
        "Keep the page breaks and label each with 'Page NNNN:' followed by the content.\n\n"
        + "\n\n".join(joined)
    )
    if provider == "gemini":
        return _call_gemini(model, system, user)
    assert client is not None, "OpenAI client is required for OpenAI provider"
    return _call_openai(client, model, system, user)


def process_pdf_dir(pdf_dir: Path, model: str, force: bool = False, skip_final: bool = False, provider: str = "openai") -> None:
    """
    Process a SINGLE PDF directory to clean and concatenate page texts.
    
    Args:
        pdf_dir: Path to a single PDF extraction directory (e.g., extracted/storyname)
        model: Model name to use
        force: Re-clean pages even if clean_text.txt exists
        skip_final: Skip final whole-story composition
        provider: LLM provider ('openai' or 'gemini')
    """
    # Safety check: ensure pdf_dir is a specific PDF directory, not the root extracted/ dir
    if not pdf_dir.exists():
        print(f"Error: Directory does not exist: {pdf_dir}")
        return
    
    if pdf_dir.name == "extracted" or str(pdf_dir).endswith("/extracted"):
        print(f"Error: Cannot process root 'extracted' directory. Please specify a single PDF directory.")
        print(f"Expected: extracted/<pdf_name>")
        print(f"Got: {pdf_dir}")
        return
    
    client: Optional["OpenAI"] = None
    if provider == "openai":
        client = _build_openai_client()
    
    pages = list_pages(pdf_dir)
    if not pages:
        print(f"No pages found in {pdf_dir}")
        return

    print(f"Processing ONLY: {pdf_dir.name} ({len(pages)} pages)")
    cleaned_pages: List[Tuple[int, str]] = []

    for page in tqdm(pages, desc=f"Cleaning pages in {pdf_dir.name}"):
        if not page.text_path.exists():
            # Nothing to do for this page
            continue
        raw_text = page.text_path.read_text(encoding="utf-8", errors="ignore")
        if (not force) and page.clean_path.exists():
            clean_text = page.clean_path.read_text(encoding="utf-8", errors="ignore")
        else:
            clean_text = clean_page_text(provider, client, model, raw_text)
            page.clean_path.write_text(clean_text, encoding="utf-8")
        cleaned_pages.append((page.index, clean_text))

    # Save concatenated raw (optional helpful artifact)
    try:
        raw_concat = []
        for page in pages:
            if page.text_path.exists():
                raw_concat.append(page.text_path.read_text(encoding="utf-8", errors="ignore"))
        if raw_concat:
            (pdf_dir / RAW_CONCAT_FILENAME).write_text("\n\n".join(raw_concat), encoding="utf-8")
    except Exception:
        pass

    if skip_final:
        return

    if not cleaned_pages:
        print(f"No cleaned pages to compose in {pdf_dir}")
        return

    final_story = clean_whole_story(provider, client, model, cleaned_pages)
    (pdf_dir / WHOLE_STORY_FILENAME).write_text(final_story, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Clean and concatenate page texts into a page-by-page whole story using OpenAI or Gemini")
    parser.add_argument("--root_dir", type=Path, default=Path.cwd() / "extracted", help="Root directory containing PDF output folders")
    parser.add_argument("--only", type=str, default="", help="Only process folders whose name contains this substring (exact match required)")
    parser.add_argument("--all", action="store_true", help="Process ALL PDF folders (use with caution)")
    parser.add_argument("--model", type=str, default=os.getenv("OPENAI_MODEL", os.getenv("GEMINI_MODEL", "gpt-4o-mini")), help="Model name to use (OpenAI or Gemini)")
    parser.add_argument("--provider", type=str, choices=["openai", "gemini"], default=os.getenv("LLM_PROVIDER", "openai"), help="LLM provider to use")
    parser.add_argument("--force", action="store_true", help="Re-clean pages even if clean_text.txt already exists")
    parser.add_argument("--skip_final", action="store_true", help="Skip final whole-story composition (only per-page cleaning)")
    args = parser.parse_args(argv)

    root = args.root_dir.resolve()
    if not root.exists():
        print(f"Root directory does not exist: {root}")
        return 1

    pdf_dirs = list_pdf_dirs(root)
    
    # Filter PDFs based on --only parameter or require --all flag
    if args.only:
        # Exact match only - the folder name must equal the --only value
        pdf_dirs = [d for d in pdf_dirs if d.name == args.only]
        if not pdf_dirs:
            print(f"No PDF folder found with name: {args.only}")
            print(f"Available folders: {', '.join(d.name for d in list_pdf_dirs(root))}")
            return 1
    elif not args.all:
        # Safety check: require explicit --all flag to process all PDFs
        print("Error: You must specify either --only <pdf_name> or --all to process PDFs")
        print(f"\nAvailable PDF folders under {root}:")
        for d in pdf_dirs:
            print(f"  - {d.name}")
        print(f"\nUsage examples:")
        print(f"  python clean_and_concatenate.py --only {pdf_dirs[0].name if pdf_dirs else 'storyname'}")
        print(f"  python clean_and_concatenate.py --all")
        return 1

    if not pdf_dirs:
        print(f"No PDF folders found under {root}")
        return 0

    print(f"Found {len(pdf_dirs)} folder(s) under {root}")
    for d in pdf_dirs:
        print(f"Processing folder: {d.name}")
        process_pdf_dir(d, model=args.model, force=args.force, skip_final=args.skip_final, provider=args.provider)

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
