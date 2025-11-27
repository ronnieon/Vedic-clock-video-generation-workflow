"""
Content Versioning System
=========================
Track and manage versions of rewritten content.
Never overwrite - always create new versions.
"""

from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import json
import shutil
import re
import os


def get_version_metadata_file(page_dir: Path) -> Path:
    """Get the path to the version metadata file for a page."""
    return page_dir / 'versions.json'


def load_version_metadata(page_dir: Path) -> Dict:
    """
    Load version metadata for a page.
    
    Returns:
        {
            'en_text': {
                'latest': 'final_text_en_v3.txt',
                'versions': [
                    {'file': 'final_text_en_v1.txt', 'created': '2024-10-24T01:30:00', 'model': 'gemini-2.5-flash'},
                    {'file': 'final_text_en_v2.txt', 'created': '2024-10-24T01:35:00', 'model': 'gemini-2.5-flash'},
                    {'file': 'final_text_en_v3.txt', 'created': '2024-10-24T01:44:00', 'model': 'gemini-2.5-flash'}
                ]
            },
            'hi_text': {...},
            'en_audio': {...},
        }
    """
    metadata_file = get_version_metadata_file(page_dir)
    
    if not metadata_file.exists():
        metadata = {
            'en_text': {'latest': '', 'versions': []},
            'hi_text': {'latest': '', 'versions': []},
            'en_audio': {'latest': '', 'versions': []},
            'hi_audio': {'latest': '', 'versions': []},
            'image': {'latest': '', 'versions': []},
            'image_video': {'latest': '', 'versions': []},
            'en_video': {'latest': '', 'versions': []},
            'hi_video': {'latest': '', 'versions': []}
        }
        return metadata
    
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # Ensure all content types exist (for backward compatibility)
    required_types = ['en_text', 'hi_text', 'en_audio', 'hi_audio', 'image', 'image_video', 'en_video', 'hi_video']
    for content_type in required_types:
        if content_type not in metadata:
            metadata[content_type] = {'latest': '', 'versions': []}
    
    return metadata
