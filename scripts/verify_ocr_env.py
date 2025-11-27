#!/usr/bin/env python3
"""Simple environment verification for OCR prerequisites.

Prints availability of:
- tesseract binary (path and version)
- Pillow import
- PyMuPDF version

Exit code 0 even if something is missing (informational).
"""
from __future__ import annotations
import shutil, subprocess, sys

report = []

# Tesseract binary
path = shutil.which("tesseract")
if path:
    try:
        proc = subprocess.run(["tesseract", "--version"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=5)
        version_info = proc.stdout.splitlines()[0] if proc.stdout else "(no output)"
    except Exception as e:
        version_info = f"error reading version: {e}" 
    report.append(f"tesseract: FOUND at {path} | {version_info}")
else:
    report.append("tesseract: NOT FOUND (install required for OCR fallback)")

# Pillow
try:
    import PIL
    from PIL import Image
    report.append(f"Pillow: FOUND version {PIL.__version__}")
except Exception as e:
    report.append(f"Pillow: NOT FOUND ({e})")

# PyMuPDF
try:
    import fitz
    report.append(f"PyMuPDF(fitz): FOUND version {fitz.__version__}")
except Exception as e:
    report.append(f"PyMuPDF(fitz): NOT FOUND ({e})")

print("\nOCR Environment Check:\n" + "\n".join(report))

# Provide quick guidance if missing components
if not path:
    print("\nInstall tesseract (Debian/Ubuntu): apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-eng")
    print("macOS (Homebrew): brew install tesseract")

