#!/usr/bin/env python3
"""
File Counter Command - Count files by extension in directories
"""

import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Tuple

# Add the src directory to path to import scli modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.base_command import InteractiveCommand
from models.file_counter_model import FileCounterModel

DESCRIPTION = "Count files by extension in current directory"


class FileCounterCommand(InteractiveCommand):
    """File counter command implementation"""
    
    # Set the validation model
    event_model = FileCounterModel
    
    def __init__(self):
        super().__init__(name="file_counter", description=DESCRIPTION)
        self.validated_data = None
    
    def preload(self, *args, **kwargs) -> bool:
        """
        Preload and validate command arguments using Pydantic model.
        
        This method validates the input arguments and prepares the command
        for execution with validated data.
        """
        try:
            # Call parent preload first
            if not super().preload(*args, **kwargs):
                return False
            
            # Convert args to a dictionary for validation
            # For file_counter, we can get arguments from various sources
            data = {}
            
            # Parse command line arguments if provided
            if args:
                # Simple argument parsing for demonstration
                i = 0
                while i < len(args):
                    arg = args[i]
                    if arg == '--directory' and i + 1 < len(args):
                        data['directory'] = args[i + 1]
                        i += 1
                    elif arg.startswith('--directory='):
                        data['directory'] = arg.split('=', 1)[1]
                    elif arg in ['--recursive', '-r']:
                        data['recursive'] = True
                    elif arg in ['--no-recursive']:
                        data['recursive'] = False
                    elif arg in ['--show-hidden']:
                        data['show_hidden'] = True
                    elif arg == '--extensions' and i + 1 < len(args):
                        data['extensions'] = args[i + 1]
                        i += 1
                    elif arg.startswith('--extensions='):
                        data['extensions'] = arg.split('=', 1)[1]
                    i += 1
            
            # Add any kwargs
            data.update(kwargs)
            
            # Validate using Pydantic model
            self.validated_data = self.event_model(**data)
            
            # Validate size range if both min and max are specified
            self.validated_data.validate_size_range()
            
            self.logger.debug(f"Arguments validated successfully: {self.validated_data.to_dict()}")
            return True
            
        except Exception as e:
            self.print_error(f"Argument validation failed: {e}")
            self.logger.error(f"Preload validation error: {e}")
            return False
    
    def execute(self, *args, **kwargs) -> bool:
        """Execute the file counter command"""
        try:
            # Use validated data if available, otherwise fall back to interactive mode
            if self.validated_data and self.validated_data.directory:
                # Use validated directory
                directory = self.validated_data.get_directory_path()
                self.print_info(f"Using directory from arguments: {directory}")
            else:
                # Interactive mode - get directory from user
                directory = self._get_target_directory()
                if not directory:
                    self.print_warning("No directory selected")
                    return False
            
            # Count files with filters from validated data
            self.print_info(f"Analyzing directory: {directory}")
            file_counts, total_files, total_size = self._count_files_with_filters(directory)
            
            # Display results
            self._display_results(directory, file_counts, total_files, total_size)
            
            # Store results
            self.set_result("directory", str(directory))
            self.set_result("file_counts", dict(file_counts))
            self.set_result("total_files", total_files)
            self.set_result("total_size", total_size)
            
            # Store validation info
            if self.validated_data:
                self.set_result("validated_args", self.validated_data.to_dict())
            
            return True
        
        except Exception as e:
            self.print_error(f"Failed to count files: {e}")
            return False
    
    def _get_target_directory(self) -> Path:
        """Get the target directory from user"""
        options = [
            {
                "name": "📁 Current directory",
                "value": "current",
                "description": f"Analyze current directory: {Path.cwd()}"
            },
            {
                "name": "🏠 Home directory", 
                "value": "home",
                "description": f"Analyze home directory: {Path.home()}"
            },
            {
                "name": "✏️  Custom path",
                "value": "custom",
                "description": "Enter custom directory path"
            },
            {
                "name": "❌ Cancel",
                "value": "cancel",
                "description": "Cancel operation"
            }
        ]
        
        choice = self.get_user_choice("Select directory to analyze:", options)
        if not choice or choice["value"] == "cancel":
            return None
        
        if choice["value"] == "current":
            return Path.cwd()
        elif choice["value"] == "home":
            return Path.home()
        elif choice["value"] == "custom":
            path_str = self.get_user_input("Enter directory path:")
            if not path_str:
                return None
            
            path = Path(path_str).expanduser()
            if not path.exists():
                self.print_error(f"Directory does not exist: {path}")
                return None
            if not path.is_dir():
                self.print_error(f"Path is not a directory: {path}")
                return None
            
            return path
        
        return None
    
    def _count_files(self, directory: Path) -> Tuple[Dict[str, int], int, int]:
        """Count files by extension in directory"""
        file_counts = defaultdict(int)
        total_files = 0
        total_size = 0
        
        try:
            # Get recursive option
            recursive = self.confirm_action("Include subdirectories?", default=True)
            
            # Walk through directory
            if recursive:
                pattern = "**/*"
            else:
                pattern = "*"
            
            for file_path in directory.glob(pattern):
                if file_path.is_file():
                    try:
                        # Get file extension
                        extension = file_path.suffix.lower()
                        if not extension:
                            extension = "[no extension]"
                        
                        # Count file and size
                        file_counts[extension] += 1
                        total_files += 1
                        total_size += file_path.stat().st_size
                        
                    except (OSError, PermissionError) as e:
                        self.add_warning(f"Could not access file {file_path}: {e}")
                        continue
        
        except PermissionError as e:
            self.print_error(f"Permission denied accessing directory: {e}")
            raise
        
        return file_counts, total_files, total_size
    
    def _count_files_with_filters(self, directory: Path) -> Tuple[Dict[str, int], int, int]:
        """Count files with filters from validated data"""
        file_counts = defaultdict(int)
        total_files = 0
        total_size = 0
        
        try:
            # Get recursion setting from validated data or user
            if self.validated_data:
                recursive = self.validated_data.recursive
            else:
                recursive = self.confirm_action("Include subdirectories?", default=True)
            
            # Walk through directory
            if recursive:
                pattern = "**/*"
            else:
                pattern = "*"
            
            for file_path in directory.glob(pattern):
                if file_path.is_file():
                    try:
                        # Apply filters if we have validated data
                        if self.validated_data and not self.validated_data.should_include_file(file_path):
                            continue
                        
                        # Get file extension
                        extension = file_path.suffix.lower()
                        if not extension:
                            extension = "[no extension]"
                        
                        # Count file and size
                        file_counts[extension] += 1
                        total_files += 1
                        total_size += file_path.stat().st_size
                        
                    except (OSError, PermissionError) as e:
                        self.add_warning(f"Could not access file {file_path}: {e}")
                        continue
        
        except PermissionError as e:
            self.print_error(f"Permission denied accessing directory: {e}")
            raise
        
        return file_counts, total_files, total_size
    
    def _display_results(self, directory: Path, file_counts: Dict[str, int], 
                        total_files: int, total_size: int):
        """Display the file counting results"""
        self.print_success("File Count Analysis Results")
        print("=" * 60)
        
        print(f"\n📁 Directory: {directory}")
        print(f"📊 Total Files: {total_files:,}")
        print(f"💾 Total Size: {self._format_size(total_size)}")
        
        if not file_counts:
            print("\n⚠️  No files found")
            return
        
        print(f"\n📋 Files by Extension:")
        print("-" * 40)
        
        # Sort by count (descending)
        sorted_counts = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Display in a table format
        print(f"{'Extension':<20} {'Count':<10} {'Percentage'}")
        print("-" * 40)
        
        for extension, count in sorted_counts:
            percentage = (count / total_files) * 100
            print(f"{extension:<20} {count:<10,} {percentage:>6.1f}%")
        
        # Show top extensions summary
        if len(sorted_counts) > 5:
            print(f"\n🔝 Top 5 Extensions:")
            for i, (ext, count) in enumerate(sorted_counts[:5], 1):
                percentage = (count / total_files) * 100
                print(f"  {i}. {ext}: {count:,} files ({percentage:.1f}%)")
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        units = ["B", "KB", "MB", "GB", "TB"]
        unit_index = 0
        size = float(size_bytes)
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        else:
            return f"{size:.1f} {units[unit_index]}"


# Create command instance for the new system
command_instance = FileCounterCommand()

