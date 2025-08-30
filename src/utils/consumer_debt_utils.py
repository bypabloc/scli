#!/usr/bin/env python3
"""
Consumer Debt Utilities - API client and processing functionality
"""

import csv
import json
import os
import random
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

try:
    from utils.menu_utils import confirm, interactive_menu, text_input
    from output_manager import OutputManager
except ImportError:
    # Fallback for standalone usage
    pass


@dataclass
class ConsumerAPIConfig:
    """Configuration for Consumer Debt API"""
    
    base_url: str
    auth_token: str
    timeout: int = 30
    max_retries: int = 3
    delay_min: float = 0.5
    delay_max: float = 2.0
    batch_size: int = 50
    
    def __post_init__(self):
        if not self.base_url.endswith('/'):
            self.base_url += '/'
    
    @classmethod
    def from_env(cls) -> 'ConsumerAPIConfig':
        """Load configuration from environment variables"""
        return cls(
            base_url=os.getenv('CONSUMER_API_BASE_URL', 'https://api.consumer.example.com/'),
            auth_token=os.getenv('CONSUMER_API_TOKEN', ''),
            timeout=int(os.getenv('CONSUMER_API_TIMEOUT', '30')),
            max_retries=int(os.getenv('CONSUMER_API_MAX_RETRIES', '3')),
            delay_min=float(os.getenv('CONSUMER_API_DELAY_MIN', '0.5')),
            delay_max=float(os.getenv('CONSUMER_API_DELAY_MAX', '2.0')),
            batch_size=int(os.getenv('CONSUMER_API_BATCH_SIZE', '50'))
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'base_url': self.base_url,
            'auth_token': self.auth_token[:10] + '...' if self.auth_token else '',
            'timeout': self.timeout,
            'max_retries': self.max_retries,
            'delay_min': self.delay_min,
            'delay_max': self.delay_max,
            'batch_size': self.batch_size
        }


class ConsumerAPI:
    """Consumer Debt API Client"""
    
    def __init__(self, config: ConsumerAPIConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {config.auth_token}',
            'Content-Type': 'application/json',
            'User-Agent': 'SCLI-Consumer-Debt-Checker/1.0'
        })
    
    def test_connection(self) -> Dict[str, Any]:
        """Test API connection and authentication"""
        try:
            url = f"{self.config.base_url}health"
            response = self.session.get(url, timeout=self.config.timeout)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'status_code': response.status_code,
                    'message': 'Connection successful',
                    'data': response.json() if response.content else {}
                }
            else:
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'message': f'HTTP {response.status_code}: {response.reason}',
                    'data': response.text[:500] if response.text else ''
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'status_code': 0,
                'message': 'Request timed out',
                'data': ''
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'status_code': 0,
                'message': 'Connection error - unable to reach API',
                'data': ''
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'status_code': 0,
                'message': f'Request error: {str(e)}',
                'data': ''
            }
        except Exception as e:
            return {
                'success': False,
                'status_code': 0,
                'message': f'Unexpected error: {str(e)}',
                'data': ''
            }
    
    def query_credit_number(self, credit_number: str) -> Dict[str, Any]:
        """Query debt information for a single credit number"""
        try:
            url = f"{self.config.base_url}debt/query"
            payload = {'credit_number': credit_number}
            
            response = self.session.post(
                url, 
                json=payload, 
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'credit_number': credit_number,
                    'status_code': response.status_code,
                    'data': data
                }
            elif response.status_code == 404:
                return {
                    'success': False,
                    'credit_number': credit_number,
                    'status_code': response.status_code,
                    'error': 'Credit number not found',
                    'data': {}
                }
            else:
                return {
                    'success': False,
                    'credit_number': credit_number,
                    'status_code': response.status_code,
                    'error': f'HTTP {response.status_code}: {response.reason}',
                    'data': response.json() if response.content else {}
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'credit_number': credit_number,
                'status_code': 0,
                'error': 'Request timed out',
                'data': {}
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'credit_number': credit_number,
                'status_code': 0,
                'error': f'Request error: {str(e)}',
                'data': {}
            }
        except Exception as e:
            return {
                'success': False,
                'credit_number': credit_number,
                'status_code': 0,
                'error': f'Unexpected error: {str(e)}',
                'data': {}
            }
    
    def batch_query(self, credit_numbers: List[str]) -> List[Dict[str, Any]]:
        """Query multiple credit numbers with rate limiting"""
        results = []
        total = len(credit_numbers)
        
        print(f"🔄 Processing {total} credit numbers...")
        
        for i, credit_number in enumerate(credit_numbers, 1):
            # Query single credit number
            result = self.query_credit_number(credit_number)
            results.append(result)
            
            # Show progress
            if i % 10 == 0 or i == total:
                success_count = sum(1 for r in results if r['success'])
                print(f"   Progress: {i}/{total} ({i/total*100:.1f}%) - "
                     f"Success: {success_count}/{i} ({success_count/i*100:.1f}%)")
            
            # Rate limiting delay (except for last item)
            if i < total:
                delay = random.uniform(self.config.delay_min, self.config.delay_max)
                time.sleep(delay)
        
        return results
    
    def close(self):
        """Close the session"""
        if self.session:
            self.session.close()


