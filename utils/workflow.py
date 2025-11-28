"""
Workflow Status Management
===========================
Functions to check and track the progress of the PDF-to-slideshow pipeline.
"""

from pathlib import Path
from typing import Dict, List, Tuple
from utils.versioning import get_latest_version_path, get_latest_version_number, migrate_legacy_files


EXTRACTED_DIR = Path('extracted')


def get_workflow_status(pdf_stem: str) -> Dict:
    """
    Check the completion status of each workflow stage for a given PDF.
    Returns detailed status including completion percentage and missing files.
    
    Args:
        pdf_stem: PDF filename without extension (e.g., 'download')
        
    Returns:
        Dictionary with detailed status for each stage:
        {
            'extracted': {'complete': bool, 'total': int, 'done': int, 'missing': []},
            'planned': {...},
            'rewritten': {...},
            'audio_generated': {...},
            'slideshow_created': {...}
        }
    """
    extraction_dir = EXTRACTED_DIR / pdf_stem
    
    status = {
        'extracted': {'complete': False, 'total': 0, 'done': 0, 'missing': [], 'present': [], 'max_version': 0, 'expected_version': 0},
        'planned': {'complete': False, 'total': 0, 'done': 0, 'missing': [], 'present': [], 'max_version': 0, 'expected_version': 0},
        'rewritten': {'complete': False, 'total': 0, 'done': 0, 'missing': [], 'present': [], 'max_version': 0, 'expected_version': 0},
        'audio_generated': {'complete': False, 'total': 0, 'done': 0, 'missing': [], 'present': [], 'max_version': 0, 'expected_version': 0},
        'page_videos': {'complete': False, 'total': 0, 'done': 0, 'missing': [], 'present': [], 'max_version': 0, 'expected_version': 0},
        'slideshow_created': {'complete': False, 'total': 0, 'done': 0, 'missing': [], 'present': [], 'max_version': 0, 'expected_version': 0}
    }
    
    # Check extraction
    if extraction_dir.exists():
        # LEGACY FORMAT DISABLED: Only support scene_XXXX units (updated format)
        page_dirs = get_page_directories(pdf_stem)
        
        if len(page_dirs) > 0:
            status['extracted']['complete'] = True
            status['extracted']['total'] = len(page_dirs)
            status['extracted']['done'] = len(page_dirs)
            status['extracted']['present'] = [str(p) for p in page_dirs]
            
            # Check story planning (clean_text.txt in each page)
            status['planned']['total'] = len(page_dirs) + 1  # units + whole_story file
            story_file = extraction_dir / 'whole_story_cleaned.txt'
            
            if story_file.exists():
                status['planned']['done'] += 1
                status['planned']['present'].append(str(story_file))
            else:
                status['planned']['missing'].append(str(story_file))
            
            for page_dir in page_dirs:
                clean_file = page_dir / 'clean_text.txt'
                if clean_file.exists():
                    status['planned']['done'] += 1
                    status['planned']['present'].append(str(clean_file))
                else:
                    status['planned']['missing'].append(str(clean_file))
            
            status['planned']['complete'] = status['planned']['done'] == status['planned']['total']
            
            # Check rewriting (versioned final_text files) across units (page or scene)
            # First pass: migrate legacy files and find max version across text AND audio
            for page_dir in page_dirs:
                migrate_legacy_files(page_dir)
                en_text_version = get_latest_version_number(page_dir, 'en_text')
                hi_text_version = get_latest_version_number(page_dir, 'hi_text')
                en_audio_version = get_latest_version_number(page_dir, 'en_audio')
                hi_audio_version = get_latest_version_number(page_dir, 'hi_audio')
                
                # Max version considers both text and audio (audio can be ahead)
                status['rewritten']['max_version'] = max(
                    status['rewritten']['max_version'], 
                    en_text_version, hi_text_version,
                    en_audio_version, hi_audio_version
                )
            
            # Expected version is the max version found across all assets
            status['rewritten']['expected_version'] = status['rewritten']['max_version']
            status['rewritten']['total'] = len(page_dirs) * 2  # EN + HI per unit
            
            # Second pass: check if all files are at expected version
            for page_dir in page_dirs:
                en_version = get_latest_version_number(page_dir, 'en_text')
                hi_version = get_latest_version_number(page_dir, 'hi_text')
                en_file = get_latest_version_path(page_dir, 'en_text')
                hi_file = get_latest_version_path(page_dir, 'hi_text')
                
                # Check EN text
                if en_file and en_file.exists() and en_version == status['rewritten']['expected_version']:
                    status['rewritten']['done'] += 1
                    status['rewritten']['present'].append(f"{en_file} (v{en_version})")
                elif en_file and en_file.exists():
                    # File exists but at wrong version
                    status['rewritten']['missing'].append(f"{page_dir}/final_text_en (has v{en_version}, needs v{status['rewritten']['expected_version']})")
                else:
                    status['rewritten']['missing'].append(f"{page_dir}/final_text_en (needs v{status['rewritten']['expected_version']})")
                
                # Check HI text
                if hi_file and hi_file.exists() and hi_version == status['rewritten']['expected_version']:
                    status['rewritten']['done'] += 1
                    status['rewritten']['present'].append(f"{hi_file} (v{hi_version})")
                elif hi_file and hi_file.exists():
                    # File exists but at wrong version
                    status['rewritten']['missing'].append(f"{page_dir}/final_text_hi (has v{hi_version}, needs v{status['rewritten']['expected_version']})")
                else:
                    status['rewritten']['missing'].append(f"{page_dir}/final_text_hi (needs v{status['rewritten']['expected_version']})")
            
            status['rewritten']['complete'] = status['rewritten']['done'] == status['rewritten']['total']
            
            # Check audio generation (versioned audio files)
            # Find max version across BOTH text and audio (audio can be ahead)
            status['audio_generated']['total'] = len(page_dirs) * 2  # EN + HI audio per unit
            
            # First pass: find max audio version AND consider text version
            for page_dir in page_dirs:
                migrate_legacy_files(page_dir)
                en_audio_version = get_latest_version_number(page_dir, 'en_audio')
                hi_audio_version = get_latest_version_number(page_dir, 'hi_audio')
                en_text_version = get_latest_version_number(page_dir, 'en_text')
                hi_text_version = get_latest_version_number(page_dir, 'hi_text')
                
                # Max version is the highest across ALL assets (text + audio)
                status['audio_generated']['max_version'] = max(
                    status['audio_generated']['max_version'], 
                    en_audio_version, hi_audio_version,
                    en_text_version, hi_text_version
                )
            
            # Expected version is the max found across all assets
            status['audio_generated']['expected_version'] = status['audio_generated']['max_version']
            
            # Second pass: check if audio matches expected text version
            for page_dir in page_dirs:
                en_audio_version = get_latest_version_number(page_dir, 'en_audio')
                hi_audio_version = get_latest_version_number(page_dir, 'hi_audio')
                en_audio = get_latest_version_path(page_dir, 'en_audio')
                hi_audio = get_latest_version_path(page_dir, 'hi_audio')
                
                # Check EN audio
                if en_audio and en_audio.exists() and en_audio_version == status['audio_generated']['expected_version']:
                    status['audio_generated']['done'] += 1
                    status['audio_generated']['present'].append(f"{en_audio} (v{en_audio_version})")
                elif en_audio and en_audio.exists():
                    status['audio_generated']['missing'].append(f"{page_dir}/final_text_en.mp3 (has v{en_audio_version}, needs v{status['audio_generated']['expected_version']})")
                else:
                    status['audio_generated']['missing'].append(f"{page_dir}/final_text_en.mp3 (needs v{status['audio_generated']['expected_version']})")
                
                # Check HI audio
                if hi_audio and hi_audio.exists() and hi_audio_version == status['audio_generated']['expected_version']:
                    status['audio_generated']['done'] += 1
                    status['audio_generated']['present'].append(f"{hi_audio} (v{hi_audio_version})")
                elif hi_audio and hi_audio.exists():
                    status['audio_generated']['missing'].append(f"{page_dir}/final_text_hi.mp3 (has v{hi_audio_version}, needs v{status['audio_generated']['expected_version']})")
                else:
                    status['audio_generated']['missing'].append(f"{page_dir}/final_text_hi.mp3 (needs v{status['audio_generated']['expected_version']})")
            
            status['audio_generated']['complete'] = status['audio_generated']['done'] == status['audio_generated']['total']
            
            # Check page/scene videos (image + audio combined per unit)
            # Find max version across text, audio, AND videos
            status['page_videos']['total'] = len(page_dirs) * 2  # EN + HI video per unit
            
            # First pass: find max across all assets
            for page_dir in page_dirs:
                # Check text and audio versions
                en_text_version = get_latest_version_number(page_dir, 'en_text')
                hi_text_version = get_latest_version_number(page_dir, 'hi_text')
                en_audio_version = get_latest_version_number(page_dir, 'en_audio')
                hi_audio_version = get_latest_version_number(page_dir, 'hi_audio')
                
                # Check for any version of page videos
                for i in range(1, 20):  # Check up to v20
                    if (page_dir / f'page_video_en_v{i}.mp4').exists():
                        status['page_videos']['max_version'] = max(status['page_videos']['max_version'], i)
                    if (page_dir / f'page_video_hi_v{i}.mp4').exists():
                        status['page_videos']['max_version'] = max(status['page_videos']['max_version'], i)
                
                # Max version is highest across ALL assets
                status['page_videos']['max_version'] = max(
                    status['page_videos']['max_version'],
                    en_text_version, hi_text_version,
                    en_audio_version, hi_audio_version
                )
            
            # Expected version is the max found
            status['page_videos']['expected_version'] = status['page_videos']['max_version']
            
            # Second pass: check if videos match expected version
            for page_dir in page_dirs:
                en_video = page_dir / f'page_video_en_v{status["page_videos"]["expected_version"]}.mp4'
                hi_video = page_dir / f'page_video_hi_v{status["page_videos"]["expected_version"]}.mp4'
                
                # Check EN page video
                if en_video.exists():
                    status['page_videos']['done'] += 1
                    status['page_videos']['present'].append(f"{en_video} (v{status['page_videos']['expected_version']})")
                else:
                    # Check if older version exists
                    has_older = False
                    for i in range(1, status['page_videos']['expected_version']):
                        if (page_dir / f'page_video_en_v{i}.mp4').exists():
                            has_older = True
                            status['page_videos']['missing'].append(f"{page_dir}/page_video_en.mp4 (has v{i}, needs v{status['page_videos']['expected_version']})")
                            break
                    if not has_older:
                        status['page_videos']['missing'].append(f"{page_dir}/page_video_en.mp4 (needs v{status['page_videos']['expected_version']})")
                
                # Check HI page video
                if hi_video.exists():
                    status['page_videos']['done'] += 1
                    status['page_videos']['present'].append(f"{hi_video} (v{status['page_videos']['expected_version']})")
                else:
                    has_older = False
                    for i in range(1, status['page_videos']['expected_version']):
                        if (page_dir / f'page_video_hi_v{i}.mp4').exists():
                            has_older = True
                            status['page_videos']['missing'].append(f"{page_dir}/page_video_hi.mp4 (has v{i}, needs v{status['page_videos']['expected_version']})")
                            break
                    if not has_older:
                        status['page_videos']['missing'].append(f"{page_dir}/page_video_hi.mp4 (needs v{status['page_videos']['expected_version']})")
            
            status['page_videos']['complete'] = status['page_videos']['done'] == status['page_videos']['total']
            
            # Check final slideshow creation
            # Find max version across ALL previous stages
            status['slideshow_created']['total'] = 2  # EN + HI slideshow
            
            # Find max slideshow version
            for i in range(1, 20):
                if (extraction_dir / f'english_slideshow_v{i}.mp4').exists():
                    status['slideshow_created']['max_version'] = max(status['slideshow_created']['max_version'], i)
                if (extraction_dir / f'hindi_slideshow_v{i}.mp4').exists():
                    status['slideshow_created']['max_version'] = max(status['slideshow_created']['max_version'], i)
            
            # Expected version is max across slideshows AND all previous stages
            status['slideshow_created']['expected_version'] = max(
                status['slideshow_created']['max_version'],
                status['page_videos']['expected_version']
            )
            
            en_slideshow = extraction_dir / f'english_slideshow_v{status["slideshow_created"]["expected_version"]}.mp4'
            hi_slideshow = extraction_dir / f'hindi_slideshow_v{status["slideshow_created"]["expected_version"]}.mp4'
            
            # Check EN slideshow
            if en_slideshow.exists():
                status['slideshow_created']['done'] += 1
                status['slideshow_created']['present'].append(f"{en_slideshow} (v{status['slideshow_created']['expected_version']})")
            else:
                has_older = False
                for i in range(1, status['slideshow_created']['expected_version']):
                    old_slideshow = extraction_dir / f'english_slideshow_v{i}.mp4'
                    if old_slideshow.exists():
                        has_older = True
                        status['slideshow_created']['missing'].append(f"english_slideshow.mp4 (has v{i}, needs v{status['slideshow_created']['expected_version']})")
                        break
                if not has_older:
                    status['slideshow_created']['missing'].append(f"english_slideshow.mp4 (needs v{status['slideshow_created']['expected_version']})")
            
            # Check HI slideshow
            if hi_slideshow.exists():
                status['slideshow_created']['done'] += 1
                status['slideshow_created']['present'].append(f"{hi_slideshow} (v{status['slideshow_created']['expected_version']})")
            else:
                has_older = False
                for i in range(1, status['slideshow_created']['expected_version']):
                    old_slideshow = extraction_dir / f'hindi_slideshow_v{i}.mp4'
                    if old_slideshow.exists():
                        has_older = True
                        status['slideshow_created']['missing'].append(f"hindi_slideshow.mp4 (has v{i}, needs v{status['slideshow_created']['expected_version']})")
                        break
                if not has_older:
                    status['slideshow_created']['missing'].append(f"hindi_slideshow.mp4 (needs v{status['slideshow_created']['expected_version']})")
            
            status['slideshow_created']['complete'] = status['slideshow_created']['done'] == status['slideshow_created']['total']
    
    return status


