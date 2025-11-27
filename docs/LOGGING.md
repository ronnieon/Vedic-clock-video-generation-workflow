# Comprehensive Logging System

## Overview

The Leela Pipeline now includes comprehensive logging to track all user actions and system operations. Logs are automatically created in the `logs/` directory with timestamps.

## Log File Location

Logs are stored in: `logs/pipeline_YYYYMMDD_HHMMSS.log`

Example: `logs/pipeline_20241024_012636.log`

## What Gets Logged

### 1. **User Actions** 
Every button click and user interaction:
- `SELECT_PDF` - When a PDF is selected from dropdown
- `CLICK_EXTRACT` - Extract button clicked
- `CONFIRM_EXTRACT` - User confirms extraction (with overwrite)
- `CANCEL_EXTRACT` - User cancels extraction
- `CLICK_PLAN` - Plan Story button clicked
- `CONFIRM_PLAN` - User confirms story planning
- `CANCEL_PLAN` - User cancels planning
- `CLICK_REWRITE_ALL` - Rewrite All Pages button clicked
- `CONFIRM_REWRITE_ALL` - User confirms rewriting
- `CANCEL_REWRITE_ALL` - User cancels rewriting
- `CLICK_REWRITE` - Individual page rewrite (in viewer)
- `CONFIRM_AUDIO_ALL` - User confirms audio generation
- `CANCEL_AUDIO_ALL` - User cancels audio generation
- `CONFIRM_SLIDESHOW` - User confirms slideshow creation
- `CANCEL_SLIDESHOW` - User cancels slideshow creation
- `VIEW_LOGS` - User views logs in sidebar

### 2. **Pipeline Stages**
Start, completion, and duration of each stage:
- `EXTRACT` - PDF content extraction
- `PLAN_STORY` - Story cleaning and planning
- `REWRITE_ALL` - Rewriting all pages for kids
- `AUDIO_ALL` - Generating audio for all pages
- `SLIDESHOW` - Creating video slideshows

Each stage logs:
- Start time with parameters (model, page count, etc.)
- Completion time with duration in seconds
- Errors with full stack trace

### 3. **API Calls**
All external API calls to AI services:
- **OpenAI** (`gpt-4o-mini`) - Story planning
- **Gemini** (`gemini-2.5-flash`) - Kid-friendly rewriting
- **ElevenLabs** - Audio generation

Logged info:
- API name
- Model used
- Input text length (characters)
- Success/failure status

### 4. **File Operations**
All file read/write/delete operations:
- Extract PDF to directory
- Write cleaned text
- Write final text (EN/HI)
- Write audio files
- Write slideshow videos

### 5. **Overwrite Warnings**
When files will be overwritten:
- Number of files affected
- File paths (first 10 shown)
- User confirmation (yes/no)

### 6. **Session State Changes**
Streamlit session state modifications:
- Key name
- Value
- Action (SET/CLEAR/UPDATE)

## Log Format

```
YYYY-MM-DD HH:MM:SS | LEVEL    | logger_name | function:line | Message
```

Example:
```
2024-10-24 01:26:37 | INFO     | leela_pipeline | log_user_action:49 | USER ACTION: SELECT_PDF | PDF: download3 | Details: {'filename': 'download3.pdf'}
2024-10-24 01:26:42 | INFO     | leela_pipeline | log_stage_start:55 | STAGE START: EXTRACT | PDF: download3 | Params: {'pdf_path': 'download3.pdf'}
2024-10-24 01:27:15 | INFO     | leela_pipeline | log_stage_complete:62 | STAGE COMPLETE: EXTRACT | PDF: download3 | Duration: 33.21s
```

## Log Levels

- **DEBUG**: Detailed file operations, session changes
- **INFO**: User actions, stage completions, API calls
- **WARNING**: Overwrite warnings, missing dependencies
- **ERROR**: Stage failures, API errors (with full traceback)

## Viewing Logs

### In the UI
1. Check the **sidebar** under "📝 Logging"
2. Click **"📄 View Logs"** button
3. Logs appear in a text area

### In Terminal
```bash
# View latest log file
ls -lt logs/ | head -2

# Tail logs in real-time
tail -f logs/pipeline_*.log | head -1

# Search for errors
grep ERROR logs/pipeline_*.log

# Search for specific PDF
grep "PDF: download3" logs/pipeline_*.log

# View all API calls
grep "API CALL" logs/pipeline_*.log
```

## Log Analysis Examples

### Track a Complete Workflow
```bash
grep "download3" logs/pipeline_20241024_*.log
```

### Count API Calls
```bash
grep "API CALL" logs/*.log | wc -l
```

### Find Failed Operations
```bash
grep "FAILED\|ERROR" logs/*.log
```

### See Processing Times
```bash
grep "Duration:" logs/*.log
```

### View User Activity
```bash
grep "USER ACTION" logs/*.log | tail -20
```

## Benefits

1. **Debugging**: Track exactly what happened when something goes wrong
2. **Performance**: See how long each stage takes
3. **Usage Analytics**: Understand which features are used most
4. **Audit Trail**: Complete record of all operations
5. **Error Tracking**: Full stack traces for all errors
6. **API Monitoring**: Track API usage and costs

## Configuration

Edit `utils/logger.py` to customize:
- Log file location
- Log levels
- Format strings
- Rotation policies

## Privacy Note

Logs contain:
- PDF filenames
- File paths
- Error messages
- Timestamps
- Processing durations

Logs do **NOT** contain:
- Full text content
- API keys
- User credentials
- Actual PDF content

## Storage

Logs accumulate over time. Clean up old logs periodically:

```bash
# Remove logs older than 30 days
find logs/ -name "*.log" -mtime +30 -delete
```

Or archive them:
```bash
# Archive old logs
tar -czf logs_archive_$(date +%Y%m%d).tar.gz logs/*.log
```

## Integration

The logging system is automatically initialized when the app starts. No configuration needed!

All components import and use the logger:
```python
from utils.logger import log_user_action, log_stage_start, log_stage_complete
```

## Troubleshooting

### Logs not appearing?
- Check `logs/` directory exists
- Verify write permissions
- Check console for initialization message

### Too much logging?
- Edit `utils/logger.py`
- Increase log level from `DEBUG` to `INFO`
- Reduce console output level

### Need more detail?
- All logs are in the file (including DEBUG)
- Console only shows INFO and above
- Read the log file directly for full details