def get_processing_subset(credit_numbers: List[str]) -> List[str]:
    """Allow user to select subset of credit numbers for processing"""
    total_count = len(credit_numbers)
    
    if total_count <= 10:
        # Small dataset, process all
        return credit_numbers
    
    print(f"\n📊 Found {total_count} credit numbers in CSV")
    
    options = [
        {
            "name": f"🔢 Process all {total_count} numbers",
            "value": "all",
            "description": f"Process all {total_count} credit numbers"
        },
        {
            "name": "📊 Process first 50",
            "value": "first_50",
            "description": "Process first 50 credit numbers for testing"
        },
        {
            "name": "🎲 Process random 50",
            "value": "random_50",
            "description": "Process random sample of 50 credit numbers"
        },
        {
            "name": "✏️  Custom range",
            "value": "custom",
            "description": "Specify custom range (e.g., 1-100)"
        },
        {
            "name": "❌ Cancel",
            "value": "cancel",
            "description": "Cancel processing"
        }
    ]
    
    selected = interactive_menu("Select processing mode:", options)
    
    if not selected or selected["value"] == "cancel":
        return []
    
    if selected["value"] == "all":
        return credit_numbers
    
    elif selected["value"] == "first_50":
        return credit_numbers[:50]
    
    elif selected["value"] == "random_50":
        if len(credit_numbers) <= 50:
            return credit_numbers
        return random.sample(credit_numbers, 50)
    
    elif selected["value"] == "custom":
        while True:
            range_input = text_input("Enter range (e.g., '1-100' or '50'):")
            if not range_input or not range_input.strip():
                return []
            
            range_input = range_input.strip()
            
            try:
                if '-' in range_input:
                    # Range format: start-end
                    start_str, end_str = range_input.split('-', 1)
                    start = int(start_str.strip())
                    end = int(end_str.strip())
                    
                    # Validate range
                    if start < 1 or end < start or start > total_count:
                        print(f"❌ Invalid range. Must be between 1 and {total_count}")
                        continue
                    
                    # Convert to 0-based index and limit to available data
                    start_idx = start - 1
                    end_idx = min(end, total_count)
                    
                    return credit_numbers[start_idx:end_idx]
                
                else:
                    # Single number format: take first N
                    count = int(range_input)
                    if count < 1 or count > total_count:
                        print(f"❌ Invalid count. Must be between 1 and {total_count}")
                        continue
                    
                    return credit_numbers[:count]
                    
            except ValueError:
                print("❌ Invalid format. Use 'N' for first N items or 'start-end' for range")
                continue
    
    return []


