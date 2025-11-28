"""
Background Processor for Queued Tasks
======================================
Processes queued image edit and image-to-video tasks.

This script runs independently and picks up queued prompts from page directories,
processes them using Replicate API, and generates new versions.

Usage:
    python background_processor.py [--pdf-stem STEM] [--interval SECONDS]
"""

import argparse
import time
from pathlib import Path
from typing import List, Optional
import sys

from utils.queue_manager import (
    get_queued_prompts,
    read_prompt_from_file,
    mark_prompt_as_processing,
    mark_prompt_as_completed,
    mark_prompt_as_failed
)
from utils.versioning import create_new_version, get_latest_version_path
from edit_images import edit_image_with_prompt
from generate_image_videos import generate_video_from_image
from utils.logger import logger


def get_all_page_directories(extracted_dir: Path = Path("extracted")) -> List[Path]:
    """Get all scene directories across all PDFs. LEGACY FORMAT DISABLED."""
    page_dirs = []
    
    if not extracted_dir.exists():
        return page_dirs
    
    for pdf_dir in extracted_dir.iterdir():
        if pdf_dir.is_dir():
            # LEGACY FORMAT DISABLED - Only collect scene_ dirs
            # for page_dir in pdf_dir.iterdir():
            #     if page_dir.is_dir() and page_dir.name.startswith('page_'):
            #         page_dirs.append(page_dir)
            for scene_dir in pdf_dir.iterdir():
                if scene_dir.is_dir() and scene_dir.name.startswith('scene_'):
                    page_dirs.append(scene_dir)
    
    return sorted(page_dirs)


def process_image_edit_queue(page_dir: Path) -> int:
    """
    Process all queued image edit prompts for a page.
    
    Returns:
        Number of successfully processed prompts
    """
    queued_prompts = get_queued_prompts(page_dir, 'image_edit')
    
    if not queued_prompts:
        return 0
    
    success_count = 0
    
    for prompt_file in queued_prompts:
        logger.info(f"Processing image edit: {prompt_file}")
        
        # Mark as processing
        mark_prompt_as_processing(prompt_file)
        
        try:
            # Read prompt
            prompt = read_prompt_from_file(prompt_file)
            if not prompt:
                raise ValueError("Failed to read prompt from file")
            
            # Get latest image
            image_path = get_latest_version_path(page_dir, 'image')
            if not image_path:
                image_path = page_dir / 'image_to_use.png'
            
            if not image_path or not image_path.exists():
                raise FileNotFoundError(f"No image found in {page_dir}")
            
            # Create temp output
            temp_output = page_dir / f'temp_bg_edit_{prompt_file.stem}.png'
            
            # Edit image
            success = edit_image_with_prompt(
                image_path,
                prompt,
                temp_output,
                output_format='png'
            )
            
            if success and temp_output.exists():
                # Create new version
                create_new_version(page_dir, 'image', str(temp_output), model='qwen-image-edit-plus')
                temp_output.unlink()
                
                # Mark as completed
                mark_prompt_as_completed(prompt_file)
                success_count += 1
                logger.info(f"✅ Successfully processed: {prompt_file.name}")
            else:
                raise RuntimeError("Image editing failed")
                
        except Exception as e:
            logger.error(f"❌ Failed to process {prompt_file.name}: {str(e)}")
            mark_prompt_as_failed(prompt_file, str(e))
    
    return success_count


