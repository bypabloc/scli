"""
SCLI Spinner Utility

Advanced loading indicators with morphing text, brightness effects, and innovative animations.
Inspired by Claude Code's dynamic spinner patterns with gradual character transitions.

Features:
- Morphing text spinners with brightness effects
- Unicode-based animations with character transitions
- Context manager support for easy integration
- Custom spinner patterns with configurable timing
- Thread-safe operations with proper cleanup
"""

import time
import threading
import sys
from typing import Optional, List, Union, Iterator
from contextlib import contextmanager
from src.utils.logger import logger


class SpinnerFrames:
    """Pre-defined spinner animation frames with various effects."""
    
    # Claude Code inspired morphing text spinner
    MORPHING_TEXT = [
        "✢",     # Initial symbol
        "✢ F",   # Starting text
        "✢ Fi",  # Growing
        "✢ Fix", # Complete word
        "✦ Fix", # Symbol change
        "✦ U",   # New word starts  
        "✧ Up",  # Morphing symbol + text
        "✧ Upd", # Growing
        "✶ Upda", # Symbol change
        "✶ Updat", # Growing
        "✶ Updati", # Growing
        "✷ Updatin", # Symbol morph
        "✷ Updating", # Complete
        "✽ Updating", # Final symbol
        "✾ Updating", # Brightness effect
        "❋ Updating", # Peak brightness
        "✽ Updating", # Fade back
        "✷ Updating", # Continue fade
        "✶ Updating", # Mid fade
        "✧ Updating", # Lower brightness
        "✦ Updating", # Dim
        "✢ Updating", # Back to start
    ]
    
    # Brightness morphing dots
    BRIGHTNESS_DOTS = [
        "⚫", "⚫", "⚫",  # Dark
        "⚪", "⚪", "⚪",  # Light
        "🔘", "🔘", "🔘",  # Medium
        "⭕", "⭕", "⭕",  # Bright
        "🟡", "🟡", "🟡",  # Golden
        "⭐", "⭐", "⭐",  # Star bright
        "✨", "✨", "✨",  # Sparkle
        "💫", "💫", "💫",  # Dizzy
        "🌟", "🌟", "🌟",  # Glowing star
    ]
    
    # Technical progress indicators
    TECH_PROGRESS = [
        "[   ]", "[=  ]", "[== ]", "[===]",
        "[  =]", "[ ==]", "[===]", "[== ]",
        "[=  ]", "[   ]"
    ]
    
    # Unicode geometric morphing
    GEOMETRIC_MORPH = [
        "◐", "◓", "◑", "◒",  # Half circles
        "◯", "◉", "⬤", "●",  # Filled circles
        "◆", "◇", "◈", "◉",  # Diamonds to circles
        "▲", "△", "▼", "▽",  # Triangles
        "■", "□", "▪", "▫",  # Squares
    ]
    
    # Pulse effect with varying intensity
    PULSE_INTENSITY = [
        "◦", "◦", "◦",      # Very dim
        "○", "○", "○",      # Dim 
        "⚬", "⚬", "⚬",      # Medium
        "⚪", "⚪", "⚪",      # Bright
        "⭕", "⭕", "⭕",      # Very bright
        "🔴", "🔴", "🔴",     # Peak intensity
        "⭕", "⭕", "⭕",      # Fade down
        "⚪", "⚪", "⚪",      # Bright
        "⚬", "⚬", "⚬",      # Medium
        "○", "○", "○",      # Dim
    ]
    
    # Text morphing like Claude Code
    CLAUDE_STYLE = [
        "●", "● L", "● Lo", "● Loa", "● Load",
        "◐ Loadi", "◓ Loadin", "◑ Loading",
        "◒ Loading", "○ Loading", "⚪ Loading",
        "⭕ Loading", "🔵 Loading", "🟢 Loading"
    ]


