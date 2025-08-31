from sys import stdout as sys_stdout
from time import sleep as time_sleep
from threading import Thread as threading_Thread
from threading import Event as threading_Event
from typing import Optional
from typing import List
from typing import Union
from typing import Iterator
from contextlib import contextmanager

from src.utils.logger import logger

try:
    from settings.config import app_config
except ImportError:
    # Fallback configuration if settings not available
    class MockConfig:
        spinner_enabled = True
        spinner_style = 'dots'
        spinner_speed = 0.1
        
    app_config = MockConfig()


class SpinnerFrames:
    """Pre-defined spinner animation frames with various effects."""
    
    # Claude Code inspired morphing text spinner with letter-by-letter brightness
    MORPHING_TEXT = [
        "✨ Processing...",
        "🌟 Processing...",
        "⭐ Processing...",
        "💫 Processing...",
        "✨ Processing...",
        "🌟 Processing...",
        "⭐ Processing...",
        "💫 Processing...",
    ]
    
    # Letter-by-letter brightness effect
    LETTER_BRIGHTNESS = [
        "✨ Processing...",
        "✨ 🌟rocessing...",
        "✨ P🌟ocessing...",
        "✨ Pr🌟cessing...",
        "✨ Pro🌟essing...",
        "✨ Proc🌟ssing...",
        "✨ Proce🌟sing...",
        "✨ Proces🌟ing...",
        "✨ Process🌟ng...",
        "✨ Processi🌟g...",
        "✨ Processin🌟...",
        "✨ Processing🌟..",
        "✨ Processing.🌟.",
        "✨ Processing..🌟",
        "✨ Processing...",
        "⭐ Processing...",
        "⭐ 💫rocessing...",
        "⭐ P💫ocessing...",
        "⭐ Pr💫cessing...",
        "⭐ Pro💫essing...",
        "⭐ Proc💫ssing...",
        "⭐ Proce💫sing...",
        "⭐ Proces💫ing...",
        "⭐ Process💫ng...",
        "⭐ Processi💫g...",
        "⭐ Processin💫...",
        "⭐ Processing💫..",
        "⭐ Processing.💫.",
        "⭐ Processing..💫",
        "⭐ Processing...",
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
        interval: float = None,
        text: str = "",
        stream=None
    ):
        """
        Initialize spinner with custom or predefined frames using app_config.
        
        Args:
            frames: List of animation frames (defaults based on app_config.spinner_style)
            interval: Time between frame updates in seconds (defaults to app_config.spinner_speed)
            text: Additional text to display after spinner
            stream: Output stream (defaults to sys.stdout)
        """
        # Use configured spinner style if frames not specified
        if frames is None:
            frames = self._get_frames_from_config()
        self.frames = frames
        
        # Use configured spinner speed if interval not specified
        self.interval = interval if interval is not None else app_config.spinner_speed
        self.text = text
        self.stream = stream or sys_stdout
        self._stop_event = threading_Event()
        self._thread: Optional[threading_Thread] = None
        self._current_frame = 0
        self._is_running = False
    
    def _get_frames_from_config(self) -> List[str]:
        """Get spinner frames based on app_config.spinner_style."""
        style = app_config.spinner_style or 'dots'
        
        style_map = {
            'dots': SpinnerFrames.LETTER_BRIGHTNESS,
            'line': SpinnerFrames.BRIGHTNESS_DOTS,
            'pipe': SpinnerFrames.PULSE_INTENSITY,
            'simpleDots': SpinnerFrames.CLAUDE_STYLE,
            'simpleDotsScrolling': SpinnerFrames.MORPHING_TEXT
        }
        
        return style_map.get(style, SpinnerFrames.LETTER_BRIGHTNESS)
    
    def _generate_brightness_frames(self, text: str) -> List[str]:
        """Generate letter-by-letter color gradient frames for given text with morphing spinner."""
        if not text:
            return ["\033[36m✢ Processing...\033[0m"]
        
        frames = []
        text_with_dots = f"{text}..."
        
        # Original morphing spinner icons
        spinner_icons = [
            "✢", "✦", "✧", "✶", "✷", "✽", "✾", "❋"
        ]
        
        # Brightness levels for cyan color gradient (dim to bright)
        brightness_levels = [
            '\033[2;36m',   # Dim cyan
            '\033[36m',     # Normal cyan
            '\033[1;36m',   # Bold cyan
            '\033[1;96m',   # Bold bright cyan
            '\033[97m',     # Bright white
            '\033[1;97m',   # Bold bright white
            '\033[1;96m',   # Bold bright cyan (fade back)
            '\033[1;36m',   # Bold cyan (fade back)
        ]
        reset = '\033[0m'
        
        # Base color for text (normal cyan)
        base_color = '\033[36m'
        spinner_color = '\033[36m'  # Same cyan color as text
        
        # Generate frames with brightness gradient effect and morphing spinner
        for cycle in range(2):  # Two cycles for smooth animation
            for highlight_pos in range(len(text_with_dots)):
                colored_text = ""
                for i, char in enumerate(text_with_dots):
                    if i == highlight_pos:
                        # Use brightness levels for highlighted character
                        brightness_index = (cycle * len(text_with_dots) + i) % len(brightness_levels)
                        colored_text += f"{brightness_levels[brightness_index]}{char}{reset}"
                    else:
                        # Use base color for other characters
                        colored_text += f"{base_color}{char}{reset}"
                
                # Get morphing spinner icon
                spinner_index = (cycle * len(text_with_dots) + highlight_pos) % len(spinner_icons)
                spinner_icon = spinner_icons[spinner_index]
                
                # Create frame with morphing spinner and colored text
                frame = f"{spinner_color}{spinner_icon}{reset} {colored_text}"
                frames.append(frame)
        
        return frames

    def _spin(self):
        """Internal spinning animation loop with dynamic text brightness and proper line clearing."""
        frame_index = 0
        current_text = self.text
        brightness_frames = self._generate_brightness_frames(current_text) if current_text else self.frames
        
        while not self._stop_event.is_set():
            # Check if text changed and regenerate frames if needed
            if current_text != self.text:
                current_text = self.text
                brightness_frames = self._generate_brightness_frames(current_text) if current_text else self.frames
                frame_index = 0  # Reset frame index for new text
            
            frame = brightness_frames[frame_index % len(brightness_frames)]
            
            # Clear line and write frame (use fixed width clearing)
            self.stream.write('\r' + ' ' * 50 + '\r' + frame)
            self.stream.flush()
            
            # Move to next frame
            frame_index += 1
            
            # Wait for next frame
            self._stop_event.wait(self.interval)
    
    def start(self, text: Optional[str] = None):
        """
        Start the spinner animation if enabled in app_config.
        
        Args:
            text: Optional text to display (overrides instance text)
        """
        # Check if spinners are enabled in configuration
        if not app_config.spinner_enabled:
            # If spinners are disabled, just show the text without animation
            if text or self.text:
                display_text = text or self.text
                self.stream.write(f"{display_text}... ")
                self.stream.flush()
            return
        
        if self._is_running:
            logger.warning("Spinner already running")
            return
        
        if text is not None:
            self.text = text
        
        self._stop_event.clear()
        self._current_frame = 0
        self._is_running = True
        
        logger.debug("Starting spinner animation", detail={
            "text": self.text,
            "style": app_config.spinner_style or 'dots',
            "speed": self.interval
        })
        
        # Hide cursor for cleaner output
        self.stream.write('\033[?25l')
        self.stream.flush()
        
        # Start animation thread
        self._thread = threading_Thread(target=self._spin, daemon=True)
        self._thread.start()
    
    def stop(self, final_text: Optional[str] = None):
        """
        Stop the spinner and optionally display final text.
        
        Args:
            final_text: Text to display after stopping spinner
        """
        if not self._is_running:
            return
        
        # Signal stop and wait for thread
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        
        # Complete cleaning: clear current line and move up to clear previous lines
        self.stream.write('\r' + ' ' * 80 + '\r')  # Clear current line completely
        self.stream.write('\033[1A\033[K')  # Move up and clear that line too
        self.stream.write('\r')  # Return to start of line
        
        # Show final text if provided with line break
        if final_text:
            self.stream.write(f"{final_text}\n")
        
        # Restore cursor
        self.stream.write('\033[?25h')
        self.stream.flush()
        
        logger.debug("Stopping spinner animation")
        
        self._is_running = False
        self._thread = None
    
    def update_text(self, new_text: str):
        """Update spinner text while running and regenerate brightness frames."""
        self.text = new_text
        # The frames will be regenerated in the next _spin iteration
    
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
def create_spinner(text: str = "Processing", style: str = None, speed: float = None) -> Spinner:
    """
    Create a spinner using app_config settings with optional overrides.
    
    Args:
        text: Text to display during processing
        style: Spinner style override (uses app_config.spinner_style if None)
        speed: Speed override (uses app_config.spinner_speed if None)
    
    Returns:
        Configured Spinner instance
    """
    return Spinner(text=text, interval=speed)


def morphing_text_spinner(text: str = "Processing") -> Spinner:
    """Create a morphing text spinner like Claude Code."""
    return Spinner(
        frames=SpinnerFrames.MORPHING_TEXT,
        interval=app_config.spinner_speed or 0.15,
        text=text
    )


def brightness_spinner(text: str = "Loading") -> Spinner:
    """Create a brightness-morphing spinner."""
    return Spinner(
        frames=SpinnerFrames.BRIGHTNESS_DOTS,
        interval=app_config.spinner_speed or 0.12,
        text=text
    )


def pulse_spinner(text: str = "Working") -> Spinner:
    """Create a pulsing intensity spinner."""
    return Spinner(
        frames=SpinnerFrames.PULSE_INTENSITY,
        interval=app_config.spinner_speed or 0.08,
        text=text
    )


def claude_style_spinner(text: str = "Updating") -> Spinner:
    """Create a Claude Code style morphing text spinner."""
    return Spinner(
        frames=SpinnerFrames.CLAUDE_STYLE,
        interval=app_config.spinner_speed or 0.18,
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
    'create_spinner',
    'morphing_text_spinner',
    'brightness_spinner',
    'pulse_spinner',
    'claude_style_spinner',
    'show_spinner'
]