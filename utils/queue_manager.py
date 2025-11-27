"""
Queue Manager for Background Processing
========================================
Manages queued tasks for image editing and image-to-video generation.
"""

from pathlib import Path
from typing import Optional
from datetime import datetime


def queue_image_edit_prompt(
    page_dir: Path,
    prompt: str,
    target_version: int
) -> Path:
    """
    Queue an image edit prompt for later processing.
    
    Args:
        page_dir: Path to page directory
        prompt: Edit instruction prompt
        target_version: Target version number for the edit
        
    Returns:
        Path to the created prompt file
    """
    prompt_file = page_dir / f'image_edit_prompt_for_v{target_version}.txt'
    
    # Write prompt with metadata
    content = f"""# Image Edit Prompt for v{target_version}
# Queued at: {datetime.now().isoformat()}
# Status: PENDING

{prompt}
"""
    
    with open(prompt_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return prompt_file


def queue_image_to_video_prompt(
    page_dir: Path,
    prompt: str,
    target_version: int
) -> Path:
    """
    Queue an image-to-video prompt for later processing.
    
    Args:
        page_dir: Path to page directory
        prompt: Motion/video generation prompt
        target_version: Target version number for the video
        
    Returns:
        Path to the created prompt file
    """
    prompt_file = page_dir / f'image_to_video_prompt_for_v{target_version}.txt'
    
    # Write ONLY the prompt text (no metadata)
    with open(prompt_file, 'w', encoding='utf-8') as f:
        f.write(prompt)
    
    return prompt_file


def get_queued_prompts(page_dir: Path, prompt_type: str) -> list[Path]:
    """
    Get all queued prompts of a specific type for a page.
    
    Args:
        page_dir: Path to page directory
        prompt_type: Either 'image_edit' or 'image_to_video'
        
    Returns:
        List of prompt file paths
    """
    if prompt_type == 'image_edit':
        pattern = 'image_edit_prompt_for_v*.txt'
    elif prompt_type == 'image_to_video':
        pattern = 'image_to_video_prompt_for_v*.txt'
    else:
        raise ValueError(f"Invalid prompt_type: {prompt_type}")
    
    return sorted(page_dir.glob(pattern))


def mark_prompt_as_processing(prompt_file: Path) -> bool:
    """
    Mark a queued prompt as being processed.
    
    Args:
        prompt_file: Path to the prompt file
        
    Returns:
        True if successful
    """
    try:
        content = prompt_file.read_text(encoding='utf-8')
        content = content.replace('# Status: PENDING', '# Status: PROCESSING')
        content += f"\n# Processing started: {datetime.now().isoformat()}\n"
        
        prompt_file.write_text(content, encoding='utf-8')
        return True
    except Exception:
        return False


def mark_prompt_as_completed(prompt_file: Path) -> bool:
    """
    Mark a queued prompt as completed and archive it.
    
    Args:
        prompt_file: Path to the prompt file
        
    Returns:
        True if successful
    """
    try:
        content = prompt_file.read_text(encoding='utf-8')
        content = content.replace('# Status: PROCESSING', '# Status: COMPLETED')
        content = content.replace('# Status: PENDING', '# Status: COMPLETED')
        content += f"\n# Completed at: {datetime.now().isoformat()}\n"
        
        # Rename to .completed extension
        completed_file = prompt_file.with_suffix('.txt.completed')
        prompt_file.write_text(content, encoding='utf-8')
        prompt_file.rename(completed_file)
        return True
    except Exception:
        return False


def mark_prompt_as_failed(prompt_file: Path, error: str) -> bool:
    """
    Mark a queued prompt as failed.
    
    Args:
        prompt_file: Path to the prompt file
        error: Error message
        
    Returns:
        True if successful
    """
    try:
        content = prompt_file.read_text(encoding='utf-8')
        content = content.replace('# Status: PROCESSING', '# Status: FAILED')
        content = content.replace('# Status: PENDING', '# Status: FAILED')
        content += f"\n# Failed at: {datetime.now().isoformat()}\n"
        content += f"# Error: {error}\n"
        
        # Rename to .failed extension
        failed_file = prompt_file.with_suffix('.txt.failed')
        prompt_file.write_text(content, encoding='utf-8')
        prompt_file.rename(failed_file)
        return True
    except Exception:
        return False


def read_prompt_from_file(prompt_file: Path) -> Optional[str]:
    """
    Read the actual prompt text from a prompt file.
    
    Handles both old format (with metadata) and new format (plain text).
    
    Args:
        prompt_file: Path to the prompt file
        
    Returns:
        The prompt text, or None if file doesn't exist
    """
    if not prompt_file.exists():
        return None
    
    try:
        content = prompt_file.read_text(encoding='utf-8').strip()
        
        # If file starts with #, it's old format with metadata
        if content.startswith('#'):
            lines = content.split('\n')
            
            # Skip metadata lines (starting with #) and empty lines
            prompt_lines = []
            for line in lines:
                if not line.strip().startswith('#') and line.strip():
                    prompt_lines.append(line)
            
            return '\n'.join(prompt_lines).strip()
        else:
            # New format - just return the content as-is
            return content
    except Exception:
        return None
