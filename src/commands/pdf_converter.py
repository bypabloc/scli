#!/usr/bin/env python3
"""
PDF Converter - Convert PDF files to different formats (TXT, Images)
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add the src directory to path to import scli modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.base_command import InteractiveCommand
from models.pdf_converter_model import PdfConverterModel
from utils.pdf_utils import (
    get_pdf_libraries_status, convert_pdf_to_text, convert_pdf_to_images,
    get_file_size_str, convert_pdf_file
)
from output_manager import OutputManager

DESCRIPTION = "PDF Converter - Convert PDF files to TXT or image formats"


class PdfConverterCommand(InteractiveCommand):
    """PDF converter command implementation"""
    
    # Set the validation model
    event_model = PdfConverterModel
    
    def __init__(self):
        super().__init__(name="pdf_converter", description=DESCRIPTION)
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
                    elif arg == '--pdf-file' and i + 1 < len(args):
                        data['pdf_file'] = args[i + 1]
                        i += 1
                    elif arg.startswith('--pdf-file='):
                        data['pdf_file'] = arg.split('=', 1)[1]
                    elif arg == '--format' and i + 1 < len(args):
                        data['output_format'] = args[i + 1]
                        i += 1
                    elif arg.startswith('--format='):
                        data['output_format'] = arg.split('=', 1)[1]
                    elif arg == '--output' and i + 1 < len(args):
                        data['output_path'] = args[i + 1]
                        i += 1
                    elif arg.startswith('--output='):
                        data['output_path'] = arg.split('=', 1)[1]
                    elif arg == '--dpi' and i + 1 < len(args):
                        data['dpi'] = int(args[i + 1])
                        i += 1
                    elif arg.startswith('--dpi='):
                        data['dpi'] = int(arg.split('=', 1)[1])
                    elif arg == '--quality' and i + 1 < len(args):
                        data['quality'] = int(args[i + 1])
                        i += 1
                    elif arg.startswith('--quality='):
                        data['quality'] = int(arg.split('=', 1)[1])
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
        """Check if PDF processing libraries are available"""
        try:
            # Check PDF libraries
            libraries = get_pdf_libraries_status()
            available_libraries = [lib for lib, status in libraries.items() if status]
            
            if not available_libraries:
                self.print_error("No PDF processing libraries found!")
                self.print_info("Install dependencies with:")
                self.print_info("  uv add PyPDF2 PyMuPDF pdf2image Pillow pdfplumber")
                return False
            
            self.print_success(f"PDF libraries available: {', '.join(available_libraries)}")
            return True
            
        except Exception as e:
            self.print_error(f"Requirements check failed: {e}")
            return False
    
    def validation(self, *args, **kwargs) -> bool:
        """Validate mode-specific requirements"""
        try:
            if not self.validated_data:
                self.print_error("No validated data available")
                return False
            
            # Check mode-specific requirements
            if self.validated_data.requires_pdf_file() and not self.validated_data.pdf_file:
                self.print_error("Convert mode requires a PDF file path")
                return False
            
            if self.validated_data.requires_output_format() and not self.validated_data.output_format:
                self.print_error("Convert mode requires an output format")
                return False
            
            return True
            
        except Exception as e:
            self.print_error(f"Validation failed: {e}")
            return False
    
    def execute(self, *args, **kwargs) -> bool:
        """Execute the PDF converter command"""
        try:
            if not self.validated_data:
                self.print_error("No validated data available")
                return False
            
            # Execute based on mode
            if self.validated_data.is_convert_mode():
                return self._execute_convert_mode()
            else:  # interactive mode
                return self._execute_interactive_mode()
        
        except Exception as e:
            self.print_error(f"Failed to execute PDF converter: {e}")
            return False
    
    def _execute_convert_mode(self) -> bool:
        """Execute direct conversion mode"""
        pdf_path = self.validated_data.get_pdf_path()
        output_format = self.validated_data.output_format
        
        self.print_info(f"Converting {pdf_path.name} to {output_format.upper()}")
        
        # Setup output
        output_manager = OutputManager()
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        base_name = pdf_path.stem
        
        if self.validated_data.is_text_format():
            # Convert to text
            if self.validated_data.output_path:
                output_path = self.validated_data.get_output_path_obj()
            else:
                output_filename = f"{base_name}_{timestamp}.txt"
                output_path = output_manager.get_output_path("pdf_converter", output_filename)
            
            success = convert_pdf_to_text(str(pdf_path), str(output_path))
            
            if success:
                file_size = get_file_size_str(output_path.stat().st_size)
                self.print_success("Text conversion completed!")
                self.print_info(f"Output file: {output_path}")
                self.print_info(f"Output size: {file_size}")
                
                # Store results
                self.set_result("output_file", str(output_path))
                self.set_result("output_format", "txt")
                self.set_result("file_size", file_size)
                
                return True
            else:
                return False
        
        elif self.validated_data.is_image_format():
            # Convert to images
            if self.validated_data.output_path:
                output_dir = self.validated_data.get_output_path_obj()
                output_dir.mkdir(parents=True, exist_ok=True)
            else:
                output_dir = output_manager.get_output_path(
                    "pdf_converter", f"{base_name}_{timestamp}"
                )
            
            image_paths = convert_pdf_to_images(
                str(pdf_path), str(output_dir), output_format.upper()
            )
            
            if image_paths:
                total_size = sum(Path(path).stat().st_size for path in image_paths)
                self.print_success("Image conversion completed!")
                self.print_info(f"Output directory: {output_dir}")
                self.print_info(f"Generated {len(image_paths)} images")
                self.print_info(f"Total size: {get_file_size_str(total_size)}")
                
                # Store results
                self.set_result("output_directory", str(output_dir))
                self.set_result("output_format", output_format)
                self.set_result("image_count", len(image_paths))
                self.set_result("total_size", get_file_size_str(total_size))
                
                return True
            else:
                return False
        
        return False
    
    def _execute_interactive_mode(self) -> bool:
        """Execute interactive mode"""
        self.print_info("Starting PDF converter interactive mode...")
        
        # Run the existing interactive conversion function
        convert_pdf_file()
        
        # Always return True for interactive mode since errors are handled internally
        return True


# Create command instance for dynamic import
command_instance = PdfConverterCommand()