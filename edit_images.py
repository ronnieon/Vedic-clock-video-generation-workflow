"""
Image Editing with Replicate API
=================================
Edit images using qwen/qwen-image-edit-plus model.
"""

import os
import replicate
from pathlib import Path
from typing import Optional, List
import requests


def edit_image_with_prompt(
    image_path: Path,
    prompt: str,
    output_path: Path,
    reference_images: Optional[List[Path]] = None,
    go_fast: bool = True,
    aspect_ratio: str = "match_input_image",
    output_format: str = "png",
    output_quality: int = 95,
    seed: Optional[int] = None
) -> bool:
    """
    Edit an image using text prompt via Replicate API.
    
    Args:
        image_path: Path to the image to edit
        prompt: Text instruction on how to edit the image
        output_path: Where to save the edited image
        reference_images: Optional list of reference images
        go_fast: Run faster predictions with optimizations
        aspect_ratio: Aspect ratio for output ("match_input_image", "1:1", "16:9", etc.)
        output_format: Output format ("png", "webp", "jpg")
        output_quality: Quality 0-100 (for jpg/webp)
        seed: Random seed for reproducibility
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Verify API token
        api_token = os.getenv('REPLICATE_API_TOKEN')
        if not api_token:
            raise ValueError("REPLICATE_API_TOKEN not found in environment")
        
        # Build input - open image as file handle
        with open(image_path, 'rb') as f:
            # Build input
            input_data = {
                "image": [f],
                "prompt": prompt,
                "go_fast": go_fast,
                "aspect_ratio": aspect_ratio,
                "output_format": output_format,
                "output_quality": output_quality,
            }
            
            if seed is not None:
                input_data["seed"] = seed
            
            # Add reference images if provided
            if reference_images:
                for ref_img in reference_images:
                    with open(ref_img, 'rb') as ref_f:
                        input_data["image"].append(ref_f)
            
            # Run the model using replicate.run() directly
            output = replicate.run(
                "qwen/qwen-image-edit-plus",
                input=input_data
            )
        
        # Download the first output image
        # Convert output to list if it's an iterator
        output_list = list(output) if output else []
        
        if output_list and len(output_list) > 0:
            # Get URL - handle both string URLs and FileOutput objects
            first_output = output_list[0]
            if isinstance(first_output, str):
                url = first_output
            elif hasattr(first_output, 'url'):
                url = first_output.url if isinstance(first_output.url, str) else first_output.url()
            else:
                url = str(first_output)
            
            # Download the image
            response = requests.get(url)
            response.raise_for_status()
            
            # Save to output path
            with open(output_path, 'wb') as out_f:
                out_f.write(response.content)
            
            return True
        else:
            return False
                
    except Exception as e:
        print(f"Error editing image: {str(e)}")
        return False


def batch_edit_images(
    image_paths: List[Path],
    prompts: List[str],
    output_dir: Path,
    **kwargs
) -> List[Path]:
    """
    Edit multiple images with corresponding prompts.
    
    Args:
        image_paths: List of image paths to edit
        prompts: List of prompts (one per image)
        output_dir: Directory to save outputs
        **kwargs: Additional arguments passed to edit_image_with_prompt
    
    Returns:
        List of successfully created output paths
    """
    if len(image_paths) != len(prompts):
        raise ValueError("Number of images must match number of prompts")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    
    for i, (img_path, prompt) in enumerate(zip(image_paths, prompts)):
        output_path = output_dir / f"edited_{i}_{img_path.name}"
        success = edit_image_with_prompt(img_path, prompt, output_path, **kwargs)
        
        if success:
            results.append(output_path)
    
    return results


def enhance_image(image_path: Path, output_path: Path, enhancement_type: str = "general") -> bool:
    """
    Enhance image quality using predefined prompts.
    
    Args:
        image_path: Path to image
        output_path: Output path
        enhancement_type: Type of enhancement
            - "general": General quality improvement
            - "colorful": Make more vibrant
            - "sharpen": Increase sharpness
            - "denoise": Remove noise
            - "upscale": Improve resolution
    
    Returns:
        True if successful
    """
    prompts = {
        "general": "Enhance the image quality, improve clarity and colors",
        "colorful": "Make the colors more vibrant and saturated",
        "sharpen": "Increase sharpness and detail",
        "denoise": "Remove noise and grain while preserving details",
        "upscale": "Upscale and enhance resolution while maintaining quality"
    }
    
    prompt = prompts.get(enhancement_type, prompts["general"])
    return edit_image_with_prompt(image_path, prompt, output_path)


def style_transfer(
    content_image: Path,
    style_reference: Path,
    output_path: Path,
    style_strength: str = "moderate"
) -> bool:
    """
    Apply style from reference image to content image.
    
    Args:
        content_image: Main image to style
        style_reference: Image with desired style
        output_path: Output path
        style_strength: "subtle", "moderate", or "strong"
    
    Returns:
        True if successful
    """
    strength_prompts = {
        "subtle": "Apply a subtle style from image 2 to image 1",
        "moderate": "Apply the artistic style from image 2 to image 1",
        "strong": "Strongly apply the style and visual characteristics from image 2 to image 1"
    }
    
    prompt = strength_prompts.get(style_strength, strength_prompts["moderate"])
    
    return edit_image_with_prompt(
        content_image,
        prompt,
        output_path,
        reference_images=[style_reference]
    )
