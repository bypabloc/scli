import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from typing import Optional
from .script_loader import ScriptLoader

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
    """Show interactive script selection"""
    console.print("\n[bold blue]Available Scripts:[/bold blue]")
    
    script_list = list(scripts.keys())
    for i, name in enumerate(script_list, 1):
        console.print(f"  {i}. [cyan]{name}[/cyan] - {scripts[name]['description']}")
    
    try:
        choice = Prompt.ask(
            "\nSelect a script to run",
            choices=[str(i) for i in range(1, len(script_list) + 1)] + ["q"],
            default="q"
        )
        
        if choice.lower() == "q":
            console.print("[yellow]Cancelled[/yellow]")
            return
        
        selected_script = script_list[int(choice) - 1]
        console.print(f"\n[green]Executing script: {selected_script}[/green]")
        
        success = loader.execute_script(selected_script, scripts)
        if not success:
            console.print(f"[red]Failed to execute script: {selected_script}[/red]")
            raise typer.Exit(1)
            
    except (ValueError, IndexError):
        console.print("[red]Invalid selection[/red]")
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