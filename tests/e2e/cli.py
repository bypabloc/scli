"""
End-to-end tests for SCLI application

Testing the complete user experience from command execution to output
"""

import pytest
import subprocess
import sys


@pytest.mark.e2e
@pytest.mark.slow
class TestCliE2E:
    """End-to-end tests for the complete CLI application."""
    
    def test_scli_command_via_uv_run(self):
        """
        Test the complete scli command execution via uv run.
        
        This is the actual way users will run the application.
        """
        # Arrange
        cmd = ["uv", "run", "scli"]
        
        # Act
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10  # 10 second timeout for e2e tests
        )
        
        # Assert
        assert result.returncode == 0
        assert "SCLI - Python CLI Project" in result.stdout
        assert "Arguments received: []" in result.stdout
    
    def test_scli_help_via_uv_run(self):
        """
        Test scli --help command via uv run.
        
        Testing complete help functionality end-to-end.
        """
        # Arrange  
        cmd = ["uv", "run", "scli", "--help"]
        
        # Act
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Assert
        assert result.returncode == 0
        assert "SCLI - Python CLI Project" in result.stdout
        assert "Arguments received: ['--help']" in result.stdout
    
    def test_python_direct_execution(self):
        """
        Test direct Python execution of src/main.py.
        
        Alternative execution method that users might use.
        """
        # Arrange
        cmd = ["uv", "run", "python", "src/main.py"]
        
        # Act
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Assert
        assert result.returncode == 0
        assert "SCLI - Python CLI Project" in result.stdout


@pytest.mark.e2e
def test_console_script_entry_point():
    """
    Test that the console script entry point is properly configured.
    
    This verifies the pyproject.toml [project.scripts] configuration.
    """
    # This test uses pytest-console-scripts if available
    pytest.importorskip("pytest_console_scripts")
    
    # The actual implementation would use script_runner fixture
    # from pytest-console-scripts when the project is installed
    pass  # Placeholder for now


@pytest.mark.e2e  
@pytest.mark.slow
class TestSystemIntegration:
    """System-level integration tests."""
    
    def test_application_handles_keyboard_interrupt(self):
        """
        Test that the application handles Ctrl+C gracefully.
        
        Important for CLI applications that might run long operations.
        """
        # This is a placeholder for future interactive features
        # When we add interactive menus, we'll test interrupt handling
        pass
    
    def test_application_handles_invalid_arguments(self):
        """
        Test application behavior with invalid arguments.
        
        CLI applications should handle invalid input gracefully.
        """
        # Arrange
        cmd = ["uv", "run", "scli", "--invalid-flag"]
        
        # Act
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Assert
        # The current implementation doesn't validate arguments,
        # so it should still return 0 and show the arguments
        assert result.returncode == 0
        assert "Arguments received: ['--invalid-flag']" in result.stdout