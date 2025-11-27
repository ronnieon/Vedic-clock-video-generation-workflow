"""
PDF to Slideshow Pipeline Dashboard
====================================
A comprehensive Streamlit dashboard for converting PDFs into multilingual slideshow videos.

Complete Workflow:
1. Extract Content - Extract text and images from PDF
2. Plan Story - Clean and organize extracted text  
3. Rewrite for Kids - Create kid-friendly English and Hindi versions
4. Generate Audio - Create voiceovers for both languages
5. Create Slideshow - Build final video slideshows

Version: 2.0
"""

import streamlit as st
import glob
from pathlib import Path
import os
import boto3
import threading
import time
from botocore.exceptions import ClientError, NoCredentialsError

# Auto-load environment variables
try:
    from dotenv import load_dotenv
    # Prefer .envrc, then .env, then .env.local
    for env_file in (".envrc", ".env", ".env.local"):
        if Path(env_file).exists():
            load_dotenv(dotenv_path=env_file, override=False)
            _ENV_LOADED_FROM = env_file
            break
        else:
            _ENV_LOADED_FROM = None
except Exception:
    _ENV_LOADED_FROM = None

# Import logging FIRST to initialize
from utils.logger import logger, log_user_action, get_current_log_file

# ============================================================================
# S3 SYNC FUNCTIONALITY - DISABLED
# ============================================================================