def extract_credit_numbers_from_csv_with_selection(
    csv_file: str
) -> Optional[List[str]]:
    """Extract credit numbers from CSV with column selection"""
    try:
        # Read first few rows to detect columns
        with open(csv_file, 'r', encoding='utf-8') as file:
            sample = file.read(1024)
            
        # Detect delimiter
        delimiter = ','
        if sample.count(';') > sample.count(','):
            delimiter = ';'
        elif sample.count('\t') > sample.count(','):
            delimiter = '\t'
        
        # Read header
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter=delimiter)
            headers = next(reader)
            
            # Read a few sample rows
            sample_rows = []
            for i, row in enumerate(reader):
                if i >= 3:  # Read max 3 sample rows
                    break
                sample_rows.append(row)
        
        if not headers:
            print("❌ Could not read CSV headers")
            return None
        
        print(f"📊 CSV file analysis:")
        print(f"   Delimiter: '{delimiter}'")
        print(f"   Columns found: {len(headers)}")
        print(f"   Sample rows: {len(sample_rows)}")
        
        print(f"\n📋 Available columns:")
        for i, header in enumerate(headers):
            sample_values = [row[i] if i < len(row) else '' for row in sample_rows]
            sample_str = ', '.join(f"'{v}'" for v in sample_values[:3] if v)
            print(f"   {i+1:2d}. {header:20s} | Sample: {sample_str}")
        
        # Let user select column
        while True:
            column_input = text_input(f"Select column number (1-{len(headers)}):")
            if not column_input or not column_input.strip():
                return None
            
            try:
                column_num = int(column_input.strip())
                if 1 <= column_num <= len(headers):
                    column_index = column_num - 1
                    column_name = headers[column_index]
                    break
                else:
                    print(f"❌ Invalid column number. Must be between 1 and {len(headers)}")
                    continue
            except ValueError:
                print("❌ Invalid input. Enter a column number")
                continue
        
        print(f"✅ Selected column: {column_name}")
        
        # Extract credit numbers from selected column
        credit_numbers = []
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter=delimiter)
            next(reader)  # Skip header
            
            for row_num, row in enumerate(reader, 2):
                if column_index < len(row):
                    value = row[column_index].strip()
                    if value and value.isdigit():
                        credit_numbers.append(value)
                    elif value:
                        # Non-numeric value warning
                        if len(credit_numbers) < 10:  # Only show first few warnings
                            print(f"⚠️  Row {row_num}: '{value}' is not a valid credit number")
        
        print(f"📊 Extracted {len(credit_numbers)} valid credit numbers")
        return credit_numbers
        
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        return None


def query_single_credit(config=None, api_client=None):
    """Query single credit number interactively"""
    print("🔍 Single Credit Number Query")
    print("-" * 35)
    
    # Get credit number from user
    credit_number = text_input("Enter credit number:")
    if not credit_number or not credit_number.strip():
        print("❌ Credit number is required")
        return
    
    credit_number = credit_number.strip()
    
    # Validate credit number format (basic validation)
    if not credit_number.isdigit():
        print("❌ Credit number should contain only digits")
        if not confirm("Continue anyway?", default=False):
            return
    
    print(f"\n🔄 Querying credit number: {credit_number}")
    
    # Initialize API client if not provided
    if not api_client:
        if not config:
            config = ConsumerAPIConfig.from_env()
        
        if not config.auth_token:
            print("❌ API token not configured")
            print("Set CONSUMER_API_TOKEN environment variable")
            return
        
        api_client = ConsumerAPI(config)
    
    try:
        # Query the API
        result = api_client.query_credit_number(credit_number)
        
        print(f"\n📊 Query Result:")
        print("-" * 20)
        
        if result['success']:
            print("✅ Status: SUCCESS")
            data = result['data']
            
            # Display key information
            if 'debt_amount' in data:
                print(f"💰 Debt Amount: ${data['debt_amount']:,.2f}")
            if 'status' in data:
                print(f"📊 Status: {data['status']}")
            if 'last_payment_date' in data:
                print(f"📅 Last Payment: {data['last_payment_date']}")
            if 'account_type' in data:
                print(f"🏦 Account Type: {data['account_type']}")
            
            # Show full data if requested
            if confirm("\nShow full response data?", default=False):
                print(f"\n📄 Full Response:")
                print(json.dumps(data, indent=2))
        
        else:
            print("❌ Status: FAILED")
            print(f"⚠️  Error: {result.get('error', 'Unknown error')}")
            print(f"🌐 Status Code: {result.get('status_code', 'N/A')}")
            
            if result.get('data'):
                print(f"📄 Response Data:")
                print(json.dumps(result['data'], indent=2))
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    finally:
        if api_client and 'api_client' not in locals():
            api_client.close()


