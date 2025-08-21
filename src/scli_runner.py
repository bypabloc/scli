#!/usr/bin/env python
"""
Alternative runner for SCLI that properly handles script arguments.
This module allows passing arguments directly to scripts.
"""
import sys
from pathlib import Path

from menu_utils import interactive_menu
from script_loader import ScriptLoader

# Add src to path to import scli modules
sys.path.insert(0, str(Path(__file__).parent))


def main():
    """Main entry point that handles script arguments properly."""
    # Parse basic arguments
    args = sys.argv[1:]

    if not args or args[0] in ["-h", "--help"]:
        print("Usage: scli [SCRIPT] [ARGS...]")
        print("       scli -s SCRIPT [ARGS...]")
        print("\nOptions:")
        print("  -s, --script SCRIPT  Name of the script to run")
        print("  -h, --help          Show this help message")
        print("\nExamples:")
        print("  scli                                  # Interactive mode")
        print("  scli code_formatter --list-actions")
        print("  scli code_quality_checker --mode all --yes")
        print("  scli -s code_formatter --mode all --yes --no-verbose")
        return

    script_name = None
    script_args = []

    # Check if first argument is -s/--script flag
    if args[0] in ["-s", "--script"]:
        # Using -s flag format
        if len(args) > 1:
            script_name = args[1]
            script_args = args[2:] if len(args) > 2 else []
        else:
            print("Error: -s/--script requires a script name")
            sys.exit(1)
    else:
        # Direct script name format (scli SCRIPT [ARGS...])
        # First check if it's a valid script name
        loader = ScriptLoader()
        scripts = loader.discover_scripts()

        if args[0] in scripts:
            script_name = args[0]
            script_args = args[1:] if len(args) > 1 else []
        # If not a script name and not a flag, show error
        elif not args[0].startswith("-"):
            print(f"Error: Unknown script '{args[0]}'")
            print(f"Available scripts: {', '.join(scripts.keys())}")
            sys.exit(1)

    # Load scripts
    loader = ScriptLoader()
    scripts = loader.discover_scripts()

    if not scripts:
        print("No scripts found in the scripts directory")
        sys.exit(1)

    if script_name:
        if script_name in scripts:
            print(f"Executing script: {script_name}")
            success = loader.execute_script(script_name, scripts, script_args)
            if not success:
                print(f"Failed to execute script: {script_name}")
                sys.exit(1)
        else:
            print(f"Script '{script_name}' not found")
            print(f"Available scripts: {', '.join(scripts.keys())}")
            sys.exit(1)
    else:
        # Interactive mode
        print("\nAvailable Scripts:")

        options = []
        script_list = []
        for name, info in scripts.items():
            description = info.get("description", name)
            options.append(f"📄 {name}: {description}")
            script_list.append(name)

        selected = interactive_menu("Select a script to run:", options)
        if selected is None:
            print("Operation cancelled.")
            return

        # Extract script name from selection
        selected_index = options.index(selected)
        script_name = script_list[selected_index]

        print(f"\nExecuting script: {script_name}")
        success = loader.execute_script(script_name, scripts, [])
        if not success:
            print(f"Failed to execute script: {script_name}")
            sys.exit(1)