def save_version_metadata(page_dir: Path, metadata: Dict):
    """Save version metadata for a page."""
    metadata_file = get_version_metadata_file(page_dir)
    tmp_file = metadata_file.with_suffix('.json.tmp')
    # Write atomically: write to temp then replace
    with open(tmp_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    tmp_file.replace(metadata_file)


def create_new_version(
    page_dir: Path,
    content_type: str,  # 'en_text', 'hi_text', 'en_audio', 'hi_audio', 'image', 'image_video'
    content: str,
    model: Optional[str] = None
) -> Path:
    """
    Create a new version of content without overwriting.
    
    Args:
        page_dir: Path to page directory
        content_type: Type of content (en_text, hi_text, en_audio, hi_audio, image, image_video)
        content: Content to write (for text) or source path (for audio/image/video)
        model: Model used to generate content
        
    Returns:
        Path to the newly created version file
    """
    metadata = load_version_metadata(page_dir)
    
    # Determine file extension and base name
    if content_type == 'en_text':
        base_name = 'final_text_en'
        extension = '.txt'
        is_binary = False
    elif content_type == 'hi_text':
        base_name = 'final_text_hi'
        extension = '.txt'
        is_binary = False
    elif content_type == 'en_audio':
        base_name = 'final_text_en'
        extension = '.mp3'
        is_binary = True
    elif content_type == 'hi_audio':
        base_name = 'final_text_hi'
        extension = '.mp3'
        is_binary = True
    elif content_type == 'image':
        base_name = 'image_to_use'
        extension = '.png'
        is_binary = True
    elif content_type == 'image_video':
        base_name = 'page_image_video'
        extension = '.mp4'
        is_binary = True
    else:
        raise ValueError(f"Unknown content_type: {content_type}")
    
    # Get next version number
    versions = metadata[content_type]['versions']
    next_version = len(versions) + 1
    
    # Create new version filename
    new_filename = f"{base_name}_v{next_version}{extension}"
    new_filepath = page_dir / new_filename
    
    # Save content
    if is_binary:
        # For binary files (audio, image), content is the source path to copy from
        if isinstance(content, (str, Path)):
            shutil.copy2(content, new_filepath)
    else:
        # For text, write directly
        new_filepath.write_text(content, encoding='utf-8')
    
    # Update metadata
    version_info = {
        'file': new_filename,
        'created': datetime.now().isoformat(),
        'model': model
    }
    
    metadata[content_type]['versions'].append(version_info)
    metadata[content_type]['latest'] = new_filename
    
    save_version_metadata(page_dir, metadata)
    
    return new_filepath


def get_latest_version_path(page_dir: Path, content_type: str) -> Optional[Path]:
    """Get the path to the latest version of content."""
    metadata = load_version_metadata(page_dir)
    latest_file = metadata.get(content_type, {}).get('latest')
    
    if not latest_file:
        return None
    
    return page_dir / latest_file


def get_all_versions(page_dir: Path, content_type: str) -> List[Dict]:
    """Get list of all versions for a content type."""
    metadata = load_version_metadata(page_dir)
    return metadata.get(content_type, {}).get('versions', [])


def get_version_path(page_dir: Path, content_type: str, version_number: int) -> Optional[Path]:
    """Get path to a specific version."""
    versions = get_all_versions(page_dir, content_type)
    
    if version_number < 1 or version_number > len(versions):
        return None
    
    version_info = versions[version_number - 1]
    return page_dir / version_info['file']


def set_as_latest(page_dir: Path, content_type: str, version_number: int) -> bool:
    """
    Set a specific version as the latest (restore old version).
    
    Returns:
        True if successful, False otherwise
    """
    metadata = load_version_metadata(page_dir)
    
    if content_type not in metadata:
        return False
    
    versions = metadata[content_type]['versions']
    
    if version_number < 1 or version_number > len(versions):
        return False
    
    version_info = versions[version_number - 1]
    metadata[content_type]['latest'] = version_info['file']
    
    save_version_metadata(page_dir, metadata)
    return True


def migrate_legacy_files(page_dir: Path):
    """
    Migrate existing non-versioned files to versioned system.
    Called once to convert old files to v1.
    """
    metadata = load_version_metadata(page_dir)
    
    # Check for legacy files and convert them to v1
    legacy_files = {
        'en_text': 'final_text_en.txt',
        'hi_text': 'final_text_hi.txt',
        'en_audio': 'final_text_en.mp3',
        'hi_audio': 'final_text_hi.mp3',
        'image': 'image_to_use.png'
    }
    
    for content_type, legacy_filename in legacy_files.items():
        legacy_path = page_dir / legacy_filename
        
        # Only migrate if legacy file exists and no versions exist yet
        if legacy_path.exists() and len(metadata[content_type]['versions']) == 0:
            extension = legacy_path.suffix
            base_name = legacy_path.stem
            
            # Rename to v1
            v1_filename = f"{base_name}_v1{extension}"
            v1_path = page_dir / v1_filename
            
            # Move legacy file to v1
            legacy_path.rename(v1_path)
            
            # Update metadata
            version_info = {
                'file': v1_filename,
                'created': datetime.fromtimestamp(v1_path.stat().st_mtime).isoformat(),
                'model': 'unknown (migrated)'
            }
            
            metadata[content_type]['versions'].append(version_info)
            metadata[content_type]['latest'] = v1_filename
    
    save_version_metadata(page_dir, metadata)


def get_version_count(page_dir: Path, content_type: str) -> int:
    """Get the total number of versions for a content type."""
    return len(get_all_versions(page_dir, content_type))


def get_latest_version_number(page_dir: Path, content_type: str) -> int:
    """
    Get the version number of the latest version.
    
    Returns:
        Version number (1, 2, 3, etc.) or 0 if no versions exist
    """
    # For videos, scan files directly (not in metadata yet)
    if content_type in ['en_video', 'hi_video']:
        import re
        pattern = 'page_video_en_v*.mp4' if content_type == 'en_video' else 'page_video_hi_v*.mp4'
        videos = list(page_dir.glob(pattern))
        max_version = 0
        for vid in videos:
            match = re.search(r'_v(\d+)\.mp4$', vid.name)
            if match:
                max_version = max(max_version, int(match.group(1)))
        return max_version
    
    return get_version_count(page_dir, content_type)


def fast_forward_version(page_dir: Path, content_type: str, target_version: int, model: str = 'fast-forward') -> bool:
    """
    Fast forward an existing version to target version by copying it.
    Creates intermediate versions if needed.
    
    Args:
        page_dir: Page directory
        content_type: Type of content (en_text, hi_text, en_audio, hi_audio)
        target_version: Version number to fast forward to
        model: Model name to record (default: 'fast-forward')
    
    Returns:
        True if successful, False otherwise
    """
    current_version = get_latest_version_number(page_dir, content_type)
    
    if current_version == 0:
        return False  # No version to copy from
    
    if current_version >= target_version:
        return False  # Already at or past target
    
    # Get the latest version file
    if content_type in ['en_video', 'hi_video']:
        # For videos, find the latest manually
        pattern = 'page_video_en' if content_type == 'en_video' else 'page_video_hi'
        latest_path = page_dir / f'{pattern}_v{current_version}.mp4'
        if not latest_path.exists():
            return False
    else:
        latest_path = get_latest_version_path(page_dir, content_type)
        if not latest_path or not latest_path.exists():
            return False
    
    # Determine file extension and base name
    if content_type in ['en_text', 'hi_text']:
        base_name = 'final_text_en' if content_type == 'en_text' else 'final_text_hi'
        extension = '.txt'
    elif content_type in ['en_audio', 'hi_audio']:
        base_name = 'final_text_en' if content_type == 'en_audio' else 'final_text_hi'
        extension = '.mp3'
    elif content_type in ['en_video', 'hi_video']:
        base_name = 'page_video_en' if content_type == 'en_video' else 'page_video_hi'
        extension = '.mp4'
    elif content_type == 'image':
        base_name = 'image_to_use'
        extension = '.png'
    elif content_type == 'image_video':
        base_name = 'page_image_video'
        extension = '.mp4'
    else:
        return False
    
    # Copy to all intermediate versions up to target
    metadata = load_version_metadata(page_dir)
    
    # Initialize content type in metadata if it doesn't exist (robust check)
    if content_type not in metadata or not isinstance(metadata.get(content_type), dict):
        metadata[content_type] = {
            'versions': [],
            'latest': None
        }
    
    # Ensure 'versions' key exists
    if 'versions' not in metadata[content_type]:
        metadata[content_type]['versions'] = []
    
    for version in range(current_version + 1, target_version + 1):
        new_filename = f"{base_name}_v{version}{extension}"
        new_path = page_dir / new_filename
        
        # Copy the file content
        if extension == '.txt':
            content = latest_path.read_text(encoding='utf-8')
            new_path.write_text(content, encoding='utf-8')
        else:  # Binary file (mp3, mp4)
            content = latest_path.read_bytes()
            new_path.write_bytes(content)
        
        # Add to metadata
        version_info = {
            'file': new_filename,
            'created': datetime.now().isoformat(),
            'model': model
        }
        metadata[content_type]['versions'].append(version_info)
        metadata[content_type]['latest'] = new_filename
    
    save_version_metadata(page_dir, metadata)
    return True


def delete_version(page_dir: Path, content_type: str, version_number: int) -> bool:
    """
    Delete a specific version (except if it's the only one or the latest).
    
    Returns:
        True if successful, False otherwise
    """
    metadata = load_version_metadata(page_dir)
    
    if content_type not in metadata:
        return False
    
    versions = metadata[content_type]['versions']
    
    # Don't allow deleting if it's the only version
    if len(versions) <= 1:
        return False
    
    if version_number < 1 or version_number > len(versions):
        return False
    
    version_info = versions[version_number - 1]
    
    # Don't allow deleting the latest version
    if version_info['file'] == metadata[content_type]['latest']:
        return False
    
    # Delete the file
    file_path = page_dir / version_info['file']
    if file_path.exists():
        file_path.unlink()
    
    # Remove from metadata
    versions.pop(version_number - 1)
    
    # Renumber remaining versions (optional, for cleaner numbering)
    # This is commented out to preserve version numbers as historical record
    # for i, ver in enumerate(versions, 1):
    #     old_path = page_dir / ver['file']
    #     new_name = f"{base_name}_v{i}{extension}"
    #     new_path = page_dir / new_name
    #     if old_path != new_path:
    #         old_path.rename(new_path)
    #         ver['file'] = new_name
    
    save_version_metadata(page_dir, metadata)
    return True


def discover_and_register_versions(page_dir: Path) -> Dict[str, int]:
    """
    Discover versions that exist on disk but aren't registered in versions.json.
    This handles externally-created versions (e.g., from background processor).
    
    Returns:
        Dictionary mapping content_type to number of newly discovered versions
    """
    if not page_dir.exists() or not page_dir.is_dir():
        return {}
    
    metadata = load_version_metadata(page_dir)
    discovered = {}
    
    # Define content type patterns
    patterns = {
        'en_text': (r'^final_text_en_v(\d+)\.txt$', 'final_text_en', '.txt'),
        'hi_text': (r'^final_text_hi_v(\d+)\.txt$', 'final_text_hi', '.txt'),
        'en_audio': (r'^final_text_en_v(\d+)\.mp3$', 'final_text_en', '.mp3'),
        'hi_audio': (r'^final_text_hi_v(\d+)\.mp3$', 'final_text_hi', '.mp3'),
        'image': (r'^image_to_use_v(\d+)\.png$', 'image_to_use', '.png'),
        'image_video': (r'^page_image_video_v(\d+)\.mp4$', 'page_image_video', '.mp4'),
        'en_video': (r'^page_video_en_v(\d+)\.mp4$', 'page_video_en', '.mp4'),
        'hi_video': (r'^page_video_hi_v(\d+)\.mp4$', 'page_video_hi', '.mp4'),
    }
    
    for content_type, (pattern, base_name, extension) in patterns.items():
        # Get currently tracked versions
        tracked_files = {v['file'] for v in metadata[content_type]['versions']}
        
        # Find all matching files on disk
        found_versions = []
        for file_path in page_dir.iterdir():
            if file_path.is_file():
                match = re.match(pattern, file_path.name)
                if match:
                    version_num = int(match.group(1))
                    if file_path.name not in tracked_files:
                        # This version exists but isn't tracked
                        file_stat = file_path.stat()
                        found_versions.append({
                            'file': file_path.name,
                            'version_num': version_num,
                            'created': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                            'model': 'external'  # Mark as externally created
                        })
        
        if found_versions:
            # Sort by version number
            found_versions.sort(key=lambda x: x['version_num'])
            
            # Add to metadata
            for ver in found_versions:
                # Check if this version number already exists (shouldn't happen but be safe)
                if not any(v['file'] == ver['file'] for v in metadata[content_type]['versions']):
                    version_info = {
                        'file': ver['file'],
                        'created': ver['created'],
                        'model': ver['model']
                    }
                    metadata[content_type]['versions'].append(version_info)
            
            # Sort versions by version number
            def extract_version_num(v):
                match = re.search(r'_v(\d+)', v['file'])
                return int(match.group(1)) if match else 0
            
            metadata[content_type]['versions'].sort(key=extract_version_num)
            
            # Update latest to highest version
            if metadata[content_type]['versions']:
                metadata[content_type]['latest'] = metadata[content_type]['versions'][-1]['file']
            
            discovered[content_type] = len(found_versions)
    
    # Save updated metadata if anything was discovered
    if discovered:
        save_version_metadata(page_dir, metadata)
    
    return discovered


def discover_all_versions(extracted_dir: Path = Path("extracted")) -> int:
    """
    Discover and register versions across all PDFs and pages.
    
    Returns:
        Total number of newly discovered versions
    """
    if not extracted_dir.exists():
        return 0
    
    total_discovered = 0
    
    for pdf_dir in extracted_dir.iterdir():
        if pdf_dir.is_dir():
            for page_dir in pdf_dir.iterdir():
                if page_dir.is_dir() and page_dir.name.startswith('page_'):
                    discovered = discover_and_register_versions(page_dir)
                    total_discovered += sum(discovered.values())
    
    return total_discovered


def cleanup_old_versions(page_dir: Path, content_type: str) -> int:
    """
    Remove all versions except the latest one for a specific content type.
    Also removes any files with unrecognized suffixes or variations.
    
    Args:
        page_dir: Path to page directory
        content_type: Type of content (en_text, hi_text, en_audio, hi_audio, image, image_video, en_video, hi_video)
    
    Returns:
        Number of versions deleted
    """
    metadata = load_version_metadata(page_dir)
    
    if content_type not in metadata:
        return 0
    
    versions = metadata[content_type]['versions']
    latest_file = metadata[content_type]['latest']
    deleted_count = 0
    
    # Determine base pattern and extension for this content type
    patterns = {
        'en_text': (r'^final_text_en', '.txt'),
        'hi_text': (r'^final_text_hi', '.txt'),
        'en_audio': (r'^final_text_en', '.mp3'),
        'hi_audio': (r'^final_text_hi', '.mp3'),
        'image': (r'^image_to_use', '.png'),
        'image_video': (r'^page_image_video', '.mp4'),
        'en_video': (r'^page_video_en', '.mp4'),
        'hi_video': (r'^page_video_hi', '.mp4'),
    }
    
    if content_type not in patterns:
        return 0
    
    base_pattern, expected_ext = patterns[content_type]
    
    # Build set of files to keep (only the latest)
    files_to_keep = {latest_file} if latest_file else set()
    
    # Get all files in the directory that match the base pattern
    all_matching_files = []
    for file_path in page_dir.iterdir():
        if file_path.is_file():
            # Check if file matches the base pattern
            if re.match(base_pattern, file_path.name):
                all_matching_files.append(file_path)
    
    # Delete all matching files except the latest
    for file_path in all_matching_files:
        if file_path.name not in files_to_keep:
            try:
                file_path.unlink()
                deleted_count += 1
            except Exception as e:
                # Log error but continue
                pass
    
    # Update metadata - keep only the latest version
    versions_to_keep = []
    for version_info in versions:
        if version_info['file'] == latest_file:
            versions_to_keep.append(version_info)
    
    metadata[content_type]['versions'] = versions_to_keep
    save_version_metadata(page_dir, metadata)
    
    return deleted_count


def cleanup_untracked_variations(page_dir: Path) -> int:
    """
    Remove untracked files with versioned patterns that aren't in the versioning system.
    Examples: image_to_video_prompt_for_v1.txt, etc.
    
    Args:
        page_dir: Path to page directory
    
    Returns:
        Number of files deleted
    """
    if not page_dir.exists() or not page_dir.is_dir():
        return 0
    
    deleted_count = 0
    metadata = load_version_metadata(page_dir)
    
    # Get all tracked files from metadata
    tracked_files = set()
    for content_type, info in metadata.items():
        if isinstance(info, dict) and 'versions' in info:
            for version_info in info['versions']:
                tracked_files.add(version_info['file'])
    
    # Also keep core extraction files
    core_files = {
        'page_text.txt',
        'whole_story_cleaned.txt',
        'versions.json',
        'image.png'  # original extracted image
    }
    
    # Pattern for versioned files that might not be in metadata
    versioned_patterns = [
        r'.*_v\d+\.(txt|mp3|mp4|png)$',  # Any file ending with _v{number}.{ext}
        r'image_to_video_prompt.*\.txt$',  # Image to video prompts
    ]
    
    for file_path in page_dir.iterdir():
        if not file_path.is_file():
            continue
        
        # Skip if it's a tracked file or core file
        if file_path.name in tracked_files or file_path.name in core_files:
            continue
        
        # Check if it matches any versioned pattern
        should_delete = False
        for pattern in versioned_patterns:
            if re.match(pattern, file_path.name):
                should_delete = True
                break
        
        if should_delete:
            try:
                file_path.unlink()
                deleted_count += 1
            except Exception as e:
                # Log error but continue
                pass
    
    return deleted_count


def cleanup_all_old_versions(pdf_stem: str, extracted_dir: Path = Path("extracted")) -> Dict[str, int]:
    """
    Remove all old versions (keeping only latest) for all artifacts in a PDF.
    Also removes untracked variations and files with versioned patterns.
    
    Args:
        pdf_stem: Name of the PDF (without extension)
        extracted_dir: Base extraction directory
    
    Returns:
        Dictionary mapping content_type to number of versions deleted
    """
    pdf_dir = extracted_dir / pdf_stem
    
    if not pdf_dir.exists():
        return {}
    
    total_deleted = {}
    content_types = ['en_text', 'hi_text', 'en_audio', 'hi_audio', 'image', 'image_video', 'en_video', 'hi_video']
    
    # Process all pages
    for page_dir in pdf_dir.iterdir():
        if page_dir.is_dir() and page_dir.name.startswith('page_'):
            # Clean up tracked old versions
            for content_type in content_types:
                deleted = cleanup_old_versions(page_dir, content_type)
                if deleted > 0:
                    total_deleted[content_type] = total_deleted.get(content_type, 0) + deleted
            
            # Clean up untracked variations
            untracked_deleted = cleanup_untracked_variations(page_dir)
            if untracked_deleted > 0:
                total_deleted['untracked_variations'] = total_deleted.get('untracked_variations', 0) + untracked_deleted
    
    return total_deleted