def process_csv_file(config=None, api_client=None):
    """Process CSV file with credit numbers"""
    print("📄 CSV File Processing")
    print("-" * 25)
    
    # Browse for CSV file
    csv_file = browse_for_csv_file()
    if not csv_file:
        print("❌ No CSV file selected")
        return
    
    print(f"✅ Selected file: {os.path.basename(csv_file)}")
    
    # Show file info
    file_size = get_file_size_str(os.path.getsize(csv_file))
    print(f"📊 File size: {file_size}")
    
    # Extract credit numbers with column selection
    print(f"\n🔍 Analyzing CSV structure...")
    credit_numbers = extract_credit_numbers_from_csv_with_selection(csv_file)
    
    if not credit_numbers:
        print("❌ No valid credit numbers found in CSV")
        return
    
    # Get processing subset
    processing_list = get_processing_subset(credit_numbers)
    if not processing_list:
        print("❌ Processing cancelled")
        return
    
    print(f"\n🎯 Processing {len(processing_list)} credit numbers")
    
    # Initialize API client if not provided
    if not api_client:
        if not config:
            config = ConsumerAPIConfig.from_env()
        
        if not config.auth_token:
            print("❌ API token not configured")
            print("Set CONSUMER_API_TOKEN environment variable")
            return
        
        api_client = ConsumerAPI(config)
    
    try:
        # Confirm processing
        delay_info = f"{config.delay_min}-{config.delay_max}s" if config else "0.5-2.0s"
        estimated_time = len(processing_list) * 1.25  # Rough estimate in seconds
        
        print(f"\n⏱️  Processing Details:")
        print(f"   Credit numbers: {len(processing_list)}")
        print(f"   Rate limiting: {delay_info} delay between requests")
        print(f"   Estimated time: {estimated_time/60:.1f} minutes")
        
        if not confirm("\nProceed with processing?", default=True):
            print("❌ Processing cancelled")
            return
        
        # Process the credit numbers
        start_time = time.time()
        results = api_client.batch_query(processing_list)
        end_time = time.time()
        
        # Show summary
        print_processing_summary(results, end_time - start_time)
        
        # Generate CSV results
        if confirm("\nGenerate results CSV?", default=True):
            generate_results_csv(csv_file, results, processing_list)
    
    except KeyboardInterrupt:
        print("\n⚠️  Processing interrupted by user")
    except Exception as e:
        print(f"❌ Processing failed: {e}")
    
    finally:
        if api_client and 'api_client' not in locals():
            api_client.close()


def browse_for_csv_file() -> Optional[str]:
    """Browse for CSV file using interactive menu"""
    current_dir = os.getcwd()
    
    while True:
        items = []
        
        # Add parent directory option
        if current_dir != os.path.dirname(current_dir):
            items.append({
                "name": "📁 ..",
                "value": "..",
                "description": "Parent directory",
                "type": "parent"
            })
        
        try:
            entries = sorted(os.listdir(current_dir))
            
            # Add directories
            for entry in entries:
                full_path = os.path.join(current_dir, entry)
                if os.path.isdir(full_path):
                    items.append({
                        "name": f"📁 {entry}",
                        "value": entry,
                        "description": "Directory", 
                        "type": "dir"
                    })
            
            # Add CSV files
            for entry in entries:
                full_path = os.path.join(current_dir, entry)
                if os.path.isfile(full_path) and entry.lower().endswith('.csv'):
                    file_size = get_file_size_str(os.path.getsize(full_path))
                    items.append({
                        "name": f"📄 {entry}",
                        "value": entry,
                        "description": f"CSV File ({file_size})",
                        "type": "file"
                    })
            
            # Add manual entry and cancel options
            items.extend([
                {
                    "name": "✏️  Enter path manually",
                    "value": "manual",
                    "description": "Type full path to CSV file",
                    "type": "manual"
                },
                {
                    "name": "❌ Cancel", 
                    "value": "cancel",
                    "description": "Cancel file selection",
                    "type": "cancel"
                }
            ])
            
            # Show current directory and menu
            print(f"\n📂 Current directory: {current_dir}")
            selected = interactive_menu("Select CSV file:", items)
            
            if not selected or selected["type"] == "cancel":
                return None
            
            if selected["type"] == "manual":
                manual_path = text_input("Enter full path to CSV file:")
                if manual_path and manual_path.strip():
                    manual_path = manual_path.strip()
                    if os.path.exists(manual_path) and manual_path.lower().endswith('.csv'):
                        return os.path.abspath(manual_path)
                    else:
                        print(f"❌ Invalid CSV file: {manual_path}")
                        continue
            
            elif selected["type"] == "parent":
                current_dir = os.path.dirname(current_dir)
            
            elif selected["type"] == "dir":
                current_dir = os.path.join(current_dir, selected["value"])
            
            elif selected["type"] == "file":
                file_path = os.path.join(current_dir, selected["value"])
                return os.path.abspath(file_path)
        
        except PermissionError:
            print(f"❌ Permission denied: {current_dir}")
            current_dir = os.path.dirname(current_dir)
        except Exception as e:
            print(f"❌ Error browsing directory: {e}")
            return None


