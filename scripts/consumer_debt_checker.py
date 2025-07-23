#!/usr/bin/env python3
"""
Consumer API Debt Checker - Consulta de deudas mediante API Consumer
"""

import os
import sys
import csv
import json
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Add the src directory to path to import scli modules
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
from scli.menu_utils import interactive_menu, text_input, confirm
from scli.output_manager import OutputManager
from scli.config_loader import get_script_config, create_sample_script_config
from scli.logger import get_logger, log_request, log_config_info


DESCRIPTION = "Consumer debt checker - Query debts via Consumer API"


# Initialize logger
logger = get_logger("consumer_debt_checker")


@dataclass
class ConsumerAPIConfig:
    """Configuration for Consumer API"""
    base_url: str
    auth_path: str
    debt_path: str
    client_id: str
    client_secret: str
    timeout: int = 30
    scope: str = "Internet_Clientes_Persona"
    oauth_type: str = "iam-scf"
    
    @classmethod
    def from_config(cls, config: Dict) -> 'ConsumerAPIConfig':
        """Create ConsumerAPIConfig from configuration dictionary"""
        api_config = config.get('api', {})
        
        return cls(
            base_url=api_config.get('base_url', ''),
            auth_path=api_config.get('auth_path', ''),
            debt_path=api_config.get('debt_path', ''),
            client_id=api_config.get('client_id', ''),
            client_secret=api_config.get('client_secret', ''),
            timeout=api_config.get('timeout', 30),
            scope=api_config.get('scope', 'Internet_Clientes_Persona'),
            oauth_type=api_config.get('oauth_type', 'iam-scf')
        )
    
    @property
    def auth_url(self) -> str:
        """Get full authentication URL"""
        return f"{self.base_url}{self.auth_path}"
    
    def debt_url(self, loan_id: str) -> str:
        """Get full debt query URL for a specific loan"""
        return f"{self.base_url}{self.debt_path}/{loan_id}/installments_payable"


