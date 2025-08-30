#!/usr/bin/env python3
"""
Network Tools Command - Network diagnostic utilities
"""

import os
import platform
import socket
import subprocess
import sys

# Add the src directory to path to import scli modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.base_command import InteractiveCommand
from models.network_tools_model import NetworkToolsModel
from utils.menu_utils import confirm, interactive_menu, text_input

DESCRIPTION = "Network diagnostic tools - ping, port check, and DNS lookup"


class NetworkToolsCommand(InteractiveCommand):
    """Network tools command implementation"""
    
    # Set the validation model
    event_model = NetworkToolsModel
    
    def __init__(self):
        super().__init__(name="network_tools", description=DESCRIPTION)
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
                    if arg == '--tool' and i + 1 < len(args):
                        data['tool'] = args[i + 1]
                        i += 1
                    elif arg.startswith('--tool='):
                        data['tool'] = arg.split('=', 1)[1]
                    elif arg == '--host' and i + 1 < len(args):
                        data['host'] = args[i + 1]
                        i += 1
                    elif arg.startswith('--host='):
                        data['host'] = arg.split('=', 1)[1]
                    elif arg == '--port' and i + 1 < len(args):
                        data['port'] = int(args[i + 1])
                        i += 1
                    elif arg.startswith('--port='):
                        data['port'] = int(arg.split('=', 1)[1])
                    elif arg == '--timeout' and i + 1 < len(args):
                        data['timeout'] = int(args[i + 1])
                        i += 1
                    elif arg.startswith('--timeout='):
                        data['timeout'] = int(arg.split('=', 1)[1])
                    elif arg == '--count' and i + 1 < len(args):
                        data['count'] = int(args[i + 1])
                        i += 1
                    elif arg.startswith('--count='):
                        data['count'] = int(arg.split('=', 1)[1])
                    i += 1
            
            # Add any kwargs
            data.update(kwargs)
            
            # Set default tool if not specified
            if 'tool' not in data:
                data['tool'] = 'interactive'
            
            # Validate using Pydantic model
            self.validated_data = self.event_model(**data)
            
            self.logger.debug(f"Arguments validated successfully: {self.validated_data.to_dict()}")
            return True
            
        except Exception as e:
            self.print_error(f"Argument validation failed: {e}")
            self.logger.error(f"Preload validation error: {e}")
            return False
    
    def validation(self, *args, **kwargs) -> bool:
        """Validate tool-specific requirements"""
        try:
            if not self.validated_data:
                self.print_error("No validated data available")
                return False
            
            # Check tool-specific requirements
            if self.validated_data.requires_host() and not self.validated_data.host:
                if not self.validated_data.is_interactive_mode():
                    self.print_error(f"Tool '{self.validated_data.tool}' requires a host parameter")
                    return False
            
            if self.validated_data.requires_port() and not self.validated_data.port:
                if not self.validated_data.is_interactive_mode():
                    self.print_error(f"Tool '{self.validated_data.tool}' requires a port parameter")
                    return False
            
            return True
            
        except Exception as e:
            self.print_error(f"Validation failed: {e}")
            return False
    
    def execute(self, *args, **kwargs) -> bool:
        """Execute the network tools command"""
        try:
            if not self.validated_data:
                self.print_error("No validated data available")
                return False
            
            # Execute based on tool
            if self.validated_data.is_ping_mode():
                self._execute_ping()
            elif self.validated_data.is_port_mode():
                self._execute_port_check()
            elif self.validated_data.is_dns_mode():
                self._execute_dns_lookup()
            elif self.validated_data.is_interfaces_mode():
                self._execute_interfaces()
            else:  # interactive mode
                self._execute_interactive_mode()
            
            # Store results
            self.set_result("tool", self.validated_data.tool)
            self.set_result("validated_args", self.validated_data.to_dict())
            
            return True
        
        except Exception as e:
            self.print_error(f"Failed to execute network tools: {e}")
            return False
    
    def _execute_ping(self):
        """Execute ping operation"""
        host = self.validated_data.host
        if not host:
            host = self.get_user_input("Enter hostname or IP to ping:")
            if not host or not host.strip():
                self.print_error("Host is required for ping")
                return
        
        self.ping_host(host.strip(), self.validated_data.count, self.validated_data.timeout)
    
    def _execute_port_check(self):
        """Execute port check operation"""
        host = self.validated_data.host
        port = self.validated_data.port
        
        if not host:
            host = self.get_user_input("Enter hostname or IP:")
            if not host or not host.strip():
                self.print_error("Host is required for port check")
                return
        
        if not port:
            port_str = self.get_user_input("Enter port number (1-65535):")
            try:
                port = int(port_str)
                if not (1 <= port <= 65535):
                    self.print_error("Port must be between 1 and 65535")
                    return
            except ValueError:
                self.print_error("Please enter a valid port number")
                return
        
        self.check_port(host.strip(), port, self.validated_data.timeout)
    
    def _execute_dns_lookup(self):
        """Execute DNS lookup operation"""
        host = self.validated_data.host
        if not host:
            host = self.get_user_input("Enter domain name:")
            if not host or not host.strip():
                self.print_error("Domain name is required for DNS lookup")
                return
        
        self.dns_lookup(host.strip())
    
    def _execute_interfaces(self):
        """Execute network interfaces operation"""
        self.show_network_interfaces()
    
    def _execute_interactive_mode(self):
        """Execute interactive mode"""
        self.print_info("Starting network tools interactive mode...")
        
        # Show menu options
        options = [
            {
                "name": "🏓 Ping Host",
                "value": "ping",
                "description": "Test connectivity to a host"
            },
            {
                "name": "🔍 Check Port",
                "value": "port",
                "description": "Check if a port is open on a host"
            },
            {
                "name": "🌐 DNS Lookup",
                "value": "dns",
                "description": "Perform DNS lookup for a domain"
            },
            {
                "name": "🖥️  Network Interfaces",
                "value": "interfaces",
                "description": "Show network interface information"
            },
            {
                "name": "❌ Exit",
                "value": "exit",
                "description": "Exit without performing any operation"
            }
        ]
        
        selected = self.get_user_choice("Select network tool:", options)
        if not selected or selected["value"] == "exit":
            self.print_info("Operation cancelled")
            return
        
        # Execute selected tool
        if selected["value"] == "ping":
            self._execute_ping()
        elif selected["value"] == "port":
            self._execute_port_check()
        elif selected["value"] == "dns":
            self._execute_dns_lookup()
        elif selected["value"] == "interfaces":
            self._execute_interfaces()
    
    def ping_host(self, host: str, count: int = 1, timeout: int = 10):
        """Ping a host to check connectivity"""
        # Determine ping command based on OS
        param = "-n" if platform.system().lower() == "windows" else "-c"
        command = ["ping", param, str(count), host]
        
        try:
            self.print_info(f"Pinging {host} ({count} packets)...")
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
            
            if result.returncode == 0:
                self.print_success(f"{host} is reachable")
                # Show summary without full output
                lines = result.stdout.strip().split("\n")
                if lines and len(lines) > 1:
                    # Show just the relevant stats line, not all output
                    for line in lines[-3:]:
                        if (
                            "time=" in line
                            or "packets transmitted" in line
                            or "packet loss" in line
                        ):
                            print(f"📊 {line.strip()}")
                            break
            else:
                self.print_error(f"{host} is not reachable")
                
        except subprocess.TimeoutExpired:
            self.print_warning(f"Ping to {host} timed out")
        except Exception as e:
            self.print_error(f"Error pinging {host}: {e}")
    
    def check_port(self, host: str, port: int, timeout: int = 5):
        """Check if a port is open on a host"""
        try:
            self.print_info(f"Checking {host}:{port}...")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                self.print_success(f"Port {port} is open on {host}")
            else:
                self.print_error(f"Port {port} is closed on {host}")
                
        except socket.gaierror:
            self.print_error(f"Could not resolve hostname: {host}")
        except Exception as e:
            self.print_error(f"Error checking port: {e}")
    
    def dns_lookup(self, domain: str):
        """Perform DNS lookup for a domain"""
        try:
            self.print_info(f"Looking up {domain}...")
            ip_address = socket.gethostbyname(domain)
            self.print_success(f"{domain} resolves to: {ip_address}")
            
            # Try reverse lookup
            try:
                hostname = socket.gethostbyaddr(ip_address)
                print(f"🔄 Reverse lookup: {hostname[0]}")
            except socket.herror:
                print("🔄 Reverse lookup: Not available")
                
        except socket.gaierror:
            self.print_error(f"Could not resolve domain: {domain}")
        except Exception as e:
            self.print_error(f"Error during DNS lookup: {e}")
    
    def show_network_interfaces(self):
        """Show basic network interface information"""
        self.print_info("Network Interface Information")
        print("-" * 40)
        
        try:
            # Get hostname
            hostname = socket.gethostname()
            print(f"Hostname: {hostname}")
            
            # Get local IP addresses
            local_ip = socket.gethostbyname(hostname)
            print(f"Local IP: {local_ip}")
            
            # Try to get external IP by connecting to a remote server
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.connect(("8.8.8.8", 80))
                    external_ip = s.getsockname()[0]
                    print(f"External IP: {external_ip}")
            except Exception:
                print("External IP: Could not determine")
                
        except Exception as e:
            self.print_error(f"Error getting network info: {e}")




# Create command instance for dynamic import
command_instance = NetworkToolsCommand()
