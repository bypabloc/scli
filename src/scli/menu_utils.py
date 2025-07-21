import inquirer
import sys
from typing import List, Dict, Any, Optional


def interactive_menu(title: str, choices: List[Dict[str, Any]], 
                    allow_filter: bool = True) -> Optional[Dict[str, Any]]:
    """
    Create an interactive menu with arrow key navigation and optional text filtering.
    Falls back to simple text menu if TTY is not available.
    
    Args:
        title: The menu title to display
        choices: List of choice dictionaries with 'name', 'value', and optional 'description'
        allow_filter: Whether to enable text filtering (default: True)
    
    Returns:
        The selected choice dictionary, or None if cancelled
    """
    if not choices:
        print("❌ No options available")
        return None
    
    # Check if we have a proper TTY for interactive input
    if not sys.stdin.isatty():
        return _fallback_menu(title, choices)
    
    # Prepare choices for inquirer
    inquirer_choices = []
    for choice in choices:
        display_name = choice.get('name', str(choice.get('value', 'Unknown')))
        if 'description' in choice:
            display_name = f"{display_name} - {choice['description']}"
        inquirer_choices.append((display_name, choice))
    
    # Create the appropriate question type
    question = inquirer.List(
        'selection',
        message=title,
        choices=inquirer_choices,
        carousel=True
    )
    
    try:
        answer = inquirer.prompt([question])
        if answer:
            return answer['selection']
        return None
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled")
        return None
    except Exception as e:
        # Fall back to simple menu on error
        print(f"⚠️  Interactive menu failed, using fallback: {e}")
        return _fallback_menu(title, choices)


def _fallback_menu(title: str, choices: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Fallback text-based menu when interactive mode fails."""
    print(f"\n{title}")
    print("-" * len(title))
    
    for i, choice in enumerate(choices, 1):
        name = choice.get('name', str(choice.get('value', 'Unknown')))
        description = choice.get('description', '')
        if description:
            print(f"{i}. {name} - {description}")
        else:
            print(f"{i}. {name}")
    
    try:
        while True:
            try:
                response = input(f"\nEnter your choice (1-{len(choices)}): ").strip()
                try:
                    choice_idx = int(response) - 1
                    if 0 <= choice_idx < len(choices):
                        return choices[choice_idx]
                    else:
                        print(f"❌ Please enter a number between 1 and {len(choices)}")
                except ValueError:
                    print("❌ Please enter a valid number")
            except EOFError:
                print("\n❌ No input available")
                return None
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled")
        return None


def simple_menu(title: str, options: List[str]) -> Optional[str]:
    """
    Create a simple interactive menu from a list of strings.
    
    Args:
        title: The menu title to display
        options: List of option strings
    
    Returns:
        The selected option string, or None if cancelled
    """
    choices = [{'name': opt, 'value': opt} for opt in options]
    result = interactive_menu(title, choices)
    return result['value'] if result else None


def confirm(message: str, default: bool = True) -> bool:
    """
    Show a yes/no confirmation prompt.
    Falls back to simple input if TTY is not available.
    
    Args:
        message: The confirmation message
        default: Default value if user just presses Enter
    
    Returns:
        True if confirmed, False otherwise
    """
    # Check if we have a proper TTY for interactive input
    if not sys.stdin.isatty():
        return _fallback_confirm(message, default)
    
    try:
        question = inquirer.Confirm('confirm', message=message, default=default)
        answer = inquirer.prompt([question])
        return answer['confirm'] if answer else default
    except KeyboardInterrupt:
        return False
    except Exception:
        return _fallback_confirm(message, default)


def _fallback_confirm(message: str, default: bool = True) -> bool:
    """Fallback confirmation when interactive mode fails."""
    default_str = "Y/n" if default else "y/N"
    
    try:
        response = input(f"{message} ({default_str}): ").strip().lower()
        if not response:
            return default
        return response in ['y', 'yes', 'true', '1']
    except (EOFError, KeyboardInterrupt):
        return default


def text_input(message: str, default: str = "", validate=None) -> Optional[str]:
    """
    Get text input from user with validation.
    Falls back to simple input if TTY is not available.
    
    Args:
        message: The input prompt message
        default: Default value
        validate: Optional validation function
    
    Returns:
        The input string, or None if cancelled
    """
    # Check if we have a proper TTY for interactive input
    if not sys.stdin.isatty():
        return _fallback_text_input(message, default, validate)
    
    try:
        question = inquirer.Text('input', message=message, default=default)
        if validate:
            question.validate = validate
        
        answer = inquirer.prompt([question])
        return answer['input'] if answer else None
    except KeyboardInterrupt:
        print("\n👋 Input cancelled")
        return None
    except Exception as e:
        # Fall back to simple input on error
        print(f"⚠️  Interactive input failed, using fallback: {e}")
        return _fallback_text_input(message, default, validate)


def _fallback_text_input(message: str, default: str = "", validate=None) -> Optional[str]:
    """Fallback text input when interactive mode fails."""
    try:
        while True:
            prompt = f"{message}"
            if default:
                prompt += f" (default: {default})"
            prompt += ": "
            
            try:
                response = input(prompt).strip()
                if not response and default:
                    response = default
                
                if validate:
                    try:
                        if validate(None, response):
                            return response
                    except Exception as e:
                        print(f"❌ {e}")
                        continue
                else:
                    return response if response else None
            except EOFError:
                print("\n❌ No input available")
                return None
    except KeyboardInterrupt:
        print("\n👋 Input cancelled")
        return None