def extract_credit_numbers_from_csv(csv_file: str) -> List[str]:
    """Extract credit numbers from CSV file (simple extraction)"""
    credit_numbers = []
    
    try:
        # Try to detect delimiter
        with open(csv_file, 'r', encoding='utf-8') as file:
            sample = file.read(1024)
        
        delimiter = ','
        if sample.count(';') > sample.count(','):
            delimiter = ';' 
        elif sample.count('\t') > sample.count(','):
            delimiter = '\t'
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter=delimiter)
            
            # Skip header if it exists
            first_row = next(reader, None)
            if first_row and not any(cell.isdigit() for cell in first_row if cell.strip()):
                pass  # First row is likely header, already skipped
            else:
                # First row contains data, process it
                for cell in first_row:
                    cell = cell.strip()
                    if cell and cell.isdigit():
                        credit_numbers.append(cell)
            
            # Process remaining rows
            for row in reader:
                for cell in row:
                    cell = cell.strip()
                    if cell and cell.isdigit():
                        credit_numbers.append(cell)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_numbers = []
        for num in credit_numbers:
            if num not in seen:
                seen.add(num)
                unique_numbers.append(num)
        
        return unique_numbers
        
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return []


def get_delay_setting(config: Dict) -> float:
    """Get delay setting from config or user input"""
    if 'delay' in config:
        return config['delay']
    
    delay_options = [
        {"name": "⚡ Fast (0.1s)", "value": 0.1, "description": "Minimal delay - use with caution"},
        {"name": "🚀 Normal (0.5s)", "value": 0.5, "description": "Recommended for most APIs"}, 
        {"name": "🐌 Slow (1.0s)", "value": 1.0, "description": "Conservative delay"},
        {"name": "🔧 Custom", "value": "custom", "description": "Enter custom delay"}
    ]
    
    selected = interactive_menu("Select delay between requests:", delay_options)
    
    if not selected:
        return 0.5  # Default
    
    if selected["value"] == "custom":
        while True:
            delay_input = text_input("Enter delay in seconds (e.g., 0.5):")
            try:
                delay = float(delay_input)
                if delay >= 0:
                    return delay
                else:
                    print("❌ Delay must be non-negative")
            except ValueError:
                print("❌ Invalid delay value")
    else:
        return selected["value"]


