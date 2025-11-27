# Fast Forward Versioning System

## Overview

The **Fast Forward** feature allows you to quickly copy an existing version to all intermediate versions up to the latest expected version, without regenerating content. This is useful when content doesn't need updating but must match the version number for consistency.

## Use Case

**Scenario:** You updated page_0002 text to v3, but page_0001 text is still at v1 and doesn't need changes.

**Problem:** System shows `⚠️ Needs v3` for page_0001

**Solution:** Click **⏩ Fast Forward to v3** to copy v1 → v2 → v3 instantly

## How It Works

### What Fast Forward Does

1. **Copies** the current latest version
2. **Creates** all intermediate versions up to target
3. **Updates** metadata to track new versions
4. **Marks** as "fast-forward" in version history

### What It Doesn't Do

- ❌ Regenerate content
- ❌ Call APIs
- ❌ Modify existing versions
- ❌ Delete anything

## UI Display

### When Asset is Behind

**Text Example:**
```
📝 Kid-Friendly EN (v1) ⚠️ Needs v3
[Text content displayed]
⏩ Fast Forward to v3 [Button]
```

**Audio Example:**
```
🎵 EN Audio (v1) ⚠️ Needs v3
[Audio player]
⏩ Fast Forward Audio to v3 [Button]
```

### When Asset is Current

```
📝 Kid-Friendly EN (v3) 🟢 Latest
[Text content displayed]
[No fast forward button]
```

## Button Locations

### Text Fast Forward
- **Location:** Under each text area in "📑 View Extracted Pages"
- **Appears:** When text version < expected version
- **Button:** `⏩ Fast Forward to v{N}`

### Audio Fast Forward
- **Location:** Under audio players in "📑 View Extracted Pages"
- **Appears:** When audio version < expected version
- **Button:** `⏩ Fast Forward Audio to v{N}`

## Example Workflow

### Initial State
```
Page 0001:
  - Text: v1
  - Audio: v1

Page 0002:
  - Text: v3 (just updated)
  - Audio: v3 (just generated)

Expected Version: v3
```

### Status Display
```
Page 0001:
  📝 Kid-Friendly EN (v1) ⚠️ Needs v3
  ⏩ Fast Forward to v3

  🎵 EN Audio (v1) ⚠️ Needs v3
  ⏩ Fast Forward Audio to v3
```

### After Fast Forward Text
```
Action: Click "⏩ Fast Forward to v3" on page_0001 text

Result:
  - Creates final_text_en_v2.txt (copy of v1)
  - Creates final_text_en_v3.txt (copy of v1)
  - Updates versions.json
  - Text now at v3

Display:
  📝 Kid-Friendly EN (v3) 🟢 Latest
  [No fast forward button]
```

### After Fast Forward Audio
```
Action: Click "⏩ Fast Forward Audio to v3" on page_0001

Result:
  - Creates final_text_en_v2.mp3 (copy of v1)
  - Creates final_text_en_v3.mp3 (copy of v1)
  - Updates versions.json
  - Audio now at v3

Display:
  🎵 EN Audio (v3) 🟢 Latest
  [No fast forward button]
```

### Final State
```
Page 0001:
  - Text: v3 (fast-forwarded from v1)
  - Audio: v3 (fast-forwarded from v1)

Page 0002:
  - Text: v3 (regenerated)
  - Audio: v3 (regenerated)

Status: ✅ All at v3
```

## Version History

Fast-forwarded versions are marked in metadata:

```json
{
  "en_text": {
    "latest": "final_text_en_v3.txt",
    "versions": [
      {
        "file": "final_text_en_v1.txt",
        "created": "2024-10-24T20:00:00",
        "model": "gemini-2.5-flash"
      },
      {
        "file": "final_text_en_v2.txt",
        "created": "2024-10-24T21:50:00",
        "model": "fast-forward"
      },
      {
        "file": "final_text_en_v3.txt",
        "created": "2024-10-24T21:50:00",
        "model": "fast-forward"
      }
    ]
  }
}
```

**Note:** Model is marked as `"fast-forward"` to indicate it was copied, not regenerated.

## Supported Asset Types

### Currently Supported
- ✅ **en_text** - English kid-friendly text
- ✅ **hi_text** - Hindi kid-friendly text
- ✅ **en_audio** - English audio MP3
- ✅ **hi_audio** - Hindi audio MP3

### Not Yet Supported
- ⏳ **Page videos** - Coming soon
- ⏳ **Final slideshows** - Coming soon

## Benefits

### 1. Time Saving
- **No API calls** - Instant copying
- **No waiting** - Completes in milliseconds
- **Bulk compatible** - Can fast forward multiple pages

### 2. Cost Saving
- **No Gemini calls** - Saves text generation costs
- **No ElevenLabs calls** - Saves audio generation costs
- **No compute** - Just file copying

### 3. Version Consistency
- **Matches expected version** - Satisfies version requirements
- **Clears warnings** - Removes ⚠️ indicators
- **Updates sidebar** - Shows correct completion status

### 4. Flexibility
- **Selective updates** - Only regenerate what needs changing
- **Preserve quality** - Keep good versions as-is
- **Easy rollback** - Can restore any version later

## When to Use Fast Forward

### ✅ Good Use Cases

**1. Content Doesn't Need Changes**
```
Situation: Page 0001 text is perfect at v1
Action: Fast forward to v3 instead of regenerating
Benefit: Saves time and API costs
```

