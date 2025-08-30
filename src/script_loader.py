import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Add the current directory to path for utils import
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from utils.base_command import BaseCommand


class CommandLoader:
    """Loads and manages commands from the commands directory"""
    
    def __init__(self, commands_dir: Optional[str] = None):
        """Initialize the command loader
        
        Args:
            commands_dir: Directory containing command files (defaults to src/commands)
        """
        if commands_dir is None:
            # Default to src/commands relative to this file
            current_dir = Path(__file__).parent
            self.commands_dir = current_dir / "commands"
        else:
            self.commands_dir = Path(commands_dir)

    def discover_commands(self) -> Dict[str, Dict[str, Any]]:
        """Discover all available commands
        
        Returns:
            Dictionary mapping command names to command information
        """
        commands = {}

        if not self.commands_dir.exists():
            print(f"Commands directory not found: {self.commands_dir}")
            return commands

        for command_file in self.commands_dir.glob("*.py"):
            if command_file.name == "__init__.py":
                continue

            command_name = command_file.stem
            try:
                command_info = self._load_command_info(command_file)
                if command_info:
                    commands[command_name] = command_info
            except Exception as e:
                print(f"Error loading command {command_name}: {e}")

        return commands

    def _load_command_info(self, command_path: Path) -> Optional[Dict[str, Any]]:
        """Load information about a command from its file
        
        Args:
            command_path: Path to the command file
            
        Returns:
            Command information dictionary or None if invalid
        """
        try:
            spec = importlib.util.spec_from_file_location(command_path.stem, command_path)
            if not spec or not spec.loader:
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Check for new command instance format first
            command_instance = getattr(module, "command_instance", None)
            if command_instance and isinstance(command_instance, BaseCommand):
                return {
                    "path": command_path,
                    "module": module,
                    "command_instance": command_instance,
                    "description": command_instance.description,
                    "type": "command_class",
                    "main_func": None  # Not used for new format
                }

            # Fallback to legacy format
            main_func = getattr(module, "main", None)
            if main_func and callable(main_func):
                description = getattr(module, "DESCRIPTION", command_path.stem)
                return {
                    "path": command_path,
                    "module": module,
                    "command_instance": None,
                    "description": description,
                    "type": "legacy",
                    "main_func": main_func
                }

            # No valid command found
            return None

        except Exception as e:
            print(f"Error loading command info from {command_path}: {e}")
            return None

    def execute_command(
        self, command_name: str, commands: Dict[str, Dict[str, Any]], args: list = None
    ) -> bool:
        """Execute a command by name
        
        Args:
            command_name: Name of the command to execute
            commands: Dictionary of available commands
            args: Arguments to pass to the command
            
        Returns:
            True if execution was successful, False otherwise
        """
        if command_name not in commands:
            print(f"Command '{command_name}' not found")
            return False

        command_info = commands[command_name]
        
        try:
            if command_info["type"] == "command_class":
                # New command class format
                return self._execute_command_class(command_info, args)
            else:
                # Legacy format
                return self._execute_legacy_command(command_info, args)
        
        except Exception as e:
            print(f"Error executing command {command_name}: {e}")
            return False

    def _execute_command_class(self, command_info: Dict[str, Any], args: list = None) -> bool:
        """Execute a command using the new command class format"""
        command_instance = command_info["command_instance"]
        
        try:
            # Execute the command with cascading methods
            result = command_instance.run(*(args or []))
            
            # Return success status
            return result.get("success", False)
            
        except Exception as e:
            print(f"Error executing command class: {e}")
            return False

    def _execute_legacy_command(self, command_info: Dict[str, Any], args: list = None) -> bool:
        """Execute a command using the legacy format"""
        try:
            # Preserve original argv
            original_argv = sys.argv.copy()

            # Set the script name as argv[0] and pass remaining arguments
            command_path = command_info["path"]
            sys.argv = [str(command_path)] + (args or [])

            try:
                # Execute the main function
                command_info["main_func"]()
                return True
            finally:
                # Restore original argv
                sys.argv = original_argv
                
        except Exception as e:
            print(f"Error executing legacy command: {e}")
            return False

    def get_command_help(self, command_name: str, commands: Dict[str, Dict[str, Any]]) -> str:
        """Get help text for a specific command"""
        if command_name not in commands:
            return f"Command '{command_name}' not found"
        
        command_info = commands[command_name]
        
        if command_info["type"] == "command_class":
            command_instance = command_info["command_instance"]
            return command_instance.get_help()
        else:
            # Legacy format - return basic info
            return f"{command_name}: {command_info['description']}"

    def list_commands(self, commands: Dict[str, Dict[str, Any]]) -> None:
        """Print a list of all available commands"""
        if not commands:
            print("No commands available")
            return
        
        print("Available commands:")
        print("-" * 40)
        
        for name, info in sorted(commands.items()):
            command_type = "📦" if info["type"] == "command_class" else "📄"
            print(f"  {command_type} {name:<20} - {info['description']}")


# Backward compatibility alias
ScriptLoader = CommandLoader
