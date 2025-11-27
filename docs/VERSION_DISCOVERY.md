# Version Discovery System

## Problem

When files are created externally (e.g., by a background processor running on another machine), they are synced to S3 and downloaded to your local `extracted/` directory, but they don't appear in the UI. This is because:

1. File exists on disk: ✅ `page_image_video_v7.mp4`
2. File in S3: ✅ Synced
3. Tracked in `versions.json`: ❌ **Missing**

Without being registered in `versions.json`, the versioning system doesn't know the file exists, so it doesn't show up in the dashboard.

## Solution

The **Version Discovery System** automatically scans for files that exist on disk but aren't registered in `versions.json`, then registers them so they appear in the UI.

## How It Works

### Automatic Discovery (Integrated with S3 Sync)

Every 60 seconds, after the S3 sync completes:

1. **Download Phase**: New files from S3 → local
2. **Upload Phase**: New local files → S3
3. **Discovery Phase**: 🔍 Scan for unregistered versions

```
S3 Sync Cycle:
├─ Step 1: Download new files from S3
├─ Step 2: Upload new files to S3
└─ Step 3: Discover and register untracked versions ← NEW!
```

### What Gets Discovered

The system looks for versioned files matching these patterns:

| Content Type | Pattern | Example |
|--------------|---------|---------|
| English Text | `final_text_en_v{N}.txt` | `final_text_en_v3.txt` |
| Hindi Text | `final_text_hi_v{N}.txt` | `final_text_hi_v2.txt` |
| English Audio | `final_text_en_v{N}.mp3` | `final_text_en_v4.mp3` |
| Hindi Audio | `final_text_hi_v{N}.mp3` | `final_text_hi_v3.mp3` |
| Image | `image_to_use_v{N}.png` | `image_to_use_v5.png` |
| Image Video | `page_image_video_v{N}.mp4` | `page_image_video_v7.mp4` |
| EN Page Video | `page_video_en_v{N}.mp4` | `page_video_en_v6.mp4` |
| HI Page Video | `page_video_hi_v{N}.mp4` | `page_video_hi_v4.mp4` |

### Discovery Process

For each page directory:

1. **Load** current `versions.json`
2. **Scan** all files in the directory
3. **Match** against version patterns
4. **Compare** with tracked versions
5. **Register** any untracked versions found
6. **Sort** versions by version number
7. **Update** latest version pointer
8. **Save** updated `versions.json`

### Example

**Before Discovery**:
```
Disk:
  page_image_video_v6.mp4 ✅
  page_image_video_v7.mp4 ✅ (created by background processor)

versions.json:
  "image_video": {
    "latest": "page_image_video_v6.mp4",
    "versions": [
      {"file": "page_image_video_v6.mp4", "created": "...", "model": "wan-video"}
    ]
  }
```

**After Discovery**:
```
versions.json:
  "image_video": {
    "latest": "page_image_video_v7.mp4",  ← Updated
    "versions": [
      {"file": "page_image_video_v6.mp4", "created": "...", "model": "wan-video"},
      {"file": "page_image_video_v7.mp4", "created": "...", "model": "external"}  ← Added
    ]
  }
```

Now v7 appears in the UI! 🎉

## Logs

When versions are discovered, you'll see:

```
S3 sync completed: ⬇️  1 downloaded, ⬆️  0 uploaded, ⏭️  1000 skipped
🔍 Discovered and registered 4 new version(s) from external sources
```

## Manual Discovery

You can also manually trigger version discovery:

```python
from pathlib import Path
from utils.versioning import discover_and_register_versions, discover_all_versions

# Discover for a single page
page_dir = Path("extracted/download/page_0001")
discovered = discover_and_register_versions(page_dir)
print(f"Discovered: {discovered}")

# Discover across all PDFs and pages
total = discover_all_versions()
print(f"Total discovered: {total}")
```

## Integration with Background Processor

Perfect workflow:

1. **Dashboard**: Queue prompts → uploaded to S3
2. **Background Processor**: 
   - Downloads prompts from S3
   - Processes them
   - Creates versioned files (e.g., `page_image_video_v7.mp4`)
   - Uploads to S3
3. **S3 Sync** (on dashboard):
   - Downloads new v7 file
   - **Discovers** it's not in `versions.json`
   - **Registers** it automatically
4. **Dashboard**: User sees v7 appear! ✅

## Metadata for External Versions

Externally-created versions are marked with:
```json
{
  "file": "page_image_video_v7.mp4",
  "created": "2025-11-04T02:00:00.123456",
  "model": "external"  ← Indicates external creation
}
```

The timestamp is taken from the file's modification time.

## Benefits

1. ✅ **Automatic**: No manual intervention needed
2. ✅ **Fast**: Runs after each sync (60 seconds)
3. ✅ **Safe**: Only adds missing versions, never overwrites
4. ✅ **Smart**: Sorts versions correctly by number
5. ✅ **Visible**: Clear logs show what was discovered
6. ✅ **Seamless**: Works with existing version system

## Edge Cases Handled

### Gap in Version Numbers
If you have v6 and v8 (no v7), both are registered:
```
versions: [v6, v8]  ← Sorted by version number
latest: v8          ← Highest version
```

### Duplicate Versions
If a version already exists in `versions.json`, it's skipped (no duplicates).

### Multiple Content Types
Discovery runs for all content types in one pass:
```
Discovered: {
  'image_video': 1,
  'en_video': 2,
  'hi_video': 1
}
```

### No versions.json
If `versions.json` doesn't exist, it's created automatically with discovered versions.

## Performance

- **Per page**: ~10-20ms to scan and register
- **Per PDF** (10 pages): ~100-200ms
- **All PDFs** (100 pages): ~1-2 seconds

Runs in the background sync thread, doesn't block the UI.

## Troubleshooting

### Versions Still Not Showing

1. **Check file name matches pattern**:
   ```bash
   # Correct: page_image_video_v7.mp4
   # Wrong:   page_image_video_7.mp4 (missing 'v')
   # Wrong:   image_video_v7.mp4 (wrong prefix)
   ```

2. **Check versions.json was updated**:
   ```bash
   cat extracted/download/page_0001/versions.json | grep "v7"
   ```

3. **Check logs**:
   ```bash
   tail -f logs/pipeline_*.log | grep "Discovered"
   ```

4. **Force re-scan**:
   ```python
   from utils.versioning import discover_and_register_versions
   from pathlib import Path
   
   discover_and_register_versions(Path("extracted/download/page_0001"))
   ```

### Refresh Dashboard

After versions are discovered, you may need to refresh the page or select the PDF again to see the new versions in the UI.

## Future Enhancements

Possible improvements:

1. **Real-time file watching**: Detect new files immediately instead of waiting for sync cycle
2. **Metadata inference**: Try to detect the model used from file metadata
3. **Conflict resolution**: Handle cases where version numbers conflict
4. **Batch notifications**: Show a toast when new versions are discovered
5. **Selective discovery**: Only scan pages that had downloads in this sync cycle
