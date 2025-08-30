#!/usr/bin/env python3
"""
Log Analytics Command for Request Metrics Analysis
Analyzes CSV log files to extract request metrics by time periods
"""

import os
import sys
from pathlib import Path

# Add the src directory to path to import scli modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.base_command import SimpleCommand
from models.log_analyzer_model import LogAnalyzerModel
from utils.log_analyzer_utils import LogAnalyzer

DESCRIPTION = "Analyze CSV log files to extract request metrics by time periods"


class LogAnalyzerCommand(SimpleCommand):
    """Log analyzer command implementation"""
    
    # Set the validation model
    event_model = LogAnalyzerModel
    
    def __init__(self):
        super().__init__(name="log_analyzer", description=DESCRIPTION)
        self.validated_data = None
        self.analyzer = None
    
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
                    if arg == '--csv-file' and i + 1 < len(args):
                        data['csv_file'] = args[i + 1]
                        i += 1
                    elif arg.startswith('--csv-file='):
                        data['csv_file'] = arg.split('=', 1)[1]
                    elif arg == '--output-file' and i + 1 < len(args):
                        data['output_file'] = args[i + 1]
                        i += 1
                    elif arg.startswith('--output-file='):
                        data['output_file'] = arg.split('=', 1)[1]
                    elif arg == '--top-n' and i + 1 < len(args):
                        data['top_n'] = int(args[i + 1])
                        i += 1
                    elif arg.startswith('--top-n='):
                        data['top_n'] = int(arg.split('=', 1)[1])
                    elif arg == '--analysis-type' and i + 1 < len(args):
                        data['analysis_type'] = args[i + 1]
                        i += 1
                    elif arg.startswith('--analysis-type='):
                        data['analysis_type'] = arg.split('=', 1)[1]
                    i += 1
            
            # Add any kwargs
            data.update(kwargs)
            
            # If no csv_file specified, try to find one interactively
            if 'csv_file' not in data:
                csv_file = self._get_csv_file_interactively()
                if csv_file:
                    data['csv_file'] = csv_file
                else:
                    self.print_error("CSV file is required for log analysis")
                    return False
            
            # Validate using Pydantic model
            self.validated_data = self.event_model(**data)
            
            self.logger.debug(f"Arguments validated successfully: {self.validated_data.to_dict()}")
            return True
            
        except Exception as e:
            self.print_error(f"Argument validation failed: {e}")
            self.logger.error(f"Preload validation error: {e}")
            return False
    
    def execute(self, *args, **kwargs) -> bool:
        """Execute the log analyzer command"""
        try:
            if not self.validated_data:
                self.print_error("No validated data available")
                return False
            
            # Initialize analyzer with validated CSV file
            csv_path = self.validated_data.get_csv_path()
            self.analyzer = LogAnalyzer(str(csv_path))
            
            self.print_info(f"Analyzing log file: {csv_path}")
            
            # Load logs
            self.analyzer.load_logs()
            
            if not self.analyzer.logs:
                self.print_warning("No log entries found in the file")
                return False
            
            self.print_success(f"Loaded {len(self.analyzer.logs)} log entries")
            
            # Perform analysis based on validated parameters
            self._perform_analysis()
            
            # Export results if requested
            output_path = self.validated_data.get_output_path()
            if output_path:
                self._export_results(output_path)
            
            # Store results
            self.set_result("csv_file", str(csv_path))
            self.set_result("total_entries", len(self.analyzer.logs))
            self.set_result("analysis_type", self.validated_data.analysis_type)
            self.set_result("validated_args", self.validated_data.to_dict())
            
            return True
        
        except Exception as e:
            self.print_error(f"Failed to analyze logs: {e}")
            return False
    
    def _get_csv_file_interactively(self) -> str:
        """Get CSV file path interactively"""
        # Look for CSV files in current directory
        csv_files = list(Path.cwd().glob("*.csv"))
        
        if not csv_files:
            # Ask user to provide path
            csv_path = self.get_user_input("Enter path to CSV log file:")
            return csv_path if csv_path and csv_path.strip() else None
        
        if len(csv_files) == 1:
            # Only one CSV file found, confirm with user
            csv_file = csv_files[0]
            if self.confirm_action(f"Use CSV file: {csv_file.name}?", default=True):
                return str(csv_file)
        else:
            # Multiple CSV files, let user choose
            options = []
            for csv_file in csv_files:
                file_size = csv_file.stat().st_size
                options.append({
                    "name": f"📄 {csv_file.name}",
                    "value": str(csv_file),
                    "description": f"Size: {self._format_size(file_size)}"
                })
            
            options.append({
                "name": "✏️  Enter custom path",
                "value": "custom",
                "description": "Enter a custom file path"
            })
            
            selected = self.get_user_choice("Select CSV file to analyze:", options)
            if selected and selected["value"] != "custom":
                return selected["value"]
            elif selected and selected["value"] == "custom":
                csv_path = self.get_user_input("Enter path to CSV log file:")
                return csv_path if csv_path and csv_path.strip() else None
        
        return None
    
    def _perform_analysis(self):
        """Perform log analysis based on validated parameters"""
        self.print_info("Performing log analysis...")
        
        # Print metrics based on analysis type
        if self.validated_data.should_analyze_daily():
            self._show_daily_analysis()
        
        if self.validated_data.should_analyze_hourly():
            self._show_hourly_analysis()
        
        if self.validated_data.should_analyze_minute():
            self._show_minute_analysis()
        
        if self.validated_data.analysis_type == "summary":
            self._show_summary_analysis()
    
    def _show_daily_analysis(self):
        """Show daily analysis results"""
        daily_data = self.analyzer.analyze_requests_by_day()
        top_days = self.analyzer.get_top_n(daily_data, self.validated_data.top_n)
        
        self.print_success(f"Top {self.validated_data.top_n} Days with Most Requests")
        print("-" * 50)
        
        total_requests = len(self.analyzer.logs)
        for i, (day, count) in enumerate(top_days, 1):
            percentage = (count / total_requests) * 100
            print(f"{i:2d}. {day}: {count:,} requests ({percentage:.2f}%)")
    
    def _show_hourly_analysis(self):
        """Show hourly analysis results"""
        hourly_data = self.analyzer.analyze_requests_by_hour()
        top_hours = self.analyzer.get_top_n(hourly_data, self.validated_data.top_n)
        
        self.print_success(f"Top {self.validated_data.top_n} Hours with Most Requests")
        print("-" * 50)
        
        total_requests = len(self.analyzer.logs)
        for i, (hour, count) in enumerate(top_hours, 1):
            percentage = (count / total_requests) * 100
            print(f"{i:2d}. {hour}: {count:,} requests ({percentage:.2f}%)")
    
    def _show_minute_analysis(self):
        """Show minute analysis results"""
        minute_data = self.analyzer.analyze_requests_by_minute()
        top_minutes = self.analyzer.get_top_n(minute_data, self.validated_data.top_n)
        
        self.print_success(f"Top {self.validated_data.top_n} Minutes with Most Requests")
        print("-" * 50)
        
        total_requests = len(self.analyzer.logs)
        for i, (minute, count) in enumerate(top_minutes, 1):
            percentage = (count / total_requests) * 100
            print(f"{i:2d}. {minute}: {count:,} requests ({percentage:.2f}%)")
    
    def _show_summary_analysis(self):
        """Show summary analysis"""
        total_requests = len(self.analyzer.logs)
        
        if total_requests == 0:
            print("No data to analyze")
            return
        
        # Time range
        timestamps = [log["timestamp"] for log in self.analyzer.logs]
        start_time = min(timestamps)
        end_time = max(timestamps)
        
        self.print_success("Log Analysis Summary")
        print("-" * 40)
        print(f"Total Requests: {total_requests:,}")
        print(f"Time Range: {start_time} to {end_time}")
        print(f"Duration: {end_time - start_time}")
    
    def _export_results(self, output_path: Path):
        """Export analysis results to JSON file"""
        try:
            self.print_info(f"Exporting results to: {output_path}")
            self.analyzer.export_to_json(str(output_path))
            self.print_success(f"Results exported successfully to {output_path}")
            self.set_result("output_file", str(output_path))
        except Exception as e:
            self.print_error(f"Failed to export results: {e}")
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        units = ["B", "KB", "MB", "GB"]
        unit_index = 0
        size = float(size_bytes)
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        else:
            return f"{size:.1f} {units[unit_index]}"


# Create command instance for dynamic import
command_instance = LogAnalyzerCommand()