class Spinner:
    """
    Advanced spinner with morphing animations and brightness effects.
    
    Features:
    - Thread-safe spinning animation
    - Customizable frames and timing
    - Context manager support
    - Clean terminal output management
    """
    
    def __init__(
        self, 
        frames: Optional[List[str]] = None,
        interval: float = 0.1,
        text: str = "",
        stream=None
    ):
        """
        Initialize spinner with custom or predefined frames.
        
        Args:
            frames: List of animation frames (defaults to MORPHING_TEXT)
            interval: Time between frame updates in seconds
            text: Additional text to display after spinner
            stream: Output stream (defaults to sys.stdout)
        """
        self.frames = frames or SpinnerFrames.MORPHING_TEXT
        self.interval = interval
        self.text = text
        self.stream = stream or sys.stdout
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._current_frame = 0
        self._is_running = False
    
    def _spin(self):
        """Internal spinning animation loop."""
        while not self._stop_event.is_set():
            frame = self.frames[self._current_frame]
            display_text = f"\r{frame}"
            if self.text:
                display_text += f" {self.text}"
            
            # Write without newline and flush
            self.stream.write(display_text)
            self.stream.flush()
            
            # Move to next frame
            self._current_frame = (self._current_frame + 1) % len(self.frames)
            
            # Wait for next frame
            self._stop_event.wait(self.interval)
    
    def start(self, text: Optional[str] = None):
        """
        Start the spinner animation.
        
        Args:
            text: Optional text to display (overrides instance text)
        """
        if self._is_running:
            logger.warning("Spinner already running")
            return
        
        if text is not None:
            self.text = text
        
        logger.debug("Starting spinner animation", detail={"text": self.text})
        
        self._stop_event.clear()
        self._current_frame = 0
        self._is_running = True
        
        # Hide cursor for cleaner output
        self.stream.write('\033[?25l')
        self.stream.flush()
        
        # Start animation thread
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()
    
    def stop(self, final_text: Optional[str] = None):
        """
        Stop the spinner and optionally display final text.
        
        Args:
            final_text: Text to display after stopping spinner
        """
        if not self._is_running:
            return
        
        logger.debug("Stopping spinner animation")
        
        # Signal stop and wait for thread
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        
        # Clear spinner line
        self.stream.write('\r' + ' ' * 80 + '\r')
        
        # Show final text if provided
        if final_text:
            self.stream.write(f"{final_text}\n")
        
        # Restore cursor
        self.stream.write('\033[?25h')
        self.stream.flush()
        
        self._is_running = False
        self._thread = None
    
    def update_text(self, new_text: str):
        """Update spinner text while running."""
        self.text = new_text
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        if exc_type is not None:
            # Error occurred, show error state
            self.stop("❌ Error occurred")
            logger.error("Spinner stopped due to error", detail={
                "exception_type": str(exc_type.__name__),
                "exception_value": str(exc_val)
            })
        else:
            # Normal completion
            self.stop("✅ Complete")


# Predefined spinner configurations
def morphing_text_spinner(text: str = "Processing") -> Spinner:
    """Create a morphing text spinner like Claude Code."""
    return Spinner(
        frames=SpinnerFrames.MORPHING_TEXT,
        interval=0.15,
        text=text
    )


def brightness_spinner(text: str = "Loading") -> Spinner:
    """Create a brightness-morphing spinner."""
    return Spinner(
        frames=SpinnerFrames.BRIGHTNESS_DOTS,
        interval=0.12,
        text=text
    )


def pulse_spinner(text: str = "Working") -> Spinner:
    """Create a pulsing intensity spinner."""
    return Spinner(
        frames=SpinnerFrames.PULSE_INTENSITY,
        interval=0.08,
        text=text
    )


def claude_style_spinner(text: str = "Updating") -> Spinner:
    """Create a Claude Code style morphing text spinner."""
    return Spinner(
        frames=SpinnerFrames.CLAUDE_STYLE,
        interval=0.18,
        text=text
    )


# Convenience context managers
@contextmanager
def show_spinner(
    spinner_type: str = "morphing", 
    text: str = "Processing",
    success_text: str = "✅ Complete",
    error_text: str = "❌ Failed"
):
    """
    Context manager for easy spinner usage.
    
    Args:
        spinner_type: Type of spinner ("morphing", "brightness", "pulse", "claude")
        text: Text to display during processing
        success_text: Text to show on success
        error_text: Text to show on error
    
    Usage:
        with show_spinner("morphing", "Loading data"):
            # Long running operation
            time.sleep(3)
    """
    spinner_map = {
        "morphing": morphing_text_spinner,
        "brightness": brightness_spinner, 
        "pulse": pulse_spinner,
        "claude": claude_style_spinner
    }
    
    spinner_func = spinner_map.get(spinner_type, morphing_text_spinner)
    spinner = spinner_func(text)
    
    try:
        spinner.start()
        yield spinner
        spinner.stop(success_text)
        logger.success("Operation completed successfully")
    except Exception as e:
        spinner.stop(error_text)
        logger.error("Operation failed", detail={"error": str(e)})
        raise


# Export public API
__all__ = [
    'Spinner',
    'SpinnerFrames',
    'morphing_text_spinner',
    'brightness_spinner',
    'pulse_spinner',
    'claude_style_spinner',
    'show_spinner'
]