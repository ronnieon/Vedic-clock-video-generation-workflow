"""
Content Viewer Components
=========================
UI components for viewing extracted content, text, images, and audio.
"""

import streamlit as st
from pathlib import Path
import os
import time

from rewrite_for_kids import _call_gemini_dual as rewrite_text_for_kids
from generate_voiceovers import generate_mp3, ElevenLabs
from utils.workflow import get_page_directories, get_extraction_dir
from utils.logger import (
    log_user_action, log_api_call, log_file_operation, log_session_info
)
from utils.versioning import (
    create_new_version, get_latest_version_path, get_all_versions,
    set_as_latest, migrate_legacy_files, get_version_count, fast_forward_version,
    get_latest_version_number
)


def get_expected_version_for_pdf(pdf_stem: str) -> int:
    """Calculate the expected version for entire PDF (max across ALL pages and assets)."""
    page_dirs = get_page_directories(pdf_stem)
    max_version = 0
    
    for page_dir in page_dirs:
        en_text_v = get_latest_version_number(page_dir, 'en_text')
        hi_text_v = get_latest_version_number(page_dir, 'hi_text')
        en_audio_v = get_latest_version_number(page_dir, 'en_audio')
        hi_audio_v = get_latest_version_number(page_dir, 'hi_audio')
        en_video_v = get_latest_version_number(page_dir, 'en_video')
        hi_video_v = get_latest_version_number(page_dir, 'hi_video')
        image_v = get_latest_version_number(page_dir, 'image')
        image_video_v = get_latest_version_number(page_dir, 'image_video')
        
        page_max = max(en_text_v, hi_text_v, en_audio_v, hi_audio_v, en_video_v, hi_video_v, image_v, image_video_v)
        max_version = max(max_version, page_max)
    
    return max_version


def render_final_story_viewer(pdf_stem: str):
    """Render the final story viewer."""
    extraction_dir = get_extraction_dir(pdf_stem)
    story_file = extraction_dir / 'whole_story_cleaned.txt'
    
    if story_file.exists():
        with st.expander("View Final Story", expanded=False):
            st.text_area("Story", story_file.read_text(), height=300, key=f"{pdf_stem}_story_view")


def render_slideshow_viewer(pdf_stem: str):
    """Render the slideshow video viewer."""
    extraction_dir = get_extraction_dir(pdf_stem)
    en_slideshow = extraction_dir / 'english_slideshow.mp4'
    hi_slideshow = extraction_dir / 'hindi_slideshow.mp4'
    
    if en_slideshow.exists() or hi_slideshow.exists():
        with st.expander("View Slideshows", expanded=False):
            if en_slideshow.exists():
                st.subheader("English Slideshow")
                st.video(str(en_slideshow))
            
            if hi_slideshow.exists():
                st.subheader("Hindi Slideshow")
                st.video(str(hi_slideshow))


