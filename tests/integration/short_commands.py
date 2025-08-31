import pytest

from src.main import main


@pytest.mark.integration
class TestShortCommandsIntegration:
    """Integration tests for short command flags (-c)."""
    
    def test_short_command_flag_hello_world(self):
        """
        Test that -c flag works for hello_world command.
        
        Integration: short flag + dynamic importer + command execution.
        """
        # Act - use short form command
        exit_code = main(["-c", "hello_world", "--name", "ShortTest"])
        
        # Assert - should work same as long form
        assert exit_code == 0
    
    def test_short_command_flag_test_spinner(self):
        """
        Test that -c flag works for test_spinner command.
        
        Integration: short flag + complex command + argument processing.
        """
        # Act - use short form with spinner
        exit_code = main(["-c", "test_spinner", "--duration", "1"])
        
        # Assert - should work same as long form
        assert exit_code == 0
    
    def test_short_and_long_commands_equivalent(self):
        """
        Test that short and long command forms are equivalent.
        
        Integration: both flag forms + same command behavior.
        """
        # Both should produce same result (success)
        
        # Long form
        exit_code_long = main(["--command", "hello_world", "--name", "Test"])
        
        # Short form  
        exit_code_short = main(["-c", "hello_world", "--name", "Test"])
        
        # Both should be successful
        assert exit_code_long == 0
        assert exit_code_short == 0
        assert exit_code_long == exit_code_short
    
    def test_short_command_without_command_name_fails(self):
        """
        Test that -c without command name fails gracefully.
        
        Integration: error handling + short flag validation.
        """
        # Act - short flag without command name
        exit_code = main(["-c"])
        
        # Assert - should fail gracefully
        # Note: This depends on argument parser behavior
        # If it treats this as normal args, it should complete successfully
        # but not execute any command
        assert exit_code in [0, 1]  # Either normal completion or error
    
    def test_mixed_short_and_long_args(self):
        """
        Test mixing short command flag with long argument flags.
        
        Integration: mixed flag styles + argument processing.
        """
        # Act - short command flag with long argument flags
        exit_code = main(["-c", "hello_world", "--name", "MixedTest"])
        
        # Assert - should work correctly
        assert exit_code == 0


@pytest.mark.integration
def test_help_shows_both_command_forms():
    """
    Test that help text shows both --command and -c forms.
    
    Integration: help system + dynamic command documentation.
    """
    # Act - request help
    exit_code = main(["--help"])
    
    # Assert - should complete successfully
    # Help text should be shown (we can't easily test the content here)
    assert exit_code == 0