def process_image_to_video_queue(page_dir: Path) -> int:
    """
    Process all queued image-to-video prompts for a page.
    
    Returns:
        Number of successfully processed prompts
    """
    queued_prompts = get_queued_prompts(page_dir, 'image_to_video')
    
    if not queued_prompts:
        return 0
    
    success_count = 0
    
    for prompt_file in queued_prompts:
        logger.info(f"Processing image-to-video: {prompt_file}")
        
        # Mark as processing
        mark_prompt_as_processing(prompt_file)
        
        try:
            # Read prompt
            prompt = read_prompt_from_file(prompt_file)
            if not prompt:
                raise ValueError("Failed to read prompt from file")
            
            # Get latest image
            image_path = get_latest_version_path(page_dir, 'image')
            if not image_path:
                image_path = page_dir / 'image_to_use.png'
            
            if not image_path or not image_path.exists():
                raise FileNotFoundError(f"No image found in {page_dir}")
            
            # Create temp output
            temp_output = page_dir / f'temp_bg_video_{prompt_file.stem}.mp4'
            
            # Generate video
            success = generate_video_from_image(
                image_path,
                prompt,
                temp_output,
                num_frames=81,
                aspect_ratio="16:9",
                frames_per_second=24,
                sample_shift=5.0
            )
            
            if success and temp_output.exists():
                # Create new version
                create_new_version(page_dir, 'image_video', str(temp_output), model='wan-video/wan-2.2-i2v-fast')
                temp_output.unlink()
                
                # Mark as completed
                mark_prompt_as_completed(prompt_file)
                success_count += 1
                logger.info(f"✅ Successfully processed: {prompt_file.name}")
            else:
                raise RuntimeError("Video generation failed")
                
        except Exception as e:
            logger.error(f"❌ Failed to process {prompt_file.name}: {str(e)}")
            mark_prompt_as_failed(prompt_file, str(e))
    
    return success_count


def process_all_queues(pdf_stem: Optional[str] = None) -> dict:
    """
    Process all queued tasks across all pages.
    
    Args:
        pdf_stem: Optional PDF stem to filter pages. If None, processes all PDFs.
        
    Returns:
        Dictionary with processing statistics
    """
    stats = {
        'image_edits': 0,
        'image_videos': 0,
        'pages_processed': 0
    }
    
    # Get page directories
    if pdf_stem:
        extracted_dir = Path("extracted") / pdf_stem
        if not extracted_dir.exists():
            logger.warning(f"PDF directory not found: {extracted_dir}")
            return stats
        page_dirs = sorted([p for p in extracted_dir.iterdir() if p.is_dir() and p.name.startswith('page_')])
    else:
        page_dirs = get_all_page_directories()
    
    logger.info(f"Scanning {len(page_dirs)} page directories for queued tasks...")
    
    for page_dir in page_dirs:
        # Check for queued tasks
        image_edit_count = len(get_queued_prompts(page_dir, 'image_edit'))
        image_video_count = len(get_queued_prompts(page_dir, 'image_to_video'))
        
        if image_edit_count == 0 and image_video_count == 0:
            continue
        
        logger.info(f"\n📁 Processing {page_dir.name}: {image_edit_count} image edits, {image_video_count} videos")
        
        # Process image edits
        if image_edit_count > 0:
            processed = process_image_edit_queue(page_dir)
            stats['image_edits'] += processed
        
        # Process image-to-video
        if image_video_count > 0:
            processed = process_image_to_video_queue(page_dir)
            stats['image_videos'] += processed
        
        stats['pages_processed'] += 1
    
    return stats


def main():
    """Main entry point for background processor."""
    parser = argparse.ArgumentParser(description='Process queued image edit and video generation tasks')
    parser.add_argument('--pdf-stem', type=str, help='Process only this PDF (e.g., "download")')
    parser.add_argument('--interval', type=int, default=60, help='Polling interval in seconds (default: 60)')
    parser.add_argument('--once', action='store_true', help='Run once and exit (don\'t loop)')
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Background Processor Started")
    logger.info("=" * 60)
    logger.info(f"PDF Filter: {args.pdf_stem or 'ALL'}")
    logger.info(f"Mode: {'Single Run' if args.once else f'Continuous (every {args.interval}s)'}")
    logger.info("=" * 60)
    
    try:
        while True:
            logger.info(f"\n🔄 Starting processing cycle...")
            
            stats = process_all_queues(args.pdf_stem)
            
            logger.info(f"\n📊 Cycle Complete:")
            logger.info(f"  - Pages processed: {stats['pages_processed']}")
            logger.info(f"  - Image edits: {stats['image_edits']}")
            logger.info(f"  - Image videos: {stats['image_videos']}")
            
            if args.once:
                logger.info("\n✅ Single run complete. Exiting.")
                break
            
            logger.info(f"\n⏸️  Waiting {args.interval} seconds before next cycle...")
            time.sleep(args.interval)
            
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Interrupted by user. Shutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n\n❌ Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
