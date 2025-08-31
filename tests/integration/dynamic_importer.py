import pytest

from src.utils.dynamic_importer import import_command
from src.utils.dynamic_importer import create_command_instance
from src.utils.dynamic_importer import execute_command_cycle
from src.utils.result_types import is_success
from src.utils.result_types import is_error
from src.utils.base_command import BaseCommand


@pytest.mark.integration
class TestDynamicImporterIntegration:
    """Integration tests for dynamic command importer system."""
    
    def test_import_existing_command_integration(self):
        """
        Test dynamic import of existing command works correctly.
        
        Integration: import_module + getattr + BaseCommand validation.
        """
        # Act - import existing command
        result = import_command("hello_world")
        
        # Assert - import was successful
        assert is_success(result), f"Import should succeed, got: {result}"
        assert result['class'] is not None
        assert result['data']['class_name'] == "HelloWorld"
        assert result['data']['operation'] == "hello_world"
        assert hasattr(result['data']['module'], 'HelloWorld')
        
        # Verify class is subclass of BaseCommand
        command_class = result['class']
        assert issubclass(command_class, BaseCommand)
    
    def test_import_test_spinner_command_integration(self):
        """
        Test import of test_spinner command works correctly.
        
        Integration: snake_case conversion + module loading + class access.
        """
        # Act - import test_spinner command
        result = import_command("test_spinner")
        
        # Assert - import successful
        assert is_success(result)
        assert result['data']['class_name'] == "TestSpinner"
        assert result['class'].__name__ == "TestSpinner"
        
        # Verify it's a valid command class
        assert issubclass(result['class'], BaseCommand)
    
    def test_import_nonexistent_command_fails(self):
        """
        Test that importing non-existent command fails gracefully.
        
        Integration: error handling + module not found + result types.
        """
        # Act - try to import non-existent command
        result = import_command("non_existent_command")
        
        # Assert - import should fail
        assert is_error(result)
        assert result['class'] is None
        assert result['data']['error_code'] == "MODULE_NOT_FOUND"
        assert "non_existent_command" in result['data']['message']
    
    def test_import_empty_command_name_fails(self):
        """
        Test that empty command name fails with appropriate error.
        
        Integration: input validation + error handling.
        """
        # Act - try to import with empty name
        result = import_command("")
        
        # Assert - should fail with validation error
        assert is_error(result)
        assert result['data']['error_code'] == "INVALID_OPERATION"
        assert "cannot be empty" in result['data']['message']
    
    def test_create_command_instance_integration(self):
        """
        Test creating command instance with arguments works.
        
        Integration: import + instantiation + argument passing.
        """
        # Act - create instance with arguments
        args = {"name": "TestUser"}
        result = create_command_instance("hello_world", args)
        
        # Assert - instance created successfully
        assert is_success(result)
        assert result['instance'] is not None
        assert isinstance(result['instance'], BaseCommand)
        assert result['instance'].args == args
        
        # Verify class information is preserved
        assert result['class'].__name__ == "HelloWorld"
        assert result['data']['operation'] == "hello_world"
    
    def test_create_instance_without_args_integration(self):
        """
        Test creating instance without arguments works.
        
        Integration: default argument handling + instantiation.
        """
        # Act - create instance without args
        result = create_command_instance("hello_world")
        
        # Assert - instance created with empty args
        assert is_success(result)
        assert result['instance'].args == {}
    
    def test_create_instance_nonexistent_command_fails(self):
        """
        Test creating instance of non-existent command fails.
        
        Integration: import failure + instance creation failure.
        """
        # Act - try to create instance of non-existent command
        result = create_command_instance("non_existent")
        
        # Assert - should fail at import stage
        assert is_error(result)
        assert result['instance'] is None
        assert result['data']['error_code'] == "MODULE_NOT_FOUND"
    
    def test_execute_command_cycle_integration(self):
        """
        Test complete command execution cycle works.
        
        Integration: import + instantiate + validate + preload + execute.
        """
        # Act - execute complete cycle
        exit_code = execute_command_cycle("hello_world", {"name": "TestUser"})
        
        # Assert - command executed successfully
        assert exit_code == 0
    
    def test_execute_command_cycle_with_test_spinner(self):
        """
        Test execution of test_spinner command through dynamic system.
        
        Integration: complex command + argument processing + execution.
        """
        # Act - execute test_spinner with short duration
        exit_code = execute_command_cycle("test_spinner", {"duration": "1"})
        
        # Assert - command should complete successfully
        assert exit_code == 0
    
    def test_execute_nonexistent_command_returns_error_code(self):
        """
        Test that executing non-existent command returns error code.
        
        Integration: error propagation + exit code handling.
        """
        # Act - try to execute non-existent command
        exit_code = execute_command_cycle("non_existent")
        
        # Assert - should return error code
        assert exit_code == 1
    
    def test_case_conversion_integration(self):
        """
        Test that snake_case to PascalCase conversion works correctly.
        
        Integration: string_converter + import system.
        """
        # Test various case conversions
        test_cases = [
            ("hello_world", "HelloWorld"),
            ("test_spinner", "TestSpinner"),
            ("complex_command_name", "ComplexCommandName"),
            ("simple", "Simple")
        ]
        
        for snake_case, expected_pascal in test_cases:
            # Act - import command (this triggers case conversion)
            result = import_command(snake_case)
            
            # For existing commands, check conversion worked
            if snake_case in ["hello_world", "test_spinner"]:
                assert is_success(result)
                assert result['data']['class_name'] == expected_pascal
            # For non-existing commands, verify conversion still worked 
            # (error should be MODULE_NOT_FOUND, not CASE_CONVERSION_ERROR)
            else:
                assert is_error(result)
                assert result['data']['error_code'] == "MODULE_NOT_FOUND"
                # The error message should contain the snake_case module name
                assert snake_case in result['data']['message']


