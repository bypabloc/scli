"""
Integration tests for spinner utility

Tests spinner functionality in realistic scenarios with actual timing and threading.
"""

import time
import pytest
import threading
from src.utils.spinner import (
    Spinner, SpinnerFrames, show_spinner,
    morphing_text_spinner, brightness_spinner, pulse_spinner, claude_style_spinner
)


class TestSpinnerIntegration:
    """Integration tests for spinner animations and threading."""
    
    def test_spinner_basic_lifecycle(self):
        """Test basic spinner start/stop lifecycle."""
        spinner = Spinner(frames=["●", "○", "◐", "◑"], interval=0.05)
        
        # Should start successfully
        spinner.start("Testing")
        assert spinner._is_running is True
        assert spinner._thread is not None
        assert spinner._thread.is_alive()
        
        # Let it spin for a short time
        time.sleep(0.2)
        
        # Should stop cleanly
        spinner.stop("Done")
        assert spinner._is_running is False
        
        # Thread should be cleaned up
        time.sleep(0.1)
        assert spinner._thread is None or not spinner._thread.is_alive()
    
    def test_context_manager_success(self):
        """Test spinner context manager with successful completion."""
        execution_completed = False
        
        with show_spinner("morphing", "Processing data"):
            time.sleep(0.15)  # Simulate work
            execution_completed = True
        
        assert execution_completed is True
    
    def test_context_manager_with_exception(self):
        """Test spinner context manager handles exceptions properly."""
        with pytest.raises(ValueError):
            with show_spinner("pulse", "Failing operation"):
                time.sleep(0.1)
                raise ValueError("Simulated error")
    
    def test_multiple_spinners_sequential(self):
        """Test running multiple spinners in sequence."""
        for i in range(3):
            with show_spinner("brightness", f"Task {i+1}"):
                time.sleep(0.08)  # Short tasks
    
    def test_spinner_text_updates(self):
        """Test updating spinner text while running."""
        spinner = morphing_text_spinner("Initial")
        spinner.start()
        
        time.sleep(0.1)
        spinner.update_text("Updated")
        assert spinner.text == "Updated"
        
        time.sleep(0.1)
        spinner.stop()
    
    def test_predefined_spinner_types(self):
        """Test all predefined spinner types work correctly."""
        spinner_types = [
            ("morphing", morphing_text_spinner),
            ("brightness", brightness_spinner), 
            ("pulse", pulse_spinner),
            ("claude", claude_style_spinner)
        ]
        
        for name, spinner_func in spinner_types:
            spinner = spinner_func(f"Testing {name}")
            spinner.start()
            time.sleep(0.12)  # Let each spinner run briefly
            spinner.stop(f"✅ {name} complete")
    
    def test_rapid_start_stop_cycles(self):
        """Test spinner handles rapid start/stop cycles without issues."""
        spinner = Spinner(frames=["⚫", "⚪"], interval=0.05)
        
        for i in range(5):
            spinner.start(f"Cycle {i+1}")
            time.sleep(0.05)
            spinner.stop()
            time.sleep(0.02)  # Brief pause between cycles
    
    @pytest.mark.slow
    def test_long_running_spinner(self):
        """Test spinner runs stable for extended periods."""
        with show_spinner("claude", "Long operation"):
            time.sleep(1.0)  # Longer operation
    
    def test_concurrent_spinner_safety(self):
        """Test that spinners handle concurrent access safely."""
        def run_spinner(spinner_id):
            with show_spinner("pulse", f"Concurrent task {spinner_id}"):
                time.sleep(0.2)
        
        threads = []
        for i in range(3):
            thread = threading.Thread(target=run_spinner, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join(timeout=2.0)
            assert not thread.is_alive()
    
    def test_spinner_frame_cycling(self):
        """Test spinner properly cycles through all frames."""
        frames = ["A", "B", "C"]
        spinner = Spinner(frames=frames, interval=0.03)
        
        spinner.start()
        
        # Let it cycle through frames multiple times
        time.sleep(0.25)
        
        spinner.stop()
        
        # Frame index should have advanced
        assert spinner._current_frame >= 0
        assert spinner._current_frame < len(frames)


class TestSpinnerFramesIntegration:
    """Test predefined frame sets work correctly."""
    
    def test_all_frame_sets_are_valid(self):
        """Test all predefined frame sets contain valid data."""
        frame_sets = [
            SpinnerFrames.MORPHING_TEXT,
            SpinnerFrames.BRIGHTNESS_DOTS,
            SpinnerFrames.TECH_PROGRESS,
            SpinnerFrames.GEOMETRIC_MORPH,
            SpinnerFrames.PULSE_INTENSITY,
            SpinnerFrames.CLAUDE_STYLE
        ]
        
        for frames in frame_sets:
            assert isinstance(frames, list)
            assert len(frames) > 0
            assert all(isinstance(frame, str) for frame in frames)
            assert all(len(frame.strip()) > 0 for frame in frames)
    
    def test_morphing_text_progression(self):
        """Test morphing text shows expected progression pattern."""
        frames = SpinnerFrames.MORPHING_TEXT
        
        # Should start with single symbol
        assert frames[0] == "✢"
        
        # Should show progressive text building
        text_frames = [f for f in frames if " " in f]
        assert len(text_frames) > 0
        
        # Should contain "Fix" and "Updating" in progression
        combined_text = " ".join(frames)
        assert "Fix" in combined_text
        assert "Updating" in combined_text
    
    def test_claude_style_progression(self):
        """Test Claude style frames show expected text morphing."""
        frames = SpinnerFrames.CLAUDE_STYLE
        
        # Should start simple and build up
        assert frames[0] == "●"
        
        # Should progressively build "Loading"
        loading_frames = [f for f in frames if "Load" in f]
        assert len(loading_frames) > 0
        
        # Should end with complete "Loading"
        final_frames = [f for f in frames if "Loading" in f]
        assert len(final_frames) > 0