#!/usr/bin/env python3
"""
Build two slideshow videos (English and Hindi) from the extracted page folders.

Each page folder under extracted/download/page_XXXX is expected to contain:
- image_to_use.png
- final_text_en.mp3 (English narration) [optional]
- final_text_hi.mp3 (Hindi narration) [optional]

The script will:
- Iterate pages in natural (zero-padded) order.
- For each language, pair the image with the corresponding audio clip.
- Set the slide duration to the audio duration.
- Concatenate into one video per language and save at extracted/download/.

Outputs:
- extracted/download/english_slideshow.mp4
- extracted/download/hindi_slideshow.mp4

Requires: moviepy, imageio-ffmpeg
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List

from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from PIL import Image


ROOT = Path(__file__).resolve().parent
DOWNLOAD_DIR = ROOT / "extracted" / "download"
PAGE_GLOB = "page_*"
IMAGE_NAME = "image_to_use.png"
AUDIO_EN = "final_text_en.mp3"
AUDIO_HI = "final_text_hi.mp3"
TARGET_IMAGE_SIZE = (994, 1935)  # width, height

OUT_EN = DOWNLOAD_DIR / "english_slideshow.mp4"
OUT_HI = DOWNLOAD_DIR / "hindi_slideshow.mp4"

FPS = 24
VIDEO_CODEC = "libx264"
AUDIO_CODEC = "aac"


def resize_and_replace_image(image_path: Path, target_size: tuple[int, int]):
    """Resizes an image to the target size and overwrites the original."""
    try:
        with Image.open(image_path) as img:
            if img.size != target_size:
                print(f"[INFO] Resizing {image_path.name} to {target_size}...")
                resized_img = img.resize(target_size, Image.Resampling.LANCZOS)
                resized_img.save(image_path)
    except Exception as e:
        print(f"[ERROR] Failed to resize image {image_path}: {e}")


def get_pages(download_dir: Path) -> List[Path]:
    pages = sorted([p for p in download_dir.glob(PAGE_GLOB) if p.is_dir()])
    return pages


DEFAULT_SLIDE_DURATION = 3  # seconds


def build_language_slideshow(
    pages: List[Path], audio_filename: str, out_path: Path, force_all_pages: bool = False
) -> None:
    clips = []
    skipped_pages = 0

    for page in pages:
        img_path = page / IMAGE_NAME
        aud_path = page / audio_filename

        if not img_path.exists():
            print(f"[WARN] Missing image, skipping page: {img_path}")
            skipped_pages += 1
            continue

        # Resize the image before creating the clip
        resize_and_replace_image(img_path, TARGET_IMAGE_SIZE)

        audio_clip = None
        duration = DEFAULT_SLIDE_DURATION

        has_audio = aud_path.exists() and aud_path.stat().st_size > 0

        if has_audio:
            try:
                audio_clip = AudioFileClip(str(aud_path))
                duration = audio_clip.duration
            except Exception as e:
                print(f"[WARN] Failed to load audio {aud_path}, using default duration: {e}")
        elif force_all_pages:
            print(f"[INFO] Missing or empty audio for {aud_path}, using default duration.")
        else:
            print(f"[WARN] Missing or empty audio, skipping page: {aud_path}")
            skipped_pages += 1
            continue

        try:
            img_clip = ImageClip(str(img_path)).set_duration(duration)
            if audio_clip:
                img_clip = img_clip.set_audio(audio_clip)
            img_clip = img_clip.set_fps(FPS)
            clips.append(img_clip)
        except Exception as e:
            print(f"[WARN] Failed to build clip for page {page.name}: {e}")
            skipped_pages += 1
            continue

    # Test: Verify that the number of clips matches the expected number of pages.
    expected_clips = len(pages) - skipped_pages
    if len(clips) != expected_clips:
        print(f"[ERROR] Clip count mismatch! Expected {expected_clips}, but found {len(clips)}.")
        # Clean up any created clips before exiting
        for c in clips:
            if c: c.close()
        return

    if not clips:
        print(f"[ERROR] No valid clips for {audio_filename}. Nothing to render.")
        return

    try:
        final = concatenate_videoclips(clips, method="compose")
        # Write the video file
        print(f"[INFO] Writing video: {out_path}")
        final.write_videofile(
            str(out_path),
            fps=FPS,
            codec=VIDEO_CODEC,
            audio_codec=AUDIO_CODEC,
            threads=2,
            temp_audiofile=str(out_path.with_suffix('.temp-audio.m4a')),
            remove_temp=True,
        )
    finally:
        # Close clips to release resources
        for c in clips:
            try:
                c.close()
            except Exception:
                pass

    if skipped_pages:
        print(f"[INFO] Completed with {skipped_pages} skipped pages for {audio_filename}.")
    else:
        print(f"[INFO] Completed without skips for {audio_filename}.")


if __name__ == "__main__":
    if not DOWNLOAD_DIR.exists():
        print(f"[ERROR] Download directory not found: {DOWNLOAD_DIR}")
        sys.exit(1)

    pages = get_pages(DOWNLOAD_DIR)
    if not pages:
        print(f"[ERROR] No page_* folders found in {DOWNLOAD_DIR}")
        sys.exit(1)

    print(f"[INFO] Found {len(pages)} pages under {DOWNLOAD_DIR}")

    # English slideshow
    try:
        build_language_slideshow(pages, AUDIO_EN, OUT_EN, force_all_pages=True)
    except Exception as e:
        print(f"[ERROR] Failed to build English slideshow: {e}")

    # Hindi slideshow
    try:
        build_language_slideshow(pages, AUDIO_HI, OUT_HI)
    except Exception as e:
        print(f"[ERROR] Failed to build Hindi slideshow: {e}")

    print("[INFO] Done.")
