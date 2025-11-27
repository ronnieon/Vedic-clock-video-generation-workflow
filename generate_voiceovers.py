#!/usr/bin/env python3
import os
import sys
import argparse
from pathlib import Path
from typing import Iterable
import time

try:
    from elevenlabs.client import ElevenLabs
except ImportError as e:
    print("Missing dependency: elevenlabs. Install with: pip install -r requirements.txt", file=sys.stderr)
    raise

DEFAULT_BASE_DIR = "extracted"
DEFAULT_MODEL_ID = "eleven_flash_v2_5"
DEFAULT_VOICE_ID = "7tRwuZTD1EWi6nydVerp"  # Jhonny
DEFAULT_HI_VOICE_ID = "trxRCYtDC6qFREKq6Ek2"  # Sourabh
TARGET_FILES = [
    ("final_text_en.txt", "final_text_en.mp3"),
    ("final_text_hi.txt", "final_text_hi.mp3"),
]


def save_audio_stream_to_file(audio_stream: Iterable[bytes], out_path: Path) -> None:
    """Write a streaming/generator response to a file without loading into memory."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("wb") as f:
        for chunk in audio_stream:
            if not chunk:
                continue
            # Expect bytes chunks from ElevenLabs SDK
            if isinstance(chunk, bytes):
                f.write(chunk)
            else:
                # Fallback for file-like
                data = getattr(chunk, "read", lambda: b"")()
                if data:
                    f.write(data)


def generate_mp3(client: ElevenLabs, text: str, voice_id: str, model_id: str, out_path: Path, retries: int = 3) -> None:
    """Generate an MP3 with simple retry logic."""
    backoff = 2
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            audio = client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id=model_id,
                output_format="mp3_44100_128",
            )
            save_audio_stream_to_file(audio, out_path)
            return
        except Exception as e:  # noqa: BLE001 (broad to retry transient http)
            last_err = e
            if attempt < retries:
                time.sleep(backoff)
                backoff *= 2
            else:
                raise last_err


def find_targets(base_dir: Path):
    for txt_name, mp3_name in TARGET_FILES:
        for txt_path in base_dir.rglob(txt_name):
            mp3_path = txt_path.parent / mp3_name
            yield txt_path, mp3_path


def main():
    parser = argparse.ArgumentParser(description="Generate ElevenLabs voiceovers for extracted text files.")
    parser.add_argument("--base-dir", default=DEFAULT_BASE_DIR, help="Base directory to search (default: extracted)")
    parser.add_argument("--voice-id", default=DEFAULT_VOICE_ID, help="ElevenLabs voice_id to use")
    parser.add_argument("--hi-voice-id", default=DEFAULT_HI_VOICE_ID, help="ElevenLabs voice_id to use for Hindi files")
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID, help="ElevenLabs model_id to use")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing MP3 files")
    parser.add_argument("--only-hi", action="store_true", help="Process only Hindi files (final_text_hi.txt)")
    parser.add_argument("--only-en", action="store_true", help="Process only English files (final_text_en.txt)")
    args = parser.parse_args()

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("ERROR: ELEVENLABS_API_KEY not set in environment. Ensure .envrc is loaded (e.g., via direnv).", file=sys.stderr)
        sys.exit(1)

    client = ElevenLabs(api_key=api_key)

    base_dir = Path(args.base_dir).resolve()
    if not base_dir.exists():
        print(f"ERROR: Base directory not found: {base_dir}", file=sys.stderr)
        sys.exit(1)

    total = 0
    skipped = 0
    generated = 0

    for txt_path, mp3_path in find_targets(base_dir):
        # Filter by language if requested
        is_hi = (txt_path.name == "final_text_hi.txt")
        if args.only_hi and not is_hi:
            continue
        if args.only_en and is_hi:
            continue
        total += 1
        try:
            if mp3_path.exists() and not args.overwrite:
                skipped += 1
                print(f"Skip (exists): {mp3_path}")
                continue

            text = txt_path.read_text(encoding="utf-8").strip()
            if not text:
                skipped += 1
                print(f"Skip (empty text): {txt_path}")
                continue

            # Choose voice based on language file
            voice_id = args.hi_voice_id if txt_path.name == "final_text_hi.txt" else args.voice_id

            print(f"Generating: {txt_path} -> {mp3_path}")
            generate_mp3(
                client=client,
                text=text,
                voice_id=voice_id,
                model_id=args.model_id,
                out_path=mp3_path,
            )
            generated += 1
        except Exception as e:  # noqa: BLE001
            print(f"ERROR processing {txt_path}: {e}", file=sys.stderr)
            if "quota_exceeded" in str(e):
                print("Quota exceeded detected. Aborting further processing.", file=sys.stderr)
                break

    print("\nSummary:")
    print(f"- Total targets: {total}")
    print(f"- Generated: {generated}")
    print(f"- Skipped: {skipped}")


if __name__ == "__main__":
    main()