**2. Bulk Version Alignment**
```
Situation: 20 pages at v1, only 1 page needs v2 changes
Action: Update 1 page to v2, fast forward other 20
Benefit: Quick version consistency
```

**3. Audio Matches Old Text**
```
Situation: Text updated to v2, but v1 audio is still good
Action: Fast forward audio from v1 to v2
Benefit: Reuse existing audio
```

### ❌ When NOT to Use

**1. Content Actually Needs Updates**
```
Wrong: Fast forward outdated content
Right: Regenerate with new prompt/model
```

**2. Quality Issues**
```
Wrong: Fast forward poor quality version
Right: Regenerate to improve quality
```

**3. Different Source Required**
```
Wrong: Fast forward when text changed
Right: Regenerate audio from new text
```

## Technical Details

### Function Signature

```python
def fast_forward_version(
    page_dir: Path, 
    content_type: str, 
    target_version: int, 
    model: str = 'fast-forward'
) -> bool:
    """
    Fast forward an existing version to target version by copying it.
    
    Args:
        page_dir: Page directory
        content_type: Type (en_text, hi_text, en_audio, hi_audio)
        target_version: Version number to reach
        model: Model name to record (default: 'fast-forward')
    
    Returns:
        True if successful, False otherwise
    """
```

### Implementation

```python
# Get current version
current_version = get_latest_version_number(page_dir, content_type)

# Get latest file
latest_path = get_latest_version_path(page_dir, content_type)

# Copy to each intermediate version
for version in range(current_version + 1, target_version + 1):
    new_filename = f"{base_name}_v{version}{extension}"
    new_path = page_dir / new_filename
    
    # Copy content (text or binary)
    if extension == '.txt':
        content = latest_path.read_text(encoding='utf-8')
        new_path.write_text(content, encoding='utf-8')
    else:  # .mp3
        content = latest_path.read_bytes()
        new_path.write_bytes(content)
    
    # Update metadata
    version_info = {
        'file': new_filename,
        'created': datetime.now().isoformat(),
        'model': 'fast-forward'
    }
    metadata[content_type]['versions'].append(version_info)
    metadata[content_type]['latest'] = new_filename
```

### File Operations

**Text Files:**
- Read as UTF-8 text
- Write as UTF-8 text
- Preserves formatting

**Audio Files:**
- Read as binary bytes
- Write as binary bytes
- Exact copy (no re-encoding)

## Logging

All fast forward operations are logged:

```
21:50:15 | INFO | USER ACTION: FAST_FORWARD_EN_TEXT | PDF: download | Details: {'page': 'page_0001', 'from': 1, 'to': 3}
21:50:15 | INFO | USER ACTION: FAST_FORWARD_EN_AUDIO | PDF: download | Details: {'page': 'page_0001', 'from': 1, 'to': 3}
```

## Error Handling

### Validation Checks

**1. No Existing Version**
```python
if current_version == 0:
    return False  # Nothing to copy from
```

**2. Already at Target**
```python
if current_version >= target_version:
    return False  # Already there or ahead
```

**3. File Not Found**
```python
if not latest_path or not latest_path.exists():
    return False  # Source file missing
```

### Error Messages

**Success:**
```
✅ Fast forwarded EN text to v3
```

**Failure:**
```
❌ Fast forward failed
```

## Comparison: Fast Forward vs Regenerate

| Aspect | Fast Forward | Regenerate |
|--------|-------------|------------|
| **Speed** | Instant (<1s) | Slow (5-30s) |
| **Cost** | Free | API costs |
| **Quality** | Same as source | Potentially better |
| **Content** | Exact copy | New generation |
| **Use Case** | No changes needed | Content needs update |
| **API Calls** | 0 | 1-2 per asset |

## Future Enhancements

### Planned Features

**1. Bulk Fast Forward**
```
Button: "⏩ Fast Forward All Pages to v3"
Action: Fast forward all pages at once
Benefit: One-click version alignment
```

**2. Video Fast Forward**
```
Support: page_video_en_vN.mp4
Action: Copy video files
Benefit: Complete pipeline support
```

**3. Selective Fast Forward**
```
UI: Checkboxes for each page
Action: Fast forward selected pages only
Benefit: Fine-grained control
```

**4. Smart Fast Forward**
```
Logic: Auto-detect which assets can be fast-forwarded
Action: Suggest fast forward vs regenerate
Benefit: Intelligent recommendations
```

## Best Practices

### 1. Review Before Fast Forward
- Check if content actually needs updating
- Verify source version quality
- Consider if regeneration would be better

### 2. Use for Unchanged Content
- Text that doesn't need rewriting
- Audio that matches old text
- Assets that are already good quality

### 3. Combine with Regeneration
- Regenerate pages that need updates
- Fast forward pages that don't
- Efficient hybrid approach

### 4. Check Version History
- View all versions before fast forwarding
- Ensure source version is correct
- Can restore if needed

## Summary

Fast Forward is a **time and cost-saving feature** that copies existing versions to match the expected version number, without regenerating content. Use it when:

- ✅ Content doesn't need changes
- ✅ Want to maintain version consistency
- ✅ Need quick alignment across pages
- ✅ Want to save API costs

The feature provides instant version updates while preserving all version history and allowing easy rollback if needed.
