"""
Pipeline Stage Components
==========================
UI components for each stage of the PDF-to-slideshow pipeline.
"""

import streamlit as st
from pathlib import Path
from typing import Optional
import os
import time

from extract_pdfs import process_pdf
from clean_and_concatenate import process_pdf_dir as clean_and_plan_story
from rewrite_for_kids import _call_gemini_dual as rewrite_text_for_kids
from generate_voiceovers import generate_mp3, ElevenLabs
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from PIL import Image

from utils.workflow import get_overwrite_files, get_page_directories, get_extraction_dir
from utils.logger import (
    log_user_action, log_stage_start, log_stage_complete, log_stage_error,
    log_file_operation, log_api_call, log_overwrite_warning, log_session_info
)
from utils.versioning import create_new_version, get_version_count, migrate_legacy_files


# ============================================================================
# STAGE 1: EXTRACTION
# ============================================================================

def render_extraction_stage(pdf_path: Path, pdf_stem: str):
    """Render the extraction stage UI. LEGACY FORMAT DISABLED - only updated format supported."""
    st.subheader("Step 1: Extract Content")
    st.write("Extract text and images from the PDF (scene-based: 2 pages = 1 scene)")
    
    # LEGACY FORMAT DISABLED - Force updated format only
    format_key = f"{pdf_stem}_pdf_format"
    st.session_state[format_key] = "updated"  # Always use updated
    # UI selector commented out - only updated format supported
    # st.selectbox(
    #     "PDF Format",
    #     options=["old", "updated"],
    #     index=0 if st.session_state[format_key] == "old" else 1,
    #     key=format_key,
    #     help="'old': 1 page = 1 unit; 'updated': 2 pages = 1 scene (text from first, image from second)."
    # )
    
    extraction_dir = get_extraction_dir(pdf_stem)
    confirm_key = f'{pdf_stem}_confirm_extract'
    
    if st.session_state.get(confirm_key):
        overwrite_files = get_overwrite_files(pdf_stem, 'extract')
        if overwrite_files:
            st.warning(f"⚠️ This will overwrite the entire directory: **{extraction_dir}**")
            log_overwrite_warning(overwrite_files, False)
        
        col1, col2 = st.columns(2)
        if col1.button("✅ Confirm Extract", key=f"{pdf_stem}_confirm_extract_btn", use_container_width=True):
            log_user_action("CONFIRM_EXTRACT", pdf_stem, {"overwrite": bool(overwrite_files)})
            log_stage_start("EXTRACT", pdf_stem, pdf_path=str(pdf_path))
            start_time = time.time()
            try:
                with st.spinner("Extracting content..."):
                    process_pdf(pdf_path, Path('extracted'), force=True, pdf_format=st.session_state[format_key])
                    log_file_operation("extract_pdf", extraction_dir, success=True)
                duration = time.time() - start_time
                log_stage_complete("EXTRACT", pdf_stem, duration=duration)
                st.session_state[confirm_key] = False
                log_session_info(confirm_key, False, "CLEAR")
                st.success("✅ Extraction complete!")
                st.rerun()
            except Exception as e:
                log_stage_error("EXTRACT", pdf_stem, e)
                st.error(f"❌ Extraction failed: {str(e)}")
        if col2.button("❌ Cancel", key=f"{pdf_stem}_cancel_extract_btn", use_container_width=True):
            log_user_action("CANCEL_EXTRACT", pdf_stem)
            st.session_state[confirm_key] = False
            log_session_info(confirm_key, False, "CLEAR")
            st.rerun()
    else:
        button_label = "Extract" if not extraction_dir.exists() else "Re-extract"
        if st.button(button_label, key=f"{pdf_stem}_extract_btn", use_container_width=True):
            log_user_action("CLICK_EXTRACT", pdf_stem, {"is_reextract": extraction_dir.exists()})
            if extraction_dir.exists():
                st.session_state[confirm_key] = True
                log_session_info(confirm_key, True, "SET")
                st.rerun()
            else:
                log_stage_start("EXTRACT", pdf_stem, pdf_path=str(pdf_path))
                start_time = time.time()
                try:
                    with st.spinner("Extracting content..."):
                        process_pdf(pdf_path, Path('extracted'), force=True, pdf_format=st.session_state[format_key])
                        log_file_operation("extract_pdf", extraction_dir, success=True)
                    duration = time.time() - start_time
                    log_stage_complete("EXTRACT", pdf_stem, duration=duration)
                    st.success("✅ Extraction complete!")
                    st.rerun()
                except Exception as e:
                    log_stage_error("EXTRACT", pdf_stem, e)
                    st.error(f"❌ Extraction failed: {str(e)}")


# ============================================================================
# STAGE 2: STORY PLANNING
# ============================================================================

def render_story_planning_stage(pdf_stem: str):
    """Render the story planning stage UI."""
    st.subheader("Step 2: Plan Story")
    st.write("Clean and organize the extracted text")
    
    extraction_dir = get_extraction_dir(pdf_stem)
    confirm_key = f'{pdf_stem}_confirm_plan'
    
    if not extraction_dir.exists():
        st.info("ℹ️ Complete Step 1 (Extract Content) first")
        return
    
    if st.session_state.get(confirm_key):
        overwrite_files = get_overwrite_files(pdf_stem, 'plan')
        if overwrite_files:
            st.warning(f"⚠️ This will overwrite {len(overwrite_files)} file(s):")
            log_overwrite_warning(overwrite_files, False)
            for file in overwrite_files[:5]:  # Show first 5
                st.code(str(file), language=None)
            if len(overwrite_files) > 5:
                st.write(f"... and {len(overwrite_files) - 5} more files")
        
        col1, col2 = st.columns(2)
        if col1.button("✅ Confirm Plan", key=f"{pdf_stem}_confirm_plan_btn", use_container_width=True):
            log_user_action("CONFIRM_PLAN", pdf_stem, {"files_to_overwrite": len(overwrite_files)})
            log_stage_start("PLAN_STORY", pdf_stem, model='gemini-2.5-flash')
            start_time = time.time()
            try:
                with st.spinner("Planning story..."):
                    clean_and_plan_story(extraction_dir, model='gemini-2.5-flash', force=True, provider='gemini')
                    log_api_call("Gemini", "gemini-2.5-flash", 0, success=True)
                duration = time.time() - start_time
                log_stage_complete("PLAN_STORY", pdf_stem, duration=duration)
                st.session_state[confirm_key] = False
                log_session_info(confirm_key, False, "CLEAR")
                st.success("✅ Story planning complete!")
                st.rerun()
            except Exception as e:
                log_stage_error("PLAN_STORY", pdf_stem, e)
                st.error(f"❌ Planning failed: {str(e)}")
        if col2.button("❌ Cancel", key=f"{pdf_stem}_cancel_plan_btn", use_container_width=True):
            log_user_action("CANCEL_PLAN", pdf_stem)
            st.session_state[confirm_key] = False
            log_session_info(confirm_key, False, "CLEAR")
            st.rerun()
    else:
        story_file = extraction_dir / 'whole_story_cleaned.txt'
        button_label = "Plan Story" if not story_file.exists() else "Re-plan Story"
        if st.button(button_label, key=f"{pdf_stem}_plan_btn", use_container_width=True):
            log_user_action("CLICK_PLAN", pdf_stem, {"is_replan": story_file.exists()})
            overwrite_files = get_overwrite_files(pdf_stem, 'plan')
            if overwrite_files:
                st.session_state[confirm_key] = True
                log_session_info(confirm_key, True, "SET")
                st.rerun()
            else:
                log_stage_start("PLAN_STORY", pdf_stem, model='gemini-2.5-flash')
                start_time = time.time()
                try:
                    with st.spinner("Planning story..."):
                        clean_and_plan_story(extraction_dir, model='gemini-2.5-flash', force=True, provider='gemini')
                        log_api_call("Gemini", "gemini-2.5-flash", 0, success=True)
                    duration = time.time() - start_time
                    log_stage_complete("PLAN_STORY", pdf_stem, duration=duration)
                    st.success("✅ Story planning complete!")
                    st.rerun()
                except Exception as e:
                    log_stage_error("PLAN_STORY", pdf_stem, e)
                    st.error(f"❌ Planning failed: {str(e)}")


