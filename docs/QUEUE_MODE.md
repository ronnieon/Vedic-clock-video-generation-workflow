# Queue Mode for Image Processing

## Overview

The queue mode feature allows you to defer expensive image editing and image-to-video generation tasks for background processing. Instead of executing immediately via Replicate API, prompts are saved as text files that a background service can pick up and process later.

## Features

### 1. Image Editing Queue Mode
- **Location**: Individual page viewer → "Edit Image" expander
- **Options**: 
  - **Execute Now**: Process immediately using Replicate API
  - **Queue for Later**: Save prompt for background processing
- **Output**: Creates `image_edit_prompt_for_v{N}.txt` in the page directory

### 2. Image-to-Video Queue Mode
- **Location**: Step 5: Generate Videos → Batch Image-to-Video Generation
- **Options**:
  - **Execute Now**: Process immediately using Replicate API
  - **Queue for Later**: Save prompts for background processing
- **Output**: Creates `image_to_video_prompt_for_v{N}.txt` in each page directory

## Prompt File Format

### Image-to-Video Prompts
```
image_to_video_prompt_for_v{N}.txt
```

**Format (NEW - simplified):**
```
Ultra high-definition, camera slowly zooms out then zooms in, subtle depth
```

**Old Format (still supported):**
```
# Image-to-Video Prompt for v2
# Queued at: 2025-01-24T15:30:00.123456
# Status: PENDING

Ultra high-definition, camera slowly zooms out then zooms in, subtle depth
```

The new format contains **only the prompt text** for simplicity. The old format with metadata is still supported for backward compatibility.

### Status Lifecycle
1. **PENDING** - Queued and waiting for processing
2. **PROCESSING** - Currently being processed by background service
3. **COMPLETED** - Successfully processed (file renamed to `.txt.completed`)
4. **FAILED** - Processing failed (file renamed to `.txt.failed`)

## Background Processing

### Running the Background Processor

The background processor continuously scans for queued tasks and processes them:

```bash
# Process all PDFs continuously (every 60 seconds)
python background_processor.py

# Process specific PDF only
python background_processor.py --pdf-stem download

# Run once and exit
python background_processor.py --once

# Custom polling interval (e.g., every 5 minutes)
python background_processor.py --interval 300
```

### How It Works

1. **Scanning**: The processor scans all page directories for prompt files
2. **Processing**: For each queued prompt:
   - Marks it as PROCESSING
   - Reads the prompt text
   - Gets the latest version of the source image
   - Calls the appropriate API (image edit or video generation)
   - Creates a new version with the result
   - Marks the prompt as COMPLETED or FAILED
3. **Versioning**: New versions are automatically created and tracked
4. **Dashboard Updates**: Once processed, new versions appear in the dashboard

### Monitoring

The background processor logs all activities:
- Processing cycles
- Successful completions
- Failures with error messages
- Statistics per cycle

Logs are written to the standard logging system in `logs/` directory.

## Use Cases

### 1. Batch Processing During Off-Hours
Queue multiple edits during the day, run the background processor overnight to process them when API costs might be lower or when you're not actively working.

### 2. Experimentation
Queue multiple different prompts for the same image/video to try different variations, then let the background service process them all.

### 3. Resource Management
Avoid blocking the UI for long-running operations. Queue tasks and continue working on other aspects of the project.

### 4. Retry Logic
If the background processor fails, you can simply restart it and it will pick up where it left off (PENDING tasks remain queued).

## File Structure

```
extracted/
  download/
    page_0001/
      image_v1.png                              # Original image
      image_v2.png                              # First edit
      image_edit_prompt_for_v3.txt              # Queued edit for v3
      image_video_v1.mp4                        # Original video
      image_to_video_prompt_for_v2.txt          # Queued video for v2
      image_to_video_prompt_for_v2.txt.completed # Processed prompt
    page_0002/
      ...
```

## API Reference

### Queue Manager (`utils/queue_manager.py`)

#### `queue_image_edit_prompt(page_dir, prompt, target_version)`
Queue an image edit prompt for later processing.

#### `queue_image_to_video_prompt(page_dir, prompt, target_version)`
Queue an image-to-video prompt for later processing.

#### `get_queued_prompts(page_dir, prompt_type)`
Get all queued prompts of a specific type for a page.

#### `mark_prompt_as_processing(prompt_file)`
Mark a queued prompt as being processed.

#### `mark_prompt_as_completed(prompt_file)`
Mark a queued prompt as completed and archive it.

#### `mark_prompt_as_failed(prompt_file, error)`
Mark a queued prompt as failed with error message.

#### `read_prompt_from_file(prompt_file)`
Read the actual prompt text from a prompt file. Handles both old format (with metadata) and new format (plain text only).

## Best Practices

1. **Clear Prompts**: Write clear, descriptive prompts that will make sense when processed later
2. **Version Awareness**: The target version is automatically determined based on current versions
3. **Monitoring**: Regularly check `.failed` files to understand any processing issues
4. **Cleanup**: Periodically archive or delete `.completed` files to keep directories clean
5. **Background Service**: Run the background processor as a daemon or scheduled task for continuous processing

## Integration with Existing Workflow

The queue mode integrates seamlessly with the existing versioning system:
- Queued tasks create new versions just like immediate execution
- Version tracking and fast-forward features work normally
- The dashboard automatically shows new versions once processed
- No changes needed to existing code or workflows

## Troubleshooting

### Prompt Not Processing
- Check if background processor is running
- Look for `.failed` files with error messages
- Verify API credentials are set in environment

### Version Conflicts
- Background processor uses the latest version at processing time
- If versions change between queuing and processing, the prompt targets the next available version

### Stale Prompts
- Delete unwanted `.txt` files before they're processed
- The processor only picks up files with `.txt` extension (not `.completed` or `.failed`)
