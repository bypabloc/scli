#!/usr/bin/env python3
"""
Test script for the dynamic command system
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from dynamic_command_handler import DynamicCommandHandler


def test_list_commands():
    """Test listing available commands"""
    print("🔍 Testing command listing...")
    
    handler = DynamicCommandHandler()
    result = handler.list_commands()
    
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Total commands: {result['total']}")
        for cmd in result['commands']:
            print(f"  📦 {cmd['name']} - {cmd['description']} (type: {cmd['type']})")
    else:
        print(f"Error: {result['error_message']}")
    
    print()


def test_command_help():
    """Test getting command help"""
    print("📖 Testing command help...")
    
    handler = DynamicCommandHandler()
    result = handler.get_command_help("hello_world")
    
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Command: {result['command']}")
        print(f"Type: {result['type']}")
        print(f"Help:\n{result['help_text']}")
    else:
        print(f"Error: {result['error_message']}")
    
    print()


def test_command_execution():
    """Test executing a command"""
    print("⚡ Testing command execution...")
    
    # Test with event format
    event = {
        "command": "hello_world",
        "args": [],
        "data": {}
    }
    
    handler = DynamicCommandHandler()
    result = handler.execute_command_event(event)
    
    print(f"Success: {result['success']}")
    print(f"Command: {result['command']}")
    print(f"Duration: {result['duration']:.3f}s")
    print(f"Type: {result['command_type']}")
    
    if result['success']:
        print(f"Results: {result.get('results', {})}")
    else:
        print(f"Errors: {result.get('errors', [])}")
    
    print()


def test_file_counter_with_args():
    """Test file counter with arguments"""
    print("📁 Testing file_counter with arguments...")
    
    event = {
        "command": "file_counter",
        "args": ["--directory=.", "--extensions=py"],
        "data": {}
    }
    
    handler = DynamicCommandHandler()
    result = handler.execute_command_event(event)
    
    print(f"Success: {result['success']}")
    print(f"Command: {result['command']}")
    print(f"Duration: {result['duration']:.3f}s")
    
    if result['success']:
        results = result.get('results', {})
        print(f"Total files: {results.get('total_files', 0)}")
        print(f"File counts: {results.get('file_counts', {})}")
    else:
        print(f"Errors: {result.get('errors', [])}")
    
    print()


def test_invalid_command():
    """Test handling of invalid command"""
    print("❌ Testing invalid command handling...")
    
    event = {
        "command": "nonexistent_command",
        "args": [],
        "data": {}
    }
    
    handler = DynamicCommandHandler()
    result = handler.execute_command_event(event)
    
    print(f"Success: {result['success']}")
    print(f"Error message: {result.get('error_message', 'No error message')}")
    
    print()


if __name__ == "__main__":
    print("🚀 Testing Dynamic Command System")
    print("=" * 50)
    
    test_list_commands()
    test_command_help()
    test_command_execution()
    test_file_counter_with_args()
    test_invalid_command()
    
    print("✅ Dynamic system testing completed!")