import pytest
import inspect
import sys
from typing import get_type_hints

from src.main import main


@pytest.mark.integration
class TestMainIntegration:
    """Integration tests for main function with real components."""
    
    def test_main_with_empty_args_returns_success(self):
        """
        Test that main() integrates properly with system components.
        
        Integration test: main() + sys + print working together.
        """
        # Act - real function call, no mocks
        result = main([])
        
        # Assert - verify behavior
        assert result == 0
    
    def test_main_with_help_args_returns_success(self):
        """
        Test main() handles argument processing correctly.
        
        Integration: main() + argument parsing + output.
        """
        # Act
        result = main(["--help"])
        
        # Assert
        assert result == 0
    
    def test_main_with_various_arguments(self):
        """
        Test main() processes different argument combinations correctly.
        
        Integration test for named flags validation behavior.
        """
        # Test cases with valid named flags (should succeed)
        valid_cases = [
            [],
            ["--help"],
            ["--version"],
            ["--flag", "value"]
        ]
        
        for args in valid_cases:
            # Act
            result = main(args)
            
            # Assert - valid cases should succeed
            assert result == 0, f"Valid args failed: {args}"
            
        # Test cases with positional args (should fail)
        invalid_cases = [
            ["command", "arg1", "arg2"]
        ]
        
        for args in invalid_cases:
            # Act
            result = main(args)
            
            # Assert - invalid cases should fail
            assert result == 1, f"Invalid args should fail but passed: {args}"
    
    def test_main_handles_none_args_integration(self):
        """
        Test main() integrates with sys.argv when args is None.
        
        Integration: main() + sys module + default behavior.
        """
        # This tests the integration between main() and sys.argv
        # We can't easily test this without modifying sys.argv
        # but we can test that the function accepts None
        
        # Act & Assert - should not raise exception
        try:
            # This will use real sys.argv
            result = main(None)
            # Should return 0 (success) with current implementation
            assert isinstance(result, int)
        except Exception as e:
            pytest.fail(f"main(None) should not raise exception: {e}")


@pytest.mark.integration
def test_main_function_integration_with_imports():
    """
    Test that main function integrates properly with its imports.
    
    Verifies all required modules are imported and working together.
    """
    # Integration test: module imports + function definition
    signature = inspect.signature(main)
    type_hints = get_type_hints(main)
    
    # Assert integration is working
    assert 'args' in signature.parameters
    assert 'return' in type_hints
    assert type_hints['return'] == int
    
    # Test that all imports in main.py work together
    assert sys is not None
    
    # Verify the function can be called (integration test)
    result = main([])
    assert isinstance(result, int)
    assert result == 0