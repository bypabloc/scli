import sys
from pathlib import Path
from typing import Optional

# Add the current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

import typer
from rich.console import Console
from rich.table import Table

from script_loader import CommandLoader
from utils.menu_utils import interactive_menu

app = typer.Typer(
    help="A CLI tool for executing selectable scripts",
    invoke_without_command=True,
    context_settings={"allow_extra_args": True, "allow_interspersed_args": False},
)
console = Console()


@app.callback()
def main(
    ctx: typer.Context,
    script: Optional[str] = typer.Option(
        None, "-s", "--script", help="Name of the script to run directly"
    ),
):
    """Main CLI entry point. Run without command for interactive selection."""
    if ctx.invoked_subcommand is None:
        loader = CommandLoader()
        commands = loader.discover_commands()

        if not commands:
            console.print("[red]No commands found in the commands directory[/red]")
            raise typer.Exit(1)

        if script:
            if script in commands:
                console.print(f"[green]Executing command: {script}[/green]")
                # Use Typer's context to get extra arguments
                script_args = ctx.args
                success = loader.execute_command(script, commands, script_args)
                if not success:
                    console.print(f"[red]Failed to execute command: {script}[/red]")
                    raise typer.Exit(1)
            else:
                console.print(f"[red]Command '{script}' not found[/red]")
                raise typer.Exit(1)
        else:
            _interactive_selection(loader, commands)


@app.command()
def list_scripts():
    """List all available commands"""
    loader = CommandLoader()
    commands = loader.discover_commands()

    if not commands:
        console.print("[yellow]No commands found in the commands directory[/yellow]")
        return

    table = Table(title="Available Commands")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Type", style="blue", no_wrap=True)
    table.add_column("Description", style="magenta")

    for name, info in commands.items():
        command_type = "Class" if info["type"] == "command_class" else "Legacy"
        table.add_row(name, command_type, info["description"])

    console.print(table)


@app.command(
    context_settings={"allow_extra_args": True, "allow_interspersed_args": False}
)
def run(
    ctx: typer.Context,
    command_name: Optional[str] = typer.Argument(None, help="Name of the command to run"),
):
    """Run a command by name, or show interactive selection"""
    loader = CommandLoader()
    commands = loader.discover_commands()

    if not commands:
        console.print("[red]No commands found in the commands directory[/red]")
        raise typer.Exit(1)

    if command_name:
        if command_name in commands:
            console.print(f"[green]Executing command: {command_name}[/green]")
            # Pass remaining arguments to the command
            command_args = ctx.args
            success = loader.execute_command(command_name, commands, command_args)
            if not success:
                console.print(f"[red]Failed to execute command: {command_name}[/red]")
                raise typer.Exit(1)
        else:
            console.print(f"[red]Command '{command_name}' not found[/red]")
            raise typer.Exit(1)
    else:
        _interactive_selection(loader, commands)


def _interactive_selection(loader: CommandLoader, commands: dict):
    """Show interactive command selection with arrow navigation and filtering"""
    console.print("\n[bold blue]Available Commands:[/bold blue]")

    # Show appropriate instructions based on TTY availability
    import sys

    if sys.stdin.isatty():
        console.print(
            "[dim]Use arrow keys to navigate, type to filter, Enter to select, Ctrl+C to cancel[/dim]\n"
        )
    else:
        console.print(
            "[dim]Interactive mode not available - using numbered selection[/dim]\n"
        )

    # Prepare menu choices
    menu_choices = []
    for name, info in commands.items():
        command_type = "📦" if info["type"] == "command_class" else "📄"
        display_name = f"{command_type} {name}"
        menu_choices.append(
            {"name": display_name, "value": name, "description": info["description"]}
        )

    # Add exit option
    menu_choices.append(
        {
            "name": "❌ Exit",
            "value": "exit",
            "description": "Quit without running a command",
        }
    )

    try:
        # Show interactive menu with filtering support
        selected = interactive_menu(
            "Select a command to run:", menu_choices, allow_filter=True
        )

        if not selected or selected["value"] == "exit":
            console.print("[yellow]Cancelled[/yellow]")
            return

        selected_command = selected["value"]
        console.print(f"\n[green]Executing command: {selected_command}[/green]")

        success = loader.execute_command(selected_command, commands)
        if not success:
            console.print(f"[red]Failed to execute command: {selected_command}[/red]")
            raise typer.Exit(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/yellow]")
        raise typer.Exit(0)


@app.command()
def info():
    """Show information about the CLI tool"""
    console.print("[bold blue]SCLI - Script CLI Tool[/bold blue]")
    console.print("\nA simple CLI tool for managing and executing Python scripts.")
    console.print("\nCommands:")
    console.print("  • [cyan]scli[/cyan] - Interactive script selection")
    console.print(
        "  • [cyan]scli -s <script_name>[/cyan] - Run specific script directly"
    )
    console.print("  • [cyan]scli run[/cyan] - Interactive script selection")
    console.print("  • [cyan]scli run <script_name>[/cyan] - Run specific script")
    console.print("  • [cyan]scli list-scripts[/cyan] - List all available scripts")
    console.print("  • [cyan]scli info[/cyan] - Show this information")