def generate_results_csv(
    original_csv: str, results: List[Dict[str, Any]], credit_numbers: List[str]
):
    """Generate CSV file with query results"""
    try:
        # Generate output filename
        output_manager = OutputManager()
        base_name = os.path.splitext(os.path.basename(original_csv))[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"{base_name}_debt_results_{timestamp}.csv"
        output_file = output_manager.get_output_path("consumer_debt_checker", csv_filename)
        
        # Prepare CSV headers
        headers = [
            'credit_number',
            'query_success', 
            'status_code',
            'debt_amount',
            'account_status',
            'account_type',
            'last_payment_date',
            'balance',
            'credit_limit',
            'error_message',
            'query_timestamp'
        ]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            
            for result in results:
                # Extract data from result
                credit_number = result.get('credit_number', '')
                success = result.get('success', False)
                status_code = result.get('status_code', 0)
                error_message = result.get('error', '')
                
                # Extract debt data if successful
                data = result.get('data', {})
                debt_amount = data.get('debt_amount', '')
                account_status = data.get('status', '')
                account_type = data.get('account_type', '')
                last_payment_date = data.get('last_payment_date', '')
                balance = data.get('balance', '')
                credit_limit = data.get('credit_limit', '')
                
                # Write row
                writer.writerow({
                    'credit_number': credit_number,
                    'query_success': 'YES' if success else 'NO',
                    'status_code': status_code,
                    'debt_amount': debt_amount,
                    'account_status': account_status,
                    'account_type': account_type,
                    'last_payment_date': last_payment_date,
                    'balance': balance,
                    'credit_limit': credit_limit,
                    'error_message': error_message,
                    'query_timestamp': datetime.now().isoformat()
                })
        
        file_size = get_file_size_str(os.path.getsize(output_file))
        print(f"✅ Results CSV generated!")
        print(f"   File: {output_file}")
        print(f"   Size: {file_size}")
        print(f"   Records: {len(results)}")
        
    except Exception as e:
        print(f"❌ Failed to generate CSV: {e}")


def print_processing_summary(results: List[Dict[str, Any]], elapsed_time: float):
    """Print summary of processing results"""
    total = len(results)
    successful = sum(1 for r in results if r.get('success', False))
    failed = total - successful
    
    print(f"\n📊 Processing Summary")
    print("=" * 30)
    print(f"Total processed: {total}")
    print(f"Successful queries: {successful} ({successful/total*100:.1f}%)")
    print(f"Failed queries: {failed} ({failed/total*100:.1f}%)")
    print(f"Processing time: {elapsed_time:.1f} seconds")
    print(f"Average time per query: {elapsed_time/total:.2f} seconds")
    
    if failed > 0:
        print(f"\n⚠️  Failed Queries:")
        failure_reasons = {}
        for result in results:
            if not result.get('success', False):
                error = result.get('error', 'Unknown error')
                failure_reasons[error] = failure_reasons.get(error, 0) + 1
        
        for error, count in failure_reasons.items():
            print(f"   • {error}: {count} occurrences")
    
    # Show some successful results if available
    successful_results = [r for r in results if r.get('success', False)]
    if successful_results:
        print(f"\n✅ Sample Successful Results:")
        for i, result in enumerate(successful_results[:3], 1):
            data = result.get('data', {})
            credit_num = result.get('credit_number', 'N/A')
            debt_amount = data.get('debt_amount', 'N/A')
            status = data.get('status', 'N/A')
            print(f"   {i}. Credit: {credit_num} | Debt: ${debt_amount} | Status: {status}")


def test_api_connection(config=None, api_client=None):
    """Test API connection and configuration"""
    print("🌐 API Connection Test")
    print("-" * 25)
    
    # Initialize config if not provided
    if not config:
        config = ConsumerAPIConfig.from_env()
    
    print(f"📋 Configuration:")
    config_dict = config.to_dict()
    for key, value in config_dict.items():
        print(f"   {key}: {value}")
    
    # Check if token is configured
    if not config.auth_token:
        print(f"\n❌ API token not configured!")
        print(f"Set the CONSUMER_API_TOKEN environment variable")
        return
    
    # Initialize API client if not provided
    if not api_client:
        api_client = ConsumerAPI(config)
    
    try:
        print(f"\n🔄 Testing connection to: {config.base_url}")
        result = api_client.test_connection()
        
        if result['success']:
            print(f"✅ Connection successful!")
            print(f"   Status code: {result['status_code']}")
            print(f"   Response: {result['message']}")
            
            if result.get('data'):
                print(f"   API Data: {json.dumps(result['data'], indent=2)}")
        else:
            print(f"❌ Connection failed!")
            print(f"   Status code: {result['status_code']}")
            print(f"   Error: {result['message']}")
            
            if result.get('data'):
                print(f"   Response: {result['data']}")
    
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
    
    finally:
        if api_client and 'api_client' not in locals():
            api_client.close()


def get_file_size_str(size_bytes: int) -> str:
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