"""
Cleanup Corrupted Images
=========================
Find and optionally remove corrupted or invalid image files.

Usage:
    python cleanup_corrupted_images.py --check     # Just check, don't delete
    python cleanup_corrupted_images.py --remove    # Remove corrupted files
"""

import argparse
from pathlib import Path
from PIL import Image


def check_image_file(image_path: Path) -> tuple[bool, str]:
    """
    Check if an image file is valid.
    
    Returns:
        (is_valid, error_message)
    """
    try:
        with Image.open(image_path) as img:
            img.verify()
        
        # Re-open to check if it can actually be loaded
        with Image.open(image_path) as img:
            img.load()
        
        return True, ""
    except Exception as e:
        return False, str(e)


def scan_directory(directory: Path, remove: bool = False) -> dict:
    """
    Scan directory for corrupted images.
    
    Args:
        directory: Directory to scan
        remove: If True, remove corrupted files
        
    Returns:
        Statistics dictionary
    """
    stats = {
        'total': 0,
        'valid': 0,
        'corrupted': 0,
        'removed': 0,
        'corrupted_files': []
    }
    
    # Find all image files
    image_patterns = ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.bmp', '*.webp']
    
    for pattern in image_patterns:
        for image_file in directory.rglob(pattern):
            stats['total'] += 1
            
            is_valid, error = check_image_file(image_file)
            
            if is_valid:
                stats['valid'] += 1
            else:
                stats['corrupted'] += 1
                stats['corrupted_files'].append((image_file, error))
                print(f"❌ CORRUPTED: {image_file}")
                print(f"   Error: {error}")
                
                if remove:
                    try:
                        image_file.unlink()
                        stats['removed'] += 1
                        print(f"   ✅ Removed")
                    except Exception as e:
                        print(f"   ⚠️  Failed to remove: {e}")
                print()
    
    return stats


def main():
    parser = argparse.ArgumentParser(description='Find and remove corrupted image files')
    parser.add_argument('--directory', type=str, default='extracted', help='Directory to scan (default: extracted)')
    parser.add_argument('--remove', action='store_true', help='Remove corrupted files')
    parser.add_argument('--check', action='store_true', help='Only check, don\'t remove (default)')
    
    args = parser.parse_args()
    
    directory = Path(args.directory)
    
    if not directory.exists():
        print(f"❌ Directory not found: {directory}")
        return
    
    print("=" * 60)
    print("Corrupted Image Scanner")
    print("=" * 60)
    print(f"Directory: {directory}")
    print(f"Mode: {'REMOVE' if args.remove else 'CHECK ONLY'}")
    print("=" * 60)
    print()
    
    stats = scan_directory(directory, remove=args.remove)
    
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total images scanned: {stats['total']}")
    print(f"Valid images: {stats['valid']}")
    print(f"Corrupted images: {stats['corrupted']}")
    
    if args.remove:
        print(f"Removed: {stats['removed']}")
    
    if stats['corrupted'] > 0:
        print()
        print("Corrupted files:")
        for file_path, error in stats['corrupted_files']:
            print(f"  - {file_path}")
        
        if not args.remove:
            print()
            print("💡 Run with --remove to delete these files")
    else:
        print()
        print("✅ No corrupted images found!")


if __name__ == "__main__":
    main()