def render_page_content(page_dir: Path, pdf_stem: str):
    """Render content for a single page."""
    st.subheader(page_dir.name)
    
    # Migrate legacy files to versioning system
    migrate_legacy_files(page_dir)
    
    # --- Text Display ---
    text_col1, text_col2, text_col3 = st.columns(3)
    
    raw_text_file = page_dir / 'text.txt'
    if raw_text_file.exists():
        text_col1.text_area("Raw Text", raw_text_file.read_text(), height=200, 
                           key=f"{pdf_stem}_raw_{page_dir.name}")
    
    clean_text_file = page_dir / 'clean_text.txt'
    if clean_text_file.exists():
        text_col2.text_area("Cleaned Text", clean_text_file.read_text(), height=200, 
                           key=f"{pdf_stem}_clean_{page_dir.name}")
    
    # Use versioned paths
    en_final_text_path = get_latest_version_path(page_dir, 'en_text')
    hi_final_text_path = get_latest_version_path(page_dir, 'hi_text')
    
    with text_col3:
        if en_final_text_path and en_final_text_path.exists():
            en_version_count = get_version_count(page_dir, 'en_text')
            expected_version = get_expected_version_for_pdf(pdf_stem)
            
            # Show version status
            if en_version_count < expected_version:
                st.caption(f"📝 Kid-Friendly EN (v{en_version_count}) ⚠️ Needs v{expected_version}")
            else:
                st.caption(f"📝 Kid-Friendly EN (v{en_version_count}) 🟢 Latest")
            
            # Editable text area (include version in key to force refresh after new version)
            original_en_text = en_final_text_path.read_text()
            edited_en_text = st.text_area("Kid-Friendly EN", original_en_text, height=100, 
                        key=f"{pdf_stem}_en_final_{page_dir.name}_v{en_version_count}", label_visibility="collapsed")
            
            # Show save button if text was modified
            if edited_en_text != original_en_text:
                if st.button(f"💾 Save Changes as v{en_version_count + 1}", key=f"save_en_text_{page_dir.name}", use_container_width=True, type="primary"):
                    log_user_action("SAVE_EN_TEXT_EDIT", pdf_stem, {"page": page_dir.name, "new_version": en_version_count + 1})
                    try:
                        # Create new version directly from edited text content
                        create_new_version(page_dir, 'en_text', edited_en_text, model='manual-edit')
                        
                        log_file_operation(f"edit_en_text_{page_dir.name}_v{en_version_count + 1}", page_dir, success=True)
                        st.success(f"✅ Saved as v{en_version_count + 1}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Save failed: {str(e)}")
            
            # Always show fast forward button (disabled if at latest)
            is_at_latest = (en_version_count >= expected_version)
            button_label = f"⏩ Fast Forward to v{expected_version}" if not is_at_latest else f"⏩ At Latest (v{expected_version})"
            
            if st.button(button_label, key=f"ff_en_text_{page_dir.name}", use_container_width=True, disabled=is_at_latest):
                log_user_action("FAST_FORWARD_EN_TEXT", pdf_stem, {"page": page_dir.name, "from": en_version_count, "to": expected_version})
                if fast_forward_version(page_dir, 'en_text', expected_version):
                    st.success(f"✅ Fast forwarded EN text to v{expected_version}")
                    st.rerun()
                else:
                    st.error("❌ Fast forward failed")
            
            # Show version history
            if en_version_count > 1:
                with st.expander(f"View {en_version_count} version(s)", expanded=False):
                    en_versions = get_all_versions(page_dir, 'en_text')
                    for i, ver in enumerate(en_versions, 1):
                        is_latest = (i == en_version_count)
                        badge = " 🟢 Latest" if is_latest else ""
                        st.caption(f"**v{i}**{badge} - {ver['created'][:19]} - {ver.get('model', 'unknown')}")
                        ver_path = page_dir / ver['file']
                        if ver_path.exists():
                            st.text(ver_path.read_text()[:150] + "...")
                            if not is_latest and st.button(f"↩️ Restore v{i}", key=f"restore_en_{page_dir.name}_v{i}"):
                                set_as_latest(page_dir, 'en_text', i)
                                st.success(f"Restored v{i} as latest")
                                st.rerun()
                        st.divider()
        
        if hi_final_text_path and hi_final_text_path.exists():
            hi_version_count = get_version_count(page_dir, 'hi_text')
            expected_version = get_expected_version_for_pdf(pdf_stem)
            
            # Show version status
            if hi_version_count < expected_version:
                st.caption(f"📝 Kid-Friendly HI (v{hi_version_count}) ⚠️ Needs v{expected_version}")
            else:
                st.caption(f"📝 Kid-Friendly HI (v{hi_version_count}) 🟢 Latest")
            
            # Editable text area (include version in key to force refresh after new version)
            original_hi_text = hi_final_text_path.read_text()
            edited_hi_text = st.text_area("Kid-Friendly HI", original_hi_text, height=100, 
                        key=f"{pdf_stem}_hi_final_{page_dir.name}_v{hi_version_count}", label_visibility="collapsed")
            
            # Show save button if text was modified
            if edited_hi_text != original_hi_text:
                if st.button(f"💾 Save Changes as v{hi_version_count + 1}", key=f"save_hi_text_{page_dir.name}", use_container_width=True, type="primary"):
                    log_user_action("SAVE_HI_TEXT_EDIT", pdf_stem, {"page": page_dir.name, "new_version": hi_version_count + 1})
                    try:
                        # Create new version directly from edited text content
                        create_new_version(page_dir, 'hi_text', edited_hi_text, model='manual-edit')
                        
                        log_file_operation(f"edit_hi_text_{page_dir.name}_v{hi_version_count + 1}", page_dir, success=True)
                        st.success(f"✅ Saved as v{hi_version_count + 1}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Save failed: {str(e)}")
            
            # Always show fast forward button (disabled if at latest)
            is_at_latest = (hi_version_count >= expected_version)
            button_label = f"⏩ Fast Forward to v{expected_version}" if not is_at_latest else f"⏩ At Latest (v{expected_version})"
            
            if st.button(button_label, key=f"ff_hi_text_{page_dir.name}", use_container_width=True, disabled=is_at_latest):
                log_user_action("FAST_FORWARD_HI_TEXT", pdf_stem, {"page": page_dir.name, "from": hi_version_count, "to": expected_version})
                if fast_forward_version(page_dir, 'hi_text', expected_version):
                    st.success(f"✅ Fast forwarded HI text to v{expected_version}")
                    st.rerun()
                else:
                    st.error("❌ Fast forward failed")
            
            # Show version history
            if hi_version_count > 1:
                with st.expander(f"View {hi_version_count} version(s)", expanded=False):
                    hi_versions = get_all_versions(page_dir, 'hi_text')
                    for i, ver in enumerate(hi_versions, 1):
                        is_latest = (i == hi_version_count)
                        badge = " 🟢 Latest" if is_latest else ""
                        st.caption(f"**v{i}**{badge} - {ver['created'][:19]} - {ver.get('model', 'unknown')}")
                        ver_path = page_dir / ver['file']
                        if ver_path.exists():
                            st.text(ver_path.read_text()[:150] + "...")
                            if not is_latest and st.button(f"↩️ Restore v{i}", key=f"restore_hi_{page_dir.name}_v{i}"):
                                set_as_latest(page_dir, 'hi_text', i)
                                st.success(f"Restored v{i} as latest")
                                st.rerun()
                        st.divider()
    
    # --- Per-Page Actions ---
    action_col1, action_col2 = st.columns(2)
    
    # Rewrite button for individual page
    if clean_text_file.exists():
        with action_col1:
            # Determine button label based on existing versions
            existing_versions = get_version_count(page_dir, 'en_text')
            if existing_versions == 0:
                label = "✏️ Create Rewrite (v1)"
            else:
                label = f"✏️ Create New Version (v{existing_versions + 1})"
            
            if st.button(label, key=f"{pdf_stem}_rewrite_{page_dir.name}", use_container_width=True):
                log_user_action("CLICK_REWRITE_PAGE", pdf_stem, {"page": page_dir.name, "new_version": existing_versions + 1})
                try:
                    with st.spinner("Creating new version..."):
                        text = clean_text_file.read_text()
                        log_api_call("Gemini", "gemini-2.5-flash", len(text), success=False)
                        
                        # Load whole story context
                        extraction_dir = get_extraction_dir(pdf_stem)
                        whole_story_file = extraction_dir / 'whole_story_cleaned.txt'
                        whole_story = None
                        if whole_story_file.exists():
                            whole_story = whole_story_file.read_text(encoding='utf-8', errors='ignore')
                        
                        # Build previous pages context
                        all_page_dirs = get_page_directories(pdf_stem)
                        current_page_index = int(page_dir.name.split('_')[1]) if '_' in page_dir.name else 0
                        previous_pages_en = []
                        
                        for prev_page_dir in all_page_dirs:
                            prev_index = int(prev_page_dir.name.split('_')[1]) if '_' in prev_page_dir.name else 0
                            if prev_index < current_page_index:
                                # Get latest EN text from previous page
                                prev_en_path = get_latest_version_path(prev_page_dir, 'en_text')
                                if prev_en_path and prev_en_path.exists():
                                    prev_en_text = prev_en_path.read_text(encoding='utf-8', errors='ignore')
                                    previous_pages_en.append(f"[Page {prev_index}] {prev_en_text}")
                        
                        prev_context = "\n\n".join(previous_pages_en) if previous_pages_en else None
                        
                        # Generate new rewritten text with context
                        en_text, hi_text = rewrite_text_for_kids(
                            'gemini-2.5-flash', 
                            text,
                            whole_story=whole_story,
                            previous_pages=prev_context
                        )
                        
                        # Create new versions (never overwrite)
                        create_new_version(page_dir, 'en_text', en_text, model='gemini-2.5-flash')
                        create_new_version(page_dir, 'hi_text', hi_text, model='gemini-2.5-flash')
                        
                        log_api_call("Gemini", "gemini-2.5-flash", len(text), success=True)
                        log_file_operation(f"rewrite_{page_dir.name}_v{existing_versions + 1}", page_dir, success=True)
                    
                    st.success(f"✅ Created v{existing_versions + 1}! Previous versions preserved.")
                    st.rerun()
                except Exception as e:
                    log_api_call("Gemini", "gemini-2.5-flash", 0, success=False)
                    st.error(f"❌ Rewrite failed: {str(e)}")
    
    # Audio generation for individual page (versioned)
    if en_final_text_path and en_final_text_path.exists():
        with action_col2:
            # Get current text version to match
            en_text_version = get_version_count(page_dir, 'en_text')
            hi_text_version = get_version_count(page_dir, 'hi_text')
            expected_audio_version = max(en_text_version, hi_text_version)
            
            # Check current audio versions
            en_audio_version = get_version_count(page_dir, 'en_audio')
            hi_audio_version = get_version_count(page_dir, 'hi_audio')
            
            # Determine button label
            if en_audio_version == 0:
                audio_label = f"🎙️ Generate Audio (v{expected_audio_version})"
            elif en_audio_version < expected_audio_version:
                audio_label = f"🎙️ Generate Audio v{expected_audio_version} (current: v{en_audio_version})"
            else:
                audio_label = f"🎙️ Create New Audio (v{expected_audio_version + 1})"
            
            if st.button(audio_label, key=f"{pdf_stem}_gen_audio_{page_dir.name}", use_container_width=True):
                log_user_action("GENERATE_AUDIO_PAGE", pdf_stem, {"page": page_dir.name, "version": expected_audio_version})
                try:
                    with st.spinner(f"Generating audio v{expected_audio_version}..."):
                        client = ElevenLabs(api_key=os.environ.get("ELEVENLABS_API_KEY"))
                        
                        # Generate EN audio
                        en_text = en_final_text_path.read_text()
                        log_api_call("ElevenLabs", "eleven_flash_v2_5", len(en_text), success=False)
                        
                        # Create temporary file then version it
                        temp_en_audio = page_dir / 'temp_audio_en.mp3'
                        generate_mp3(client, en_text, "7tRwuZTD1EWi6nydVerp", 
                                   "eleven_flash_v2_5", temp_en_audio)
                        create_new_version(page_dir, 'en_audio', str(temp_en_audio), model='eleven_flash_v2_5')
                        temp_en_audio.unlink()  # Delete temp file
                        
                        log_api_call("ElevenLabs", "eleven_flash_v2_5", len(en_text), success=True)
                        
                        # Generate HI audio if text exists
                        if hi_final_text_path and hi_final_text_path.exists():
                            hi_text = hi_final_text_path.read_text()
                            log_api_call("ElevenLabs", "eleven_flash_v2_5", len(hi_text), success=False)
                            
                            temp_hi_audio = page_dir / 'temp_audio_hi.mp3'
                            generate_mp3(client, hi_text, "trxRCYtDC6qFREKq6Ek2", 
                                       "eleven_flash_v2_5", temp_hi_audio)
                            create_new_version(page_dir, 'hi_audio', str(temp_hi_audio), model='eleven_flash_v2_5')
                            temp_hi_audio.unlink()
                            
                            log_api_call("ElevenLabs", "eleven_flash_v2_5", len(hi_text), success=True)
                        
                        log_file_operation(f"audio_{page_dir.name}_v{expected_audio_version}", page_dir, success=True)
                    
                    st.success(f"✅ Audio v{expected_audio_version} generated!")
                    st.rerun()
                except Exception as e:
                    log_api_call("ElevenLabs", "eleven_flash_v2_5", 0, success=False)
                    st.error(f"❌ Audio generation failed: {str(e)}")
            
            # Display audio players for latest versions
            en_audio_path = get_latest_version_path(page_dir, 'en_audio')
            hi_audio_path = get_latest_version_path(page_dir, 'hi_audio')
            expected_version = get_expected_version_for_pdf(pdf_stem)
            
            if en_audio_path and en_audio_path.exists():
                # Show version status
                if en_audio_version < expected_version:
                    st.caption(f"🎵 EN Audio (v{en_audio_version}) ⚠️ Needs v{expected_version}")
                else:
                    st.caption(f"🎵 EN Audio (v{en_audio_version}) 🟢 Latest")
                
                st.audio(str(en_audio_path), format='audio/mp3')
                
                # Always show fast forward button (disabled if at latest)
                is_at_latest = (en_audio_version >= expected_version)
                button_label = f"⏩ Fast Forward Audio to v{expected_version}" if not is_at_latest else f"⏩ Audio At Latest (v{expected_version})"
                
                if st.button(button_label, key=f"ff_en_audio_{page_dir.name}", use_container_width=True, disabled=is_at_latest):
                    log_user_action("FAST_FORWARD_EN_AUDIO", pdf_stem, {"page": page_dir.name, "from": en_audio_version, "to": expected_version})
                    if fast_forward_version(page_dir, 'en_audio', expected_version):
                        st.success(f"✅ Fast forwarded EN audio to v{expected_version}")
                        st.rerun()
                    else:
                        st.error("❌ Fast forward failed")
            
            if hi_audio_path and hi_audio_path.exists():
                # Show version status
                if hi_audio_version < expected_version:
                    st.caption(f"🎵 HI Audio (v{hi_audio_version}) ⚠️ Needs v{expected_version}")
                else:
                    st.caption(f"🎵 HI Audio (v{hi_audio_version}) 🟢 Latest")
                
                st.audio(str(hi_audio_path), format='audio/mp3')
                
                # Always show fast forward button (disabled if at latest)
                is_at_latest = (hi_audio_version >= expected_version)
                button_label = f"⏩ Fast Forward Audio to v{expected_version}" if not is_at_latest else f"⏩ Audio At Latest (v{expected_version})"
                
                if st.button(button_label, key=f"ff_hi_audio_{page_dir.name}", use_container_width=True, disabled=is_at_latest):
                    log_user_action("FAST_FORWARD_HI_AUDIO", pdf_stem, {"page": page_dir.name, "from": hi_audio_version, "to": expected_version})
                    if fast_forward_version(page_dir, 'hi_audio', expected_version):
                        st.success(f"✅ Fast forwarded HI audio to v{expected_version}")
                        st.rerun()
                    else:
                        st.error("❌ Fast forward failed")
    
    # --- Image Display ---
    primary_image_path = next((p for p in page_dir.glob('image_001.*')), None)
    
    # Check for versioned image_to_use
    image_latest_path = get_latest_version_path(page_dir, 'image')
    image_version_count = get_version_count(page_dir, 'image')
    expected_version = get_expected_version_for_pdf(pdf_stem)
    
    # Legacy fallback
    if not image_latest_path or not image_latest_path.exists():
        image_latest_path = page_dir / 'image_to_use.png'
    
    img_col1, img_col2 = st.columns(2)
    
    # Primary image (original extract)
    if primary_image_path and primary_image_path.exists():
        img_col1.image(str(primary_image_path), caption=f"📷 Original Extract", width=450)
    
    # Versioned image_to_use
    if image_latest_path and image_latest_path.exists():
        # Show version status
        if image_version_count > 0:
            if image_version_count < expected_version:
                img_col2.caption(f"🖼️ Image to Use (v{image_version_count}) ⚠️ Needs v{expected_version}")
            else:
                img_col2.caption(f"🖼️ Image to Use (v{image_version_count}) 🟢 Latest")
        else:
            img_col2.caption("🖼️ Image to Use")
        
        img_col2.image(str(image_latest_path), width=300)
        
        # Image editing interface
        with img_col2:
            with st.expander("✏️ Edit Image", expanded=False):
                edit_prompt = st.text_area(
                    "Edit Instruction",
                    placeholder="e.g., Make the background brighter, Remove text from image, Add more vibrant colors",
                    height=80,
                    key=f"img_edit_prompt_{page_dir.name}"
                )
                
                # Execution mode selection
                edit_mode = st.radio(
                    "Execution Mode",
                    options=["Execute Now", "Queue for Later"],
                    key=f"img_edit_mode_{page_dir.name}",
                    horizontal=True,
                    help="Execute Now: Process immediately using Replicate API\nQueue for Later: Save prompt for background processing"
                )
                
                button_label = f"🎨 Generate Edited Image (v{image_version_count + 1})" if edit_mode == "Execute Now" else f"📝 Queue Edit for v{image_version_count + 1}"
                button_icon = "🎨" if edit_mode == "Execute Now" else "📝"
                
                if st.button(button_label, 
                           key=f"edit_img_{page_dir.name}", use_container_width=True, disabled=(not edit_prompt)):
                    if edit_prompt:
                        if edit_mode == "Queue for Later":
                            # Queue the prompt for later processing
                            from utils.queue_manager import queue_image_edit_prompt
                            
                            log_user_action("QUEUE_IMAGE_EDIT", pdf_stem, {"page": page_dir.name, "prompt": edit_prompt, "target_version": image_version_count + 1})
                            
                            try:
                                prompt_file = queue_image_edit_prompt(page_dir, edit_prompt, image_version_count + 1)
                                st.success(f"✅ Queued image edit for v{image_version_count + 1}")
                                st.info(f"📄 Prompt saved to: `{prompt_file.name}`")
                                st.caption("💡 Background service will process this when ready")
                            except Exception as e:
                                st.error(f"❌ Failed to queue: {str(e)}")
                        else:
                            # Execute immediately
                            log_user_action("EDIT_IMAGE", pdf_stem, {"page": page_dir.name, "prompt": edit_prompt, "new_version": image_version_count + 1})
                            try:
                                with st.spinner(f"Editing image with AI..."):
                                    from edit_images import edit_image_with_prompt
                                    
                                    # Create temp output file
                                    temp_output = page_dir / 'temp_edited_image.png'
                                    
                                    # Edit image
                                    success = edit_image_with_prompt(
                                        image_latest_path,
                                        edit_prompt,
                                        temp_output,
                                        output_format='png'
                                    )
                                    
                                    if success:
                                        # Create new version
                                        create_new_version(page_dir, 'image', str(temp_output), model='qwen-image-edit-plus')
                                        temp_output.unlink()
                                        
                                        log_file_operation(f"edit_image_{page_dir.name}_v{image_version_count + 1}", page_dir, success=True)
                                        log_api_call("Replicate", "qwen-image-edit-plus", len(edit_prompt), success=True)
                                        
                                        st.success(f"✅ Created edited image v{image_version_count + 1}")
                                        st.rerun()
                                    else:
                                        log_api_call("Replicate", "qwen-image-edit-plus", len(edit_prompt), success=False)
                                        st.error("❌ Image editing failed")
                            except Exception as e:
                                log_api_call("Replicate", "qwen-image-edit-plus", len(edit_prompt), success=False)
                                st.error(f"❌ Error: {str(e)}")
            
            # Image upload interface - Upload a new version directly
            with st.expander("📤 Upload New Version", expanded=False):
                st.caption(f"Upload a replacement image as v{image_version_count + 1}")
                
                uploaded_image = st.file_uploader(
                    "Choose an image file",
                    type=['png', 'jpg', 'jpeg', 'webp'],
                    key=f"img_upload_{page_dir.name}",
                    help="Upload a new version of the image. The file will be saved with the correct version number."
                )
                
                if uploaded_image is not None:
                    # Show preview of uploaded image
                    st.image(uploaded_image, caption="Preview of uploaded image", width=300)
                    
                    if st.button(f"💾 Save as v{image_version_count + 1}", 
                               key=f"save_uploaded_img_{page_dir.name}", 
                               use_container_width=True,
                               type="primary"):
                        log_user_action("UPLOAD_IMAGE", pdf_stem, {
                            "page": page_dir.name, 
                            "new_version": image_version_count + 1,
                            "original_filename": uploaded_image.name
                        })
                        
                        try:
                            with st.spinner(f"Saving uploaded image as v{image_version_count + 1}..."):
                                # Save uploaded file to temporary location
                                temp_upload = page_dir / 'temp_uploaded_image.png'
                                with open(temp_upload, 'wb') as f:
                                    f.write(uploaded_image.getbuffer())
                                
                                # Create new version with proper naming
                                create_new_version(page_dir, 'image', str(temp_upload), model='user-upload')
                                temp_upload.unlink()  # Delete temp file
                                
                                log_file_operation(f"upload_image_{page_dir.name}_v{image_version_count + 1}", page_dir, success=True)
                                
                                st.success(f"✅ Uploaded image saved as v{image_version_count + 1}")
                                st.rerun()
                        except Exception as e:
                            st.error(f"❌ Upload failed: {str(e)}")
                            log_file_operation(f"upload_image_{page_dir.name}_v{image_version_count + 1}", page_dir, success=False)
            
            # Caption generation interface
            with st.expander("📝 Generate Caption for Video", expanded=False):
                caption_file = page_dir / 'image_caption.txt'
                
                # Display existing caption if available
                if caption_file.exists():
                    current_caption = caption_file.read_text(encoding='utf-8').strip()
                    st.info(f"**Current Caption:** {current_caption}")
                else:
                    st.caption("No caption generated yet")
                
                # Caption mode selection
                caption_mode = st.radio(
                    "Mode",
                    options=["Auto Caption", "Ask Question"],
                    key=f"caption_mode_{page_dir.name}",
                    horizontal=True,
                    help="Auto Caption: AI describes the image\nAsk Question: Ask specific questions"
                )
                
                # Question input (only shown if Ask Question mode)
                caption_question = None
                if caption_mode == "Ask Question":
                    caption_question = st.text_input(
                        "Question",
                        value="What is happening in this image?",
                        key=f"caption_question_{page_dir.name}"
                    )
                
                # Generate button
                generate_label = "🔄 Regenerate Caption" if caption_file.exists() else "📝 Generate Caption"
                
                if st.button(generate_label, key=f"gen_caption_{page_dir.name}", use_container_width=True):
                    from generate_image_captions import generate_image_caption
                    
                    log_user_action("GENERATE_CAPTION", pdf_stem, {
                        "page": page_dir.name,
                        "mode": caption_mode,
                        "question": caption_question
                    })
                    
                    try:
                        with st.spinner("Generating caption..."):
                            caption = generate_image_caption(
                                image_latest_path,
                                question=caption_question,
                                use_caption_mode=(caption_mode == "Auto Caption")
                            )
                            
                            if caption:
                                caption_file.write_text(caption, encoding='utf-8')
                                log_api_call("Replicate", "blip-2", 0, success=True)
                                log_file_operation(f"caption_{page_dir.name}", page_dir, success=True)
                                st.success(f"✅ Caption generated!")
                                st.info(f"**Caption:** {caption}")
                                st.rerun()
                            else:
                                log_api_call("Replicate", "blip-2", 0, success=False)
                                st.error("❌ Caption generation failed")
                    except Exception as e:
                        log_api_call("Replicate", "blip-2", 0, success=False)
                        st.error(f"❌ Error: {str(e)}")
            
            # Fast forward button for images
            if image_version_count > 0:
                is_at_latest = (image_version_count >= expected_version)
                ff_button_label = f"⏩ Fast Forward Image to v{expected_version}" if not is_at_latest else f"⏩ Image At Latest (v{expected_version})"
                
                if st.button(ff_button_label, key=f"ff_image_{page_dir.name}", use_container_width=True, disabled=is_at_latest):
                    log_user_action("FAST_FORWARD_IMAGE", pdf_stem, {"page": page_dir.name, "from": image_version_count, "to": expected_version})
                    if fast_forward_version(page_dir, 'image', expected_version):
                        st.success(f"✅ Fast forwarded image to v{expected_version}")
                        st.rerun()
                    else:
                        st.error("❌ Fast forward failed")
            
            # Show version history
            if image_version_count > 1:
                with st.expander(f"View {image_version_count} version(s)", expanded=False):
                    image_versions = get_all_versions(page_dir, 'image')
                    for i, ver in enumerate(image_versions, 1):
                        is_latest = (i == image_version_count)
                        badge = " 🟢 Latest" if is_latest else ""
                        st.caption(f"**v{i}**{badge} - {ver['created'][:19]} - {ver.get('model', 'unknown')}")
                        ver_path = page_dir / ver['file']
                        if ver_path.exists():
                            st.image(str(ver_path), width=200)
                            if not is_latest and st.button(f"↩️ Restore v{i}", key=f"restore_img_{page_dir.name}_v{i}"):
                                set_as_latest(page_dir, 'image', i)
                                st.success(f"Restored v{i} as latest")
                                st.rerun()
                        st.divider()
    
    # Other images
    all_images = set(page_dir.glob('image_*.*'))
    special_images = {primary_image_path, image_latest_path}
    other_images = sorted([img for img in all_images if img not in special_images])
    
    if other_images:
        st.write("Other Images:")
        cols = st.columns(len(other_images) or 1)
        for i, image_file in enumerate(other_images):
            try:
                # Verify the file is a valid image before displaying
                from PIL import Image
                with Image.open(image_file) as img:
                    img.verify()  # Verify it's a valid image
                cols[i].image(str(image_file), width=150)
            except Exception as e:
                # Skip corrupted or invalid images
                cols[i].caption(f"⚠️ {image_file.name}")
                cols[i].caption(f"Invalid/corrupted")
    
    st.divider()
    
    # --- Image Video Generation (Image to Video) ---
    st.subheader("🎥 Image-to-Video Animation")
    
    if image_latest_path and image_latest_path.exists():
        # Get image video version info
        image_video_latest_path = get_latest_version_path(page_dir, 'image_video')
        image_video_version_count = get_version_count(page_dir, 'image_video')
        expected_version = get_expected_version_for_pdf(pdf_stem)
        
        video_col1, video_col2 = st.columns(2)
        
        with video_col1:
            # Show current video if exists
            if image_video_latest_path and image_video_latest_path.exists():
                # Show version status
                if image_video_version_count > 0:
                    if image_video_version_count < expected_version:
                        st.caption(f"🎥 Image Video (v{image_video_version_count}) ⚠️ Needs v{expected_version}")
                    else:
                        st.caption(f"🎥 Image Video (v{image_video_version_count}) 🟢 Latest")
                else:
                    st.caption("🎥 Image Video")
                
                st.video(str(image_video_latest_path))
                
                # Fast forward button
                if image_video_version_count > 0:
                    is_at_latest = (image_video_version_count >= expected_version)
                    ff_button_label = f"⏩ Fast Forward Video to v{expected_version}" if not is_at_latest else f"⏩ Video At Latest (v{expected_version})"
                    
                    if st.button(ff_button_label, key=f"ff_image_video_{page_dir.name}", use_container_width=True, disabled=is_at_latest):
                        log_user_action("FAST_FORWARD_IMAGE_VIDEO", pdf_stem, {"page": page_dir.name, "from": image_video_version_count, "to": expected_version})
                        if fast_forward_version(page_dir, 'image_video', expected_version):
                            st.success(f"✅ Fast forwarded image video to v{expected_version}")
                            st.rerun()
                        else:
                            st.error("❌ Fast forward failed")
                
                # Show version history
                if image_video_version_count > 1:
                    with st.expander(f"View {image_video_version_count} version(s)", expanded=False):
                        image_video_versions = get_all_versions(page_dir, 'image_video')
                        for i, ver in enumerate(image_video_versions, 1):
                            is_latest = (i == image_video_version_count)
                            badge = " 🟢 Latest" if is_latest else ""
                            st.caption(f"**v{i}**{badge} - {ver['created'][:19]} - {ver.get('model', 'unknown')}")
                            ver_path = page_dir / ver['file']
                            if ver_path.exists():
                                st.video(str(ver_path))
                                if not is_latest and st.button(f"↩️ Restore v{i}", key=f"restore_img_video_{page_dir.name}_v{i}"):
                                    set_as_latest(page_dir, 'image_video', i)
                                    st.success(f"Restored v{i} as latest")
                                    st.rerun()
                            st.divider()
        
        with video_col2:
            # Video generation interface
            with st.expander("🎬 Generate Video from Image", expanded=False):
                st.caption(f"Using latest image: `{image_latest_path.name}`")
                
                # Show caption if exists
                caption_file = page_dir / 'image_caption.txt'
                enhanced_file = page_dir / 'enhanced_video_prompt.txt'
                
                if caption_file.exists():
                    current_caption = caption_file.read_text(encoding='utf-8').strip()
                    st.info(f"**Image Caption:** {current_caption}")
                    
                    # Enhance button (centered in full width)
                    col1, col2, col3 = st.columns([1, 2, 1])
                    
                    with col2:
                        if st.button(
                            "✨ AI Enhance",
                            key=f"enhance_prompt_{page_dir.name}",
                            use_container_width=True,
                            help="Create generic, visually exciting prompt (no character names - video model doesn't recognize them)"
                        ):
                            from enhance_video_prompt import enhance_video_prompt
                            
                            log_user_action("ENHANCE_PROMPT", pdf_stem, {"page": page_dir.name})
                            
                            try:
                                with st.spinner("Enhancing prompt with AI (creating generic, visually exciting prompt)..."):
                                    # Get page text
                                    page_text = None
                                    en_text_path = get_latest_version_path(page_dir, 'en_text')
                                    if not en_text_path:
                                        en_text_path = page_dir / 'final_text_en.txt'
                                    
                                    if en_text_path and en_text_path.exists():
                                        page_text = en_text_path.read_text(encoding='utf-8', errors='ignore')
                                    
                                    # Get whole story for context summary
                                    extraction_dir = get_extraction_dir(pdf_stem)
                                    whole_story_file = extraction_dir / 'whole_story_cleaned.txt'
                                    whole_story = None
                                    if whole_story_file.exists():
                                        whole_story = whole_story_file.read_text(encoding='utf-8', errors='ignore')
                                    
                                    # Enhance prompt using whole story summary + current page
                                    # Creates generic prompts without character names
                                    enhanced_prompt = enhance_video_prompt(
                                        caption=current_caption,
                                        page_text=page_text,
                                        whole_story=whole_story,  # Used for summary/context
                                        previous_pages=None  # Not used
                                    )
                                    
                                    # Save enhanced prompt
                                    enhanced_file.write_text(enhanced_prompt, encoding='utf-8')
                                    log_api_call("Gemini", "gemini-2.0-flash-exp", 0, success=True)
                                    log_file_operation(f"enhance_prompt_{page_dir.name}", page_dir, success=True)
                                    
                                    st.success("✅ Prompt enhanced!")
                                    st.info(f"**Enhanced:** {enhanced_prompt}")
                                    
                                    # Set the text area session state to the new enhanced prompt
                                    text_area_key = f"img_video_prompt_{page_dir.name}"
                                    st.session_state[text_area_key] = enhanced_prompt
                                    
                                    st.rerun()
                            except Exception as e:
                                log_api_call("Gemini", "gemini-2.0-flash-exp", 0, success=False)
                                st.error(f"❌ Error: {str(e)}")
                    
                    # Show enhanced prompt if exists
                    if enhanced_file.exists():
                        enhanced_prompt = enhanced_file.read_text(encoding='utf-8').strip()
                        st.success(f"**Enhanced Prompt:** {enhanced_prompt}")
                else:
                    st.caption("💡 Tip: Generate a caption first, then use AI Enhance for better video prompts")
                
                # Determine default prompt - use enhanced prompt if available
                text_area_key = f"img_video_prompt_{page_dir.name}"
                if enhanced_file.exists():
                    default_video_prompt = enhanced_file.read_text(encoding='utf-8').strip()
                    st.info("✨ **Enhanced prompt auto-loaded below** - you can edit it before generating")
                    
                    # Initialize or update session state with enhanced prompt if it's the default fallback
                    # This ensures enhanced prompts override the default but preserves user edits
                    if text_area_key not in st.session_state:
                        st.session_state[text_area_key] = default_video_prompt
                    elif st.session_state[text_area_key] in ["Ultra high-definition, camera slowly zooms out then zooms in, subtle depth", 
                                                               "Gentle camera movement with soft lighting and minimal motion"]:
                        # If it's still the default fallback, update it to the enhanced prompt
                        st.session_state[text_area_key] = default_video_prompt
                else:
                    default_video_prompt = "Ultra high-definition, camera slowly zooms out then zooms in, subtle depth"
                
                video_prompt = st.text_area(
                    "Motion Prompt (Final - will be used as-is)",
                    value=default_video_prompt,
                    placeholder="e.g., camera slowly zooms in, subtle movements and depth\ngentle pan across the scene, characters slightly animated",
                    height=100,
                    key=text_area_key,
                    help="This is the FINAL prompt that will be used. Edit as needed."
                )
                
                # Use the Motion Prompt box content as-is (no modifications)
                final_video_prompt = video_prompt.strip()
                
                if final_video_prompt:
                    st.caption(f"**Will use:** {final_video_prompt[:100]}..." if len(final_video_prompt) > 100 else f"**Will use:** {final_video_prompt}")
                
                # Execution mode selection
                video_mode = st.radio(
                    "Execution Mode",
                    options=["Execute Now", "Queue for Later"],
                    index=1,  # Default to "Queue for Later"
                    key=f"img_video_mode_{page_dir.name}",
                    horizontal=True,
                    help="Execute Now: Process immediately using Replicate API\nQueue for Later: Save prompt for background processing"
                )
                
                # Advanced options
                with st.expander("⚙️ Advanced Options", expanded=False):
                    num_frames = st.slider("Number of Frames", 81, 121, 81, help="81 frames recommended", key=f"img_vid_frames_{page_dir.name}")
                    aspect_ratio = st.selectbox("Aspect Ratio", ["16:9", "9:16"], index=0, key=f"img_vid_aspect_{page_dir.name}")
                    fps = st.slider("Frames Per Second", 5, 30, 24, key=f"img_vid_fps_{page_dir.name}")
                    sample_shift = st.slider("Sample Shift", 1.0, 20.0, 5.0, 0.5, key=f"img_vid_shift_{page_dir.name}")
                
                button_label = f"🎬 Generate Video (v{image_video_version_count + 1})" if video_mode == "Execute Now" else f"📝 Queue Video for v{image_video_version_count + 1}"
                
                if st.button(button_label, 
                           key=f"gen_img_video_{page_dir.name}", use_container_width=True, disabled=(not video_prompt)):
                    if video_prompt:
                        if video_mode == "Queue for Later":
                            # Queue the prompt for later processing
                            from utils.queue_manager import queue_image_to_video_prompt
                            
                            log_user_action("QUEUE_IMAGE_VIDEO", pdf_stem, {"page": page_dir.name, "prompt": final_video_prompt, "target_version": image_video_version_count + 1})
                            
                            try:
                                prompt_file = queue_image_to_video_prompt(page_dir, final_video_prompt, image_video_version_count + 1)
                                st.success(f"✅ Queued video generation for v{image_video_version_count + 1}")
                                st.info(f"📄 Prompt saved to: `{prompt_file.name}`")
                                st.caption("💡 Background service will process this when ready")
                            except Exception as e:
                                st.error(f"❌ Failed to queue: {str(e)}")
                        else:
                            # Execute immediately
                            log_user_action("GENERATE_IMAGE_VIDEO", pdf_stem, {"page": page_dir.name, "prompt": final_video_prompt, "new_version": image_video_version_count + 1})
                            try:
                                with st.spinner(f"Generating video from image (this may take 1-2 minutes)..."):
                                    from generate_image_videos import generate_video_from_image
                                    
                                    # Create temp output file
                                    temp_output = page_dir / 'temp_image_video.mp4'
                                    
                                    # Generate video
                                    success = generate_video_from_image(
                                        image_latest_path,
                                        final_video_prompt,
                                        temp_output,
                                        num_frames=num_frames,
                                        aspect_ratio=aspect_ratio,
                                        frames_per_second=fps,
                                        sample_shift=sample_shift
                                    )
                                    
                                    if success:
                                        # Create new version
                                        create_new_version(page_dir, 'image_video', str(temp_output), model='wan-video/wan-2.2-i2v-fast')
                                        temp_output.unlink()
                                        
                                        log_file_operation(f"gen_image_video_{page_dir.name}_v{image_video_version_count + 1}", page_dir, success=True)
                                        log_api_call("Replicate", "wan-video/wan-2.2-i2v-fast", len(final_video_prompt), success=True)
                                        
                                        st.success(f"✅ Created image video v{image_video_version_count + 1}")
                                        st.rerun()
                                    else:
                                        log_api_call("Replicate", "wan-video/wan-2.2-i2v-fast", len(final_video_prompt), success=False)
                                        st.error("❌ Video generation failed")
                            except Exception as e:
                                log_api_call("Replicate", "wan-video/wan-2.2-i2v-fast", len(final_video_prompt) if final_video_prompt else 0, success=False)
                                st.error(f"❌ Error: {str(e)}")
    else:
        st.info("ℹ️ No image available for video generation")
    
    st.divider()
    
    # --- Page Video Generation (Animated Image Video + Audio) ---
    st.subheader("🎬 Page Videos (Animated Image Video + Audio)")
    
    # Check if we have the required components
    image_video_latest_path = get_latest_version_path(page_dir, 'image_video')
    en_audio_path = get_latest_version_path(page_dir, 'en_audio')
    hi_audio_path = get_latest_version_path(page_dir, 'hi_audio')
    
    if image_video_latest_path and image_video_latest_path.exists() and (en_audio_path or hi_audio_path):
        # Get audio versions to match
        en_audio_version = get_version_count(page_dir, 'en_audio')
        hi_audio_version = get_version_count(page_dir, 'hi_audio')
        expected_video_version = max(en_audio_version, hi_audio_version)
        
        video_col1, video_col2 = st.columns(2)
        
        # EN Video Generation
        with video_col1:
            # Get current video version and expected version
            current_en_video_version = get_latest_version_number(page_dir, 'en_video')
            page_expected_version = get_expected_version_for_pdf(pdf_stem)
            en_video_path = page_dir / f'page_video_en_v{page_expected_version}.mp4'
            
            # Show version status
            if current_en_video_version > 0:
                if current_en_video_version < page_expected_version:
                    st.caption(f"📹 EN Video (v{current_en_video_version}) ⚠️ Needs v{page_expected_version}")
                else:
                    st.caption(f"📹 EN Video (v{current_en_video_version}) 🟢 Latest")
            
            # Generate button
            if en_audio_path and en_audio_path.exists():
                # Button label
                if current_en_video_version == 0:
                    en_video_label = f"🎬 Generate EN Video (v{page_expected_version})"
                elif current_en_video_version < page_expected_version:
                    en_video_label = f"🎬 Generate EN Video v{page_expected_version}"
                else:
                    en_video_label = f"🎬 EN Video v{current_en_video_version} ✅"
                
                needs_generation = (current_en_video_version < page_expected_version)
                
                if st.button(en_video_label, key=f"{pdf_stem}_gen_en_video_{page_dir.name}", use_container_width=True, disabled=(not needs_generation)):
                    log_user_action("GENERATE_EN_VIDEO", pdf_stem, {"page": page_dir.name, "version": page_expected_version})
                    try:
                        with st.spinner(f"Creating EN video v{page_expected_version}..."):
                            from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, concatenate_videoclips
                            
                            # Load animated image video
                            video_clip = VideoFileClip(str(image_video_latest_path))
                            
                            # Load audio
                            audio_clip = AudioFileClip(str(en_audio_path))
                            audio_duration = audio_clip.duration
                            video_duration = video_clip.duration
                            
                            # Adjust video to match audio duration
                            if video_duration < audio_duration:
                                # Loop video to match audio length
                                loops_needed = int(audio_duration / video_duration) + 1
                                video_clip = concatenate_videoclips([video_clip] * loops_needed).subclip(0, audio_duration)
                            elif video_duration > audio_duration:
                                # Trim video to match audio
                                video_clip = video_clip.subclip(0, audio_duration)
                            
                            # Set audio to video
                            final_clip = video_clip.set_audio(audio_clip)
                            
                            # Write video file
                            final_clip.write_videofile(
                                str(en_video_path),
                                fps=24,
                                codec='libx264',
                                audio_codec='aac',
                                logger=None
                            )
                            
                            # Clean up
                            final_clip.close()
                            video_clip.close()
                            audio_clip.close()
                            
                            log_file_operation(f"video_en_{page_dir.name}_v{page_expected_version}", page_dir, success=True)
                        
                        st.success(f"✅ EN video v{page_expected_version} created!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Video generation failed: {str(e)}")
                
                # Display latest EN video
                if current_en_video_version > 0:
                    latest_en_video = page_dir / f'page_video_en_v{current_en_video_version}.mp4'
                    if latest_en_video.exists():
                        st.video(str(latest_en_video))
                
                # Fast forward button (always show, disabled if at latest)
                if current_en_video_version > 0:
                    is_at_latest = (current_en_video_version >= page_expected_version)
                    ff_button_label = f"⏩ Fast Forward Video to v{page_expected_version}" if not is_at_latest else f"⏩ Video At Latest (v{page_expected_version})"
                    
                    if st.button(ff_button_label, key=f"ff_en_video_{page_dir.name}", use_container_width=True, disabled=is_at_latest):
                        log_user_action("FAST_FORWARD_EN_VIDEO", pdf_stem, {"page": page_dir.name, "from": current_en_video_version, "to": page_expected_version})
                        if fast_forward_version(page_dir, 'en_video', page_expected_version):
                            st.success(f"✅ Fast forwarded EN video to v{page_expected_version}")
                            st.rerun()
                        else:
                            st.error("❌ Fast forward failed")
            else:
                st.info("ℹ️ Generate EN audio first")
        
        # HI Video Generation
        with video_col2:
            # Get current video version and expected version
            current_hi_video_version = get_latest_version_number(page_dir, 'hi_video')
            page_expected_version = get_expected_version_for_pdf(pdf_stem)
            hi_video_path = page_dir / f'page_video_hi_v{page_expected_version}.mp4'
            
            # Show version status
            if current_hi_video_version > 0:
                if current_hi_video_version < page_expected_version:
                    st.caption(f"📹 HI Video (v{current_hi_video_version}) ⚠️ Needs v{page_expected_version}")
                else:
                    st.caption(f"📹 HI Video (v{current_hi_video_version}) 🟢 Latest")
            
            # Generate button
            if hi_audio_path and hi_audio_path.exists():
                # Button label
                if current_hi_video_version == 0:
                    hi_video_label = f"🎬 Generate HI Video (v{page_expected_version})"
                elif current_hi_video_version < page_expected_version:
                    hi_video_label = f"🎬 Generate HI Video v{page_expected_version}"
                else:
                    hi_video_label = f"🎬 HI Video v{current_hi_video_version} ✅"
                
                needs_generation = (current_hi_video_version < page_expected_version)
                
                if st.button(hi_video_label, key=f"{pdf_stem}_gen_hi_video_{page_dir.name}", use_container_width=True, disabled=(not needs_generation)):
                    log_user_action("GENERATE_HI_VIDEO", pdf_stem, {"page": page_dir.name, "version": page_expected_version})
                    try:
                        with st.spinner(f"Creating HI video v{page_expected_version}..."):
                            from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, concatenate_videoclips
                            
                            # Load animated image video
                            video_clip = VideoFileClip(str(image_video_latest_path))
                            
                            # Load audio
                            audio_clip = AudioFileClip(str(hi_audio_path))
                            audio_duration = audio_clip.duration
                            video_duration = video_clip.duration
                            
                            # Adjust video to match audio duration
                            if video_duration < audio_duration:
                                # Loop video to match audio length
                                loops_needed = int(audio_duration / video_duration) + 1
                                video_clip = concatenate_videoclips([video_clip] * loops_needed).subclip(0, audio_duration)
                            elif video_duration > audio_duration:
                                # Trim video to match audio
                                video_clip = video_clip.subclip(0, audio_duration)
                            
                            # Set audio to video
                            final_clip = video_clip.set_audio(audio_clip)
                            
                            # Write video file
                            final_clip.write_videofile(
                                str(hi_video_path),
                                fps=24,
                                codec='libx264',
                                audio_codec='aac',
                                logger=None
                            )
                            
                            # Clean up
                            final_clip.close()
                            video_clip.close()
                            audio_clip.close()
                            
                            log_file_operation(f"video_hi_{page_dir.name}_v{page_expected_version}", page_dir, success=True)
                        
                        st.success(f"✅ HI video v{page_expected_version} created!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Video generation failed: {str(e)}")
                
                # Display latest HI video
                if current_hi_video_version > 0:
                    latest_hi_video = page_dir / f'page_video_hi_v{current_hi_video_version}.mp4'
                    if latest_hi_video.exists():
                        st.video(str(latest_hi_video))
                
                # Fast forward button (always show, disabled if at latest)
                if current_hi_video_version > 0:
                    is_at_latest = (current_hi_video_version >= page_expected_version)
                    ff_button_label = f"⏩ Fast Forward Video to v{page_expected_version}" if not is_at_latest else f"⏩ Video At Latest (v{page_expected_version})"
                    
                    if st.button(ff_button_label, key=f"ff_hi_video_{page_dir.name}", use_container_width=True, disabled=is_at_latest):
                        log_user_action("FAST_FORWARD_HI_VIDEO", pdf_stem, {"page": page_dir.name, "from": current_hi_video_version, "to": page_expected_version})
                        if fast_forward_version(page_dir, 'hi_video', page_expected_version):
                            st.success(f"✅ Fast forwarded HI video to v{page_expected_version}")
                            st.rerun()
                        else:
                            st.error("❌ Fast forward failed")
            else:
                st.info("ℹ️ Generate HI audio first")
    else:
        if not image_video_latest_path or not image_video_latest_path.exists():
            st.info("ℹ️ Generate animated image video first (see Image-to-Video Animation section above)")
        elif not (en_audio_path or hi_audio_path):
            st.info("ℹ️ Generate audio files first")
        else:
            st.info("ℹ️ Need animated image video and audio files to generate page videos")


def render_pages_viewer(pdf_stem: str):
    """Render the pages content viewer."""
    page_dirs = get_page_directories(pdf_stem)
    
    if not page_dirs:
        return
    
    with st.expander("View Extracted Pages", expanded=False):
        for page_dir in page_dirs:
            render_page_content(page_dir, pdf_stem)
            st.divider()
