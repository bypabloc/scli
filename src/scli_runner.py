#!/usr/bin/env python
"""
SCLI Runner - Main entry point for SCLI command execution.
Uses dynamic command system for improved scalability and maintainability.
"""
import sys
from pathlib import Path

# Add src to path to import scli modules
sys.path.insert(0, str(Path(__file__).parent))

from dynamic_command_handler import DynamicCommandHandler
from utils.menu_utils import interactive_menu


def show_available_commands():
    """Show available commands using the dynamic system"""
    print("🚀 SCLI - Dynamic Command Line Interface")
    print("=" * 50)
    
    handler = DynamicCommandHandler()
    result = handler.list_commands()
    
    if not result['success']:
        print(f"❌ Error listing commands: {result['error_message']}")
        return
    
    commands = result['commands']
    working_commands = [cmd for cmd in commands if cmd['type'] != 'error']
    error_commands = [cmd for cmd in commands if cmd['type'] == 'error']
    
    if working_commands:
        print(f"\n✅ Available Commands ({len(working_commands)}):")
        print("-" * 40)
        for cmd in working_commands:
            command_type_icon = "📦" if cmd['type'] == 'command_class' else "📄"
            print(f"  {command_type_icon} {cmd['name']:<20} - {cmd['description']}")
    
    if error_commands:
        print(f"\n⚠️  Commands with Issues ({len(error_commands)}):")
        print("-" * 40)
        for cmd in error_commands:
            print(f"  ❌ {cmd['name']:<20} - {cmd['description']}")
    
    print(f"\nTotal: {result['total']} commands found")
    
    print("\n💡 Usage Examples:")
    print("  scli hello_world                     # Run command directly")
    print("  scli file_counter --directory=.      # Run with arguments")
    print("  scli -s hello_world                  # Alternative syntax")
    print("  scli --help                          # Show help")
    print("  scli [command] --help                # Get command-specific help")


def main():
    """Main entry point for SCLI command execution."""
    # Parse basic arguments
    args = sys.argv[1:]

    # Show interactive menu if no arguments provided
    if not args:
        show_interactive_mode()
        return

    # Show help
    if args[0] in ["-h", "--help"]:
        print("SCLI - Dynamic Command Line Interface")
        print("\nUsage:")
        print("  scli                                  # Interactive command selection")
        print("  scli -l, --list                      # List available commands")
        print("  scli [COMMAND] [ARGS...]              # Run command with arguments")
        print("  scli -s [COMMAND] [ARGS...]           # Alternative syntax")
        print("\nOptions:")
        print("  -l, --list           List available commands")
        print("  -s, --script COMMAND  Name of the command to run")
        print("  -h, --help           Show this help message")
        print("\nExamples:")
        print("  scli                                  # Interactive menu")
        print("  scli --list                          # List commands")
        print("  scli hello_world                     # Run hello_world command")
        print("  scli file_counter --directory=.      # Run file_counter with args")
        print("  scli -s system_info                  # Alternative syntax")
        return

    # Show available commands list if --list flag is used
    if args[0] in ["-l", "--list"]:
        show_available_commands()
        return

    command_name = None
    command_args = []

    # Check if first argument is -s/--script flag
    if args[0] in ["-s", "--script"]:
        # Using -s flag format
        if len(args) > 1:
            command_name = args[1]
            command_args = args[2:] if len(args) > 2 else []
        else:
            print("Error: -s/--script requires a command name")
            sys.exit(1)
    else:
        # Direct command name format (scli COMMAND [ARGS...])
        # Check if it's a valid command name using dynamic system
        handler = DynamicCommandHandler()
        result = handler.list_commands()
        
        if result['success']:
            available_commands = [cmd['name'] for cmd in result['commands'] if cmd['type'] != 'error']
            
            if args[0] in available_commands:
                command_name = args[0]
                command_args = args[1:] if len(args) > 1 else []
            # If not a command name and not a flag, show error
            elif not args[0].startswith("-"):
                print(f"❌ Error: Unknown command '{args[0]}'")
                print(f"\n✅ Available commands: {', '.join(available_commands)}")
                print(f"\n💡 Run 'scli' without arguments to see all commands with descriptions")
                sys.exit(1)
        else:
            print(f"❌ Error: Could not list available commands: {result['error_message']}")
            sys.exit(1)

    # Execute command using dynamic handler
    if command_name:
        print(f"🚀 Executing command: {command_name}")
        
        handler = DynamicCommandHandler()
        result = handler.execute_command_from_args(command_name, command_args)
        
        if not result['success']:
            print(f"❌ Command '{command_name}' failed: {result.get('error_message', 'Unknown error')}")
            if result.get('errors'):
                for error in result['errors']:
                    print(f"   Error: {error}")
            sys.exit(1)
        else:
            print(f"✅ Command '{command_name}' completed successfully in {result['duration']:.3f}s")
    else:
        # Interactive mode using dynamic system
        show_interactive_mode()


def show_interactive_mode():
    """Show interactive command selection mode"""
    print("🚀 SCLI - Dynamic Command Line Interface")
    print("=" * 50)
    
    handler = DynamicCommandHandler()
    result = handler.list_commands()
    
    if not result['success']:
        print(f"❌ Error listing commands: {result['error_message']}")
        return
    
    commands = result['commands']
    working_commands = [cmd for cmd in commands if cmd['type'] != 'error']
    error_commands = [cmd for cmd in commands if cmd['type'] == 'error']
    
    if not working_commands:
        print("❌ No working commands available")
        return
    
    menu_choices = []
    for cmd in working_commands:
        command_type_icon = "📦" if cmd['type'] == 'command_class' else "📄"
        display_name = f"{command_type_icon} {cmd['name']}"
        menu_choices.append({
            "name": display_name,
            "value": cmd['name'],
            "description": cmd['description']
        })
    
    # Add exit option
    menu_choices.append({
        "name": "❌ Exit",
        "value": "exit",
        "description": "Exit without running a command"
    })
    
    selected = interactive_menu("Select a command to run:", menu_choices)
    if selected is None or selected["value"] == "exit":
        print("👋 Operation cancelled.")
        return
    
    command_name = selected["value"]
    print(f"\n🚀 Executing command: {command_name}")
    
    # Execute selected command
    result = handler.execute_command_from_args(command_name, [])
    
    if not result['success']:
        print(f"❌ Command '{command_name}' failed: {result.get('error_message', 'Unknown error')}")
        if result.get('errors'):
            for error in result['errors']:
                print(f"   Error: {error}")
        sys.exit(1)
    else:
        print(f"✅ Command '{command_name}' completed successfully in {result['duration']:.3f}s")
