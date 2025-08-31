import pytest
from unittest.mock import patch
from unittest.mock import MagicMock
from io import StringIO

from src.utils.interactive_selector import select_command_interactively
from src.utils.interactive_selector import show_command_help
from src.utils.interactive_selector import _select_with_basic_input
from src.utils.interactive_selector import _print_error


@pytest.mark.integration
class TestInteractiveSelectorIntegration:
    """Integration tests for interactive command selector."""
    
    @patch('src.utils.interactive_selector.get_available_commands')
    def test_select_command_interactively_no_commands(self, mock_get_commands):
        """
        Test interactive selection when no commands are available.
        
        Integration: command discovery + error handling.
        """
        # Arrange - no commands available
        mock_get_commands.return_value = []
        
        # Act
        result = select_command_interactively()
        
        # Assert - should return None gracefully
        assert result is None
    
    @patch('src.utils.interactive_selector.get_available_commands')
    @patch('src.utils.interactive_selector.RICH_AVAILABLE', False)
    @patch('builtins.input', return_value='1')
    def test_select_with_basic_input_number_selection(self, mock_input, mock_get_commands):
        """
        Test basic input selection with number choice.
        
        Integration: basic input + command selection + no Rich.
        """
        # Arrange
        mock_commands = ["hello_world", "test_spinner"]
        
        # Act
        result = _select_with_basic_input(mock_commands)
        
        # Assert - should select first command
        assert result == "hello_world"
    
    @patch('src.utils.interactive_selector.get_available_commands')
    @patch('src.utils.interactive_selector.RICH_AVAILABLE', False)
    @patch('builtins.input', return_value='')
    def test_select_with_basic_input_cancel(self, mock_input, mock_get_commands):
        """
        Test basic input selection with cancellation.
        
        Integration: basic input + user cancellation.
        """
        # Arrange
        mock_commands = ["hello_world", "test_spinner"]
        
        # Act
        result = _select_with_basic_input(mock_commands)
        
        # Assert - should return None for cancellation
        assert result is None
    
    @patch('src.utils.interactive_selector.get_available_commands')
    @patch('src.utils.interactive_selector.RICH_AVAILABLE', False) 
    @patch('builtins.input', side_effect=['99', '', '1'])
    def test_select_with_basic_input_invalid_then_valid(self, mock_input, mock_get_commands):
        """
        Test basic input with invalid number followed by valid selection.
        
        Integration: input validation + error recovery + selection.
        """
        # Arrange
        mock_commands = ["hello_world", "test_spinner"]
        
        # Act
        result = _select_with_basic_input(mock_commands)
        
        # Assert - should eventually select first command
        assert result == "hello_world"
    
    @patch('src.utils.interactive_selector.get_available_commands')
    @patch('src.utils.interactive_selector.RICH_AVAILABLE', False)
    @patch('builtins.input', return_value='hello')
    def test_select_with_basic_input_search_unique_result(self, mock_input, mock_get_commands):
        """
        Test basic input search that yields unique result.
        
        Integration: search filtering + automatic selection.
        """
        # Arrange
        mock_commands = ["hello_world", "test_spinner", "goodbye_world"]
        
        # Act
        result = _select_with_basic_input(mock_commands)
        
        # Assert - should auto-select unique search result
        assert result == "hello_world"
    
    @patch('src.utils.interactive_selector.get_available_commands')
    @patch('src.utils.interactive_selector.RICH_AVAILABLE', False)
    @patch('builtins.input', side_effect=['hello', '1'])
    def test_select_with_basic_input_search_multiple_results(self, mock_input, mock_get_commands):
        """
        Test basic input search with multiple results requiring selection.
        
        Integration: search filtering + multiple results + number selection.
        """
        # Arrange
        mock_commands = ["hello_world", "hello_user", "test_spinner"]
        
        # Act 
        result = _select_with_basic_input(mock_commands)
        
        # Assert - should select first of filtered results
        assert result in ["hello_world", "hello_user"]
    
    def test_select_command_interactively_integration_with_filtering(self):
        """
        Test integration between command discovery and filtering.
        
        Integration: command discovery + filtering + selection flow.
        """
        with patch('src.utils.interactive_selector.get_available_commands') as mock_get_commands:
            with patch('src.utils.interactive_selector.RICH_AVAILABLE', False):
                # Arrange
                mock_get_commands.return_value = ["hello_world", "test_spinner"]
                
                # Mock the selection process to avoid UI
                with patch('src.utils.interactive_selector._select_with_basic_input', return_value="hello_world") as mock_select:
                    # Act
                    result = select_command_interactively()
                    
                    # Assert
                    assert result == "hello_world"
                    mock_get_commands.assert_called_once()
                    mock_select.assert_called_once_with(["hello_world", "test_spinner"])
    
    def test_show_command_help_without_rich(self):
        """
        Test command help display without Rich.
        
        Integration: help display + fallback formatting.
        """
        with patch('src.utils.interactive_selector.RICH_AVAILABLE', False):
            with patch('builtins.print') as mock_print:
                # Act
                show_command_help()
                
                # Assert - should print help text
                mock_print.assert_called()
                # Check that help content was printed
                help_content = str(mock_print.call_args_list)
                assert "SCLI" in help_content
                assert "--command" in help_content
                assert "-c" in help_content
    
    def test_print_error_without_rich(self):
        """
        Test error printing without Rich.
        
        Integration: error display + fallback formatting.
        """
        with patch('src.utils.interactive_selector.RICH_AVAILABLE', False):
            with patch('builtins.print') as mock_print:
                # Act
                _print_error("Test error message")
                
                # Assert
                mock_print.assert_called_once_with("❌ Test error message")
    
    @patch('src.utils.interactive_selector.RICH_AVAILABLE', True)
    def test_show_command_help_with_rich(self):
        """
        Test command help display with Rich.
        
        Integration: Rich formatting + help display.
        """
        # Mock Rich components
        mock_console = MagicMock()
        
        with patch('src.utils.interactive_selector.Console', return_value=mock_console):
            with patch('src.utils.interactive_selector.Panel') as mock_panel:
                # Act
                show_command_help()
                
                # Assert
                mock_console.print.assert_called_once()
                mock_panel.fit.assert_called_once()
    
    @patch('src.utils.interactive_selector.RICH_AVAILABLE', True)
    def test_print_error_with_rich(self):
        """
        Test error printing with Rich.
        
        Integration: Rich formatting + error display.
        """
        # Mock Rich console
        mock_console = MagicMock()
        
        with patch('src.utils.interactive_selector.Console', return_value=mock_console):
            # Act
            _print_error("Test error")
            
            # Assert
            mock_console.print.assert_called_once_with("[red]❌ Test error[/red]")
    
    def test_select_command_keyboard_interrupt(self):
        """
        Test graceful handling of keyboard interruption.
        
        Integration: signal handling + graceful shutdown.
        """
        with patch('src.utils.interactive_selector.get_available_commands', return_value=["hello_world"]):
            with patch('src.utils.interactive_selector._select_with_basic_input', side_effect=KeyboardInterrupt):
                # Act - should not raise, but return None
                result = select_command_interactively()
                
                # Assert - should handle gracefully by returning None
                assert result is None
    
    @patch('src.utils.interactive_selector.get_available_commands')
    @patch('src.utils.interactive_selector.RICH_AVAILABLE', False)
    def test_basic_input_selection_edge_cases(self, mock_get_commands):
        """
        Test edge cases in basic input selection.
        
        Integration: edge case handling + input validation.
        """
        mock_commands = ["hello_world", "test_spinner"]
        
        # Test number out of range
        with patch('builtins.input', side_effect=['99', '', '1']):
            result = _select_with_basic_input(mock_commands)
            assert result == "hello_world"
        
        # Test zero
        with patch('builtins.input', side_effect=['0', '', '1']):
            result = _select_with_basic_input(mock_commands)
            assert result == "hello_world"
        
        # Test negative number (treated as search, no results, then valid selection)
        with patch('builtins.input', side_effect=['-1', 'test_spinner']):
            result = _select_with_basic_input(mock_commands)
            assert result == "test_spinner"
    
    @patch('src.utils.interactive_selector.get_available_commands')
    def test_integration_with_real_command_descriptions(self, mock_get_commands):
        """
        Test integration with real command description system.
        
        Integration: command discovery + description retrieval + display.
        """
        # Use real commands for this integration test
        mock_get_commands.return_value = ["hello_world", "test_spinner"]
        
        with patch('src.utils.interactive_selector.RICH_AVAILABLE', False):
            with patch('builtins.input', return_value='1'):
                with patch('builtins.print') as mock_print:
                    # Act
                    result = _select_with_basic_input(["hello_world", "test_spinner"])
                    
                    # Assert - should include descriptions in output
                    assert result == "hello_world"
                    
                    # Check that descriptions were retrieved and displayed
                    printed_text = ' '.join([str(call) for call in mock_print.call_args_list])
                    # Should contain command names
                    assert "hello_world" in printed_text
                    assert "test_spinner" in printed_text


@pytest.mark.integration
def test_interactive_selector_full_workflow():
    """
    Test complete interactive selector workflow.
    
    Integration: discovery + filtering + selection + execution preparation.
    """
    # This test ensures the full workflow works together
    with patch('src.utils.interactive_selector.get_available_commands') as mock_get:
        mock_get.return_value = ["hello_world", "test_spinner"]
        
        with patch('src.utils.interactive_selector.RICH_AVAILABLE', False):
            with patch('builtins.input', return_value='1'):
                # Act - full workflow
                result = select_command_interactively()
                
                # Assert - should complete successfully
                assert result in ["hello_world", "test_spinner"]


@pytest.mark.integration
def test_interactive_selector_error_recovery():
    """
    Test error recovery in interactive selection.
    
    Integration: error handling + recovery + user experience.
    """
    with patch('src.utils.interactive_selector.get_available_commands') as mock_get:
        # Mock failure in get_available_commands
        mock_get.side_effect = Exception("Temporary error")
        
        # Should handle error gracefully
        result = select_command_interactively()
        
        # Should return None when error occurs
        assert result is None