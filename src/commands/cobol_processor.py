#!/usr/bin/env python3
"""
COBOL Processor Command - Process COBOL copybook and data files
"""

import os
import sys
from pathlib import Path

# Add the src directory to path to import scli modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.base_command import InteractiveCommand
from models.cobol_processor_model import CobolProcessorModel
from utils.cobol_utils import (
    select_and_process_files, browse_directory_files, process_files,
    validate_file_path
)
from utils.menu_utils import interactive_menu

DESCRIPTION = "COBOL file processor - Process .cpy and .txt files to interpret data"


class CobolProcessorCommand(InteractiveCommand):
    """COBOL processor command implementation"""
    
    # Set the validation model
    event_model = CobolProcessorModel
    
    def __init__(self):
        super().__init__(name="cobol_processor", description=DESCRIPTION)
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
                    elif arg == '--cpy-file' and i + 1 < len(args):
                        data['cpy_file'] = args[i + 1]
                        i += 1
                    elif arg.startswith('--cpy-file='):
                        data['cpy_file'] = arg.split('=', 1)[1]
                    elif arg == '--txt-file' and i + 1 < len(args):
                        data['txt_file'] = args[i + 1]
                        i += 1
                    elif arg.startswith('--txt-file='):
                        data['txt_file'] = arg.split('=', 1)[1]
                    elif arg == '--directory' and i + 1 < len(args):
                        data['directory'] = args[i + 1]
                        i += 1
                    elif arg.startswith('--directory='):
                        data['directory'] = arg.split('=', 1)[1]
                    elif arg == '--export-csv':
                        data['export_csv'] = True
                    elif arg == '--no-export-csv':
                        data['export_csv'] = False
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
        """Check if required dependencies are available"""
        try:
            # COBOL processor has no special requirements beyond standard library
            self.print_success("All required dependencies available")
            return True
            
        except Exception as e:
            self.print_error(f"Requirements check failed: {e}")
            return False
    
    def validation(self, *args, **kwargs) -> bool:
        """Validate files and parameters"""
        try:
            if not self.validated_data:
                self.print_error("No validated data available")
                return False
            
            # Validate files if provided
            if self.validated_data.cpy_file:
                cpy_path = self.validated_data.get_cpy_path()
                if not cpy_path.exists():
                    self.print_error(f"CPY file not found: {cpy_path}")
                    return False
                
                if not validate_file_path(str(cpy_path), ".cpy"):
                    return False
            
            if self.validated_data.txt_file:
                txt_path = self.validated_data.get_txt_path()
                if not txt_path.exists():
                    self.print_error(f"TXT file not found: {txt_path}")
                    return False
                
                if not validate_file_path(str(txt_path), ".txt"):
                    return False
            
            # Validate directory if provided
            if self.validated_data.directory:
                dir_path = self.validated_data.get_directory_path()
                if not dir_path.exists():
                    self.print_error(f"Directory not found: {dir_path}")
                    return False
                
                if not dir_path.is_dir():
                    self.print_error(f"Path is not a directory: {dir_path}")
                    return False
            
            # Validate mode-specific requirements
            if self.validated_data.is_direct_mode():
                if not self.validated_data.cpy_file:
                    self.print_error("Direct mode requires a CPY file")
                    return False
                
                if not self.validated_data.txt_file:
                    self.print_error("Direct mode requires a TXT file")
                    return False
            
            elif self.validated_data.is_directory_mode():
                if not self.validated_data.directory:
                    self.print_error("Directory mode requires a directory path")
                    return False
            
            return True
            
        except Exception as e:
            self.print_error(f"Validation failed: {e}")
            return False
    
    def execute(self, *args, **kwargs) -> bool:
        """Execute the COBOL processor command"""
        try:
            if not self.validated_data:
                self.print_error("No validated data available")
                return False
            
            # Execute based on mode
            if self.validated_data.is_direct_mode():
                return self._execute_direct_mode()
            elif self.validated_data.is_directory_mode():
                return self._execute_directory_mode()
            else:  # interactive mode
                return self._execute_interactive_mode()
        
        except Exception as e:
            self.print_error(f"Failed to execute COBOL processor: {e}")
            return False
    
    def _execute_direct_mode(self) -> bool:
        """Execute direct processing mode"""
        cpy_path = self.validated_data.get_cpy_path()
        txt_path = self.validated_data.get_txt_path()
        
        self.print_info(f"Processing files directly:")
        self.print_info(f"  CPY: {cpy_path.name}")
        self.print_info(f"  TXT: {txt_path.name}")
        
        try:
            process_files(str(cpy_path), str(txt_path))
            
            # Store results
            self.set_result("cpy_file", str(cpy_path))
            self.set_result("txt_file", str(txt_path))
            self.set_result("mode", "direct")
            self.set_result("validated_args", self.validated_data.to_dict())
            
            return True
            
        except Exception as e:
            self.print_error(f"Failed to process files: {e}")
            return False
    
    def _execute_directory_mode(self) -> bool:
        """Execute directory scanning mode"""
        dir_path = self.validated_data.get_directory_path()
        
        self.print_info(f"Scanning directory: {dir_path}")
        
        try:
            browse_directory_files()  # This function handles the directory internally
            
            # Store results
            self.set_result("directory", str(dir_path))
            self.set_result("mode", "directory")
            self.set_result("validated_args", self.validated_data.to_dict())
            
            return True
            
        except Exception as e:
            self.print_error(f"Failed to scan directory: {e}")
            return False
    
    def _execute_interactive_mode(self) -> bool:
        """Execute interactive mode"""
        self.print_info("Starting COBOL processor interactive mode...")
        
        # Show mode selection menu
        mode_options = [
            {
                "name": "📂 Select Files Manually",
                "value": "select",
                "description": "Browse and select .cpy and .txt files individually"
            },
            {
                "name": "📁 Scan Directory",
                "value": "directory",
                "description": "Scan directory for .cpy and .txt files"
            },
            {
                "name": "❌ Exit",
                "value": "exit",
                "description": "Exit without processing"
            }
        ]
        
        selected = self.get_user_choice("Select processing mode:", mode_options)
        if not selected or selected["value"] == "exit":
            self.print_info("Operation cancelled")
            return True
        
        try:
            if selected["value"] == "select":
                select_and_process_files()
            elif selected["value"] == "directory":
                browse_directory_files()
            
            # Store results
            self.set_result("mode", "interactive")
            self.set_result("interactive_choice", selected["value"])
            self.set_result("validated_args", self.validated_data.to_dict())
            
            return True
            
        except Exception as e:
            self.print_error(f"Interactive processing failed: {e}")
            return False


# Create command instance for dynamic import
command_instance = CobolProcessorCommand()