# def sync_to_s3():
#     """
#     Bidirectional sync between local directory and S3 bucket.
#     - Downloads new files from S3 that don't exist locally
#     - Uploads new/modified files from local to S3
#     Runs continuously every 60 seconds in a background thread.
#     """
#     s3_bucket = "contentextract"
#     s3_prefix = "extract/"
#     local_dir = Path("extracted")
#     
#     # Initialize S3 client
#     try:
#         s3_client = boto3.client(
#             's3',
#             aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
#             aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
#             region_name=os.getenv('AWS_DEFAULT_REGION', 'ap-south-1')
#         )
#         logger.info(f"S3 bidirectional sync initialized for {local_dir} <-> s3://{s3_bucket}/{s3_prefix}")
#     except NoCredentialsError:
#         logger.error("AWS credentials not found. S3 sync disabled.")
#         return
#     except Exception as e:
#         logger.error(f"Failed to initialize S3 client: {e}")
#         return
#     
#     while True:
#         try:
#             # Ensure local directory exists
#             local_dir.mkdir(parents=True, exist_ok=True)
#             
#             files_downloaded = 0
#             files_uploaded = 0
#             files_skipped_download = 0
#             files_skipped_upload = 0
#             
#             # ============================================================
#             # STEP 1: Download files from S3 that don't exist locally
#             # ============================================================
#             try:
#                 # List all objects in S3 bucket with the prefix
#                 paginator = s3_client.get_paginator('list_objects_v2')
#                 pages = paginator.paginate(Bucket=s3_bucket, Prefix=s3_prefix)
#                 
#                 for page in pages:
#                     if 'Contents' not in page:
#                         continue
#                     
#                     for obj in page['Contents']:
#                         s3_key = obj['Key']
#                         
#                         # Skip directory markers
#                         if s3_key.endswith('/'):
#                             continue
#                         
#                         # Calculate local file path
#                         relative_path = s3_key[len(s3_prefix):]
#                         if not relative_path:
#                             continue
#                         
#                         local_file = local_dir / relative_path
#                         
#                         # Only download if file doesn't exist locally
#                         if local_file.exists():
#                             # File already exists locally, skip download
#                             files_skipped_download += 1
#                             continue
#                         
#                         # File doesn't exist locally, download it
#                         try:
#                             # Create parent directories
#                             local_file.parent.mkdir(parents=True, exist_ok=True)
#                             
#                             # Download file
#                             s3_client.download_file(s3_bucket, s3_key, str(local_file))
#                             files_downloaded += 1
#                             logger.info(f"⬇️  Downloaded from S3: {relative_path}")
#                         except Exception as e:
#                             logger.error(f"Failed to download {s3_key}: {e}")
#             
#             except Exception as e:
#                 logger.error(f"Error during S3 download phase: {e}")
#             
#             # ============================================================
#             # STEP 2: Upload local files to S3
#             # ============================================================
#             try:
#                 for file_path in local_dir.rglob('*'):
#                     if file_path.is_file():
#                         # Calculate relative path for S3 key
#                         relative_path = file_path.relative_to(local_dir)
#                         s3_key = f"{s3_prefix}{relative_path.as_posix()}"
#                         
#                         try:
#                             # Check if file already exists in S3
#                             try:
#                                 s3_client.head_object(Bucket=s3_bucket, Key=s3_key)
#                                 # File already exists in S3, skip upload
#                                 files_skipped_upload += 1
#                                 continue
#                             except ClientError as e:
#                                 if e.response['Error']['Code'] == '404':
#                                     # File doesn't exist in S3, proceed with upload
#                                     pass
#                                 else:
#                                     # Some other error, re-raise it
#                                     raise
#                             
#                             # File doesn't exist in S3, upload it
#                             s3_client.upload_file(
#                                 str(file_path),
#                                 s3_bucket,
#                                 s3_key
#                             )
#                             files_uploaded += 1
#                             logger.info(f"⬆️  Uploaded to S3: {relative_path}")
#                         except ClientError as e:
#                             logger.error(f"Failed to upload {file_path} to S3: {e}")
#                         except Exception as e:
#                             logger.error(f"Unexpected error uploading {file_path}: {e}")
#             
#             except Exception as e:
#                 logger.error(f"Error during S3 upload phase: {e}")
#             
#             # Log summary (always log, even if everything was skipped)
#             if files_downloaded > 0 or files_uploaded > 0:
#                 logger.info(f"S3 sync completed: ⬇️  {files_downloaded} downloaded, ⬆️  {files_uploaded} uploaded, ⏭️  {files_skipped_download + files_skipped_upload} skipped")
#             elif files_skipped_download > 0 or files_skipped_upload > 0:
#                 # All files were skipped (already in sync)
#                 logger.debug(f"S3 sync: All files in sync (⏭️  {files_skipped_download + files_skipped_upload} files already exist)")
#             
#             # ============================================================
#             # STEP 3: Discover and register externally-created versions
#             # ============================================================
#             # After syncing files, check if any new versions exist on disk
#             # that aren't registered in versions.json (e.g., from background processor)
#             try:
#                 from utils.versioning import create_new_version, get_version_count, migrate_legacy_files, cleanup_all_old_versions, discover_all_versions
#                 
#                 discovered_count = discover_all_versions(local_dir)
#                 if discovered_count > 0:
#                     logger.info(f"🔍 Discovered and registered {discovered_count} new version(s) from external sources")
#             except Exception as e:
#                 logger.error(f"Error during version discovery: {e}")
#             
#         except Exception as e:
#             logger.error(f"Error during S3 sync: {e}")
#         
#         # Wait 60 seconds before next sync
#         time.sleep(60)

# def start_s3_sync_thread():
#     """
#     Start the S3 sync thread in daemon mode.
#     This ensures the thread stops when the main application exits.
#     """
#     sync_thread = threading.Thread(target=sync_to_s3, daemon=True)
#     sync_thread.start()
#     logger.info("S3 sync thread started (syncing every 60 seconds)")

# Start S3 sync when the app loads - DISABLED
# if 's3_sync_started' not in st.session_state:
#     start_s3_sync_thread()
#     st.session_state.s3_sync_started = True



# Import components
from components.pipeline_stages import (
    render_extraction_stage,
    render_story_planning_stage,
    render_rewriting_stage,
    render_audio_generation_stage,
    render_video_generation_stage,
    render_slideshow_stage
)
from components.content_viewer import (
    render_final_story_viewer,
    render_slideshow_viewer,
    render_pages_viewer
)
from utils.workflow import get_workflow_status
from utils.versioning import cleanup_all_old_versions
from utils.pdf_state import load_marked_done_pdfs, mark_pdf_as_done, unmark_pdf_as_done

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="PDF to Slideshow Pipeline",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# MAIN DASHBOARD
# ============================================================================

