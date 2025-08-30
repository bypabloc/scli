#!/usr/bin/env python3
"""
CSV Viewer Command - Interactive CSV file viewer with filtering and column management
"""

import os
import sys
from pathlib import Path

# Add the src directory to path to import scli modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.base_command import InteractiveCommand
from models.csv_viewer_model import CsvViewerModel
from utils.csv_utils import (
    CSVViewerApp, CSVData, select_csv_file, detect_separator, 
    load_csv_file, TEXTUAL_AVAILABLE
)

DESCRIPTION = "Interactive CSV viewer with filtering and column management"


class CsvViewerCommand(InteractiveCommand):
    """CSV viewer command implementation"""
    
    # Set the validation model
    event_model = CsvViewerModel
    
    def __init__(self):
        super().__init__(name="csv_viewer", description=DESCRIPTION)
        self.validated_data = None
    
    def preload(self, *args, **kwargs) -> bool:
        """
        Preload and validate command arguments using Pydantic model.
        """
        try:
            # Call parent preload first
            if not super().preload(*args, **kwargs):
                return False
            
            # Convert args to a dictionary for validation
            data = {}
            
            # Parse command line arguments if provided
            if args:
                i = 0
                while i < len(args):
                    arg = args[i]
                    if arg == '--mode' and i + 1 < len(args):
                        data['mode'] = args[i + 1]
                        i += 1
                    elif arg.startswith('--mode='):
                        data['mode'] = arg.split('=', 1)[1]
                    elif arg == '--csv-file' and i + 1 < len(args):
                        data['csv_file'] = args[i + 1]
                        i += 1
                    elif arg.startswith('--csv-file='):
                        data['csv_file'] = arg.split('=', 1)[1]
                    elif arg == '--separator' and i + 1 < len(args):
                        data['separator'] = args[i + 1]
                        i += 1
                    elif arg.startswith('--separator='):
                        data['separator'] = arg.split('=', 1)[1]
                    elif arg == '--page-size' and i + 1 < len(args):
                        data['page_size'] = int(args[i + 1])
                        i += 1
                    elif arg.startswith('--page-size='):
                        data['page_size'] = int(arg.split('=', 1)[1])
                    elif arg == '--visible-columns' and i + 1 < len(args):
                        data['visible_columns'] = args[i + 1].split(',')
                        i += 1
                    elif arg.startswith('--visible-columns='):
                        data['visible_columns'] = arg.split('=', 1)[1].split(',')
                    elif arg == '--encoding' and i + 1 < len(args):
                        data['encoding'] = args[i + 1]
                        i += 1
                    elif arg.startswith('--encoding='):
                        data['encoding'] = arg.split('=', 1)[1]
                    i += 1
            
            # Add any kwargs
            data.update(kwargs)
            
            # Set default mode if not specified
            if 'mode' not in data:
                data['mode'] = 'interactive'
            
            # Validate using Pydantic model
            self.validated_data = self.event_model(**data)
            
            self.logger.debug(f"Arguments validated successfully: {self.validated_data.to_dict()}")
            return True
            
        except Exception as e:
            self.print_error(f"Argument validation failed: {e}")
            self.logger.error(f"Preload validation error: {e}")
            return False
    
    def requirements(self, *args, **kwargs) -> bool:
        """Check if required libraries are available"""
        try:
            if not TEXTUAL_AVAILABLE:
                self.print_error("Textual library is required for CSV viewer")
                self.print_info("Install with: uv add textual pandas")
                return False
            
            # Check pandas
            try:
                import pandas as pd
                self.print_success("Required libraries available: textual, pandas")
                return True
            except ImportError:
                self.print_error("Pandas library is required for CSV processing")
                self.print_info("Install with: uv add pandas")
                return False
            
        except Exception as e:
            self.print_error(f"Requirements check failed: {e}")
            return False
    
    def validation(self, *args, **kwargs) -> bool:
        """Validate CSV file and parameters"""
        try:
            if not self.validated_data:
                self.print_error("No validated data available")
                return False
            
            # If CSV file specified, validate it exists
            if self.validated_data.csv_file:
                csv_path = self.validated_data.get_csv_path()
                if not csv_path.exists():
                    self.print_error(f"CSV file not found: {csv_path}")
                    return False
                
                if not csv_path.is_file():
                    self.print_error(f"Path is not a file: {csv_path}")
                    return False
            
            return True
            
        except Exception as e:
            self.print_error(f"Validation failed: {e}")
            return False
    
    def execute(self, *args, **kwargs) -> bool:
        """Execute the CSV viewer command"""
        try:
            if not self.validated_data:
                self.print_error("No validated data available")
                return False
            
            # Get CSV file
            if self.validated_data.csv_file:
                csv_file = str(self.validated_data.get_csv_path())
            else:
                # Interactive file selection
                self.print_info("Select CSV file to view...")
                csv_file = select_csv_file()
                if not csv_file:
                    self.print_warning("No CSV file selected")
                    return False
            
            self.print_info(f"Loading CSV file: {Path(csv_file).name}")
            
            # Detect or use provided separator
            separator = self.validated_data.separator or detect_separator(csv_file)
            self.print_info(f"Using separator: '{separator}'")
            
            # Load CSV metadata
            result = load_csv_file(csv_file, separator)
            if not result:
                self.print_error("Failed to load CSV file")
                return False
            
            csv_data, encoding = result
            
            # Apply validated parameters
            if self.validated_data.page_size:
                csv_data.page_size = self.validated_data.page_size
            
            if self.validated_data.visible_columns:
                # Filter to only valid columns
                valid_columns = set(self.validated_data.visible_columns) & set(csv_data.columns)
                if valid_columns:
                    csv_data.visible_columns = valid_columns
                else:
                    self.print_warning("None of the specified columns exist in the CSV")
            
            # Start the Textual application
            self.print_success("Starting CSV viewer...")
            app = CSVViewerApp(csv_data)
            app.encoding = encoding  # Set encoding for the app
            
            try:
                app.run()
                
                # Store results
                self.set_result("csv_file", csv_file)
                self.set_result("separator", separator)
                self.set_result("total_rows", csv_data.total_rows)
                self.set_result("total_columns", len(csv_data.columns))
                self.set_result("encoding", encoding)
                self.set_result("validated_args", self.validated_data.to_dict())
                
                return True
                
            except KeyboardInterrupt:
                self.print_info("CSV viewer closed by user")
                return True
            except Exception as e:
                self.print_error(f"Error running CSV viewer: {e}")
                return False
        
        except Exception as e:
            self.print_error(f"Failed to execute CSV viewer: {e}")
            return False


# Create command instance for dynamic import
command_instance = CsvViewerCommand()