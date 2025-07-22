"""Output directory manager for SCLI scripts."""

from pathlib import Path
from datetime import datetime
from typing import Optional


class OutputManager:
    """Manages output directory structure for scripts."""
    
    def __init__(self, base_output_dir: str = "output"):
        """Initialize output manager.
        
        Args:
            base_output_dir: Base directory for all outputs (default: "output")
        """
        self.base_output_dir = Path(base_output_dir)
    
    def get_output_path(self, script_name: str, filename: str, subfolder: Optional[str] = None) -> Path:
        """Get the full output path for a file.
        
        Args:
            script_name: Name of the script generating the output
            filename: Name of the output file
            subfolder: Optional subfolder name (empty string means no subfolder)
            
        Returns:
            Full path for the output file
        """
        if subfolder == "":
            # No subfolder, just script_name directory
            output_dir = self.base_output_dir / script_name
        else:
            # Use provided subfolder or default to timestamp
            if subfolder is None:
                subfolder = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            output_dir = self.base_output_dir / script_name / subfolder
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        return output_dir / filename
    
    def create_script_output_dir(self, script_name: str, subfolder: Optional[str] = None) -> Path:
        """Create and return the output directory for a script.
        
        Args:
            script_name: Name of the script
            subfolder: Optional subfolder name (defaults to timestamp)
            
        Returns:
            Path to the created directory
        """
        if subfolder is None:
            subfolder = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        
        output_dir = self.base_output_dir / script_name / subfolder
        output_dir.mkdir(parents=True, exist_ok=True)
        
        return output_dir