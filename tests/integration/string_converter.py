import pytest

from src.utils.string_converter import detect_case_style
from src.utils.string_converter import convert_case_style
from src.utils.string_converter import get_supported_styles


@pytest.mark.integration
class TestStringConverterIntegration:
    """Integration tests for string case conversion utilities."""
    
    def test_detect_case_style_integration(self):
        """
        Test case style detection works with real examples.
        
        Integration test: detection logic + string analysis.
        """
        # Test various real-world cases
        test_cases = [
            ("hello_world", "snake_case"),
            ("hello-world", "kebab-case"), 
            ("helloWorld", "camelCase"),
            ("HelloWorld", "PascalCase"),
            ("HELLO_WORLD", "UPPER_CASE"),
            ("hello world", "space_separated"),
            ("", "unknown"),
            ("singleword", "unknown")
        ]
        
        for text, expected in test_cases:
            # Act - real detection, no mocks
            result = detect_case_style(text)
            
            # Assert - verify detection works
            assert result == expected, f"Failed to detect {text} as {expected}, got {result}"
    
    def test_convert_case_style_integration(self):
        """
        Test case conversion works between different styles.
        
        Integration: detection + word splitting + conversion.
        """
        # Test conversions from snake_case
        snake_text = "hello_world_example"
        
        assert convert_case_style(snake_text, "camelCase") == "helloWorldExample"
        assert convert_case_style(snake_text, "PascalCase") == "HelloWorldExample" 
        assert convert_case_style(snake_text, "kebab-case") == "hello-world-example"
        assert convert_case_style(snake_text, "snake_case") == "hello_world_example"  # Same
        
        # Test conversions from camelCase
        camel_text = "helloWorldExample"
        
        assert convert_case_style(camel_text, "snake_case") == "hello_world_example"
        assert convert_case_style(camel_text, "kebab-case") == "hello-world-example"
        assert convert_case_style(camel_text, "PascalCase") == "HelloWorldExample"
        assert convert_case_style(camel_text, "camelCase") == "helloWorldExample"  # Same
        
        # Test conversions from kebab-case
        kebab_text = "hello-world-example"
        
        assert convert_case_style(kebab_text, "snake_case") == "hello_world_example"
        assert convert_case_style(kebab_text, "camelCase") == "helloWorldExample"
        assert convert_case_style(kebab_text, "PascalCase") == "HelloWorldExample"
        assert convert_case_style(kebab_text, "kebab-case") == "hello-world-example"  # Same
    
    def test_space_separated_text_conversion(self):
        """
        Test conversion from space-separated text works.
        
        Integration: space detection + splitting + conversion.
        """
        space_text = "hello world example"
        
        # Act - convert from spaces to different formats
        snake_result = convert_case_style(space_text, "snake_case")
        camel_result = convert_case_style(space_text, "camelCase") 
        pascal_result = convert_case_style(space_text, "PascalCase")
        kebab_result = convert_case_style(space_text, "kebab-case")
        
        # Assert - verify all conversions work
        assert snake_result == "hello_world_example"
        assert camel_result == "helloWorldExample"
        assert pascal_result == "HelloWorldExample"
        assert kebab_result == "hello-world-example"
    
    def test_upper_case_conversion(self):
        """
        Test conversion from UPPER_CASE works correctly.
        
        Integration: upper case detection + conversion logic.
        """
        upper_text = "HELLO_WORLD_EXAMPLE"
        
        # Act - convert from UPPER_CASE
        snake_result = convert_case_style(upper_text, "snake_case")
        camel_result = convert_case_style(upper_text, "camelCase")
        pascal_result = convert_case_style(upper_text, "PascalCase") 
        kebab_result = convert_case_style(upper_text, "kebab-case")
        
        # Assert - verify conversions handle uppercase correctly
        assert snake_result == "hello_world_example"
        assert camel_result == "helloWorldExample"
        assert pascal_result == "HelloWorldExample"
        assert kebab_result == "hello-world-example"
    
    def test_edge_cases_integration(self):
        """
        Test edge cases work correctly with real integration.
        
        Integration: error handling + validation + conversion.
        """
        # Empty string
        assert convert_case_style("", "camelCase") == ""
        
        # Single word
        assert convert_case_style("hello", "snake_case") == "hello"
        assert convert_case_style("hello", "camelCase") == "hello"
        assert convert_case_style("hello", "PascalCase") == "Hello"
        assert convert_case_style("hello", "kebab-case") == "hello"
        
        # Already in target format
        assert convert_case_style("helloWorld", "camelCase") == "helloWorld"
        assert convert_case_style("hello_world", "snake_case") == "hello_world"
    
    def test_invalid_target_style_raises_error(self):
        """
        Test that invalid target styles raise appropriate errors.
        
        Integration: validation + error handling.
        """
        with pytest.raises(ValueError) as exc_info:
            convert_case_style("hello_world", "invalid_style")
        
        assert "target_style debe ser uno de" in str(exc_info.value)
        assert "invalid_style" in str(exc_info.value)
    
    def test_get_supported_styles_integration(self):
        """
        Test supported styles function returns correct values.
        
        Integration: API consistency + supported formats.
        """
        # Act - get supported styles
        styles = get_supported_styles()
        
        # Assert - verify all expected styles are present
        expected_styles = ['snake_case', 'kebab-case', 'camelCase', 'PascalCase']
        
        assert isinstance(styles, list)
        assert len(styles) == len(expected_styles)
        
        for style in expected_styles:
            assert style in styles, f"Style {style} should be supported"
    
    def test_complex_text_conversion_integration(self):
        """
        Test complex text with multiple words converts correctly.
        
        Integration: complex parsing + conversion accuracy.
        """
        # Complex camelCase
        complex_camel = "getUserAccountInformationFromDatabase"
        
        # Act - convert to different formats  
        snake_result = convert_case_style(complex_camel, "snake_case")
        kebab_result = convert_case_style(complex_camel, "kebab-case")
        pascal_result = convert_case_style(complex_camel, "PascalCase")
        
        # Assert - verify complex conversion works
        assert snake_result == "get_user_account_information_from_database"
        assert kebab_result == "get-user-account-information-from-database" 
        assert pascal_result == "GetUserAccountInformationFromDatabase"
        
        # Test reverse conversion
        back_to_camel = convert_case_style(snake_result, "camelCase")
        assert back_to_camel == "getUserAccountInformationFromDatabase"


@pytest.mark.integration  
def test_string_converter_import_integration():
    """
    Test that string converter can be imported from utils package.
    
    Integration: module imports + public API.
    """
    # Test direct imports work
    from src.utils.string_converter import convert_case_style, get_supported_styles
    
    # Test package imports work
    from src.utils import convert_case_style as utils_convert
    from src.utils import get_supported_styles as utils_styles
    
    # Verify functions are the same
    assert convert_case_style is utils_convert
    assert get_supported_styles is utils_styles
    
    # Test basic functionality
    result = utils_convert("hello_world", "camelCase")
    assert result == "helloWorld"
    
    styles = utils_styles()
    assert "snake_case" in styles