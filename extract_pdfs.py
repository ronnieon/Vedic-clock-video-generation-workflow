#!/usr/bin/env python3
"""
Extract page-by-page text and images from all PDFs in a directory.

- Creates an output folder per PDF under the specified out_dir (default: ./extracted)
- For each page, writes text to page_<NNNN>/text.txt and images as page_<NNNN>/image_<MMM>.<ext>
- Skips PDFs already processed (presence of completed.flag) unless --force is provided

Usage:
  python extract_pdfs.py --input_dir . --out_dir extracted
  python extract_pdfs.py --force

Requires:
  pip install -r requirements.txt
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, Tuple, Optional

import fitz  # PyMuPDF
import subprocess
import shutil

# Optional OCR dependency: Pillow
try:
    from PIL import Image, ImageOps, ImageFilter
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False


def find_pdfs(input_dir: Path) -> Iterable[Path]:
    """Yield all PDF files (case-insensitive) in the given directory (non-recursive)."""
    for p in sorted(input_dir.iterdir()):
        if p.is_file() and p.suffix.lower() == ".pdf":
            yield p


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _tesseract_cli_ready() -> bool:
    """Return True if the tesseract binary is available on PATH."""
    return shutil.which("tesseract") is not None


def _ocr_with_tesseract_cli(pil_img: Image.Image, debug_path: Path | None = None) -> str:
    """Run Tesseract CLI on a PIL image and return extracted text.

    Saves a temporary PNG next to page_dir when debug_path is provided for inspection.
    """
    try:
        from tempfile import NamedTemporaryFile
        with NamedTemporaryFile(suffix=".png", delete=False) as tmp_in:
            pil_img.save(tmp_in.name)
            if debug_path is not None:
                try:
                    pil_img.save(debug_path)
                except Exception:
                    pass
            # Use stdout output: tesseract <input> stdout
            proc = subprocess.run(
                ["tesseract", tmp_in.name, "stdout", "--psm", "6"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                text=True,
            )
        if proc.returncode != 0:
            return ""
        return proc.stdout or ""
    except Exception:
        return ""


def extract_page_text(page: fitz.Page, page_dir: Path, debug: bool = False) -> str:
    """Extract text from a page.

    1) Try embedded text via PyMuPDF
    2) If none and OCR available, render page to image and OCR
    """
    # 1) Embedded text
    # Try both PyMuPDF API variants for compatibility
    # Use PyMuPDF legacy API for compatibility
    text = page.get_text("text") or ""
    if text.strip():
        return text

    # 2) OCR fallback via Tesseract CLI
    if not PIL_AVAILABLE or not _tesseract_cli_ready():
        if debug and not PIL_AVAILABLE:
            print("  - OCR not available: missing Pillow (PIL)")
        elif debug and not _tesseract_cli_ready():
            print("  - OCR not available: Tesseract binary not found. Install it (e.g., brew install tesseract)")
        return text  # empty or whitespace

    try:
        # Render at higher resolution for better OCR results
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        from PIL import Image, ImageOps, ImageFilter
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        # Basic preprocessing: grayscale -> increase contrast -> slight sharpen -> binary
        gray = ImageOps.grayscale(img)
        enhanced = ImageOps.autocontrast(gray, cutoff=2)
        enhanced = enhanced.filter(ImageFilter.SHARPEN)
        # Save preprocessed image for debugging if requested
        if debug:
            ensure_dir(page_dir)
            enhanced.save(page_dir / "ocr_preprocessed.png")
        # OCR via tesseract CLI
        debug_img_path = page_dir / "ocr_preprocessed.png" if debug else None
        ocr_text = _ocr_with_tesseract_cli(enhanced, debug_path=debug_img_path)
        return ocr_text if ocr_text is not None else ""
    except Exception:
        # If anything goes wrong in OCR, return empty string
        return text



def extract_page_images(doc: fitz.Document, page: fitz.Page, page_dir: Path) -> int:
    """Extract embedded images from the page. Returns count of saved images."""
    images = page.get_images(full=True)
    count = 0
    for idx, img in enumerate(images, start=1):
        xref = img[0]
        try:
            image_info = doc.extract_image(xref)
        except Exception as e:
            # If extraction fails for a specific xref, skip it
            print(f"  - Warn: failed to extract image xref={xref}: {e}")
            continue
        if not image_info:
            continue
        img_bytes = image_info.get("image")
        ext = image_info.get("ext", "png")
        if not img_bytes:
            continue
        out_path = page_dir / f"image_{idx:03d}.{ext}"
        try:
            out_path.write_bytes(img_bytes)
            count += 1
        except Exception as e:
            print(f"  - Warn: failed to write image {out_path.name}: {e}")
    return count


def render_page_png(page: fitz.Page, page_dir: Path, zoom: float = 2.0) -> Path:
    """Render the full page to a PNG image and save it as page_render.png.

    This acts as a fallback/visual reference when embedded image extraction misses content
    (e.g., vector graphics, background images, or artwork not stored as separate xrefs).
    Returns the saved file path.
    """
    try:
        ensure_dir(page_dir)
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        out_path = page_dir / "page_render.png"
        pix.save(str(out_path))
        return out_path
    except Exception as e:
        print(f"  - Warn: failed to render page PNG: {e}")
        return page_dir / "page_render.png"


def save_primary_image_for_layout(page_dir: Path, page_number: int, layout_mode: str) -> Path | None:
    """Populate image_to_use.png according to layout mode.

    Layout modes:
      legacy_spread / spread: Treat each PDF page as a scanned two-page spread.
        - First physical page is on the right (recto) side of the first spread -> take right half.
        - Subsequent logical pages appear on left side of each spread -> take left half.
      single: Do not crop; use the first extracted image if present, else rendered page PNG.
      auto: Heuristic – if width/height > 1.1 assume spread, else single.

    Returns path to created image_to_use.png or None.
    """
    try:
        from PIL import Image
        # Find source image candidate(s)
        candidates = []
        for ext in ("png", "jpg", "jpeg", "webp"):
            p = page_dir / f"image_001.{ext}"
            if p.exists():
                candidates.append(p)
        if not candidates:
            images = sorted(page_dir.glob("image_*.*"))
            if images:
                candidates.append(images[0])
        # Fallback to page_render.png
        render_png = page_dir / "page_render.png"
        if not candidates and render_png.exists():
            candidates.append(render_png)
        if not candidates:
            return None

        src = candidates[0]
        with Image.open(src) as im:
            width, height = im.size
            # Determine effective mode if auto
            effective_mode = layout_mode
            if layout_mode == "auto":
                ratio = width / max(height, 1)
                effective_mode = "spread" if ratio > 1.1 else "single"

            out_path = page_dir / "image_to_use.png"
            if effective_mode in ("legacy_spread", "spread"):
                mid = width // 2
                if page_number == 1:
                    box = (mid, 0, width, height)  # right half
                else:
                    box = (0, 0, mid, height)      # left half
                im.crop(box).save(out_path)
            else:
                # single page: just copy (re-save) full image
                im.save(out_path)
            return out_path
    except Exception as e:
        print(f"  - Warn: failed to prepare primary image: {e}")
        return None


def _save_image_for_scene(doc: fitz.Document, page: fitz.Page, scene_dir: Path, debug: bool = False) -> Optional[Path]:
    """Save a representative image from the given page into scene_dir/image.png.
    Falls back to rendered PNG if no embedded images. Returns saved path or None."""
    ensure_dir(scene_dir)
    image_out = scene_dir / "image.png"
    try:
        images = page.get_images(full=True)
        if images:
            # Take first embedded image
            xref = images[0][0]
            image_info = doc.extract_image(xref)
            if image_info:
                img_bytes = image_info.get("image")
                ext = image_info.get("ext", "png")
                if img_bytes:
                    tmp = scene_dir / f"_tmp_embed.{ext}"
                    tmp.write_bytes(img_bytes)
                    from PIL import Image as _PILImage
                    with _PILImage.open(tmp) as im:
                        im.save(image_out)
                    try:
                        tmp.unlink()
                    except Exception:
                        pass
                    return image_out
        # Fallback: render page
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        pix.save(str(image_out))
        return image_out
    except Exception as e:
        if debug:
            print(f"  - Warn: scene image extraction failed: {e}")
        return None


def process_pdf(pdf_path: Path, out_root: Path, force: bool = False, debug: bool = False, no_images: bool = False, layout_mode: str = "auto", pdf_format: str = "old") -> Tuple[int, int]:
    """Process a single PDF. Returns (units_processed, images_extracted).

    pdf_format:
      old      -> legacy behavior: each PDF page becomes its own directory `page_XXXX`.
      updated  -> paired-page behavior: two consecutive PDF pages become one scene directory `scene_XXXX`.

    When in updated mode:
      - text comes from first page in the pair
      - image comes from second page in the pair
      - if the PDF has an odd number of pages, the last scene will use the last page for both text and image (fallback)

    layout_mode (legacy single-page mode only) controls page image post-processing.
    """
    pdf_name = pdf_path.stem
    pdf_out_dir = out_root / pdf_name
    ensure_dir(pdf_out_dir)

    completed_flag = pdf_out_dir / "completed.flag"
    if completed_flag.exists() and not force:
        print(f"Skip (completed): {pdf_path.name}")
        return (0, 0)

    try:
        doc = fitz.open(str(pdf_path))
    except Exception as e:
        print(f"Error: cannot open {pdf_path.name}: {e}")
        return (0, 0)

    if doc.needs_pass:
        print(f"Warn: PDF is encrypted and requires a password, skipping: {pdf_path.name}")
        return (0, 0)

    total_images = 0
    pages_done = 0

    meta = {
        "source": str(pdf_path.name),
        "pages": int(doc.page_count),
    }
    (pdf_out_dir / "metadata.json").write_text(json.dumps(meta, indent=2))

    if pdf_format == "updated":
        scene_index = 1
        for i in range(0, doc.page_count, 2):
            text_page = doc.load_page(i)
            image_page = doc.load_page(i + 1) if i + 1 < doc.page_count else text_page  # fallback if odd
            scene_dir = pdf_out_dir / f"scene_{scene_index:04d}"
            ensure_dir(scene_dir)

            scene_done_flag = scene_dir / "done.flag"
            if scene_done_flag.exists() and not force:
                pages_done += 1
                scene_index += 1
                continue

            # TEXT from first page of pair
            text = extract_page_text(text_page, scene_dir, debug=debug)
            (scene_dir / "text.txt").write_text(text, encoding="utf-8")

            # IMAGE from second page of pair
            img_count = 0
            if not no_images:
                img_path = _save_image_for_scene(doc, image_page, scene_dir, debug=debug)
                if img_path and img_path.exists():
                    img_count = 1
                    total_images += 1
                    # For compatibility with downstream code expecting image_to_use.png
                    compat_path = scene_dir / "image_to_use.png"
                    try:
                        if compat_path.exists():
                            compat_path.unlink()
                        shutil.copy2(img_path, compat_path)
                    except Exception:
                        pass

            # Summary
            summary = {
                "scene_index": scene_index,
                "source_page_indices": [i, i + 1 if i + 1 < doc.page_count else i],
                "text_page_number": i + 1,
                "image_page_number": i + 2 if i + 1 < doc.page_count else i + 1,
                "text_chars": len(text),
                "images": img_count,
            }
            (scene_dir / "summary.json").write_text(json.dumps(summary, indent=2))
            scene_done_flag.write_text("ok")
            pages_done += 1
            scene_index += 1
    else:
        # Legacy single-page mode
        for i in range(doc.page_count):
            page = doc.load_page(i)
            page_dir = pdf_out_dir / f"page_{i + 1:04d}"
            ensure_dir(page_dir)

            page_done_flag = page_dir / "done.flag"
            if page_done_flag.exists() and not force:
                pages_done += 1
                continue

            text = extract_page_text(page, page_dir, debug=debug)
            (page_dir / "text.txt").write_text(text, encoding="utf-8")

            if debug:
                preview = (text or "").strip().replace("\n", " ")
                if len(preview) > 200:
                    preview = preview[:200] + "..."
                print(f"    Page {i + 1}: text_chars={len(text)} preview=\"{preview}\"")

            img_count = 0
            if not no_images:
                img_count = extract_page_images(doc, page, page_dir)
                total_images += img_count
                render_page_png(page, page_dir)
                save_primary_image_for_layout(page_dir, i + 1, layout_mode)

            page_summary = {
                "page_index": i,
                "page_number": i + 1,
                "text_chars": len(text),
                "images": img_count,
            }
            (page_dir / "summary.json").write_text(json.dumps(page_summary, indent=2))
            page_done_flag.write_text("ok")
            pages_done += 1

    # Mark PDF done
    completed_flag.write_text("ok")

    doc.close()
    return (pages_done, total_images)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract pagewise text and images from PDFs.")
    parser.add_argument("--input_dir", type=Path, default=Path("pdfs"), help="Directory to scan for PDFs (non-recursive). Defaults to ./pdfs/")
    parser.add_argument("--out_dir", type=Path, default=Path.cwd() / "extracted", help="Output directory for extracted data")
    parser.add_argument("--force", action="store_true", help="Reprocess PDFs/pages even if already completed")
    parser.add_argument("--debug", action="store_true", help="Print per-page extraction details and OCR diagnostics")
    parser.add_argument("--only", type=str, default="", help="Only process PDFs whose filename contains this substring")
    parser.add_argument("--no_images", action="store_true", help="Skip extracting embedded images (faster)")
    parser.add_argument("--layout_mode", choices=["auto", "spread", "legacy_spread", "single"], default="auto", help="Page image post-processing mode (legacy single-page mode only).")
    parser.add_argument("--pdf_format", choices=["old", "updated"], default="old", help="PDF format: 'old' (1 page = 1 scene), 'updated' (2 pages = 1 scene).")
    args = parser.parse_args(argv)

    input_dir: Path = args.input_dir.resolve()
    out_dir: Path = args.out_dir.resolve()
    ensure_dir(out_dir)

    pdfs = list(find_pdfs(input_dir))
    if args.only:
        substr = args.only.lower()
        pdfs = [p for p in pdfs if substr in p.name.lower()]
    if not pdfs:
        print(f"No PDFs found in {input_dir}")
        return 0

    print(f"Found {len(pdfs)} PDF(s) in {input_dir}")
    total_pages = 0
    total_images = 0

    for pdf in pdfs:
        print(f"Processing: {pdf.name} (format={args.pdf_format}, layout_mode={args.layout_mode})")
        pages, images = process_pdf(pdf, out_dir, force=args.force, debug=args.debug, no_images=args.no_images, layout_mode=args.layout_mode, pdf_format=args.pdf_format)
        print(f"  -> pages: {pages}, images: {images}")
        total_pages += pages
        total_images += images

    print("\nSummary:")
    print(f"  PDFs: {len(pdfs)}")
    print(f"  Pages processed: {total_pages}")
    print(f"  Images extracted: {total_images}")
    print(f"  Output dir: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
