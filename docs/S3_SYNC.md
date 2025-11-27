# S3 Bidirectional Sync

## Overview

The S3 sync functionality now performs **bidirectional synchronization** between your local `extracted/` directory and the S3 bucket. This means:

- 🔽 **Download**: Files that exist in S3 but not locally are automatically downloaded
- 🔼 **Upload**: Files that exist locally but not in S3 are automatically uploaded

This enables seamless collaboration and processing across multiple machines or services.

## How It Works

### Automatic Background Sync

When you run the Streamlit app, a background thread automatically starts that:
1. Runs every **60 seconds**
2. Performs bidirectional sync in two phases:

#### Phase 1: Download from S3
- Lists all files in `s3://contentextract/extract/`
- For each file in S3:
  - Checks if it exists locally
  - If **not found locally**: downloads it to the corresponding path
  - Creates parent directories as needed
  - Logs each download

#### Phase 2: Upload to S3
- Scans all files in local `extracted/` directory
- For each local file:
  - Checks if it exists in S3
  - If **not found in S3**: uploads it
  - Preserves directory structure
  - Logs each upload

### Sync Summary Logs

After each sync cycle, you'll see logs like:
```
S3 sync completed: ⬇️  5 downloaded, ⬆️  3 uploaded
```

## Use Cases

### 1. Background Processor Results
When your background processor (running on another machine or as a service) generates new versions:
1. It writes files locally and syncs to S3
2. Your Streamlit dashboard automatically downloads these new files
3. New versions appear in the dashboard without manual intervention

### 2. Multi-Machine Workflow
- Edit and queue tasks on **Machine A**
- Process queued tasks on **Machine B** (with GPU)
- View results on **Machine A** (or any other machine)
- All machines stay in sync automatically

### 3. Collaborative Editing
- Multiple users can work on different PDFs
- Changes from any user propagate to S3
- Other users automatically get the latest files

### 4. Backup & Recovery
- All local work is automatically backed up to S3
- If you lose local files, they're automatically restored from S3
- Start fresh on a new machine and get all your files

## Configuration

### S3 Bucket Details
- **Bucket**: `contentextract`
- **Prefix**: `extract/`
- **Region**: `ap-south-1` (Asia Pacific - Mumbai)

### Environment Variables Required
Set these in your `.envrc` or `.env` file:
```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=ap-south-1
```

### Sync Interval
Default: 60 seconds

To change, modify the `time.sleep(60)` value in `app.py`:
```python
# Wait 60 seconds before next sync
time.sleep(60)  # Change to your desired interval
```

## File Handling

### Conflict Resolution
Current behavior:
- **Downloads only if file doesn't exist locally** (local files take precedence)
- **Uploads only if file doesn't exist in S3** (S3 files take precedence)
- No overwriting of existing files
- No timestamp-based sync (yet)

### What Gets Synced
All files in the `extracted/` directory including:
- ✅ Images (`.png`, `.jpg`, etc.)
- ✅ Videos (`.mp4`)
- ✅ Text files (`.txt`)
- ✅ Audio files (`.mp3`)
- ✅ Metadata (`.json`)
- ✅ Queue files (`image_edit_prompt_for_v*.txt`, `image_to_video_prompt_for_v*.txt`)
- ✅ Completed/failed queue files (`.txt.completed`, `.txt.failed`)

### What Doesn't Get Synced
- Temporary files (e.g., `temp_*.mp4`, `temp_*.png`)
- Files outside the `extracted/` directory

## Monitoring

### View Sync Status
Sync activity is logged to the pipeline log file:
```bash
tail -f logs/pipeline_*.log | grep "S3"
```

Look for:
```
S3 bidirectional sync initialized for extracted <-> s3://contentextract/extract/
Downloaded from S3: download/page_0001/image_v5.png
S3 sync completed: ⬇️  1 downloaded, ⬆️  2 uploaded
```

### Troubleshooting

#### No Files Downloading
- Check AWS credentials are set correctly
- Verify S3 bucket permissions allow `s3:GetObject` and `s3:ListBucket`
- Check log for error messages

#### No Files Uploading
- Verify S3 bucket permissions allow `s3:PutObject`
- Check file paths don't contain special characters
- Ensure files aren't being skipped due to existing S3 objects

#### Sync Too Slow
- Reduce sync interval (but be mindful of API rate limits)
- Consider filtering which files to sync
- Check network connectivity

## Advanced: Timestamp-Based Sync (Future Enhancement)

The current implementation uses existence-based sync. For timestamp-based sync (overwrite older files), you could enhance the logic to:

1. Compare modification times
2. Download if S3 file is newer
3. Upload if local file is newer

This would require storing and comparing `LastModified` timestamps.

## Integration with Queue Mode

The bidirectional sync is perfect for queue mode:

1. **Queue on Dashboard**: User queues tasks via Streamlit UI
2. **Sync to S3**: Queue files (`*_prompt_for_v*.txt`) uploaded to S3
3. **Background Processor Pulls**: Processor downloads queue files from S3
4. **Process & Upload**: Processor generates assets and uploads to S3
5. **Dashboard Pulls**: Streamlit downloads new assets from S3
6. **Display Results**: New versions appear in dashboard automatically

This enables a fully distributed processing pipeline!

## Permissions Required

### S3 IAM Policy
Your AWS user/role needs these permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": "arn:aws:s3:::contentextract"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:HeadObject"
      ],
      "Resource": "arn:aws:s3:::contentextract/extract/*"
    }
  ]
}
```

## Best Practices

1. **Let it run**: Don't interrupt the sync thread during operations
2. **Monitor logs**: Check for errors regularly
3. **Network stability**: Ensure stable internet connection for continuous sync
4. **Credentials security**: Never commit AWS credentials to git
5. **Backup strategy**: S3 versioning recommended for critical files
6. **Cost monitoring**: Be aware of S3 storage and transfer costs

## Performance Notes

- **Download phase**: Uses pagination for large buckets
- **Upload phase**: Checks existence before uploading (uses `head_object`)
- **Thread safety**: Runs in daemon thread, stops gracefully on app exit
- **Error handling**: Individual file failures don't stop the sync cycle