# ============================================================================
# STAGE 3: REWRITE FOR KIDS
# ============================================================================

def render_rewriting_stage(pdf_stem: str):
    """Render the rewriting for kids stage UI."""
    st.subheader("Step 3: Rewrite for Kids")
    st.write("Create kid-friendly English and Hindi versions")
    
    extraction_dir = get_extraction_dir(pdf_stem)
    page_dirs = get_page_directories(pdf_stem)
    
    if not page_dirs:
        st.info("ℹ️ Complete Step 1 (Extract Content) first")
        return
    
    # Check if any page has clean_text
    has_clean_text = any((p / 'clean_text.txt').exists() for p in page_dirs)
    if not has_clean_text:
        st.info("ℹ️ Complete Step 2 (Plan Story) first")
        return
    
    # Migrate legacy files and get version info
    for page_dir in page_dirs:
        migrate_legacy_files(page_dir)
    
    # Check max versions across all pages
    max_version = max([get_version_count(p, 'en_text') for p in page_dirs], default=0)
    
    # Update button label to show versioning
    if max_version == 0:
        button_label = "Create Rewrites (v1) for All Pages"
    else:
        button_label = f"Create New Versions for All Pages"
    
    if st.button(button_label, key=f"{pdf_stem}_rewrite_all_btn", use_container_width=True):
        log_user_action("CLICK_REWRITE_ALL", pdf_stem, {"pages": len(page_dirs), "creating_versions": True})
        log_stage_start("REWRITE_ALL", pdf_stem, model='gemini-2.5-flash', pages=len(page_dirs))
        start_time = time.time()
        
        # Load whole story context
        extraction_dir = get_extraction_dir(pdf_stem)
        whole_story_file = extraction_dir / 'whole_story_cleaned.txt'
        whole_story = None
        if whole_story_file.exists():
            whole_story = whole_story_file.read_text(encoding='utf-8', errors='ignore')
        
        versions_created = []
        previous_pages_en = []
        
        try:
            with st.spinner("Creating new versions for all pages..."):
                for page_dir in page_dirs:
                    clean_file = page_dir / 'clean_text.txt'
                    if clean_file.exists():
                        text = clean_file.read_text()
                        log_api_call("Gemini", "gemini-2.5-flash", len(text), success=False)
                        
                        # Build previous pages context
                        prev_context = "\n\n".join(previous_pages_en) if previous_pages_en else None
                        
                        # Generate rewritten text with context
                        en_text, hi_text = rewrite_text_for_kids(
                            'gemini-2.5-flash', 
                            text,
                            whole_story=whole_story,
                            previous_pages=prev_context
                        )
                        
                        # Create new versions (never overwrite)
                        create_new_version(page_dir, 'en_text', en_text, model='gemini-2.5-flash')
                        create_new_version(page_dir, 'hi_text', hi_text, model='gemini-2.5-flash')
                        
                        new_version = get_version_count(page_dir, 'en_text')
                        versions_created.append((page_dir.name, new_version))
                        
                        # Add to previous pages for next iteration
                        page_index = int(page_dir.name.split('_')[1]) if '_' in page_dir.name else 0
                        previous_pages_en.append(f"[Page {page_index}] {en_text}")
                        
                        log_api_call("Gemini", "gemini-2.5-flash", len(text), success=True)
                        log_file_operation(f"rewrite_page_{page_dir.name}_v{new_version}", page_dir, success=True)
            
            duration = time.time() - start_time
            log_stage_complete("REWRITE_ALL", pdf_stem, duration=duration)
            
            st.success(f"✅ Created new versions for {len(versions_created)} pages! All previous versions preserved.")
            st.info(f"💡 Check individual pages to view version history and restore older versions")
            st.rerun()
        except Exception as e:
            log_stage_error("REWRITE_ALL", pdf_stem, e)
            st.error(f"❌ Rewriting failed: {str(e)}")


# ============================================================================
# STAGE 4: AUDIO GENERATION
# ============================================================================

def render_audio_generation_stage(pdf_stem: str):
    """Render the audio generation stage UI."""
    st.subheader("Step 4: Generate Audio")
    st.write("Create English and Hindi voiceovers")
    
    page_dirs = get_page_directories(pdf_stem)
    
    if not page_dirs:
        st.info("ℹ️ Complete Step 1 (Extract Content) first")
        return
    
    # Check if any page has final text (check versioned files)
    from utils.versioning import get_latest_version_path
    has_final_text = any(
        (p / 'final_text_en.txt').exists() or 
        get_latest_version_path(p, 'en_text') 
        for p in page_dirs
    )
    if not has_final_text:
        st.info("ℹ️ Complete Step 3 (Rewrite for Kids) first")
        return
    
    confirm_key = f'{pdf_stem}_confirm_audio_all'
    
    if st.session_state.get(confirm_key):
        overwrite_files = get_overwrite_files(pdf_stem, 'audio')
        if overwrite_files:
            st.warning(f"⚠️ This will overwrite {len(overwrite_files)} audio file(s)")
        
        col1, col2 = st.columns(2)
        if col1.button("✅ Confirm Generate All", key=f"{pdf_stem}_confirm_audio_all_btn", use_container_width=True):
            with st.spinner("Generating audio (versioned) for all pages..."):
                client = ElevenLabs(api_key=os.environ.get("ELEVENLABS_API_KEY"))
                for page_dir in page_dirs:
                    en_source = get_latest_version_path(page_dir, 'en_text') or page_dir / 'final_text_en.txt'
                    hi_source = get_latest_version_path(page_dir, 'hi_text') or page_dir / 'final_text_hi.txt'
                    # English audio
                    if en_source and en_source.exists():
                        temp_en_audio = page_dir / 'temp_gen_en_audio.mp3'
                        generate_mp3(client, en_source.read_text(), "7tRwuZTD1EWi6nydVerp", "eleven_flash_v2_5", temp_en_audio)
                        if temp_en_audio.exists():
                            create_new_version(page_dir, 'en_audio', str(temp_en_audio), model='eleven_flash_v2_5')
                            temp_en_audio.unlink(missing_ok=True)
                    # Hindi audio
                    if hi_source and hi_source.exists():
                        temp_hi_audio = page_dir / 'temp_gen_hi_audio.mp3'
                        generate_mp3(client, hi_source.read_text(), "trxRCYtDC6qFREKq6Ek2", "eleven_flash_v2_5", temp_hi_audio)
                        if temp_hi_audio.exists():
                            create_new_version(page_dir, 'hi_audio', str(temp_hi_audio), model='eleven_flash_v2_5')
                            temp_hi_audio.unlink(missing_ok=True)
            st.session_state[confirm_key] = False
            st.success("✅ Audio generation complete!")
            st.rerun()
        if col2.button("❌ Cancel", key=f"{pdf_stem}_cancel_audio_all_btn", use_container_width=True):
            st.session_state[confirm_key] = False
            st.rerun()
    else:
        has_audio = any((p / 'final_text_en.mp3').exists() for p in page_dirs)
        button_label = "Generate All Audio" if not has_audio else "Re-generate All Audio"
        if st.button(button_label, key=f"{pdf_stem}_audio_all_btn", use_container_width=True):
            overwrite_files = get_overwrite_files(pdf_stem, 'audio')
            if overwrite_files:
                st.session_state[confirm_key] = True
                st.rerun()
            else:
                with st.spinner("Generating audio (versioned) for all pages..."):
                    client = ElevenLabs(api_key=os.environ.get("ELEVENLABS_API_KEY"))
                    for page_dir in page_dirs:
                        en_source = get_latest_version_path(page_dir, 'en_text') or page_dir / 'final_text_en.txt'
                        hi_source = get_latest_version_path(page_dir, 'hi_text') or page_dir / 'final_text_hi.txt'
                        if en_source and en_source.exists():
                            temp_en_audio = page_dir / 'temp_gen_en_audio.mp3'
                            generate_mp3(client, en_source.read_text(), "7tRwuZTD1EWi6nydVerp", "eleven_flash_v2_5", temp_en_audio)
                            if temp_en_audio.exists():
                                create_new_version(page_dir, 'en_audio', str(temp_en_audio), model='eleven_flash_v2_5')
                                temp_en_audio.unlink(missing_ok=True)
                        if hi_source and hi_source.exists():
                            temp_hi_audio = page_dir / 'temp_gen_hi_audio.mp3'
                            generate_mp3(client, hi_source.read_text(), "trxRCYtDC6qFREKq6Ek2", "eleven_flash_v2_5", temp_hi_audio)
                            if temp_hi_audio.exists():
                                create_new_version(page_dir, 'hi_audio', str(temp_hi_audio), model='eleven_flash_v2_5')
                                temp_hi_audio.unlink(missing_ok=True)
                st.success("✅ Audio generation complete!")
                st.rerun()


