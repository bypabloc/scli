#!/usr/bin/env python3
"""
Consumer Debt Checker Command - Query consumer debt information via API
"""

import os
import sys

# Add the src directory to path to import scli modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.base_command import InteractiveCommand
from models.consumer_debt_checker_model import ConsumerDebtCheckerModel
from utils.consumer_debt_utils import (
    ConsumerAPIConfig, ConsumerAPI, query_single_credit, process_csv_file,
    test_api_connection
)
from utils.menu_utils import interactive_menu

DESCRIPTION = "Consumer debt checker - Query debt information via API"


class ConsumerDebtCheckerCommand(InteractiveCommand):
    """Consumer debt checker command implementation"""
    
    # Set the validation model
    event_model = ConsumerDebtCheckerModel
    
    def __init__(self):
        super().__init__(name="consumer_debt_checker", description=DESCRIPTION)
        self.validated_data = None
        self.config = None
        self.api_client = None
    
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
                    elif arg == '--api-url' and i + 1 < len(args):
                        data['api_url'] = args[i + 1]
                        i += 1
                    elif arg.startswith('--api-url='):
                        data['api_url'] = arg.split('=', 1)[1]
                    elif arg == '--api-token' and i + 1 < len(args):
                        data['api_token'] = args[i + 1]
                        i += 1
                    elif arg.startswith('--api-token='):
                        data['api_token'] = arg.split('=', 1)[1]
                    elif arg == '--csv-file' and i + 1 < len(args):
                        data['csv_file'] = args[i + 1]
                        i += 1
                    elif arg.startswith('--csv-file='):
                        data['csv_file'] = arg.split('=', 1)[1]
                    elif arg == '--credit-number' and i + 1 < len(args):
                        data['credit_number'] = args[i + 1]
                        i += 1
                    elif arg.startswith('--credit-number='):
                        data['credit_number'] = arg.split('=', 1)[1]
                    elif arg == '--batch-size' and i + 1 < len(args):
                        data['batch_size'] = int(args[i + 1])
                        i += 1
                    elif arg.startswith('--batch-size='):
                        data['batch_size'] = int(arg.split('=', 1)[1])
                    elif arg == '--delay' and i + 1 < len(args):
                        data['delay'] = float(args[i + 1])
                        i += 1
                    elif arg.startswith('--delay='):
                        data['delay'] = float(arg.split('=', 1)[1])
                    elif arg == '--timeout' and i + 1 < len(args):
                        data['timeout'] = int(args[i + 1])
                        i += 1
                    elif arg.startswith('--timeout='):
                        data['timeout'] = int(arg.split('=', 1)[1])
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
            # Check requests library
            import requests
            self.print_success("Required libraries available: requests")
            return True
            
        except ImportError:
            self.print_error("Requests library is required for API calls")
            self.print_info("Install with: uv add requests")
            return False
        except Exception as e:
            self.print_error(f"Requirements check failed: {e}")
            return False
    
    def validation(self, *args, **kwargs) -> bool:
        """Validate API configuration and parameters"""
        try:
            if not self.validated_data:
                self.print_error("No validated data available")
                return False
            
            # Create configuration from validated data and environment
            self.config = ConsumerAPIConfig(
                base_url=self.validated_data.api_url or os.getenv('CONSUMER_API_BASE_URL', ''),
                auth_token=self.validated_data.api_token or os.getenv('CONSUMER_API_TOKEN', ''),
                timeout=self.validated_data.timeout,
                batch_size=self.validated_data.batch_size,
                delay_min=self.validated_data.delay,
                delay_max=self.validated_data.delay + 0.5
            )
            
            # Validate API configuration for modes that need it
            if self.validated_data.requires_api():
                if not self.config.base_url:
                    self.print_error("API URL is required")
                    self.print_info("Set --api-url or CONSUMER_API_BASE_URL environment variable")
                    return False
                
                if not self.config.auth_token:
                    self.print_error("API token is required")
                    self.print_info("Set --api-token or CONSUMER_API_TOKEN environment variable")
                    return False
            
            # Validate CSV file if specified
            if self.validated_data.csv_file:
                csv_path = self.validated_data.get_csv_path()
                if not csv_path.exists():
                    self.print_error(f"CSV file not found: {csv_path}")
                    return False
                
                if not csv_path.is_file():
                    self.print_error(f"Path is not a file: {csv_path}")
                    return False
            
            # Validate credit number format if specified
            if self.validated_data.credit_number:
                if not self.validated_data.credit_number.isdigit():
                    self.print_warning("Credit number contains non-digit characters")
                    # Allow continuation since some systems might accept non-numeric IDs
            
            return True
            
        except Exception as e:
            self.print_error(f"Validation failed: {e}")
            return False
    
    def execute(self, *args, **kwargs) -> bool:
        """Execute the consumer debt checker command"""
        try:
            if not self.validated_data:
                self.print_error("No validated data available")
                return False
            
            # Initialize API client if needed
            if self.validated_data.requires_api():
                self.api_client = ConsumerAPI(self.config)
            
            # Execute based on mode
            if self.validated_data.is_single_mode():
                return self._execute_single_mode()
            elif self.validated_data.is_csv_mode():
                return self._execute_csv_mode()
            elif self.validated_data.is_test_mode():
                return self._execute_test_mode()
            else:  # interactive mode
                return self._execute_interactive_mode()
        
        except Exception as e:
            self.print_error(f"Failed to execute consumer debt checker: {e}")
            return False
        
        finally:
            # Close API client
            if self.api_client:
                self.api_client.close()
    
    def _execute_single_mode(self) -> bool:
        """Execute single credit number query mode"""
        credit_number = self.validated_data.credit_number
        
        self.print_info(f"Querying credit number: {credit_number}")
        
        try:
            result = self.api_client.query_credit_number(credit_number)
            
            if result['success']:
                self.print_success("Query successful")
                data = result['data']
                
                # Display key information
                if 'debt_amount' in data:
                    self.print_info(f"Debt Amount: ${data['debt_amount']:,.2f}")
                if 'status' in data:
                    self.print_info(f"Status: {data['status']}")
                if 'last_payment_date' in data:
                    self.print_info(f"Last Payment: {data['last_payment_date']}")
                
                # Store results
                self.set_result("credit_number", credit_number)
                self.set_result("query_success", True)
                self.set_result("debt_data", data)
                
                return True
            else:
                self.print_error(f"Query failed: {result.get('error', 'Unknown error')}")
                self.set_result("credit_number", credit_number)
                self.set_result("query_success", False)
                self.set_result("error", result.get('error'))
                return False
        
        except Exception as e:
            self.print_error(f"Failed to query credit number: {e}")
            return False
    
    def _execute_csv_mode(self) -> bool:
        """Execute CSV processing mode"""
        csv_path = self.validated_data.get_csv_path()
        
        self.print_info(f"Processing CSV file: {csv_path.name}")
        
        try:
            # Use the utility function for CSV processing
            process_csv_file(self.config, self.api_client)
            
            # Store results
            self.set_result("csv_file", str(csv_path))
            self.set_result("mode", "csv")
            self.set_result("validated_args", self.validated_data.to_dict())
            
            return True
        
        except Exception as e:
            self.print_error(f"Failed to process CSV file: {e}")
            return False
    
    def _execute_test_mode(self) -> bool:
        """Execute API connection test mode"""
        self.print_info("Testing API connection...")
        
        try:
            test_api_connection(self.config, self.api_client)
            
            # Store results
            self.set_result("mode", "test")
            self.set_result("api_config", self.config.to_dict())
            self.set_result("validated_args", self.validated_data.to_dict())
            
            return True
        
        except Exception as e:
            self.print_error(f"API connection test failed: {e}")
            return False
    
    def _execute_interactive_mode(self) -> bool:
        """Execute interactive mode"""
        self.print_info("Starting consumer debt checker interactive mode...")
        
        # Show mode selection menu
        mode_options = [
            {
                "name": "🔍 Query Single Credit Number",
                "value": "single",
                "description": "Query debt information for one credit number"
            },
            {
                "name": "📄 Process CSV File",
                "value": "csv",
                "description": "Process multiple credit numbers from CSV file"
            },
            {
                "name": "🌐 Test API Connection",
                "value": "test",
                "description": "Test API connection and authentication"
            },
            {
                "name": "❌ Exit",
                "value": "exit",
                "description": "Exit without processing"
            }
        ]
        
        selected = self.get_user_choice("Select operation mode:", mode_options)
        if not selected or selected["value"] == "exit":
            self.print_info("Operation cancelled")
            return True
        
        try:
            if selected["value"] == "single":
                query_single_credit(self.config, self.api_client)
            elif selected["value"] == "csv":
                process_csv_file(self.config, self.api_client)
            elif selected["value"] == "test":
                test_api_connection(self.config, self.api_client)
            
            # Store results
            self.set_result("mode", "interactive")
            self.set_result("interactive_choice", selected["value"])
            self.set_result("validated_args", self.validated_data.to_dict())
            
            return True
            
        except Exception as e:
            self.print_error(f"Interactive processing failed: {e}")
            return False


# Create command instance for dynamic import
command_instance = ConsumerDebtCheckerCommand()