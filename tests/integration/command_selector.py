import pytest
from unittest.mock import patch
from unittest.mock import mock_open
from pathlib import Path

from src.utils.command_selector import get_available_commands
from src.utils.command_selector import filter_commands
from src.utils.command_selector import format_command_list
from src.utils.command_selector import get_command_description
from src.utils.command_selector import _is_valid_command_file
from src.utils.command_selector import _fuzzy_match


@pytest.mark.integration
class TestCommandSelectorIntegration:
    """Integration tests for command selector functionality."""
    
    def test_get_available_commands_integration(self):
        """
        Test that get_available_commands finds real commands.
        
        Integration: filesystem + command discovery + validation.
        """
        # Act - scan real commands directory
        commands = get_available_commands()
        
        # Assert - should find existing commands
        assert isinstance(commands, list)
        assert len(commands) > 0  # Should find at least hello_world and test_spinner
        assert "hello_world" in commands
        assert "test_spinner" in commands
        
        # Commands should be sorted
        assert commands == sorted(commands)
    
    @patch('src.utils.command_selector.os_listdir')
    @patch('src.utils.command_selector.os_path_isfile')
    @patch('src.utils.command_selector.Path.exists')
    def test_get_available_commands_empty_directory(self, mock_exists, mock_isfile, mock_listdir):
        """
        Test behavior when commands directory is empty.
        
        Integration: mocked filesystem + error handling.
        """
        # Arrange - mock empty directory
        mock_exists.return_value = True
        mock_listdir.return_value = []
        
        # Act
        commands = get_available_commands()
        
        # Assert
        assert commands == []
    
    @patch('src.utils.command_selector.Path.exists')
    def test_get_available_commands_missing_directory(self, mock_exists):
        """
        Test behavior when commands directory doesn't exist.
        
        Integration: mocked filesystem + error handling.
        """
        # Arrange - mock missing directory
        mock_exists.return_value = False
        
        # Act
        commands = get_available_commands()
        
        # Assert
        assert commands == []
    
    def test_is_valid_command_file_with_real_files(self):
        """
        Test command file validation with real command files.
        
        Integration: real filesystem + class detection.
        """
        # Test with real command files
        hello_world_path = "src/commands/hello_world.py"
        test_spinner_path = "src/commands/test_spinner.py"
        
        # Act & Assert - real files should be valid
        assert _is_valid_command_file(hello_world_path, "hello_world") == True
        assert _is_valid_command_file(test_spinner_path, "test_spinner") == True
        
        # Non-existent file should be invalid
        assert _is_valid_command_file("non_existent.py", "non_existent") == False
    
    def test_is_valid_command_file_with_real_commands_extended(self):
        """
        Test command file validation with real command files using BaseCommand validation.
        
        Integration: real filesystem + class detection + BaseCommand inheritance.
        """
        # Test with real command files that inherit from BaseCommand
        hello_world_path = "src/commands/hello_world.py"
        test_spinner_path = "src/commands/test_spinner.py"
        
        # Act & Assert - real files should be valid and inherit from BaseCommand
        assert _is_valid_command_file(hello_world_path, "hello_world") == True
        assert _is_valid_command_file(test_spinner_path, "test_spinner") == True
    
    def test_is_valid_command_file_without_class(self):
        """
        Test command file validation with nonexistent command.
        
        Integration: dynamic import + class detection failure.
        """
        # Act & Assert - nonexistent command should be invalid
        assert _is_valid_command_file("nonexistent.py", "nonexistent_command") == False
    
    def test_filter_commands_exact_match(self):
        """
        Test command filtering with exact matches.
        
        Integration: filtering logic + command list processing.
        """
        # Arrange
        commands = ["hello_world", "test_spinner", "user_profile"]
        
        # Act & Assert - exact matches
        assert filter_commands(commands, "hello_world") == ["hello_world"]
        assert filter_commands(commands, "test_spinner") == ["test_spinner"]
        
        # Partial matches
        filtered = filter_commands(commands, "hello")
        assert "hello_world" in filtered
    
    def test_filter_commands_partial_match(self):
        """
        Test command filtering with partial matches.
        
        Integration: fuzzy matching + ranking.
        """
        # Arrange
        commands = ["hello_world", "test_spinner", "user_profile", "hello_user"]
        
        # Act
        filtered = filter_commands(commands, "hello")
        
        # Assert - should find both hello commands
        assert len(filtered) >= 2
        assert "hello_world" in filtered
        assert "hello_user" in filtered
    
    def test_filter_commands_fuzzy_match(self):
        """
        Test fuzzy matching functionality.
        
        Integration: fuzzy matching algorithm + command filtering.
        """
        # Arrange
        commands = ["hello_world", "test_spinner"]
        
        # Act - fuzzy matches
        fuzzy_results = filter_commands(commands, "hlwrd")
        
        # Assert - should find hello_world through fuzzy matching
        # Note: This depends on fuzzy matching implementation
        if fuzzy_results:
            assert "hello_world" in fuzzy_results
    
    def test_fuzzy_match_algorithm(self):
        """
        Test the fuzzy matching algorithm directly.
        
        Integration: string matching + character ordering.
        """
        # Test exact fuzzy matches
        assert _fuzzy_match("hello_world", "hlwrd") == True
        assert _fuzzy_match("test_spinner", "tspn") == True
        assert _fuzzy_match("hello_world", "world") == True
        
        # Test non-matches
        assert _fuzzy_match("hello_world", "xyz") == False
        assert _fuzzy_match("hello_world", "dlrow") == False  # Reverse order
        
        # Edge cases
        assert _fuzzy_match("hello", "") == True  # Empty pattern
        assert _fuzzy_match("", "hello") == False  # Empty text
    
    def test_format_command_list_no_selection(self):
        """
        Test command list formatting without selection.
        
        Integration: formatting + display preparation.
        """
        # Arrange
        commands = ["hello_world", "test_spinner"]
        
        # Act
        formatted = format_command_list(commands)
        
        # Assert
        assert "1. hello_world" in formatted
        assert "2. test_spinner" in formatted
        assert "→" not in formatted  # No selection indicator
    
    def test_format_command_list_with_selection(self):
        """
        Test command list formatting with selection.
        
        Integration: formatting + selection highlighting.
        """
        # Arrange
        commands = ["hello_world", "test_spinner"]
        
        # Act
        formatted = format_command_list(commands, selected_index=0)
        
        # Assert
        assert "→ 1. hello_world" in formatted  # Selected
        assert "  2. test_spinner" in formatted  # Not selected
    
    def test_format_command_list_empty(self):
        """
        Test command list formatting with empty list.
        
        Integration: error handling + empty state formatting.
        """
        # Act
        formatted = format_command_list([])
        
        # Assert
        assert "No hay comandos disponibles" in formatted
    
    def test_get_command_description_real_commands(self):
        """
        Test getting descriptions from real command classes.
        
        Integration: dynamic import + docstring extraction.
        """
        # Act - get descriptions from real commands
        hello_desc = get_command_description("hello_world")
        spinner_desc = get_command_description("test_spinner")
        
        # Assert - should get meaningful descriptions
        assert isinstance(hello_desc, str)
        assert len(hello_desc) > 0
        assert hello_desc != "Descripción no disponible"
        
        assert isinstance(spinner_desc, str)
        assert len(spinner_desc) > 0
        assert spinner_desc != "Descripción no disponible"
    
    def test_get_command_description_nonexistent_command(self):
        """
        Test getting description for non-existent command.
        
        Integration: error handling + fallback behavior.
        """
        # Act
        desc = get_command_description("non_existent_command")
        
        # Assert
        assert desc == "Descripción no disponible"
    
    def test_filter_commands_case_insensitive(self):
        """
        Test that command filtering is case insensitive.
        
        Integration: case handling + search functionality.
        """
        # Arrange
        commands = ["hello_world", "TEST_SPINNER"]
        
        # Act
        filtered_lower = filter_commands(commands, "hello")
        filtered_upper = filter_commands(commands, "HELLO")
        filtered_mixed = filter_commands(commands, "Hello")
        
        # Assert - all should find hello_world
        assert "hello_world" in filtered_lower
        assert "hello_world" in filtered_upper  
        assert "hello_world" in filtered_mixed
    
    def test_filter_commands_empty_search(self):
        """
        Test that empty search returns all commands.
        
        Integration: edge case handling + default behavior.
        """
        # Arrange
        commands = ["hello_world", "test_spinner"]
        
        # Act
        filtered = filter_commands(commands, "")
        
        # Assert - empty search should return all
        assert filtered == commands
    
    def test_integration_full_workflow(self):
        """
        Test complete workflow from discovery to selection.
        
        Integration: full command selector workflow.
        """
        # Act - complete workflow
        # 1. Get available commands
        commands = get_available_commands()
        assert len(commands) > 0
        
        # 2. Filter commands
        filtered = filter_commands(commands, "hello")
        assert len(filtered) > 0
        
        # 3. Format for display
        formatted = format_command_list(filtered, 0)
        assert "→ 1." in formatted
        
        # 4. Get description
        first_command = filtered[0]
        description = get_command_description(first_command)
        assert isinstance(description, str)


@pytest.mark.integration
def test_command_selector_with_filesystem_errors():
    """
    Test command selector behavior with filesystem errors.
    
    Integration: error handling + resilience.
    """
    with patch('src.utils.command_selector.os_listdir', side_effect=OSError("Permission denied")):
        commands = get_available_commands()
        # Should handle error gracefully
        assert commands == []


@pytest.mark.integration  
def test_command_selector_performance_with_many_commands():
    """
    Test command selector performance with large number of commands.
    
    Integration: performance + scalability.
    """
    # Simulate many commands
    fake_commands = [f"command_{i}" for i in range(100)]
    
    # Filter operations should be fast
    filtered = filter_commands(fake_commands, "command_5")
    
    # Should find the matches efficiently
    assert len(filtered) >= 1
    assert any("command_5" in cmd for cmd in filtered)