# ============================================================================
# STAGE 5: VIDEO GENERATION
# ============================================================================

def render_video_generation_stage(pdf_stem: str):
    """Render the video generation stage UI for batch processing."""
    from utils.versioning import get_latest_version_path, get_version_count, fast_forward_version
    
    st.subheader("Step 5: Generate Videos")
    st.write("Create animated videos and combine with audio")
    
    page_dirs = get_page_directories(pdf_stem)
    
    if not page_dirs:
        st.info("ℹ️ Complete Step 1 (Extract Content) first")
        return
    
    # Check if images exist
    has_images = any((p / 'image_to_use.png').exists() or get_latest_version_path(p, 'image') for p in page_dirs)
    if not has_images:
        st.info("ℹ️ No images found. Complete Step 1 (Extract Content) first")
        return
    
    st.divider()
    
    # --- Image Caption Generation ---
    st.subheader("Image Caption Generation")
    st.write("Generate AI captions for images to enhance video prompts")
    
    # Check which pages have captions
    pages_with_captions = []
    pages_without_captions = []
    for page_dir in page_dirs:
        caption_file = page_dir / 'image_caption.txt'
        if caption_file.exists():
            pages_with_captions.append(page_dir)
        else:
            pages_without_captions.append(page_dir)
    
    if pages_with_captions:
        st.success(f"✅ {len(pages_with_captions)} page(s) have captions")
    if pages_without_captions:
        st.info(f"📊 {len(pages_without_captions)} page(s) need captions")
    
    # Caption generation mode
    col1, col2 = st.columns([2, 1])
    with col1:
        caption_mode = st.radio(
            "Caption Mode",
            options=["Auto Caption", "Ask Question"],
            key=f"{pdf_stem}_caption_mode",
            horizontal=True,
            help="Auto Caption: AI describes the image\nAsk Question: Ask specific questions about the image"
        )
    
    with col2:
        use_auto_caption = caption_mode == "Auto Caption"
    
    # Question input (only shown if Ask Question mode)
    caption_question = None
    if not use_auto_caption:
        caption_question = st.text_input(
            "Question to ask about images",
            value="What is happening in this image?",
            key=f"{pdf_stem}_caption_question",
            help="This question will be asked about each image"
        )
    
    # Caption generation buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button(
            f"Generate Captions for All ({len(page_dirs)})",
            key=f"{pdf_stem}_gen_all_captions",
            use_container_width=True
        ):
            from generate_image_captions import batch_generate_captions
            from utils.logger import log_user_action, log_api_call
            
            log_user_action("GENERATE_ALL_CAPTIONS", pdf_stem, {
                "pages": len(page_dirs),
                "mode": caption_mode,
                "question": caption_question
            })
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            results = {}
            success_count = 0
            
            for idx, page_dir in enumerate(page_dirs):
                status_text.text(f"Generating caption for {page_dir.name}... ({idx+1}/{len(page_dirs)})")
                
                image_path = get_latest_version_path(page_dir, 'image')
                if not image_path:
                    image_path = page_dir / 'image_to_use.png'
                
                if image_path and image_path.exists():
                    from generate_image_captions import generate_image_caption
                    
                    caption = generate_image_caption(
                        image_path,
                        question=caption_question,
                        use_caption_mode=use_auto_caption
                    )
                    
                    if caption:
                        caption_file = page_dir / 'image_caption.txt'
                        caption_file.write_text(caption, encoding='utf-8')
                        results[page_dir.name] = caption
                        success_count += 1
                        log_api_call("Replicate", "blip-2", 0, success=True)
                    else:
                        log_api_call("Replicate", "blip-2", 0, success=False)
                
                progress_bar.progress((idx + 1) / len(page_dirs))
            
            progress_bar.empty()
            status_text.empty()
            
            if success_count > 0:
                st.success(f"✅ Generated {success_count} captions!")
                st.rerun()
            else:
                st.error("❌ Failed to generate captions")
    
    with col2:
        if st.button(
            f"Generate Missing ({len(pages_without_captions)})",
            key=f"{pdf_stem}_gen_missing_captions",
            use_container_width=True,
            disabled=(len(pages_without_captions) == 0)
        ):
            from generate_image_captions import batch_generate_captions
            from utils.logger import log_user_action, log_api_call
            
            log_user_action("GENERATE_MISSING_CAPTIONS", pdf_stem, {
                "pages": len(pages_without_captions),
                "mode": caption_mode,
                "question": caption_question
            })
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            success_count = 0
            
            for idx, page_dir in enumerate(pages_without_captions):
                status_text.text(f"Generating caption for {page_dir.name}... ({idx+1}/{len(pages_without_captions)})")
                
                image_path = get_latest_version_path(page_dir, 'image')
                if not image_path:
                    image_path = page_dir / 'image_to_use.png'
                
                if image_path and image_path.exists():
                    from generate_image_captions import generate_image_caption
                    
                    caption = generate_image_caption(
                        image_path,
                        question=caption_question,
                        use_caption_mode=use_auto_caption
                    )
                    
                    if caption:
                        caption_file = page_dir / 'image_caption.txt'
                        caption_file.write_text(caption, encoding='utf-8')
                        success_count += 1
                        log_api_call("Replicate", "blip-2", 0, success=True)
                    else:
                        log_api_call("Replicate", "blip-2", 0, success=False)
                
                progress_bar.progress((idx + 1) / len(pages_without_captions))
            
            progress_bar.empty()
            status_text.empty()
            
            if success_count > 0:
                st.success(f"✅ Generated {success_count} captions!")
                st.rerun()
            else:
                st.error("❌ Failed to generate captions")
    
    with col3:
        if st.button(
            "View All Captions",
            key=f"{pdf_stem}_view_captions",
            use_container_width=True,
            disabled=(len(pages_with_captions) == 0)
        ):
            st.session_state[f'{pdf_stem}_show_captions'] = not st.session_state.get(f'{pdf_stem}_show_captions', False)
    
    # Display captions if toggled
    if st.session_state.get(f'{pdf_stem}_show_captions', False):
        st.markdown("### Generated Captions")
        for page_dir in sorted(page_dirs, key=lambda p: p.name):
            caption_file = page_dir / 'image_caption.txt'
            if caption_file.exists():
                caption = caption_file.read_text(encoding='utf-8')
                with st.expander(f"📄 {page_dir.name}", expanded=False):
                    st.write(caption)
                    # Show image
                    image_path = get_latest_version_path(page_dir, 'image')
                    if not image_path:
                        image_path = page_dir / 'image_to_use.png'
                    if image_path and image_path.exists():
                        st.image(str(image_path), width=300)
    
    st.divider()
    
    # --- Batch Image-to-Video Generation ---
    st.subheader("Batch Image-to-Video Generation")
    
    # Count pages with images but no videos
    pages_needing_video = []
    pages_already_queued = []
    for page_dir in page_dirs:
        image_path = get_latest_version_path(page_dir, 'image')
        if not image_path:
            image_path = page_dir / 'image_to_use.png'
        
        if image_path and image_path.exists():
            video_path = get_latest_version_path(page_dir, 'image_video')
            if not video_path or not video_path.exists():
                pages_needing_video.append(page_dir)
                
                # Check if already queued
                queued_prompts = list(page_dir.glob('image_to_video_prompt_for_v*.txt'))
                if queued_prompts:
                    pages_already_queued.append(page_dir)
    
    # Display status with queue information
    if pages_needing_video:
        status_parts = [f"📊 {len(pages_needing_video)} page(s) need animated videos"]
        if pages_already_queued:
            status_parts.append(f"({len(pages_already_queued)} already queued)")
        st.info(" ".join(status_parts))
    else:
        st.success(f"✅ All {len(page_dirs)} pages have animated videos")
    
    # Default prompt
    default_prompt = "Ultra high-definition, camera slowly zooms out then zooms in, subtle depth"
    
    batch_prompt = st.text_area(
        "Motion Prompt (for all pages)",
        value=default_prompt,
        height=80,
        key=f"{pdf_stem}_batch_video_prompt",
        help="This prompt will be used for all pages"
    )
    
    # Caption enhancement options
    col1, col2 = st.columns([2, 1])
    
    with col1:
        use_captions_in_prompt = st.checkbox(
            "Enhance prompts with AI-generated captions",
            value=False,
            key=f"{pdf_stem}_use_captions",
            help="If enabled, will prepend the image caption to the motion prompt for more contextual animations"
        )
    
    with col2:
        if st.button(
            "AI Enhance Prompts",
            key=f"{pdf_stem}_enhance_all_prompts",
            use_container_width=True,
            disabled=(len(pages_with_captions) == 0),
            help="Create generic, visually exciting prompts (no character names - video model doesn't recognize them)"
        ):
            from enhance_video_prompt import batch_enhance_prompts
            from utils.logger import log_user_action, log_api_call
            
            log_user_action("ENHANCE_ALL_PROMPTS", pdf_stem, {"pages": len(pages_with_captions)})
            
            with st.spinner("Creating generic, visually exciting prompts for all pages..."):
                enhanced_prompts = batch_enhance_prompts(page_dirs, pdf_stem)
                
                success_count = sum(1 for v in enhanced_prompts.values() if v)
                
                # Save enhanced prompts
                for page_dir, enhanced_prompt in enhanced_prompts.items():
                    if enhanced_prompt:
                        prompt_file = page_dirs[next(i for i, p in enumerate(page_dirs) if p.name == page_dir)] / 'enhanced_video_prompt.txt'
                        prompt_file.write_text(enhanced_prompt, encoding='utf-8')
                        log_api_call("Gemini", "gemini-2.0-flash-exp", 0, success=True)
                
                if success_count > 0:
                    st.success(f"✅ Enhanced {success_count} prompts!")
                    st.info("Enhanced prompts saved and ready to use")
                    
                    # Set all text area session states to the enhanced prompts
                    for page_dir in page_dirs:
                        enhanced_file = page_dir / 'enhanced_video_prompt.txt'
                        if enhanced_file.exists():
                            text_area_key = f"img_video_prompt_{page_dir.name}"
                            enhanced_prompt = enhanced_file.read_text(encoding='utf-8').strip()
                            st.session_state[text_area_key] = enhanced_prompt
                    
                    st.rerun()
    
    if use_captions_in_prompt and len(pages_with_captions) == 0:
        st.warning("⚠️ No captions generated yet. Generate captions first to use this option.")
    
    # Show enhanced prompts if they exist
    enhanced_count = sum(1 for p in page_dirs if (p / 'enhanced_video_prompt.txt').exists())
    if enhanced_count > 0:
        with st.expander(f"View {enhanced_count} Enhanced Prompt(s)", expanded=False):
            for page_dir in sorted(page_dirs, key=lambda p: p.name):
                enhanced_file = page_dir / 'enhanced_video_prompt.txt'
                if enhanced_file.exists():
                    enhanced_prompt = enhanced_file.read_text(encoding='utf-8')
                    st.markdown(f"**{page_dir.name}:** {enhanced_prompt}")
    
    # Execution mode selection
    video_gen_mode = st.radio(
        "Execution Mode",
        options=["Execute Now", "Queue for Later"],
        index=1,  # Default to "Queue for Later"
        key=f"{pdf_stem}_video_gen_mode",
        horizontal=True,
        help="Execute Now: Process immediately using Replicate API\nQueue for Later: Save prompts for background processing"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Show queue count in button label
        if video_gen_mode == "Execute Now":
            button_label = f"🎬 Generate Videos for All Pages ({len(page_dirs)})"
        else:
            if pages_already_queued:
                button_label = f"Queue Videos for All Pages ({len(page_dirs)}) - {len(pages_already_queued)} queued"
            else:
                button_label = f"Queue Videos for All Pages ({len(page_dirs)})"
        
        if st.button(
            button_label,
            key=f"{pdf_stem}_batch_gen_videos",
            use_container_width=True,
            disabled=(not batch_prompt)
        ):
            if batch_prompt:
                if video_gen_mode == "Queue for Later":
                    # Queue prompts for all pages
                    from utils.queue_manager import queue_image_to_video_prompt
                    from utils.logger import log_user_action
                    
                    log_user_action("QUEUE_BATCH_IMAGE_VIDEOS", pdf_stem, {"pages": len(page_dirs), "prompt": batch_prompt})
                    
                    queued_count = 0
                    for page_dir in page_dirs:
                        # Get current image version
                        image_version = get_version_count(page_dir, 'image')
                        video_version = get_version_count(page_dir, 'image_video')
                        target_version = video_version + 1
                        
                        # Build prompt with optional caption/enhanced prompt
                        final_prompt = batch_prompt
                        if use_captions_in_prompt:
                            enhanced_file = page_dir / 'enhanced_video_prompt.txt'
                            caption_file = page_dir / 'image_caption.txt'
                            
                            if enhanced_file.exists():
                                # Use enhanced prompt directly (it's already complete)
                                final_prompt = enhanced_file.read_text(encoding='utf-8').strip()
                            elif caption_file.exists():
                                # Fallback to caption + batch prompt
                                caption = caption_file.read_text(encoding='utf-8').strip()
                                final_prompt = f"{caption}. {batch_prompt}"
                        
                        try:
                            queue_image_to_video_prompt(page_dir, final_prompt, target_version)
                            queued_count += 1
                        except Exception as e:
                            st.warning(f"❌ Failed to queue {page_dir.name}: {str(e)}")
                    
                    st.success(f"✅ Queued {queued_count} video generation tasks!")
                    st.info(f"Prompts saved as `image_to_video_prompt_for_v*.txt`")
                    st.caption("Background service will process these when ready")
                else:
                    # Execute immediately
                    from generate_image_videos import generate_video_from_image
                    from utils.versioning import create_new_version
                    from utils.logger import log_user_action, log_api_call, log_file_operation
                    
                    log_user_action("BATCH_GENERATE_IMAGE_VIDEOS", pdf_stem, {"pages": len(page_dirs), "prompt": batch_prompt})
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    success_count = 0
                    fail_count = 0
                    
                    for idx, page_dir in enumerate(page_dirs):
                        status_text.text(f"Processing {page_dir.name}... ({idx+1}/{len(page_dirs)})")
                        
                        # Get image
                        image_path = get_latest_version_path(page_dir, 'image')
                        if not image_path:
                            image_path = page_dir / 'image_to_use.png'
                        
                        if not image_path or not image_path.exists():
                            fail_count += 1
                            continue
                        
                        # Build prompt with optional caption/enhanced prompt
                        final_prompt = batch_prompt
                        if use_captions_in_prompt:
                            enhanced_file = page_dir / 'enhanced_video_prompt.txt'
                            caption_file = page_dir / 'image_caption.txt'
                            
                            if enhanced_file.exists():
                                # Use enhanced prompt directly (it's already complete)
                                final_prompt = enhanced_file.read_text(encoding='utf-8').strip()
                            elif caption_file.exists():
                                # Fallback to caption + batch prompt
                                caption = caption_file.read_text(encoding='utf-8').strip()
                                final_prompt = f"{caption}. {batch_prompt}"
                        
                        try:
                            temp_output = page_dir / 'temp_batch_image_video.mp4'
                            
                            success = generate_video_from_image(
                                image_path,
                                final_prompt,
                                temp_output,
                                num_frames=81,
                                aspect_ratio="16:9",
                                frames_per_second=24,
                                sample_shift=5.0
                            )
                            
                            if success and temp_output.exists():
                                create_new_version(page_dir, 'image_video', str(temp_output), model='wan-video/wan-2.2-i2v-fast')
                                temp_output.unlink()
                                log_api_call("Replicate", "wan-video/wan-2.2-i2v-fast", len(batch_prompt), success=True)
                                log_file_operation(f"batch_gen_video_{page_dir.name}", page_dir, success=True)
                                success_count += 1
                            else:
                                log_api_call("Replicate", "wan-video/wan-2.2-i2v-fast", len(batch_prompt), success=False)
                                fail_count += 1
                        
                        except Exception as e:
                            st.warning(f"❌ Failed for {page_dir.name}: {str(e)}")
                            log_api_call("Replicate", "wan-video/wan-2.2-i2v-fast", len(batch_prompt), success=False)
                            fail_count += 1
                        
                        progress_bar.progress((idx + 1) / len(page_dirs))
                    
                    progress_bar.empty()
                    status_text.empty()
                    
                    if success_count > 0:
                        st.success(f"✅ Generated {success_count} videos successfully!")
                    if fail_count > 0:
                        st.warning(f"⚠️ {fail_count} videos failed")
                    
                    st.rerun()
    
    with col2:
        # Show queue count for missing videos
        if video_gen_mode == "Execute Now":
            button_label_missing = f"🎬 Generate Only Missing Videos ({len(pages_needing_video)})"
        else:
            if pages_already_queued:
                button_label_missing = f"Queue Only Missing Videos ({len(pages_needing_video)}) - {len(pages_already_queued)} queued"
            else:
                button_label_missing = f"Queue Only Missing Videos ({len(pages_needing_video)})"
        
        if st.button(
            button_label_missing,
            key=f"{pdf_stem}_batch_gen_missing_videos",
            use_container_width=True,
            disabled=(not batch_prompt or len(pages_needing_video) == 0)
        ):
            if batch_prompt and pages_needing_video:
                if video_gen_mode == "Queue for Later":
                    # Queue prompts for missing pages only
                    from utils.queue_manager import queue_image_to_video_prompt
                    from utils.logger import log_user_action
                    
                    log_user_action("QUEUE_MISSING_IMAGE_VIDEOS", pdf_stem, {"pages": len(pages_needing_video), "prompt": batch_prompt})
                    
                    queued_count = 0
                    for page_dir in pages_needing_video:
                        video_version = get_version_count(page_dir, 'image_video')
                        target_version = video_version + 1
                        
                        # Build prompt with optional caption/enhanced prompt
                        final_prompt = batch_prompt
                        if use_captions_in_prompt:
                            enhanced_file = page_dir / 'enhanced_video_prompt.txt'
                            caption_file = page_dir / 'image_caption.txt'
                            
                            if enhanced_file.exists():
                                # Use enhanced prompt directly (it's already complete)
                                final_prompt = enhanced_file.read_text(encoding='utf-8').strip()
                            elif caption_file.exists():
                                # Fallback to caption + batch prompt
                                caption = caption_file.read_text(encoding='utf-8').strip()
                                final_prompt = f"{caption}. {batch_prompt}"
                        
                        try:
                            queue_image_to_video_prompt(page_dir, final_prompt, target_version)
                            queued_count += 1
                        except Exception as e:
                            st.warning(f"❌ Failed to queue {page_dir.name}: {str(e)}")
                    
                    st.success(f"✅ Queued {queued_count} video generation tasks!")
                    st.info(f"Prompts saved as `image_to_video_prompt_for_v*.txt`")
                    st.caption("Background service will process these when ready")
                else:
                    # Execute immediately
                    from generate_image_videos import generate_video_from_image
                    from utils.versioning import create_new_version
                    from utils.logger import log_user_action, log_api_call, log_file_operation
                    
                    log_user_action("BATCH_GENERATE_MISSING_IMAGE_VIDEOS", pdf_stem, {"pages": len(pages_needing_video), "prompt": batch_prompt})
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    success_count = 0
                    fail_count = 0
                    
                    for idx, page_dir in enumerate(pages_needing_video):
                        status_text.text(f"Processing {page_dir.name}... ({idx+1}/{len(pages_needing_video)})")
                        
                        image_path = get_latest_version_path(page_dir, 'image')
                        if not image_path:
                            image_path = page_dir / 'image_to_use.png'
                        
                        if not image_path or not image_path.exists():
                            fail_count += 1
                            continue
                        
                        # Build prompt with optional caption/enhanced prompt
                        final_prompt = batch_prompt
                        if use_captions_in_prompt:
                            enhanced_file = page_dir / 'enhanced_video_prompt.txt'
                            caption_file = page_dir / 'image_caption.txt'
                            
                            if enhanced_file.exists():
                                # Use enhanced prompt directly (it's already complete)
                                final_prompt = enhanced_file.read_text(encoding='utf-8').strip()
                            elif caption_file.exists():
                                # Fallback to caption + batch prompt
                                caption = caption_file.read_text(encoding='utf-8').strip()
                                final_prompt = f"{caption}. {batch_prompt}"
                        
                        try:
                            temp_output = page_dir / 'temp_batch_image_video.mp4'
                            
                            success = generate_video_from_image(
                                image_path,
                                final_prompt,
                                temp_output,
                                num_frames=81,
                                aspect_ratio="16:9",
                                frames_per_second=24,
                                sample_shift=5.0
                            )
                            
                            if success and temp_output.exists():
                                create_new_version(page_dir, 'image_video', temp_output, model='wan-video/wan-2.2-i2v-fast')
                                temp_output.unlink()
                                log_api_call("Replicate", "wan-video/wan-2.2-i2v-fast", len(batch_prompt), success=True)
                                log_file_operation(f"batch_gen_missing_video_{page_dir.name}", page_dir, success=True)
                                success_count += 1
                            else:
                                log_api_call("Replicate", "wan-video/wan-2.2-i2v-fast", len(batch_prompt), success=False)
                                fail_count += 1
                        
                        except Exception as e:
                            st.warning(f"❌ Failed for {page_dir.name}: {str(e)}")
                            log_api_call("Replicate", "wan-video/wan-2.2-i2v-fast", len(batch_prompt), success=False)
                            fail_count += 1
                        
                        progress_bar.progress((idx + 1) / len(pages_needing_video))
                    
                    progress_bar.empty()
                    status_text.empty()
                    
                    if success_count > 0:
                        st.success(f"✅ Generated {success_count} videos successfully!")
                    if fail_count > 0:
                        st.warning(f"⚠️ {fail_count} videos failed")
                    
                    st.rerun()
    
    st.divider()
    
    # --- Batch Page Video Generation (Animated Video + Audio) ---
    st.subheader("Batch Page Video Generation (Animated + Audio)")
    
    # Count pages with videos and audio
    pages_ready_for_final = []
    for page_dir in page_dirs:
        image_video_path = get_latest_version_path(page_dir, 'image_video')
        en_audio_path = get_latest_version_path(page_dir, 'en_audio')
        hi_audio_path = get_latest_version_path(page_dir, 'hi_audio')
        
        if image_video_path and image_video_path.exists() and (en_audio_path or hi_audio_path):
            pages_ready_for_final.append(page_dir)
    
    if pages_ready_for_final:
        st.info(f"{len(pages_ready_for_final)} page(s) ready for final video generation")
    else:
        st.warning("⚠️ No pages have both animated videos and audio yet")
    
    expected_version = get_expected_version_for_pdf(pdf_stem)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(
            f"🎬 Generate All EN Page Videos (v{expected_version})",
            key=f"{pdf_stem}_batch_gen_en_page_videos",
            use_container_width=True,
            disabled=(len(pages_ready_for_final) == 0)
        ):
            from moviepy.editor import VideoFileClip, AudioFileClip
            from utils.logger import log_user_action, log_file_operation
            
            log_user_action("BATCH_GENERATE_EN_PAGE_VIDEOS", pdf_stem, {"pages": len(pages_ready_for_final), "version": expected_version})
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            success_count = 0
            fail_count = 0
            
            for idx, page_dir in enumerate(pages_ready_for_final):
                status_text.text(f"Processing {page_dir.name}... ({idx+1}/{len(pages_ready_for_final)})")
                
                image_video_path = get_latest_version_path(page_dir, 'image_video')
                en_audio_path = get_latest_version_path(page_dir, 'en_audio')
                
                if not en_audio_path or not en_audio_path.exists():
                    fail_count += 1
                    continue
                
                try:
                    video_clip = VideoFileClip(str(image_video_path))
                    audio_clip = AudioFileClip(str(en_audio_path))
                    
                    audio_duration = audio_clip.duration
                    video_duration = video_clip.duration
                    
                    # Adjust video to match audio
                    if video_duration < audio_duration:
                        loops_needed = int(audio_duration / video_duration) + 1
                        video_clip = concatenate_videoclips([video_clip] * loops_needed).subclip(0, audio_duration)
                    elif video_duration > audio_duration:
                        video_clip = video_clip.subclip(0, audio_duration)
                    
                    final_clip = video_clip.set_audio(audio_clip)
                    
                    en_video_path = page_dir / f'page_video_en_v{expected_version}.mp4'
                    final_clip.write_videofile(
                        str(en_video_path),
                        fps=24,
                        codec='libx264',
                        audio_codec='aac',
                        logger=None
                    )
                    
                    final_clip.close()
                    video_clip.close()
                    audio_clip.close()
                    
                    log_file_operation(f"batch_gen_en_page_video_{page_dir.name}_v{expected_version}", page_dir, success=True)
                    success_count += 1
                
                except Exception as e:
                    st.warning(f"❌ Failed for {page_dir.name}: {str(e)}")
                    fail_count += 1
                
                progress_bar.progress((idx + 1) / len(pages_ready_for_final))
            
            progress_bar.empty()
            status_text.empty()
            
            if success_count > 0:
                st.success(f"✅ Generated {success_count} EN page videos!")
            if fail_count > 0:
                st.warning(f"⚠️ {fail_count} videos failed")
            
            st.rerun()
    
    with col2:
        if st.button(
            f"🎬 Generate All HI Page Videos (v{expected_version})",
            key=f"{pdf_stem}_batch_gen_hi_page_videos",
            use_container_width=True,
            disabled=(len(pages_ready_for_final) == 0)
        ):
            from moviepy.editor import VideoFileClip, AudioFileClip
            from utils.logger import log_user_action, log_file_operation
            
            log_user_action("BATCH_GENERATE_HI_PAGE_VIDEOS", pdf_stem, {"pages": len(pages_ready_for_final), "version": expected_version})
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            success_count = 0
            fail_count = 0
            
            for idx, page_dir in enumerate(pages_ready_for_final):
                status_text.text(f"Processing {page_dir.name}... ({idx+1}/{len(pages_ready_for_final)})")
                
                image_video_path = get_latest_version_path(page_dir, 'image_video')
                hi_audio_path = get_latest_version_path(page_dir, 'hi_audio')
                
                if not hi_audio_path or not hi_audio_path.exists():
                    fail_count += 1
                    continue
                
                try:
                    video_clip = VideoFileClip(str(image_video_path))
                    audio_clip = AudioFileClip(str(hi_audio_path))
                    
                    audio_duration = audio_clip.duration
                    video_duration = video_clip.duration
                    
                    # Adjust video to match audio
                    if video_duration < audio_duration:
                        loops_needed = int(audio_duration / video_duration) + 1
                        video_clip = concatenate_videoclips([video_clip] * loops_needed).subclip(0, audio_duration)
                    elif video_duration > audio_duration:
                        video_clip = video_clip.subclip(0, audio_duration)
                    
                    final_clip = video_clip.set_audio(audio_clip)
                    
                    hi_video_path = page_dir / f'page_video_hi_v{expected_version}.mp4'
                    final_clip.write_videofile(
                        str(hi_video_path),
                        fps=24,
                        codec='libx264',
                        audio_codec='aac',
                        logger=None
                    )
                    
                    final_clip.close()
                    video_clip.close()
                    audio_clip.close()
                    
                    log_file_operation(f"batch_gen_hi_page_video_{page_dir.name}_v{expected_version}", page_dir, success=True)
                    success_count += 1
                
                except Exception as e:
                    st.warning(f"❌ Failed for {page_dir.name}: {str(e)}")
                    fail_count += 1
                
                progress_bar.progress((idx + 1) / len(pages_ready_for_final))
            
            progress_bar.empty()
            status_text.empty()
            
            if success_count > 0:
                st.success(f"✅ Generated {success_count} HI page videos!")
            if fail_count > 0:
                st.warning(f"⚠️ {fail_count} videos failed")
            
            st.rerun()
    
    st.divider()
    
    # --- Batch Fast Forward ---
    st.subheader("Batch Fast Forward to Latest")
    st.write("Bring all versions to the latest expected version")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button(
            f"Fast Forward All EN Text to v{expected_version}",
            key=f"{pdf_stem}_batch_ff_en_text",
            use_container_width=True
        ):
            from utils.versioning import fast_forward_version
            from utils.logger import log_user_action
            
            log_user_action("BATCH_FAST_FORWARD_EN_TEXT", pdf_stem, {"pages": len(page_dirs), "to_version": expected_version})
            
            success_count = 0
            for page_dir in page_dirs:
                if fast_forward_version(page_dir, 'en_text', expected_version):
                    success_count += 1
            
            st.success(f"Fast forwarded {success_count} EN texts to v{expected_version}")
            st.rerun()
        
        if st.button(
            f"Fast Forward All HI Text to v{expected_version}",
            key=f"{pdf_stem}_batch_ff_hi_text",
            use_container_width=True
        ):
            from utils.versioning import fast_forward_version
            from utils.logger import log_user_action
            
            log_user_action("BATCH_FAST_FORWARD_HI_TEXT", pdf_stem, {"pages": len(page_dirs), "to_version": expected_version})
            
            success_count = 0
            for page_dir in page_dirs:
                if fast_forward_version(page_dir, 'hi_text', expected_version):
                    success_count += 1
            
            st.success(f"✅ Fast forwarded {success_count} HI texts to v{expected_version}")
            st.rerun()
    
    with col2:
        if st.button(
            f"Fast Forward All EN Audio to v{expected_version}",
            key=f"{pdf_stem}_batch_ff_en_audio",
            use_container_width=True
        ):
            from utils.versioning import fast_forward_version
            from utils.logger import log_user_action
            
            log_user_action("BATCH_FAST_FORWARD_EN_AUDIO", pdf_stem, {"pages": len(page_dirs), "to_version": expected_version})
            
            success_count = 0
            for page_dir in page_dirs:
                if fast_forward_version(page_dir, 'en_audio', expected_version):
                    success_count += 1
            
            st.success(f"✅ Fast forwarded {success_count} EN audio to v{expected_version}")
            st.rerun()
        
        if st.button(
            f"Fast Forward All HI Audio to v{expected_version}",
            key=f"{pdf_stem}_batch_ff_hi_audio",
            use_container_width=True
        ):
            from utils.versioning import fast_forward_version
            from utils.logger import log_user_action
            
            log_user_action("BATCH_FAST_FORWARD_HI_AUDIO", pdf_stem, {"pages": len(page_dirs), "to_version": expected_version})
            
            success_count = 0
            for page_dir in page_dirs:
                if fast_forward_version(page_dir, 'hi_audio', expected_version):
                    success_count += 1
            
            st.success(f"✅ Fast forwarded {success_count} HI audio to v{expected_version}")
            st.rerun()
    
    with col3:
        if st.button(
            f"Fast Forward All EN Videos to v{expected_version}",
            key=f"{pdf_stem}_batch_ff_en_video",
            use_container_width=True
        ):
            from utils.versioning import fast_forward_version
            from utils.logger import log_user_action
            
            log_user_action("BATCH_FAST_FORWARD_EN_VIDEO", pdf_stem, {"pages": len(page_dirs), "to_version": expected_version})
            
            success_count = 0
            for page_dir in page_dirs:
                if fast_forward_version(page_dir, 'en_video', expected_version):
                    success_count += 1
            
            st.success(f"✅ Fast forwarded {success_count} EN videos to v{expected_version}")
            st.rerun()
        
        if st.button(
            f"Fast Forward All HI Videos to v{expected_version}",
            key=f"{pdf_stem}_batch_ff_hi_video",
            use_container_width=True
        ):
            from utils.versioning import fast_forward_version
            from utils.logger import log_user_action
            
            log_user_action("BATCH_FAST_FORWARD_HI_VIDEO", pdf_stem, {"pages": len(page_dirs), "to_version": expected_version})
            
            success_count = 0
            for page_dir in page_dirs:
                if fast_forward_version(page_dir, 'hi_video', expected_version):
                    success_count += 1
            
            st.success(f"✅ Fast forwarded {success_count} HI videos to v{expected_version}")
            st.rerun()
    
    # Master fast forward button
    st.divider()
    if st.button(
        f"⚡ FAST FORWARD EVERYTHING to v{expected_version}",
        key=f"{pdf_stem}_batch_ff_all",
        use_container_width=True,
        type="primary"
    ):
        from utils.versioning import fast_forward_version
        from utils.logger import log_user_action
        
        log_user_action("BATCH_FAST_FORWARD_ALL", pdf_stem, {"pages": len(page_dirs), "to_version": expected_version})
        
        total_ff = 0
        for page_dir in page_dirs:
            for content_type in ['en_text', 'hi_text', 'en_audio', 'hi_audio', 'en_video', 'hi_video', 'image_video']:
                if fast_forward_version(page_dir, content_type, expected_version):
                    total_ff += 1
        
        st.success(f"✅ Fast forwarded {total_ff} items across all pages to v{expected_version}")
        st.rerun()


def get_expected_version_for_pdf(pdf_stem: str) -> int:
    """Get the expected version number for a PDF based on the highest version across all pages."""
    from utils.versioning import get_version_count
    page_dirs = get_page_directories(pdf_stem)
    
    max_version = 1
    for page_dir in page_dirs:
        for content_type in ['en_text', 'hi_text', 'en_audio', 'hi_audio', 'en_video', 'hi_video', 'image_video']:
            try:
                version = get_version_count(page_dir, content_type)
                if version > max_version:
                    max_version = version
            except (KeyError, FileNotFoundError):
                # Content type doesn't exist yet, skip it
                continue
    
    return max_version


# ============================================================================
# STAGE 6: SLIDESHOW CREATION
# ============================================================================

def resize_image(image_path: Path, target_size: tuple):
    """Resize an image to target size."""
    try:
        with Image.open(image_path) as img:
            if img.size != target_size:
                resized_img = img.resize(target_size, Image.Resampling.LANCZOS)
                resized_img.save(image_path)
    except Exception as e:
        st.error(f"Failed to resize {image_path.name}: {e}")


def concatenate_page_videos(page_dirs, language: str, expected_version: int, output_path: Path):
    """Concatenate page videos (animated video + audio) into final slideshow."""
    from moviepy.editor import VideoFileClip
    
    clips = []
    FPS = 24
    
    for page_dir in page_dirs:
        video_path = page_dir / f'page_video_{language}_v{expected_version}.mp4'
        
        if not video_path.exists():
            st.warning(f"⚠️ Missing: {video_path.name}")
            continue
        
        try:
            video_clip = VideoFileClip(str(video_path))
            clips.append(video_clip)
        except Exception as e:
            st.warning(f"Failed to load {page_dir.name}: {e}")
            continue
    
    if not clips:
        raise ValueError(f"No valid {language.upper()} page videos found to concatenate")
    
    # Concatenate all page videos
    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(
        str(output_path),
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        logger=None
    )
    
    # Cleanup
    for clip in clips:
        try:
            clip.close()
        except:
            pass
    
    try:
        final.close()
    except:
        pass


def build_slideshow(page_dirs, audio_filename: str, output_path: Path):
    """Build a slideshow video from pages (legacy method: static images + audio)."""
    from utils.versioning import get_latest_version_path
    
    clips = []
    TARGET_SIZE = (994, 1935)
    FPS = 24
    
    for page_dir in page_dirs:
        img_path = page_dir / 'image_to_use.png'
        
        # Try to get versioned audio first, fallback to legacy
        if 'en' in audio_filename:
            aud_path = get_latest_version_path(page_dir, 'en_audio') or page_dir / audio_filename
        else:
            aud_path = get_latest_version_path(page_dir, 'hi_audio') or page_dir / audio_filename
        
        if not img_path.exists():
            continue
        
        # Resize image
        resize_image(img_path, TARGET_SIZE)
        
        # Get duration from audio
        duration = 3  # default
        audio_clip = None
        
        if aud_path and aud_path.exists() and aud_path.stat().st_size > 0:
            try:
                audio_clip = AudioFileClip(str(aud_path))
                duration = audio_clip.duration
            except Exception:
                pass
        
        # Create clip
        try:
            img_clip = ImageClip(str(img_path)).set_duration(duration)
            if audio_clip:
                img_clip = img_clip.set_audio(audio_clip)
            img_clip = img_clip.set_fps(FPS)
            clips.append(img_clip)
        except Exception as e:
            st.warning(f"Failed to process {page_dir.name}: {e}")
            continue
    
    if not clips:
        raise ValueError("No valid clips to create slideshow")
    
    # Concatenate and write
    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(
        str(output_path),
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        threads=2,
        temp_audiofile=str(output_path.with_suffix('.temp-audio.m4a')),
        remove_temp=True,
    )
    
    # Cleanup
    for clip in clips:
        try:
            clip.close()
        except:
            pass


def render_slideshow_stage(pdf_stem: str):
    """Render the slideshow creation stage UI."""
    from utils.versioning import get_latest_version_path
    
    st.subheader("Step 6: Create Slideshow")
    st.write("Build final English and Hindi video slideshows")
    
    extraction_dir = get_extraction_dir(pdf_stem)
    page_dirs = get_page_directories(pdf_stem)
    
    if not page_dirs:
        st.info("ℹ️ Complete Step 1 (Extract Content) first")
        return
    
    # Check if page videos exist (preferred method)
    expected_version = get_expected_version_for_pdf(pdf_stem)
    has_page_videos_en = any((p / f'page_video_en_v{expected_version}.mp4').exists() for p in page_dirs)
    has_page_videos_hi = any((p / f'page_video_hi_v{expected_version}.mp4').exists() for p in page_dirs)
    
    # Fallback: check if any page has audio (for legacy static image slideshows)
    has_audio = any(
        (p / 'final_text_en.mp3').exists() or 
        get_latest_version_path(p, 'en_audio')
        for p in page_dirs
    )
    
    if not has_page_videos_en and not has_page_videos_hi and not has_audio:
        st.info("ℹ️ Complete Step 5 (Generate Videos) first")
        return
    
    # Show method indicator
    if has_page_videos_en or has_page_videos_hi:
        st.success("✅ Ready to concatenate **animated page videos** (Step 5)")
        if has_page_videos_en:
            st.caption(f"🎬 English: {sum(1 for p in page_dirs if (p / f'page_video_en_v{expected_version}.mp4').exists())} page videos found")
        if has_page_videos_hi:
            st.caption(f"🎬 Hindi: {sum(1 for p in page_dirs if (p / f'page_video_hi_v{expected_version}.mp4').exists())} page videos found")
    else:
        st.warning("⚠️ Will use **static images + audio** (legacy method)")
        st.caption("Tip: Complete Step 5 to create animated page videos for better results")
    
    st.divider()
    
    confirm_key = f'{pdf_stem}_confirm_slideshow'
    
    if st.session_state.get(confirm_key):
        overwrite_files = get_overwrite_files(pdf_stem, 'slideshow')
        if overwrite_files:
            st.warning(f"⚠️ This will overwrite:")
            for file in overwrite_files:
                st.code(str(file), language=None)
        
        col1, col2 = st.columns(2)
        if col1.button("✅ Confirm Create", key=f"{pdf_stem}_confirm_slideshow_btn", use_container_width=True):
            with st.spinner("Creating slideshows... This may take several minutes."):
                try:
                    # Use page videos if available, otherwise fallback to static images + audio
                    if has_page_videos_en or has_page_videos_hi:
                        st.info("🎬 Using animated page videos (Step 5)")
                        
                        # English slideshow from page videos
                        if has_page_videos_en:
                            en_output = extraction_dir / 'english_slideshow.mp4'
                            concatenate_page_videos(page_dirs, 'en', expected_version, en_output)
                            st.success(f"✅ English slideshow created: {en_output.name}")
                        
                        # Hindi slideshow from page videos
                        if has_page_videos_hi:
                            hi_output = extraction_dir / 'hindi_slideshow.mp4'
                            concatenate_page_videos(page_dirs, 'hi', expected_version, hi_output)
                            st.success(f"✅ Hindi slideshow created: {hi_output.name}")
                    else:
                        st.info("📷 Using static images + audio (legacy method)")
                        
                        # English slideshow (legacy)
                        en_output = extraction_dir / 'english_slideshow.mp4'
                        build_slideshow(page_dirs, 'final_text_en.mp3', en_output)
                        st.success(f"✅ English slideshow created: {en_output.name}")
                        
                        # Hindi slideshow (legacy)
                        hi_output = extraction_dir / 'hindi_slideshow.mp4'
                        build_slideshow(page_dirs, 'final_text_hi.mp3', hi_output)
                        st.success(f"✅ Hindi slideshow created: {hi_output.name}")
                    
                except Exception as e:
                    st.error(f"❌ Failed to create slideshow: {e}")
            
            st.session_state[confirm_key] = False
            st.rerun()
        if col2.button("❌ Cancel", key=f"{pdf_stem}_cancel_slideshow_btn", use_container_width=True):
            st.session_state[confirm_key] = False
            st.rerun()
    else:
        en_slideshow = extraction_dir / 'english_slideshow.mp4'
        button_label = "🚀 Create Slideshows" if not en_slideshow.exists() else "🔄 Re-create Slideshows"
        if st.button(button_label, key=f"{pdf_stem}_slideshow_btn", use_container_width=True):
            overwrite_files = get_overwrite_files(pdf_stem, 'slideshow')
            if overwrite_files:
                st.session_state[confirm_key] = True
                st.rerun()
            else:
                with st.spinner("Creating slideshows... This may take several minutes."):
                    try:
                        # Use page videos if available, otherwise fallback to static images + audio
                        if has_page_videos_en or has_page_videos_hi:
                            st.info("🎬 Using animated page videos (Step 5)")
                            
                            # English slideshow from page videos
                            if has_page_videos_en:
                                en_output = extraction_dir / 'english_slideshow.mp4'
                                concatenate_page_videos(page_dirs, 'en', expected_version, en_output)
                                st.success(f"✅ English slideshow created")
                            
                            # Hindi slideshow from page videos
                            if has_page_videos_hi:
                                hi_output = extraction_dir / 'hindi_slideshow.mp4'
                                concatenate_page_videos(page_dirs, 'hi', expected_version, hi_output)
                                st.success(f"✅ Hindi slideshow created")
                        else:
                            st.info("📷 Using static images + audio (legacy method)")
                            
                            # English slideshow (legacy)
                            en_output = extraction_dir / 'english_slideshow.mp4'
                            build_slideshow(page_dirs, 'final_text_en.mp3', en_output)
                            st.success(f"✅ English slideshow created")
                            
                            # Hindi slideshow (legacy)
                            hi_output = extraction_dir / 'hindi_slideshow.mp4'
                            build_slideshow(page_dirs, 'final_text_hi.mp3', hi_output)
                            st.success(f"✅ Hindi slideshow created")
                        
                    except Exception as e:
                        st.error(f"❌ Failed to create slideshow: {e}")
                st.rerun()
