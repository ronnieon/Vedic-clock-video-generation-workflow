"""Type stubs for google.generativeai package."""

from typing import Any, Optional, Sequence

def configure(api_key: str) -> None:
    """Configure the Generative AI client with an API key."""
    ...

class GenerativeModel:
    """Generative AI model for content generation."""
    
    def __init__(self, model_name: str) -> None:
        """Initialize a generative model.
        
        Args:
            model_name: Name of the model (e.g., 'gemini-2.0-flash')
        """
        ...
    
    def generate_content(
        self,
        contents: str | Sequence[str],
        *,
        generation_config: Optional[Any] = None,
        safety_settings: Optional[Any] = None,
        stream: bool = False,
        **kwargs: Any
    ) -> Any:
        """Generate content from the model.
        
        Args:
            contents: Input prompt or sequence of prompts
            generation_config: Optional generation configuration
            safety_settings: Optional safety settings
            stream: Whether to stream the response
            **kwargs: Additional arguments
            
        Returns:
            Generated response object with .text attribute
        """
        ...

class GenerationConfig:
    """Configuration for content generation."""
    
    def __init__(
        self,
        *,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        candidate_count: Optional[int] = None,
        max_output_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> None:
        ...

class ChatSession:
    """Chat session for multi-turn conversations."""
    
    def send_message(self, message: str) -> Any:
        """Send a message in the chat session."""
        ...

__version__: str