@pytest.mark.integration
def test_dynamic_importer_main_integration():
    """
    Test that dynamic importer integrates with main function.
    
    Integration: main.py + dynamic importer + command execution.
    """
    from src.main import main
    
    # Test dynamic command execution through main (long form)
    args = ["--command", "hello_world", "--name", "IntegrationTest"]
    
    # Act - run main with dynamic command
    exit_code = main(args)
    
    # Assert - should complete successfully
    assert exit_code == 0


@pytest.mark.integration
def test_main_integration_only_dynamic_system():
    """
    Test that main only supports the new dynamic system.
    
    Integration: main.py + dynamic command system only.
    """
    from src.main import main
    
    # Test new dynamic system works
    new_style_args = ["--command", "test_spinner", "--duration", "2"]
    exit_code = main(new_style_args)
    
    # Should work perfectly
    assert exit_code == 0
    
    # Test that old system no longer exists
    old_style_args = ["--test-spinner", "2"]
    exit_code_old = main(old_style_args)
    
    # Should complete but not execute spinner (just normal output)
    assert exit_code_old == 0


@pytest.mark.integration
def test_result_types_integration():
    """
    Test result types work correctly with importer.
    
    Integration: result_types + dynamic_importer + error handling.
    """
    from src.utils.result_types import success, error, is_success, is_error
    
    # Test success result
    success_result = success({"test": "data"})
    assert is_success(success_result)
    assert not is_error(success_result)
    assert success_result['data']['test'] == "data"
    
    # Test error result
    error_result = error(code=404, message="Not found")
    assert is_error(error_result)
    assert not is_success(error_result)
    assert error_result['code'] == 404
    
    # Test integration with import_command
    # Success case
    good_import = import_command("hello_world")
    assert is_success(good_import)
    
    # Error case  
    bad_import = import_command("non_existent")
    assert is_error(bad_import)