st.title("PDF to Slideshow Pipeline")

# Initialize session state for marked-as-done PDFs from persistent storage
if 'marked_done_pdfs' not in st.session_state:
    st.session_state.marked_done_pdfs = load_marked_done_pdfs()

# PDF Selection
pdf_paths = glob.glob("pdfs/*.pdf")
pdf_files = [os.path.basename(p) for p in pdf_paths]

if not pdf_files:
    st.warning("No PDF files found in the current directory.")
    st.info("Please place PDF files in this directory to get started.")
else:
    # Format PDF names with status indicators
    def format_pdf_option(pdf):
        if pdf in st.session_state.marked_done_pdfs:
            return f"✅ {pdf} (Done)"
        return pdf
    
    # Create formatted options
    pdf_options = [format_pdf_option(pdf) for pdf in pdf_files]
    
    selected_option = st.selectbox(
        "Select a PDF file to process:",
        pdf_options,
        help="Choose the PDF you want to convert into a slideshow. ✅ indicates completed PDFs."
    )
    
    # Extract actual PDF filename from formatted option
    if selected_option.startswith("✅ "):
        selected_pdf = selected_option.replace("✅ ", "").replace(" (Done)", "")
    else:
        selected_pdf = selected_option

    if selected_pdf:
        pdf_path = Path("pdfs") / selected_pdf
        pdf_stem = pdf_path.stem
        log_user_action("SELECT_PDF", pdf_stem, {"filename": selected_pdf})
        
        # Check if PDF is marked as done
        is_marked_done = selected_pdf in st.session_state.marked_done_pdfs
        
        # Display PDF info
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            with col1:
                status_badge = "✅ Done" if is_marked_done else "🔄 In Progress"
                st.text(f"Processing - {selected_pdf} - {status_badge}")
            with col2:
                # Download PDF button
                with open(os.path.join("pdfs", selected_pdf), "rb") as pdf_file:
                    PDFbyte = pdf_file.read()
                st.download_button(
                    label="Download PDF",
                    data=PDFbyte,
                    file_name=selected_pdf,
                    mime='application/pdf',
                    use_container_width=True
                )
            with col3:
                # Mark as Done / Re-enable button
                if is_marked_done:
                    if st.button("🔄 Re-enable", key=f"{pdf_stem}_reenable", use_container_width=True,
                                help="Re-enable this PDF to show the pipeline"):
                        # Update both persistent storage and session state
                        if unmark_pdf_as_done(selected_pdf):
                            st.session_state.marked_done_pdfs.discard(selected_pdf)
                            log_user_action("REENABLE_PDF", pdf_stem)
                            st.rerun()
                        else:
                            st.error("❌ Failed to re-enable PDF")
                else:
                    if st.button("✅ Mark as Done", key=f"{pdf_stem}_mark_done", use_container_width=True,
                                help="Mark this PDF as completed and hide the pipeline"):
                        # Update both persistent storage and session state
                        if mark_pdf_as_done(selected_pdf):
                            st.session_state.marked_done_pdfs.add(selected_pdf)
                            log_user_action("MARK_DONE_PDF", pdf_stem)
                            st.rerun()
                        else:
                            st.error("❌ Failed to mark PDF as done")
            with col4:
                # Cleanup button
                cleanup_key = f'{pdf_stem}_cleanup'
                if st.button("Cleanup", key=cleanup_key, use_container_width=True, 
                            help="Remove all but the latest version of each artifact"):
                    log_user_action("CLEANUP_VERSIONS", pdf_stem)
                    with st.spinner("Cleaning up old versions..."):
                        try:
                            deleted = cleanup_all_old_versions(pdf_stem)
                            total_deleted = sum(deleted.values())
                            if total_deleted > 0:
                                st.success(f"✅ Cleaned up {total_deleted} old version(s)")
                                details = ", ".join([f"{count} {ct}" for ct, count in deleted.items()])
                                st.info(f"Deleted: {details}")
                                logger.info(f"Cleaned up {total_deleted} old versions for {pdf_stem}: {deleted}")
                            else:
                                st.info("ℹ️ No old versions to cleanup")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Cleanup failed: {str(e)}")
                            logger.error(f"Cleanup error for {pdf_stem}: {e}")
        
        st.divider()
        
        # Only show pipeline if PDF is not marked as done
        if is_marked_done:
            st.success("🎉 This PDF has been marked as completed!")
            st.info("💡 Click the 'Re-enable' button above to show the pipeline again.")
        else:
            # Get workflow status
            status = get_workflow_status(pdf_stem)
            
            # Workflow Status Dashboard
            with st.sidebar:
                st.header("Workflow Status")
                st.markdown(f"**PDF:** {selected_pdf}")
                st.divider()
                # if _ENV_LOADED_FROM:
                #     st.caption(f"🔑 Env loaded from `{_ENV_LOADED_FROM}`")
                
                stages = [
                    ("Extract Content", status['extracted']),
                    ("Plan Story", status['planned']),
                    ("Rewrite for Kids", status['rewritten']),
                    ("Generate Audio", status['audio_generated']),
                    ("Create Page Videos", status['page_videos']),
                    ("Create Final Slideshow", status['slideshow_created'])
                ]
                
                for stage_name, stage_status in stages:
                    total = stage_status['total']
                    done = stage_status['done']
                    missing = stage_status['missing']
                    present = stage_status.get('present', [])
                    complete = stage_status['complete']
                    expected_version = stage_status.get('expected_version', 0)
                    max_version = stage_status.get('max_version', 0)
                    
                    if total == 0:
                        # Stage not started
                        st.info(f"⏳ {stage_name}")
                    elif complete:
                        # All files present at expected version
                        version_info = f" [v{expected_version}]" if expected_version > 0 else ""
                        st.success(f"✅ {stage_name} ({done}/{total}){version_info}")
                        # Show complete files list
                        if present:
                            with st.expander(f"✅ View {len(present)} complete file(s)", expanded=False):
                                for file_path in present:
                                    st.caption(f"✅ `{file_path}`")
                    else:
                        # Incomplete - show progress and version info
                        version_info = f" [needs v{expected_version}]" if expected_version > 0 else ""
                        st.warning(f"⚠️ {stage_name} ({done}/{total}){version_info}")
                        
                        # Show present files
                        if present:
                            with st.expander(f"✅ View {len(present)} complete file(s)", expanded=False):
                                for file_path in present:
                                    st.caption(f"✅ `{file_path}`")
                        
                        # Show missing files
                        if missing:
                            with st.expander(f"❌ View {len(missing)} missing/outdated file(s)", expanded=False):
                                for file_path in missing:
                                    st.caption(f"❌ `{file_path}`")
                
                st.divider()
                st.caption("Tip: Complete stages in order for best results")
                
                st.divider()
                st.subheader("Logging")
                log_file = get_current_log_file()
                st.caption(f"Log file: `{log_file.name}`")
                if st.button("📄 View Logs", use_container_width=True):
                    log_user_action("VIEW_LOGS", pdf_stem)
                    with open(log_file, 'r', encoding='utf-8') as f:
                        st.text_area("Recent Logs", f.read(), height=300)
            
            # Pipeline Stages
            st.header("Pipeline Stages")
            
            # Use tabs for better organization
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                "Extract", 
                "Plan", 
                "Rewrite", 
                "Audio", 
                "Videos",
                "Slideshow"
            ])
            
            with tab1:
                render_extraction_stage(pdf_path, pdf_stem)
            
            with tab2:
                render_story_planning_stage(pdf_stem)
            
            with tab3:
                render_rewriting_stage(pdf_stem)
            
            with tab4:
                render_audio_generation_stage(pdf_stem)
            
            with tab5:
                render_video_generation_stage(pdf_stem)
            
            with tab6:
                render_slideshow_stage(pdf_stem)
            
            st.divider()
            
            # Content Viewers
            st.header("View Content")
            
            # Show final story
            render_final_story_viewer(pdf_stem)
            
            # Show detailed pages
            render_pages_viewer(pdf_stem)
            
            # Show slideshows
            render_slideshow_viewer(pdf_stem)