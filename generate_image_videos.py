"""
Generate Videos from Images using Replicate API
===============================================
Convert images to videos using wan-video/wan-2.2-5b-fast model.
"""

import os
import replicate
from pathlib import Path
from typing import Optional
import requests


def generate_video_from_image(
    image_path: Path,
    prompt: str,
    output_path: Path,
    num_frames: int = 81,
    aspect_ratio: str = "16:9",
    resolution: str = "720p",
    frames_per_second: int = 24,
    sample_shift: float = 5,
    go_fast: bool = True,
    seed: Optional[int] = None,
    negative_prompt: Optional[str] = None,
    optimize_prompt: bool = False
) -> bool:
    """
    Generate video from image using Replicate wan-video API.
    
    Args:
        image_path: Path to the input image
        prompt: Text prompt describing video motion/action
        output_path: Where to save the generated video
        num_frames: Number of frames (81-121, 81 recommended)
        aspect_ratio: Video aspect ratio ("16:9" or "9:16")
        resolution: Video resolution ("720p", "1080p", etc.)
        frames_per_second: FPS (5-30, default 24)
        sample_shift: Sample shift factor (1-20, default 5)
        go_fast: Enable fast processing
        seed: Random seed for reproducibility
        negative_prompt: What to avoid in the video
        optimize_prompt: Translate prompt to Chinese before generation
    
    Returns:
        True if successful, False otherwise
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
                "prompt": prompt,
                "num_frames": num_frames,
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
                "frames_per_second": frames_per_second,
                "sample_shift": sample_shift,
                "go_fast": go_fast,
            }
            
            if seed is not None:
                input_data["seed"] = seed
            
            if negative_prompt:
                input_data["negative_prompt"] = negative_prompt
            
            if optimize_prompt:
                input_data["optimize_prompt"] = optimize_prompt
            
            # Run the model
            output = replicate.run(
                "wan-video/wan-2.2-i2v-fast",
                input=input_data
            )
        
        # Handle output - it should be a single video file
        if output:
            # Get URL from output
            if isinstance(output, str):
                url = output
            elif hasattr(output, 'url'):
                url = output.url if isinstance(output.url, str) else output.url()
            elif hasattr(output, 'read'):
                # FileOutput object
                with open(output_path, 'wb') as out_f:
                    out_f.write(output.read())
                return True
            else:
                url = str(output)
            
            # Download the video
            response = requests.get(url)
            response.raise_for_status()
            
            # Save to output path
            with open(output_path, 'wb') as out_f:
                out_f.write(response.content)
            
            return True
        else:
            return False
                
    except Exception as e:
        print(f"Error generating video from image: {str(e)}")
        return False


def generate_default_prompt(page_index: int, page_text: Optional[str] = None) -> str:
    """
    Generate a default prompt for video generation based on page content.
    
    Args:
        page_index: Page number (1-indexed)
        page_text: Optional page text content to inform the prompt
    
    Returns:
        Default prompt string
    """
    # Generic prompts that work well for story pages
    prompts = [
        "camera slowly zooms in, subtle movements and depth",
        "gentle pan across the scene, characters slightly animated",
        "scene comes to life with subtle motion and atmosphere",
        "camera drifts smoothly, adding life to the static scene",
        "soft movement brings the illustration to life"
    ]
    
    # Rotate through prompts based on page index
    return prompts[page_index % len(prompts)]


def batch_generate_videos(
    page_dirs: list[Path],
    prompts: Optional[dict[str, str]] = None,
    **kwargs
) -> dict[str, bool]:
    """
    Generate videos for multiple pages.
    
    Args:
        page_dirs: List of page directories
        prompts: Optional dict mapping page_dir.name to prompt
        **kwargs: Additional arguments for generate_video_from_image
    
    Returns:
        Dict mapping page_dir.name to success status
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
                results[page_dir.name] = False
                continue
        
        # Get prompt
        if prompts and page_dir.name in prompts:
            prompt = prompts[page_dir.name]
        else:
            # Extract page number from directory name
            page_num = int(page_dir.name.split('_')[1]) if '_' in page_dir.name else 1
            prompt = generate_default_prompt(page_num)
        
        # Generate output path
        output_path = page_dir / 'page_image_video_temp.mp4'
        
        # Generate video
        success = generate_video_from_image(
            image_path,
            prompt,
            output_path,
            **kwargs
        )
        
        results[page_dir.name] = success
    
    return results
