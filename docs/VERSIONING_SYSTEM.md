# Content Versioning System

## Overview

The pipeline now includes a **complete versioning system** for all rewritten content. **Nothing is ever overwritten** - each rewrite creates a new version, preserving all previous versions for comparison and rollback.

## Key Features

- Never Lose Work: All previous versions are preserved
- Version History: See all versions with timestamps and model info
- Easy Rollback: Restore any previous version as latest
- Latest Flag: Clear indicator of which version is current
- Automatic Migration: Existing files are automatically converted to v1

## How It Works

### File Structure

Before (Old System):
```
page_0001/
  final_text_en.txt        (Overwritten each time)
  final_text_hi.txt        (Lost previous versions)
  final_text_en.mp3
```

After (Versioned System):
```
page_0001/
  final_text_en_v1.txt     (First version preserved)
  final_text_en_v2.txt     (Second version preserved)
  final_text_en_v3.txt     (Latest version)
  final_text_hi_v1.txt
  final_text_hi_v2.txt
  final_text_hi_v3.txt     (Latest version)
  final_text_en.mp3
  final_text_hi.mp3
  versions.json            (Metadata tracking)
```

### Metadata File

Each page directory contains a versions.json file tracking all versions with timestamps, model used, and which is latest.

## User Interface

### Text Display
Shows: Kid-Friendly EN (v3) with Latest badge

### Version History
Expandable section showing all versions with:
- Version number
- Creation timestamp
- Model used
- Preview of content
- Restore button for older versions

### Rewrite Buttons
- First time: Create Rewrite (v1)
- Subsequent: Create New Version (v4, v5, etc.)
- No more overwrite confirmations needed

## Workflow Changes

### Individual Page Rewrite
1. Click button (shows next version number)
2. New version created immediately
3. Previous versions preserved
4. Success message shows version created

### Bulk Rewrite All Pages
1. Click button (no confirmation needed)
2. Creates new version for each page
3. All previous versions preserved
4. Shows total versions created

## Restoring Previous Versions

To restore an older version as latest:
1. Expand version history
2. Click Restore button on desired version
3. That version becomes latest
4. Original file remains (not deleted)
5. Status updates immediately

## Migration

### Automatic
When you first load a page, any existing non-versioned files are automatically migrated to v1.

### Manual
Run migrate_legacy_files(page_dir) to convert old files.

## API Reference

### Core Functions

**create_new_version(page_dir, content_type, content, model)**
- Creates new version without overwriting
- Returns: Path to new version file

**get_latest_version_path(page_dir, content_type)**
- Returns: Path to latest version or None

**get_all_versions(page_dir, content_type)**
- Returns: List of all version metadata

**get_version_count(page_dir, content_type)**
- Returns: Total number of versions

**set_as_latest(page_dir, content_type, version_number)**
- Sets specific version as latest
- Returns: True if successful

**migrate_legacy_files(page_dir)**
- Converts old files to versioned system
- Called automatically

### Content Types

- en_text: English kid-friendly text
- hi_text: Hindi kid-friendly text  
- en_audio: English audio MP3
- hi_audio: Hindi audio MP3

## Benefits

### For Users
- Never lose work by accident
- Compare different rewrites easily
- Experiment without fear
- Rollback to any previous version

### For Development
- Complete audit trail
- A/B testing different prompts
- Track model performance
- Debug issues with specific versions

## Examples

### Example 1: First Rewrite
```
Before: No versions exist
Action: Click Create Rewrite (v1)
Result: Creates final_text_en_v1.txt and final_text_hi_v1.txt
```

### Example 2: Second Rewrite
```
Before: v1 exists
Action: Click Create New Version (v2)
Result: Creates v2, v1 still exists, v2 marked as latest
```

### Example 3: Restore Old Version
```
Before: v1, v2, v3 exist, v3 is latest
Action: Click Restore v1
Result: v1 marked as latest, v2 and v3 still exist
```

### Example 4: Bulk Rewrite
```
Before: 11 pages, some with v1, some with v2
Action: Click Create New Versions for All Pages
Result: Each page gets new version (v2, v3, etc.)
```

## Storage Considerations

### Disk Space
Each version stores the full text/audio file. With many versions, storage grows.

Typical sizes:
- Text: ~500 bytes per version
- Audio: ~50-200 KB per version

For 11 pages with 5 versions each:
- Text: ~27.5 KB total
- Audio: ~5.5 MB total

### Cleanup
Future enhancement: Add button to delete old versions (except latest).

## Logging

All version operations are logged:
```
01:45:23 | INFO | FILE OP: rewrite_page_0001_v3 | SUCCESS
01:45:24 | INFO | API CALL: Gemini | gemini-2.5-flash | 245 chars | SUCCESS
```

## Status Tracking

The sidebar workflow status now checks for latest versions:
- Uses get_latest_version_path() instead of hardcoded filenames
- Shows accurate completion based on any version existing
- Missing files message updated to indicate version-aware checking

## Future Enhancements

Potential additions:
- Version diff viewer (compare v1 vs v2)
- Bulk restore (restore all pages to v1)
- Export version history as report
- Version notes/comments
- Delete old versions UI
- Automatic cleanup of versions older than N days
- Version branching (experimental versions)

## Migration Notes

### Backward Compatibility
Old code checking for final_text_en.txt will need updates to use get_latest_version_path().

### Breaking Changes
Direct file access like page_dir / final_text_en.txt no longer guaranteed to exist.

### Updated Code Locations
- components/content_viewer.py: Individual page rewrite
- components/pipeline_stages.py: Bulk rewrite stage
- utils/workflow.py: Status checking
- utils/versioning.py: Core versioning logic

## Troubleshooting

### Versions not showing
- Check that versions.json exists in page directory
- Run migrate_legacy_files() manually
- Check file permissions

### Restore not working
- Cannot restore if only one version exists
- Cannot restore the current latest
- Check versions.json is valid JSON

### Missing latest version
- Check versions.json latest field
- Verify file actually exists
- Check for file system issues

## Technical Details

### Version Numbering
- Sequential: v1, v2, v3, ...
- Never reused (even after delete)
- Gaps preserved if versions deleted

### Metadata Format
JSON with ISO 8601 timestamps, model names, filenames.

### File Naming Convention
{base_name}_v{number}.{extension}

Examples:
- final_text_en_v1.txt
- final_text_hi_v2.txt
- final_text_en_v3.mp3

### Concurrency
No locks implemented. Avoid simultaneous rewrites of same page.

## Summary

The versioning system provides complete protection against accidental overwrites while maintaining full history and easy rollback. All previous versions are preserved, viewable, and restorable through a simple UI.