class ConsumerAPI:
    """Consumer API client"""
    
    def __init__(self, config: ConsumerAPIConfig):
        self.config = config
        self.access_token = None
        self.token_expires_at = None
        self.response_cache = {}  # Cache for avoiding duplicate queries
        logger.info("Initialized Consumer API client")
        logger.debug(f"Base URL: {config.base_url}")
        logger.debug(f"Auth URL: {config.auth_url}")
        logger.debug(f"Client ID: {config.client_id[:8]}***")
        
    def authenticate(self) -> bool:
        """Authenticate with Consumer API"""
        logger.info("Starting authentication with Consumer API")
        
        headers = {
            'oauth_type': self.config.oauth_type,
            'X-Consumer-Client-Id': self.config.client_id,
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'curl/8.7.1',  # Emulate curl to bypass User-Agent blocking
            'Accept': '*/*'
        }
        
        data = {
            'grant_type': 'client_credentials',
            'scope': self.config.scope
        }
        
        try:
            # Log request details
            logger.info(f"🔍 Sending authentication request...")
            logger.debug(f"URL: {self.config.auth_url}")
            logger.debug(f"Headers: {headers}")
            logger.debug(f"Data: {data}")
            logger.debug(f"Auth credentials: {self.config.client_id}:{self.config.client_secret[:4]}***")
            
            log_request(
                logger, 
                'POST', 
                self.config.auth_url, 
                headers=headers, 
                data=data
            )
            
            # Make the request with detailed logging
            logger.info(f"📡 Making POST request to Consumer API...")
            response = requests.post(
                self.config.auth_url,
                headers=headers,
                data=data,
                auth=(self.config.client_id, self.config.client_secret),
                timeout=self.config.timeout,
                allow_redirects=False  # Don't follow redirects
            )
            
            logger.info(f"📥 Received response: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            
            # Check if this is a redirect
            if response.status_code in [301, 302, 303, 307, 308]:
                logger.warning(f"🔄 Received redirect {response.status_code}")
                logger.warning(f"Location: {response.headers.get('Location', 'N/A')}")
                logger.warning("This might indicate geographic blocking or URL changes")
            
            # Log response details
            log_request(
                logger, 
                'POST', 
                self.config.auth_url,
                response_status=response.status_code,
                response_text=response.text
            )
            
            if response.status_code == 200:
                auth_data = response.json()
                self.access_token = auth_data.get('access_token')
                expires_in = int(auth_data.get('expires_in', 300))
                self.token_expires_at = time.time() + expires_in - 30
                
                logger.info(f"✅ Authentication successful, token expires in {expires_in}s")
                logger.debug(f"Access token: {self.access_token[:20]}..." if self.access_token else "No token received")
                return True
            else:
                logger.error(f"❌ Authentication failed with status {response.status_code}")
                logger.error(f"Response headers: {dict(response.headers)}")
                
                # Enhanced logging for common error scenarios
                if response.status_code == 403:
                    logger.error("🚫 403 Forbidden - Possible causes:")
                    logger.error("   - IP address blocked by Consumer API firewall")
                    logger.error("   - Geographic restrictions (need Chilean IP)")
                    logger.error("   - Invalid client credentials")
                    logger.error("   - Missing required headers")
                elif response.status_code == 401:
                    logger.error("🔑 401 Unauthorized - Authentication credential issues:")
                    logger.error("   - Invalid client_id or client_secret")
                    logger.error("   - Credentials expired or revoked")
                elif response.status_code == 400:
                    logger.error("📝 400 Bad Request - Request format issues:")
                    logger.error("   - Invalid grant_type or scope")
                    logger.error("   - Missing required parameters")
                
                # Log the exact request that was sent for debugging
                logger.error("🔍 Request details for debugging:")
                logger.error(f"   URL: {self.config.auth_url}")
                logger.error(f"   Method: POST")
                logger.error(f"   Headers: {headers}")
                logger.error(f"   Data: {data}")
                logger.error(f"   Auth: {self.config.client_id}:{self.config.client_secret[:4]}***")
                
                # Show curl equivalent that works
                logger.error("💡 Working curl command equivalent:")
                logger.error(f"   curl -X POST '{self.config.auth_url}' \\")
                logger.error(f"     -H 'oauth_type: {self.config.oauth_type}' \\")
                logger.error(f"     -H 'X-Consumer-Client-Id: {self.config.client_id}' \\")
                logger.error(f"     -H 'Content-Type: application/x-www-form-urlencoded' \\")
                logger.error(f"     -u '{self.config.client_id}:{self.config.client_secret}' \\")
                logger.error(f"     -d 'grant_type=client_credentials&scope={self.config.scope}'")
                
                logger.error(f"Response: {response.text}")
                print(f"❌ Authentication error: {response.status_code}")
                
                # Try to parse error details
                try:
                    error_data = response.json()
                    logger.error(f"Error details: {error_data}")
                except:
                    pass
                
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Connection error during authentication: {e}")
            print(f"❌ Connection error during authentication: {e}")
            return False
    
    def is_token_valid(self) -> bool:
        """Check if current token is valid"""
        return self.access_token and time.time() < self.token_expires_at
    
    def ensure_authentication(self) -> bool:
        """Ensure we have a valid token"""
        if not self.is_token_valid():
            print("🔄 Token expired, re-authenticating...")
            return self.authenticate()
        return True
    
    def format_loan_id(self, credit_number: str) -> str:
        """Format credit number according to API standard"""
        clean_number = credit_number.replace('00350001', '')
        
        if len(clean_number) > 12:
            clean_number = clean_number[-12:]
        elif len(clean_number) < 12:
            clean_number = clean_number.zfill(12)
        
        return f"00350001{clean_number}"
    
    def categorize_error(self, error_message: str) -> str:
        """Categorize error message"""
        if not error_message:
            return "UNKNOWN"
        
        error_upper = error_message.upper()
        
        if "NO SE PUDO VALIDAR OPERACION" in error_upper:
            return "NO_VALIDAR_OPERACION"
        elif "REVISAR SITUACION DE PRESTAMO" in error_upper:
            return "REVISAR_SITUACION_PRESTAMO"
        elif "REVISAR SITUACION CONTABLE" in error_upper:
            return "REVISAR_SITUACION_CONTABLE"
        elif "LA APLICACION SE ENCUENTRA DESACTIVA" in error_upper:
            return "APLICACION_DESACTIVA"
        elif "REINTENTAR POR CONTEXTO" in error_upper:
            return "REINTENTAR_CONTEXTO"
        elif "UNAUTHORIZED" in error_upper or "TOKEN" in error_upper:
            return "TOKEN_INVALIDO"
        else:
            return f"OTRO"
    
    def parse_amount(self, amount_str: str) -> float:
        """Convert API amount format to Chilean pesos"""
        if not amount_str or not amount_str.isdigit():
            return 0.0
        
        amount_int = int(amount_str)
        return amount_int / 10000.0
    
    def query_debt(self, credit_number: str) -> Dict:
        """Query debt for specific credit number with caching and retry logic"""
        logger.debug(f"Querying debt for credit number: {credit_number}")
        
        # Check cache first
        if credit_number in self.response_cache:
            logger.debug(f"Using cached response for credit {credit_number}")
            cached_result = self.response_cache[credit_number].copy()
            cached_result['from_cache'] = True
            return cached_result
        
        # Try to query (with retry on auth errors)
        return self._query_debt_with_retry(credit_number)
    
    def _query_debt_with_retry(self, credit_number: str, retry_count: int = 0) -> Dict:
        """Internal method to query debt with automatic re-authentication"""
        max_retries = 2
        
        if not self.ensure_authentication():
            logger.error(f"Authentication failed for credit {credit_number}")
            return {
                'credit_number': credit_number,
                'status_code': 'AUTH_ERROR',
                'error': 'Authentication failed',
                'response': None,
                'timestamp': datetime.now().isoformat(),
                'from_cache': False
            }
        
        formatted_id = self.format_loan_id(credit_number)
        debt_url = self.config.debt_url(formatted_id)
        
        headers = {
            'X-Consumer-Client-Id': self.config.client_id,
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'User-Agent': 'curl/8.7.1'  # Consistent User-Agent
        }
        
        try:
            # Log request details
            log_request(
                logger,
                'GET',
                debt_url,
                headers=headers
            )
            
            response = requests.get(debt_url, headers=headers, timeout=self.config.timeout)
            
            # Log response details
            log_request(
                logger,
                'GET',
                debt_url,
                response_status=response.status_code,
                response_text=response.text
            )
            
            # Check for authentication errors and retry if needed
            if response.status_code in [401, 403] and retry_count < max_retries:
                logger.warning(f"🔄 Authentication error {response.status_code} for {credit_number}, retrying...")
                logger.info(f"🔑 Re-authenticating (attempt {retry_count + 1}/{max_retries})")
                
                # Force re-authentication
                self.access_token = None
                self.token_expires_at = None
                
                if self.authenticate():
                    logger.info(f"✅ Re-authentication successful, retrying query for {credit_number}")
                    return self._query_debt_with_retry(credit_number, retry_count + 1)
                else:
                    logger.error(f"❌ Re-authentication failed for {credit_number}")
            
            result = {
                'credit_number': credit_number,
                'formatted_id': formatted_id,
                'status_code': response.status_code,
                'error': None,
                'response': None,
                'timestamp': datetime.now().isoformat(),
                'from_cache': False,
                'retry_count': retry_count
            }
            
            if response.status_code == 200:
                result['response'] = response.json()
                installments = result['response'].get('listRestInstallmentsPayableResponse', [])
                logger.info(f"✅ Successfully queried {credit_number}: {len(installments)} installments")
            else:
                logger.warning(f"❌ Failed to query {credit_number}: status {response.status_code}")
                try:
                    error_data = response.json()
                    if 'errors' in error_data:
                        if isinstance(error_data['errors'], list) and len(error_data['errors']) > 0:
                            result['error'] = error_data['errors'][0].get('message', 'Unknown error')
                        elif isinstance(error_data['errors'], dict):
                            result['error'] = error_data['errors'].get('message', 'Unknown error')
                        else:
                            result['error'] = str(error_data['errors'])
                    else:
                        result['error'] = response.text
                    logger.error(f"Error details for {credit_number}: {result['error']}")
                except json.JSONDecodeError:
                    result['error'] = response.text
                    logger.error(f"Raw error response for {credit_number}: {response.text}")
            
            # Cache the result (successful or failed)
            self.response_cache[credit_number] = result.copy()
            logger.debug(f"Cached response for {credit_number}")
            
            return result
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout querying {credit_number}")
            result = {
                'credit_number': credit_number,
                'formatted_id': formatted_id,
                'status_code': 'TIMEOUT',
                'error': 'Request timeout',
                'response': None,
                'timestamp': datetime.now().isoformat(),
                'from_cache': False,
                'retry_count': retry_count
            }
            # Cache timeout results too
            self.response_cache[credit_number] = result.copy()
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Connection error querying {credit_number}: {e}")
            result = {
                'credit_number': credit_number,
                'formatted_id': formatted_id,
                'status_code': 'CONNECTION_ERROR',
                'error': str(e),
                'response': None,
                'timestamp': datetime.now().isoformat(),
                'from_cache': False,
                'retry_count': retry_count
            }
            # Cache connection errors too
            self.response_cache[credit_number] = result.copy()
            return result


def get_processing_subset(credit_numbers: List[str]) -> List[str]:
    """Ask user how many records to process and return subset"""
    total_count = len(credit_numbers)
    
    # Show options
    print(f"\n📊 Processing Options:")
    print(f"   Total records available: {total_count}")
    
    options = [
        {
            'name': f'🚀 Process all {total_count} records',
            'value': 'all',
            'description': 'Process every credit number in the file'
        },
        {
            'name': '🔢 Process specific quantity',
            'value': 'quantity',
            'description': 'Enter exact number of records to process'
        },
        {
            'name': '📊 Process percentage',
            'value': 'percentage', 
            'description': 'Enter percentage of records to process'
        },
        {
            'name': '❌ Cancel',
            'value': 'cancel',
            'description': 'Cancel processing'
        }
    ]
    
    selected = interactive_menu("Select processing option:", options)
    
    if not selected or selected['value'] == 'cancel':
        return []
    
    if selected['value'] == 'all':
        return credit_numbers
    
    elif selected['value'] == 'quantity':
        while True:
            try:
                quantity_str = text_input(f"Enter number of records to process (1-{total_count}):")
                if not quantity_str:
                    return []
                
                quantity = int(quantity_str)
                if 1 <= quantity <= total_count:
                    return credit_numbers[:quantity]
                else:
                    print(f"❌ Please enter a number between 1 and {total_count}")
            except ValueError:
                print("❌ Please enter a valid number")
    
    elif selected['value'] == 'percentage':
        while True:
            try:
                percentage_str = text_input("Enter percentage to process (1-100):")
                if not percentage_str:
                    return []
                
                percentage = float(percentage_str)
                if 1 <= percentage <= 100:
                    quantity = max(1, int(total_count * percentage / 100))
                    print(f"📊 {percentage}% = {quantity} records")
                    return credit_numbers[:quantity]
                else:
                    print("❌ Please enter a percentage between 1 and 100")
            except ValueError:
                print("❌ Please enter a valid percentage")
    
    return []


def extract_credit_numbers_from_csv_with_selection(csv_file: str) -> Tuple[List[str], List[Dict]]:
    """Extract credit numbers from CSV with column selection and return original data"""
    print("📋 Analyzing CSV structure...")
    
    # First, read CSV to show available columns
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            # Try different delimiters
            sample = f.read(1024)
            f.seek(0)
            
            delimiter = ';' if sample.count(';') > sample.count(',') else ','
            reader = csv.DictReader(f, delimiter=delimiter)
            
            # Get column names
            columns = reader.fieldnames
            if not columns:
                print("❌ Could not read CSV columns")
                return [], []
            
            print(f"\n📊 Available columns in CSV:")
            for i, col in enumerate(columns, 1):
                # Highlight potential credit code columns
                if any(keyword in col.lower() for keyword in ['credit', 'codigo', 'ident', 'loan', 'credito']):
                    print(f"   {i}. {col} ⭐ (Potential credit code column)")
                elif any(keyword in col.lower() for keyword in ['numero', 'number', 'num', 'id']):
                    print(f"   {i}. {col} ✓ (May contain credit codes)")
                else:
                    print(f"   {i}. {col}")
            
            print(f"\n💡 Credit codes should be 12-digit numbers (API requires 00350001 + 12 digits)")
            
            # Let user select code column using interactive menu
            column_options = []
            for i, col in enumerate(columns):
                # Create description based on column type
                if any(keyword in col.lower() for keyword in ['credit', 'codigo', 'ident', 'loan', 'credito']):
                    description = "⭐ Potential credit code column"
                elif any(keyword in col.lower() for keyword in ['numero', 'number', 'num', 'id']):
                    description = "✓ May contain credit codes"
                else:
                    description = "Regular column"
                
                column_options.append({
                    'name': col,
                    'value': col,
                    'description': description
                })
            
            # Add cancel option
            column_options.append({
                'name': '❌ Cancel',
                'value': None,
                'description': 'Cancel column selection'
            })
            
            selected_option = interactive_menu("Select column for credit codes:", column_options)
            if not selected_option or selected_option['value'] is None:
                return [], []
            
            selected_column = selected_option['value']
            print(f"✅ Selected column: {selected_column}")
            
            # Read all data
            f.seek(0)
            reader = csv.DictReader(f, delimiter=delimiter)
            original_data = list(reader)
            
            # Extract credit numbers from selected column
            credit_numbers = []
            for row in original_data:
                credit_code = row.get(selected_column, '').strip()
                if credit_code and credit_code.isdigit() and len(credit_code) >= 10:
                    credit_numbers.append(credit_code)
            
            # Remove duplicates while preserving order
            unique_credits = []
            seen = set()
            for credit in credit_numbers:
                if credit not in seen:
                    unique_credits.append(credit)
                    seen.add(credit)
            
            print(f"📊 Extracted {len(unique_credits)} unique credit numbers")
            return unique_credits, original_data
            
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return [], []


def main():
    print("🏦 Consumer API Debt Checker")
    print("=" * 50)
    
    # Load configuration
    config = get_script_config("consumer_debt_checker")
    log_config_info(logger, config, "consumer_debt_checker")
    
    # Create sample config if none exists
    if not config:
        logger.warning("No configuration found, creating sample config file")
        sample_config = {
            'api': {
                'base_url': 'https://openbanking.consumer-homo.cl',
                'auth_path': '/party_authentication/oauth-dss-sos/v1/token',
                'debt_path': '/merchandising_loan/merchandising_loan_payment_plan/v1/loans',
                'client_id': 'YOUR_CLIENT_ID_HERE',
                'client_secret': 'YOUR_CLIENT_SECRET_HERE',
                'timeout': 30,
                'scope': 'Internet_Clientes_Persona',
                'oauth_type': 'iam-scf'
            },
            'processing': {
                'default_delay': 1.0,
                'max_delay': 10.0,
                'min_delay': 0.1,
                'batch_size': 100
            },
            'logging': {
                'level': 'DEBUG',
                'log_requests': True,
                'log_auth_success': True,
                'log_responses': True
            },
            'csv': {
                'default_delimiter': ';',
                'fallback_delimiter': ',',
                'debt_record_type': 'UGEC-DET-RECAUDAC',
                'credit_number_column': 'UGEC-DET-IDENT01',
                'min_credit_length': 10
            },
            'output': {
                'filename_pattern': 'consumer_debt_results_{timestamp}.csv',
                'include_raw_responses': False,
                'output_delimiter': ','
            }
        }
        
        config_path = create_sample_script_config("consumer_debt_checker", sample_config)
        print(f"⚠️  Created sample configuration file: {config_path}")
        print("📝 Please edit the configuration file with your API credentials before continuing")
        return
    
    # Validate required config
    if not config.get('api', {}).get('client_id') or config.get('api', {}).get('client_id') == 'YOUR_CLIENT_ID_HERE':
        print("❌ Please configure your API credentials in config_consumer_debt_checker.yml")
        return
    
    # Set logging level from config
    log_level = config.get('logging', {}).get('level', 'INFO')
    logger.setLevel(getattr(__import__('logging'), log_level))
    
    logger.info("Starting Consumer Debt Checker application")
    
    # Test API authentication first
    print("\n🔐 Verifying API connection...")
    print("-" * 30)
    
    # Initialize API client
    consumer_config = ConsumerAPIConfig.from_config(config)
    api_client = ConsumerAPI(consumer_config)
    
    # Test authentication
    if not api_client.authenticate():
        print("❌ Failed to authenticate with Consumer API")
        print("💡 Please check your credentials and network connection")
        print("🔧 You can test the connection manually with option '🧪 Test API connection'")
        print("\nWould you like to continue anyway? (Some features may not work)")
        
        if not confirm("Continue without authentication?", default=False):
            print("👋 Goodbye!")
            return
        
        print("⚠️  Continuing without authentication - some features may fail")
    else:
        print("✅ API authentication successful!")
        print("🚀 Ready to process debt queries")
    
    # Define menu options
    menu_options = [
        {
            'name': '🔍 Query single credit',
            'value': 'single_credit',
            'description': 'Query debt for a single credit number',
            'action': query_single_credit
        },
        {
            'name': '📂 Process CSV file',
            'value': 'process_csv',
            'description': 'Process multiple credits from CSV file',
            'action': process_csv_file
        },
        {
            'name': '🧪 Test API connection',
            'value': 'test_connection',
            'description': 'Test authentication with Consumer API',
            'action': test_api_connection
        },
        {
            'name': '👋 Exit',
            'value': 'exit',
            'description': 'Quit the debt checker',
            'action': None
        }
    ]
    
    while True:
        try:
            print("\n" + "=" * 50)
            selected = interactive_menu("Select an option:", menu_options)
            
            if not selected or selected['value'] == 'exit':
                print("👋 Goodbye!")
                break
                
            # Execute the selected action
            if selected['action']:
                print(f"\n🔧 Running: {selected['name']}")
                print("-" * 40)
                selected['action'](config, api_client)
                
                # Ask if user wants to continue
                if not confirm("\nWould you like to perform another action?", default=True):
                    print("👋 Goodbye!")
                    break
                    
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            if not confirm("Would you like to continue?", default=True):
                break


def query_single_credit(config=None, api_client=None):
    """Query debt for a single credit number"""
    print("🔍 Single Credit Query")
    print("-" * 30)
    
    # Use passed config or load it
    if config is None:
        config = get_script_config("consumer_debt_checker")
    if not config:
        print("❌ Configuration not found")
        return
    
    # Get credit number from user
    credit_number = text_input("Enter credit number (12 digits):")
    if not credit_number or not credit_number.strip():
        print("❌ Credit number is required")
        return
    
    credit_number = credit_number.strip()
    
    # Validate credit number
    min_length = config.get('csv', {}).get('min_credit_length', 10)
    if not credit_number.isdigit():
        print("❌ Credit number must contain only digits")
        return
        
    if len(credit_number) < min_length:
        print(f"❌ Credit number must be at least {min_length} digits")
        return
    
    # Use passed API client or create new one
    if api_client is None:
        consumer_config = ConsumerAPIConfig.from_config(config)
        api = ConsumerAPI(consumer_config)
        
        # Authenticate
        print("\n🔐 Authenticating with Consumer API...")
        if not api.authenticate():
            print("❌ Authentication failed")
            return
        
        print("✅ Authentication successful")
    else:
        api = api_client
        print("\n✅ Using authenticated API client")
    
    # Query debt
    print(f"\n💳 Querying debt for credit: {credit_number}")
    formatted_id = api.format_loan_id(credit_number)
    print(f"📋 API loan ID: {formatted_id}")
    
    result = api.query_debt(credit_number)
    
    # Display results
    print("\n" + "=" * 50)
    print("📊 QUERY RESULT")
    print("=" * 50)
    
    print(f"Credit Number: {result['credit_number']}")
    print(f"API Loan ID: {result.get('formatted_id', 'N/A')}")
    print(f"Status Code: {result['status_code']}")
    print(f"Timestamp: {result['timestamp']}")
    
    if result['status_code'] == 200 and result['response']:
        # Successful response
        installments = result['response'].get('listRestInstallmentsPayableResponse', [])
        metadata = result['response'].get('_metadata_', [])
        
        print(f"\n✅ SUCCESS - Found {len(installments)} installments")
        
        if installments:
            total_debt = 0.0
            print("\n💰 INSTALLMENT DETAILS:")
            print("-" * 30)
            
            for inst in installments:
                receipt_number = inst.get('receipNumber', 'N/A')
                due_date = inst.get('receiptSettlementDate', 'N/A')
                amount_raw = inst.get('totalAmountReceipt', '0')
                amount = api.parse_amount(amount_raw)
                total_debt += amount
                
                print(f"  Installment {receipt_number}: ${amount:,.0f} CLP (Due: {due_date})")
            
            print(f"\n💵 TOTAL DEBT: ${total_debt:,.0f} CLP")
        
        if metadata:
            print(f"\n📋 METADATA:")
            for meta in metadata:
                if isinstance(meta, dict):
                    code = meta.get('code', 'N/A')
                    meta_type = meta.get('type', 'N/A')
                    print(f"  {code}: {meta_type}")
    
    elif result['error']:
        # Error response
        error_category = api.categorize_error(result['error'])
        print(f"\n❌ ERROR")
        print(f"Category: {error_category}")
        print(f"Message: {result['error']}")
    
    else:
        print(f"\n⚠️  UNEXPECTED RESPONSE")
        print(f"No response data available")


def process_csv_file(config=None, api_client=None):
    """Process multiple credits from CSV file"""
    print("📂 CSV File Processing")
    print("-" * 30)
    
    # Get CSV file path
    csv_file = browse_for_csv_file()
    if not csv_file:
        print("❌ CSV file selection cancelled")
        return
    
    print(f"✅ Selected CSV file: {os.path.basename(csv_file)}")
    
    # Extract credit numbers from CSV
    print("\n🔍 Analyzing CSV file...")
    credit_numbers, original_data = extract_credit_numbers_from_csv_with_selection(csv_file)
    
    if not credit_numbers:
        print("❌ No valid credit numbers found in CSV")
        return
    
    print(f"📊 Found {len(credit_numbers)} unique credit numbers")
    
    # Ask how many records to process
    credit_numbers = get_processing_subset(credit_numbers)
    if not credit_numbers:
        print("❌ Processing cancelled")
        return
    
    print(f"🎯 Will process {len(credit_numbers)} credit numbers")
    
    # Use passed config or load it
    if config is None:
        config = get_script_config("consumer_debt_checker")
    if not config:
        print("❌ Configuration not found")
        return
    
    # Get processing options
    delay = get_delay_setting(config)
    
    # Use passed API client or create new one
    if api_client is None:
        consumer_config = ConsumerAPIConfig.from_config(config)
        api = ConsumerAPI(consumer_config)
        
        # Authenticate
        print("\n🔐 Authenticating with Consumer API...")
        if not api.authenticate():
            print("❌ Authentication failed")
            return
        
        print("✅ Authentication successful")
    else:
        api = api_client
        print("\n✅ Using authenticated API client")
    
    # Process credits
    print(f"\n🔄 Processing {len(credit_numbers)} credits...")
    print("=" * 50)
    
    results = []
    successful_count = 0
    
    for i, credit_number in enumerate(credit_numbers, 1):
        print(f"\n[{i}/{len(credit_numbers)}] Processing {credit_number}...")
        
        result = api.query_debt(credit_number)
        results.append(result)
        
        # Show result
        if result['status_code'] == 200:
            installments = result.get('response', {}).get('listRestInstallmentsPayableResponse', [])
            print(f"✅ Success ({len(installments)} installments)")
            successful_count += 1
        else:
            error_category = api.categorize_error(result.get('error', ''))
            print(f"❌ Error: {error_category}")
        
        # Delay between requests
        if i < len(credit_numbers):
            time.sleep(delay)
    
    # Generate output file
    print(f"\n📤 Generating results file...")
    output_file = generate_results_csv(results, api, original_data)
    
    # Show summary
    print_processing_summary(results, successful_count, output_file)


def browse_for_csv_file() -> Optional[str]:
    """Browse for CSV file using interactive menu"""
    current_dir = os.getcwd()
    
    while True:
        # Get directory contents
        items = []
        
        # Add parent directory option
        if current_dir != os.path.dirname(current_dir):
            items.append({
                'name': '📁 ..',
                'value': '..',
                'description': 'Parent directory',
                'type': 'parent'
            })
        
        try:
            entries = sorted(os.listdir(current_dir))
            
            # Add directories
            for entry in entries:
                full_path = os.path.join(current_dir, entry)
                if os.path.isdir(full_path):
                    items.append({
                        'name': f'📁 {entry}',
                        'value': entry,
                        'description': 'Directory',
                        'type': 'dir'
                    })
            
            # Add CSV files
            for entry in entries:
                full_path = os.path.join(current_dir, entry)
                if os.path.isfile(full_path) and entry.lower().endswith('.csv'):
                    file_size = get_file_size_str(os.path.getsize(full_path))
                    items.append({
                        'name': f'📄 {entry}',
                        'value': entry,
                        'description': f'CSV File ({file_size})',
                        'type': 'file'
                    })
            
            # Add manual entry option
            items.append({
                'name': '✏️  Enter path manually',
                'value': 'manual',
                'description': 'Type the full file path',
                'type': 'manual'
            })
            
            # Add cancel option
            items.append({
                'name': '❌ Cancel',
                'value': 'cancel',
                'description': 'Cancel file selection',
                'type': 'cancel'
            })
            
            # Show current directory and menu
            print(f"\n📂 Current directory: {current_dir}")
            selected = interactive_menu("Select CSV file:", items)
            
            if not selected or selected['type'] == 'cancel':
                return None
            
            if selected['type'] == 'manual':
                manual_path = text_input("Enter full path to CSV file:")
                if manual_path and manual_path.strip():
                    manual_path = manual_path.strip()
                    if os.path.exists(manual_path) and manual_path.lower().endswith('.csv'):
                        return os.path.abspath(manual_path)
                    else:
                        print(f"❌ Invalid CSV file: {manual_path}")
                        continue
                continue
            
            elif selected['type'] == 'parent':
                current_dir = os.path.dirname(current_dir)
            
            elif selected['type'] == 'dir':
                current_dir = os.path.join(current_dir, selected['value'])
            
            elif selected['type'] == 'file':
                file_path = os.path.join(current_dir, selected['value'])
                return os.path.abspath(file_path)
                
        except PermissionError:
            print(f"❌ Permission denied: {current_dir}")
            current_dir = os.path.dirname(current_dir)
        except Exception as e:
            print(f"❌ Error browsing directory: {e}")
            return None


def extract_credit_numbers_from_csv(csv_file: str) -> List[str]:
    """Extract unique credit numbers from CSV file"""
    # Load configuration
    config = get_script_config("consumer_debt_checker")
    csv_config = config.get('csv', {}) if config else {}
    
    default_delimiter = csv_config.get('default_delimiter', ';')
    fallback_delimiter = csv_config.get('fallback_delimiter', ',')
    debt_record_type = csv_config.get('debt_record_type', 'UGEC-DET-RECAUDAC')
    credit_number_column = csv_config.get('credit_number_column', 'UGEC-DET-IDENT01')
    min_credit_length = csv_config.get('min_credit_length', 10)
    
    logger.info(f"Extracting credit numbers from CSV: {csv_file}")
    logger.debug(f"Using delimiter: {default_delimiter} (fallback: {fallback_delimiter})")
    
    credit_numbers = set()
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            # Detect delimiter
            sample = file.read(1024)
            file.seek(0)
            if default_delimiter in sample:
                delimiter = default_delimiter
            elif fallback_delimiter in sample:
                delimiter = fallback_delimiter
            else:
                delimiter = default_delimiter
                
            logger.debug(f"Detected delimiter: '{delimiter}'")
            
            # Check for header
            first_line = file.readline().strip()
            file.seek(0)
            
            if credit_number_column in first_line:
                # Has header
                logger.debug("CSV has header row")
                reader = csv.DictReader(file, delimiter=delimiter)
                for row_num, row in enumerate(reader, 2):  # Start from 2 (after header)
                    if row.get('RECORD_TYPE') == debt_record_type:
                        credit_number = row.get(credit_number_column, '').strip()
                        if credit_number and credit_number.isdigit() and len(credit_number) >= min_credit_length:
                            credit_numbers.add(credit_number)
                            logger.debug(f"Found credit number at row {row_num}: {credit_number}")
            else:
                # No header, use positions
                logger.debug("CSV has no header, using positions")
                file.seek(0)
                reader = csv.reader(file, delimiter=delimiter)
                for row_num, row in enumerate(reader, 1):
                    if len(row) > 8 and row[0] == debt_record_type:
                        credit_number = row[8].strip()
                        if credit_number and credit_number.isdigit() and len(credit_number) >= min_credit_length:
                            credit_numbers.add(credit_number)
                            logger.debug(f"Found credit number at row {row_num}: {credit_number}")
        
        logger.info(f"Extracted {len(credit_numbers)} unique credit numbers")
        
    except Exception as e:
        logger.error(f"Error reading CSV: {e}")
        print(f"❌ Error reading CSV: {e}")
        return []
    
    return list(credit_numbers)


def get_delay_setting(config: Dict) -> float:
    """Get delay setting from user or configuration"""
    processing_config = config.get('processing', {})
    default_delay = processing_config.get('default_delay', 1.0)
    max_delay = processing_config.get('max_delay', 10.0)
    min_delay = processing_config.get('min_delay', 0.1)
    
    delay_str = text_input(f"Enter delay between requests in seconds (default: {default_delay}):", default=str(default_delay))
    try:
        delay = float(delay_str)
        return max(min_delay, min(max_delay, delay))
    except ValueError:
        logger.warning(f"Invalid delay value '{delay_str}', using default: {default_delay}")
        return default_delay


def generate_results_csv(results: List[Dict], api: ConsumerAPI, original_data: List[Dict] = None) -> str:
    """Generate CSV file with results ordered by: http_code > codigo > rut > response > original"""
    # Generate output filename with date
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"consumer_debt_results_{timestamp}.csv"
    
    # Use OutputManager to create path: output/consumer_debt_checker/filename
    output_manager = OutputManager()
    output_file = output_manager.get_output_path('consumer_debt_checker', filename, subfolder="")
    
    # Create index of original data by credit number
    original_index = {}
    if original_data:
        for row in original_data:
            # Find credit number in any column
            for key, value in row.items():
                if str(value).strip().isdigit() and len(str(value).strip()) >= 10:
                    credit_num = str(value).strip()
                    if credit_num not in original_index:
                        original_index[credit_num] = row
                    break
    
    # Sort results by: http_code > codigo > rut 
    def sort_key(result):
        status_code = str(result['status_code'])
        credit_number = result['credit_number']
        
        # Extract RUT if available in original data
        rut = ""
        if credit_number in original_index:
            original_row = original_index[credit_number]
            # Look for RUT-like fields
            for key, value in original_row.items():
                key_lower = key.lower()
                if 'rut' in key_lower or 'dni' in key_lower or 'id' in key_lower:
                    rut = str(value).strip()
                    break
        
        return (status_code, rut, credit_number)
    
    results.sort(key=sort_key)
    
    # Write CSV with new column order: http_code > codigo > rut > response > original
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        
        # Build fieldnames in the required order
        fieldnames = ['http_code', 'codigo', 'rut']  # Priority columns first
        
        # Add response fields
        response_fields = ['error_category', 'error_message', 'installments_count', 
                          'total_debt_clp', 'first_due_date', 'last_due_date', 
                          'installment_details', 'metadata_status', 'formatted_loan_id', 'timestamp', 'from_cache']
        fieldnames.extend(response_fields)
        
        # Add original CSV columns (if available)
        original_columns = []
        if original_data and len(original_data) > 0:
            original_columns = list(original_data[0].keys())
            # Avoid duplicates
            for col in original_columns:
                if col not in fieldnames:
                    fieldnames.append(col)
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            credit_number = result['credit_number']
            
            # Priority columns
            row = {
                'http_code': result['status_code'],
                'codigo': credit_number,
                'rut': ''
            }
            
            # Extract RUT and original data
            original_row = original_index.get(credit_number, {})
            if original_row:
                # Find RUT
                for key, value in original_row.items():
                    key_lower = key.lower()
                    if 'rut' in key_lower or 'dni' in key_lower or 'id' in key_lower:
                        row['rut'] = str(value).strip()
                        break
                
                # Add all original CSV columns
                for col in original_columns:
                    if col in original_row:
                        row[col] = original_row[col]
            
            # Response fields
            row.update({
                'error_category': api.categorize_error(result.get('error', '')) if result.get('error') else '',
                'error_message': result.get('error', ''),
                'installments_count': '',
                'total_debt_clp': '',
                'first_due_date': '',
                'last_due_date': '',
                'installment_details': '',
                'metadata_status': '',
                'formatted_loan_id': result.get('formatted_id', ''),
                'timestamp': result['timestamp'],
                'from_cache': result.get('from_cache', False)
            })
            
            # Process successful responses
            if result['status_code'] == 200 and result.get('response'):
                installments = result['response'].get('listRestInstallmentsPayableResponse', [])
                metadata = result['response'].get('_metadata_', [])
                
                if installments:
                    row['installments_count'] = len(installments)
                    
                    total_debt = 0.0
                    installment_details = []
                    dates = []
                    
                    for inst in installments:
                        amount = api.parse_amount(inst.get('totalAmountReceipt', '0'))
                        total_debt += amount
                        
                        receipt_num = inst.get('receipNumber', 'N/A')
                        due_date = inst.get('receiptSettlementDate', 'N/A')
                        dates.append(due_date)
                        
                        installment_details.append(f"#{receipt_num}:${amount:,.0f}({due_date})")
                    
                    row['total_debt_clp'] = f"{total_debt:,.0f}"
                    row['installment_details'] = " | ".join(installment_details)
                    
                    if dates:
                        valid_dates = [d for d in dates if d != 'N/A']
                        if valid_dates:
                            row['first_due_date'] = min(valid_dates)
                            row['last_due_date'] = max(valid_dates)
                
                if metadata:
                    metadata_info = []
                    for meta in metadata:
                        if isinstance(meta, dict):
                            code = meta.get('code', 'N/A')
                            meta_type = meta.get('type', 'N/A')
                            metadata_info.append(f"{code}:{meta_type}")
                    row['metadata_status'] = " | ".join(metadata_info)
            
            writer.writerow(row)
    
    return output_file


def print_processing_summary(results: List[Dict], successful_count: int, output_file: str):
    """Print processing summary"""
    print("\n" + "=" * 60)
    print("📊 PROCESSING SUMMARY")
    print("=" * 60)
    
    # Basic stats
    total_count = len(results)
    error_count = total_count - successful_count
    
    print(f"Total processed: {total_count}")
    print(f"✅ Successful: {successful_count}")
    print(f"❌ With errors: {error_count}")
    
    # Success rate
    success_rate = (successful_count / total_count * 100) if total_count > 0 else 0
    print(f"📈 Success rate: {success_rate:.1f}%")
    
    # Status code breakdown
    status_counts = {}
    error_categories = {}
    total_debt = 0.0
    total_installments = 0
    
    for result in results:
        status = str(result['status_code'])
        status_counts[status] = status_counts.get(status, 0) + 1
        
        if result['status_code'] == 200 and result.get('response'):
            installments = result['response'].get('listRestInstallmentsPayableResponse', [])
            total_installments += len(installments)
            
            for inst in installments:
                amount_str = inst.get('totalAmountReceipt', '0')
                if amount_str.isdigit():
                    total_debt += int(amount_str) / 10000.0
        elif result.get('error'):
            category = "UNKNOWN"
            error_upper = result['error'].upper()
            if "NO SE PUDO VALIDAR OPERACION" in error_upper:
                category = "NO_VALIDAR_OPERACION"
            elif "REVISAR SITUACION" in error_upper:
                category = "REVISAR_SITUACION"
            elif "APLICACION" in error_upper:
                category = "APLICACION_DESACTIVA"
            elif "CONTEXTO" in error_upper:
                category = "REINTENTAR_CONTEXTO"
            elif "UNAUTHORIZED" in error_upper:
                category = "TOKEN_INVALIDO"
            
            error_categories[category] = error_categories.get(category, 0) + 1
    
    # Show financial summary if there were successful queries
    if successful_count > 0:
        print(f"\n💰 Financial Summary:")
        print(f"  Total installments found: {total_installments}")
        print(f"  Total debt amount: ${total_debt:,.0f} CLP")
        avg_debt = total_debt / successful_count if successful_count > 0 else 0
        print(f"  Average debt per credit: ${avg_debt:,.0f} CLP")
    
    # Show status code distribution
    print(f"\n📈 Status Code Distribution:")
    for status, count in sorted(status_counts.items()):
        percentage = (count / total_count) * 100
        emoji = "✅" if status == "200" else "❌"
        print(f"  {emoji} {status}: {count} ({percentage:.1f}%)")
    
    # Show error categories
    if error_categories:
        print(f"\n🔍 Error Categories:")
        for category, count in sorted(error_categories.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_count) * 100
            print(f"  • {category}: {count} ({percentage:.1f}%)")
    
    # Output file info
    file_size = get_file_size_str(os.path.getsize(output_file))
    print(f"\n📁 Output File:")
    print(f"  Path: {output_file}")
    print(f"  Size: {file_size}")


def test_api_connection(config=None, api_client=None):
    """Test connection to Consumer API"""
    print("🧪 API Connection Test")
    print("-" * 30)
    
    # Use passed config or load it
    if config is None:
        config = get_script_config("consumer_debt_checker")
    if not config:
        print("❌ Configuration not found")
        return
    
    # Use passed API client or create new one
    if api_client is None:
        consumer_config = ConsumerAPIConfig.from_config(config)
        api = ConsumerAPI(consumer_config)
        
        # Test authentication
        print("\n🔐 Testing authentication...")
        print(f"Base URL: {consumer_config.base_url}")
        print(f"Auth URL: {consumer_config.auth_url}")
        print(f"Client ID: {consumer_config.client_id[:8]}***")
    else:
        api = api_client
        
        # Using existing authenticated client
        print("\n✅ Using authenticated API client")
        print(f"Base URL: {api.config.base_url}")
        print(f"Client ID: {api.config.client_id[:8]}***")
    
    if api.authenticate():
        print("✅ Authentication successful!")
        print(f"Token expires in: {int(api.token_expires_at - time.time())} seconds")
        
        # Test with a sample credit number
        if confirm("Test with sample credit number?", default=True):
            sample_credit = "420010086760"  # From the CSV sample
            print(f"\n💳 Testing with credit: {sample_credit}")
            
            result = api.query_debt(sample_credit)
            
            print(f"Status: {result['status_code']}")
            if result['status_code'] == 200:
                installments = result.get('response', {}).get('listRestInstallmentsPayableResponse', [])
                print(f"✅ Success! Found {len(installments)} installments")
            else:
                error_category = api.categorize_error(result.get('error', ''))
                print(f"❌ Error: {error_category}")
                print(f"Message: {result.get('error', 'N/A')}")
    else:
        print("❌ Authentication failed!")
        print("Please check your credentials and network connection.")


def get_file_size_str(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB']
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"


if __name__ == "__main__":
    main()