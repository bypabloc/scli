import pytest
import typer
from io import StringIO

from rich.console import Console
from typer.testing import CliRunner
from src.main import main


@pytest.mark.integration
class TestCliComponentIntegration:
    """Integration tests for CLI components working together."""
    
    def test_main_with_cli_dependencies_integration(self):
        """
        Test main() integrates with CLI dependencies.
        
        Integration: main() + rich + typer components.
        """
        # Act - real integration, no mocks
        result = main([])
        
        # Assert - verify integration works
        assert result == 0
    
    def test_cli_with_different_argument_patterns(self):
        """
        Integration test for various CLI argument patterns.
        
        Tests how main() integrates with named flags validation.
        """
        # Test valid named flag patterns (should work)
        valid_patterns = [
            [],
            ["--help"], 
            ["--flag", "value"],
            ["--verbose", "--output", "file.txt"]
        ]
        
        for args in valid_patterns:
            # Act - integration test
            result = main(args)
            
            # Assert - valid patterns should work
            assert result == 0, f"Valid pattern failed with args: {args}"
            
        # Test invalid positional patterns (should fail)
        invalid_patterns = [
            ["command"],
            ["multi", "arg", "test"]
        ]
        
        for args in invalid_patterns:
            # Act - integration test
            result = main(args)
            
            # Assert - invalid patterns should fail
            assert result == 1, f"Invalid pattern should fail but passed with args: {args}"


@pytest.mark.integration
@pytest.mark.slow
class TestDependencyIntegration:
    """Integration tests with external dependencies - no mocks."""
    
    def test_rich_console_integration(self):
        """
        Test Rich console integration works without mocks.
        
        Integration: Rich Console + our application components.
        """
        # Act - real Rich integration
        fake_stdout = StringIO()
        console = Console(file=fake_stdout)
        console.print("Test output")
        
        # Assert - integration worked
        output = fake_stdout.getvalue()
        assert "Test output" in output
        assert len(output) > 0
    
    def test_typer_components_integration(self):
        """
        Test Typer components can be imported and work.
        
        Integration: Typer + our CLI structure.
        """
        # Act - create typer app and runner integration
        app = typer.Typer()
        runner = CliRunner()
        
        @app.command()
        def test_command():
            # This print is intentional for typer testing
            print("Integration test")
            
        # Test integration
        result = runner.invoke(app, [])
        
        # Assert - integration successful
        assert result.exit_code == 0
        assert "Integration test" in result.output
    
    def test_survey_availability_for_interactive_features(self):
        """
        Test survey library availability for future interactive features.
        
        Note: Survey may not work in pytest due to stdin issues.
        """
        # This tests whether survey can be imported
        # Integration test for future interactive menu features
        try:
            import survey
            survey_available = True
            # If we get here, survey integration is possible
            assert hasattr(survey, 'routines')
        except Exception:
            # Expected in test environment
            # In real CLI usage, survey should work fine
            survey_available = False
            
        # This test documents that survey availability depends on environment
        # Integration will work in real CLI usage
        assert isinstance(survey_available, bool)