"""
Generate Image Captions using Replicate BLIP-2 API
===================================================
Generate descriptive captions for images using the BLIP-2 model.
"""

import os
import replicate
from pathlib import Path
from typing import Optional


def generate_image_caption(
    image_path: Path,
    question: Optional[str] = None,
    use_caption_mode: bool = True,
    context: Optional[str] = None,
    temperature: float = 1.0,
    use_nucleus_sampling: bool = False
) -> Optional[str]:
    """
    Generate caption or answer question about an image using BLIP-2.
    
    Args:
        image_path: Path to the input image
        question: Question to ask about the image (leave None for captioning)
        use_caption_mode: If True, generates image caption instead of answering questions
        context: Optional previous questions/answers for context
        temperature: Temperature for nucleus sampling (0.5-1.0)
        use_nucleus_sampling: Toggle nucleus sampling
    
    Returns:
        Generated caption/answer or None if failed
    """
    try:
        # Verify API token
        api_token = os.getenv('REPLICATE_API_TOKEN')
        if not api_token:
            raise ValueError("REPLICATE_API_TOKEN not found in environment")
        
        # Open image as file handle
        with open(image_path, 'rb') as f:
            # Build input
            input_data = {
                "image": f,
                "temperature": temperature,
                "use_nucleus_sampling": use_nucleus_sampling,
            }
            
            # Add caption mode or question
            if use_caption_mode:
                input_data["caption"] = True
            else:
                input_data["question"] = question or "What is this a picture of?"
            
            # Add context if provided
            if context:
                input_data["context"] = context
            
            # Run the model
            output = replicate.run(
                "andreasjansson/blip-2:f677695e5e89f8b236e52ecd1d3f01beb44c34606419bcc19345e046d8f786f9",
                input=input_data
            )
        
        # Return the caption/answer
        if output:
            return str(output).strip()
        else:
            return None
                
    except Exception as e:
        print(f"Error generating caption: {str(e)}")
        return None


def batch_generate_captions(
    page_dirs: list[Path],
    use_caption_mode: bool = True,
    question: Optional[str] = None
) -> dict[str, Optional[str]]:
    """
    Generate captions for multiple pages.
    
    Args:
        page_dirs: List of page directories
        use_caption_mode: If True, generates captions; if False, asks questions
        question: Optional question to ask (used when use_caption_mode=False)
    
    Returns:
        Dict mapping page_dir.name to generated caption/answer
    """
    results = {}
    
    for page_dir in page_dirs:
        # Get latest image
        from utils.versioning import get_latest_version_path
        image_path = get_latest_version_path(page_dir, 'image')
        
        if not image_path or not image_path.exists():
            # Try legacy
            image_path = page_dir / 'image_to_use.png'
            if not image_path.exists():
                results[page_dir.name] = None
                continue
        
        # Generate caption
        caption = generate_image_caption(
            image_path,
            question=question,
            use_caption_mode=use_caption_mode
        )
        
        results[page_dir.name] = caption
        
        # Save caption to file if generated
        if caption:
            caption_file = page_dir / 'image_caption.txt'
            caption_file.write_text(caption, encoding='utf-8')
    
    return results