def get_page_directories(pdf_stem: str) -> List[Path]:
    """Get sorted list of content unit directories (scenes) for a PDF.

    LEGACY FORMAT DISABLED: Only returns scene_ directories (updated format).
    Old page_ directories are ignored going forward.
    """
    extraction_dir = EXTRACTED_DIR / pdf_stem
    if not extraction_dir.exists():
        return []
    scene_dirs = [d for d in extraction_dir.iterdir() if d.is_dir() and d.name.startswith('scene_')]
    return sorted(scene_dirs)
    # LEGACY FORMAT DISABLED - page_ directories no longer supported
    # if scene_dirs:
    #     return sorted(scene_dirs)
    # page_dirs = [d for d in extraction_dir.iterdir() if d.is_dir() and d.name.startswith('page_')]
    # return sorted(page_dirs)


def get_extraction_dir(pdf_stem: str) -> Path:
    """Get the extraction directory path for a PDF."""
    return EXTRACTED_DIR / pdf_stem


def check_files_exist(*file_paths: Path) -> bool:
    """Check if all provided file paths exist."""
    return all(p.exists() for p in file_paths)


def get_overwrite_files(pdf_stem: str, stage: str) -> List[Path]:
    """
    Get list of files that will be overwritten for a given stage.
    
    Args:
        pdf_stem: PDF filename without extension
        stage: One of 'extract', 'plan', 'rewrite', 'audio', 'slideshow'
        
    Returns:
        List of file paths that will be overwritten
    """
    extraction_dir = EXTRACTED_DIR / pdf_stem
    files = []
    
    if stage == 'extract':
        if extraction_dir.exists():
            files.append(extraction_dir)
            
    elif stage == 'plan':
        story_file = extraction_dir / 'whole_story_cleaned.txt'
        if story_file.exists():
            files.append(story_file)
        # Also include clean_text.txt files
        for page_dir in get_page_directories(pdf_stem):
            clean_file = page_dir / 'clean_text.txt'
            if clean_file.exists():
                files.append(clean_file)
                
    elif stage == 'rewrite':
        for page_dir in get_page_directories(pdf_stem):
            en_file = page_dir / 'final_text_en.txt'
            hi_file = page_dir / 'final_text_hi.txt'
            if en_file.exists():
                files.append(en_file)
            if hi_file.exists():
                files.append(hi_file)
                
    elif stage == 'audio':
        for page_dir in get_page_directories(pdf_stem):
            en_audio = page_dir / 'final_text_en.mp3'
            hi_audio = page_dir / 'final_text_hi.mp3'
            if en_audio.exists():
                files.append(en_audio)
            if hi_audio.exists():
                files.append(hi_audio)
                
    elif stage == 'slideshow':
        en_slideshow = extraction_dir / 'english_slideshow.mp4'
        hi_slideshow = extraction_dir / 'hindi_slideshow.mp4'
        if en_slideshow.exists():
            files.append(en_slideshow)
        if hi_slideshow.exists():
            files.append(hi_slideshow)
    
    return files
