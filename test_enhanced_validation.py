#!/usr/bin/env python3
"""
Test script for the enhanced validation system with Pydantic models

This script tests the new InteractiveCommand base class with argument parsing 
and Pydantic validation functionality.
"""

import sys
import os
from pathlib import Path

# Add the src directory to path to import scli modules
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / "src"))

def test_hello_world_command():
    """Test the enhanced HelloWorld command with various arguments"""
    print("🧪 Testing Enhanced HelloWorld Command with Pydantic Validation")
    print("=" * 60)
    
    # Import the command
    from commands.hello_world import HelloWorldCommand
    
    # Test cases with different argument combinations
    test_cases = [
        {
            "name": "Basic test - no arguments",
            "args": [],
            "expected_success": True
        },
        {
            "name": "Test with name argument",
            "args": ["--name", "Alice"],
            "expected_success": True
        },
        {
            "name": "Test with positional name",
            "args": ["Bob"],
            "expected_success": True
        },
        {
            "name": "Test with language",
            "args": ["--name", "Carlos", "--language", "spanish"],
            "expected_success": True
        },
        {
            "name": "Test with emoji disabled",
            "args": ["--name", "Diana", "--no-emoji"],
            "expected_success": True
        },
        {
            "name": "Test with uppercase",
            "args": ["--name", "Eve", "--uppercase", "--language", "french"],
            "expected_success": True
        },
        {
            "name": "Test with verbose",
            "args": ["--name", "Frank", "--verbose"],
            "expected_success": True
        },
        {
            "name": "Test invalid language (should fail)",
            "args": ["--language", "klingon"],
            "expected_success": False
        },
        {
            "name": "Test very long name (should fail)",
            "args": ["--name", "A" * 100],
            "expected_success": False
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Arguments: {test_case['args']}")
        
        try:
            # Create command instance
            command = HelloWorldCommand()
            
            # Run the command with test arguments
            result = command.run(*test_case['args'])
            
            success = result.get('success', False)
            
            if success == test_case['expected_success']:
                print(f"   ✅ PASSED - Success: {success}")
                if success:
                    print(f"   📝 Results: {result.get('results', {})}")
                results.append(True)
            else:
                print(f"   ❌ FAILED - Expected: {test_case['expected_success']}, Got: {success}")
                if not success:
                    print(f"   🚫 Error: {result.get('error_message', 'Unknown error')}")
                results.append(False)
                
        except Exception as e:
            print(f"   💥 EXCEPTION: {str(e)}")
            results.append(False)
    
    # Print summary
    passed = sum(results)
    total = len(results)
    print(f"\n📊 Test Results Summary")
    print(f"   Passed: {passed}/{total}")
    print(f"   Success Rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("   🎉 All tests passed!")
    else:
        print("   ⚠️  Some tests failed")
    
    return passed == total


def test_argument_parsing():
    """Test the argument parsing functionality separately"""
    print("\n🔍 Testing Argument Parsing Functionality")
    print("=" * 60)
    
    from utils.base_command import InteractiveCommand
    
    # Create a concrete test command class
    class TestCommand(InteractiveCommand):
        def execute(self, *args, **kwargs) -> bool:
            return True
    
    # Create test command instance
    command = TestCommand(name="test", description="Test command")
    
    test_cases = [
        {
            "name": "Named arguments with =",
            "args": ["--name=Alice", "--verbose=true"],
            "expected_keys": ["name", "verbose"]
        },
        {
            "name": "Named arguments with spaces",
            "args": ["--name", "Bob", "--output", "json"],
            "expected_keys": ["name", "output"]
        },
        {
            "name": "Short flags",
            "args": ["-v", "-f", "-o", "file.txt"],
            "expected_keys": ["verbose", "force", "output"]
        },
        {
            "name": "Mixed arguments",
            "args": ["Alice", "--language=spanish", "-v", "--no-emoji"],
            "expected_keys": ["arg_0", "language", "verbose", "no_emoji"]
        },
        {
            "name": "Boolean values",
            "args": ["--flag1=true", "--flag2=false", "--flag3=yes", "--flag4=no"],
            "expected_keys": ["flag1", "flag2", "flag3", "flag4"]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Input: {test_case['args']}")
        
        try:
            parsed = command.parse_arguments_to_dict(*test_case['args'])
            print(f"   Parsed: {parsed}")
            
            # Check if expected keys are present
            missing_keys = [key for key in test_case['expected_keys'] if key not in parsed]
            if missing_keys:
                print(f"   ⚠️  Missing expected keys: {missing_keys}")
            else:
                print(f"   ✅ All expected keys found")
                
        except Exception as e:
            print(f"   💥 ERROR: {str(e)}")


def main():
    """Main test function"""
    print("🚀 Enhanced Validation System Test Suite")
    print("=" * 80)
    
    try:
        # Test argument parsing
        test_argument_parsing()
        
        # Test hello world command
        success = test_hello_world_command()
        
        print(f"\n{'🎉 All tests completed successfully!' if success else '⚠️  Some tests failed'}")
        
    except Exception as e:
        print(f"\n💥 Test suite failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()