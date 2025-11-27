"""Type stubs for PyMuPDF (fitz) package."""

from typing import Any, Optional, Tuple, List

class Matrix:
    """Transformation matrix for PDF operations."""
    def __init__(self, a: float = 1.0, b: float = 0.0, c: float = 0.0, d: float = 1.0, e: float = 0.0, f: float = 0.0) -> None: ...

class Pixmap:
    """Pixel map representing rendered page content."""
    width: int
    height: int
    samples: bytes
    
    def save(self, filename: str, output: Optional[str] = None) -> None:
        """Save pixmap to file."""
        ...

class Page:
    """PDF page object."""
    
    def get_text(self, option: str = "text", **kwargs: Any) -> str:
        """Extract text from page.
        
        Args:
            option: Output format ('text', 'html', 'dict', 'json', 'rawdict', 'xhtml', 'xml')
        
        Returns:
            Extracted text content
        """
        ...
    
    def get_pixmap(
        self,
        *,
        matrix: Optional[Matrix] = None,
        dpi: Optional[int] = None,
        colorspace: Optional[Any] = None,
        clip: Optional[Any] = None,
        alpha: bool = False,
        annots: bool = True
    ) -> Pixmap:
        """Render page to a pixmap.
        
        Args:
            matrix: Transformation matrix for scaling/rotation
            dpi: Resolution in dots per inch
            colorspace: Color space to use
            clip: Clipping rectangle
            alpha: Include alpha channel
            annots: Include annotations
            
        Returns:
            Rendered pixmap
        """
        ...
    
    def get_images(self, full: bool = False) -> List[Tuple[int, ...]]:
        """Get list of images on the page.
        
        Args:
            full: Return full image info
            
        Returns:
            List of image references
        """
        ...
    
    def load_page(self, page_num: int) -> "Page":
        """Load a specific page."""
        ...

class Document:
    """PDF document object."""
    
    page_count: int
    needs_pass: bool
    
    def load_page(self, page_num: int) -> Page:
        """Load a specific page by number."""
        ...
    
    def extract_image(self, xref: int) -> Optional[dict]:
        """Extract image by cross-reference number.
        
        Args:
            xref: Cross-reference number of the image
            
        Returns:
            Dictionary with 'image' (bytes) and 'ext' (extension) keys
        """
        ...
    
    def close(self) -> None:
        """Close the document."""
        ...

def open(filename: str = "", stream: Optional[bytes] = None, filetype: Optional[str] = None, **kwargs: Any) -> Document:
    """Open a PDF document.
    
    Args:
        filename: Path to PDF file
        stream: PDF data as bytes
        filetype: File type hint
        
    Returns:
        Document object
    """
    ...
