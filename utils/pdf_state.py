"""
PDF State Management
====================
Persistent storage for PDF completion status.
"""

from pathlib import Path
import json
from typing import Set
from utils.logger import logger


STATE_FILE = Path(".pdf_completion_state.json")


def load_marked_done_pdfs() -> Set[str]:
    """
    Load the set of marked-as-done PDFs from persistent storage.
    
    Returns:
        Set of PDF filenames that are marked as done
    """
    if not STATE_FILE.exists():
        return set()
    
    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            marked_done = set(data.get('marked_done_pdfs', []))
            logger.info(f"Loaded {len(marked_done)} marked-as-done PDF(s) from state file")
            return marked_done
    except Exception as e:
        logger.error(f"Error loading PDF state: {e}")
        return set()


def save_marked_done_pdfs(marked_done: Set[str]):
    """
    Save the set of marked-as-done PDFs to persistent storage.
    
    Args:
        marked_done: Set of PDF filenames that are marked as done
    """
    try:
        data = {
            'marked_done_pdfs': list(marked_done)
        }
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.debug(f"Saved {len(marked_done)} marked-as-done PDF(s) to state file")
    except Exception as e:
        logger.error(f"Error saving PDF state: {e}")


def mark_pdf_as_done(pdf_filename: str) -> bool:
    """
    Mark a PDF as done and persist the change.
    
    Args:
        pdf_filename: Name of the PDF file
        
    Returns:
        True if successful
    """
    try:
        marked_done = load_marked_done_pdfs()
        marked_done.add(pdf_filename)
        save_marked_done_pdfs(marked_done)
        logger.info(f"Marked as done: {pdf_filename}")
        return True
    except Exception as e:
        logger.error(f"Error marking PDF as done: {e}")
        return False


def unmark_pdf_as_done(pdf_filename: str) -> bool:
    """
    Remove the done marking from a PDF and persist the change.
    
    Args:
        pdf_filename: Name of the PDF file
        
    Returns:
        True if successful
    """
    try:
        marked_done = load_marked_done_pdfs()
        marked_done.discard(pdf_filename)
        save_marked_done_pdfs(marked_done)
        logger.info(f"Re-enabled (unmarked): {pdf_filename}")
        return True
    except Exception as e:
        logger.error(f"Error unmarking PDF: {e}")
        return False


def is_pdf_marked_done(pdf_filename: str) -> bool:
    """
    Check if a PDF is marked as done.
    
    Args:
        pdf_filename: Name of the PDF file
        
    Returns:
        True if marked as done, False otherwise
    """
    marked_done = load_marked_done_pdfs()
    return pdf_filename in marked_done
