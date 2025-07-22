import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from typing import Optional
from .script_loader import ScriptLoader
from .menu_utils import interactive_menu

app = typer.Typer(help="A CLI tool for executing selectable scripts", invoke_without_command=True)
console = Console()


@app.callback()
def main(
    ctx: typer.Context,
    script: Optional[str] = typer.Option(None, "-s", "--script", help="Name of the script to run directly")
):
    """Main CLI entry point. Run without command for interactive selection."""
    if ctx.invoked_subcommand is None:
        loader = ScriptLoader()
        scripts = loader.discover_scripts()
        
        if not scripts:
            console.print("[red]No scripts found in the scripts directory[/red]")
            raise typer.Exit(1)
        
        if script:
            if script in scripts:
                console.print(f"[green]Executing script: {script}[/green]")
                success = loader.execute_script(script, scripts)
                if not success:
                    console.print(f"[red]Failed to execute script: {script}[/red]")
                    raise typer.Exit(1)
            else:
                console.print(f"[red]Script '{script}' not found[/red]")
                raise typer.Exit(1)
        else:
            _interactive_selection(loader, scripts)


@app.command()
def list_scripts():
    """List all available scripts"""
    loader = ScriptLoader()
    scripts = loader.discover_scripts()
    
    if not scripts:
        console.print("[yellow]No scripts found in the scripts directory[/yellow]")
        return
    
    table = Table(title="Available Scripts")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Description", style="magenta")
    
    for name, info in scripts.items():
        table.add_row(name, info['description'])
    
    console.print(table)


@app.command()
def run(script_name: Optional[str] = typer.Argument(None, help="Name of the script to run")):
    """Run a script by name, or show interactive selection"""
    loader = ScriptLoader()
    scripts = loader.discover_scripts()
    
    if not scripts:
        console.print("[red]No scripts found in the scripts directory[/red]")
        raise typer.Exit(1)
    
    if script_name:
        if script_name in scripts:
            console.print(f"[green]Executing script: {script_name}[/green]")
            success = loader.execute_script(script_name, scripts)
            if not success:
                console.print(f"[red]Failed to execute script: {script_name}[/red]")
                raise typer.Exit(1)
        else:
            console.print(f"[red]Script '{script_name}' not found[/red]")
            raise typer.Exit(1)
    else:
        _interactive_selection(loader, scripts)


def _interactive_selection(loader: ScriptLoader, scripts: dict):
    """Show interactive script selection with arrow navigation and filtering"""
    console.print("\n[bold blue]Available Scripts:[/bold blue]")
    
    # Show appropriate instructions based on TTY availability
    import sys
    if sys.stdin.isatty():
        console.print("[dim]Use arrow keys to navigate, type to filter, Enter to select, Ctrl+C to cancel[/dim]\n")
    else:
        console.print("[dim]Interactive mode not available - using numbered selection[/dim]\n")
    
    # Prepare menu choices
    menu_choices = []
    for name, info in scripts.items():
        menu_choices.append({
            'name': name,
            'value': name,
            'description': info['description']
        })
    
    # Add exit option
    menu_choices.append({
        'name': '❌ Exit',
        'value': 'exit',
        'description': 'Quit without running a script'
    })
    
    try:
        # Show interactive menu with filtering support
        selected = interactive_menu(
            "Select a script to run:",
            menu_choices,
            allow_filter=True
        )
        
        if not selected or selected['value'] == 'exit':
            console.print("[yellow]Cancelled[/yellow]")
            return
        
        selected_script = selected['value']
        console.print(f"\n[green]Executing script: {selected_script}[/green]")
        
        success = loader.execute_script(selected_script, scripts)
        if not success:
            console.print(f"[red]Failed to execute script: {selected_script}[/red]")
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
    console.print("  • [cyan]scli -s <script_name>[/cyan] - Run specific script directly")
    console.print("  • [cyan]scli run[/cyan] - Interactive script selection")
    console.print("  • [cyan]scli run <script_name>[/cyan] - Run specific script")
    console.print("  • [cyan]scli list-scripts[/cyan] - List all available scripts")
    console.print("  • [cyan]scli info[/cyan] - Show this information")


if __name__ == "__main__":
    app()