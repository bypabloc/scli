import subprocess
import socket
import platform
import sys
import os
from urllib.parse import urlparse

# Add the src directory to path to import scli modules
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
from menu_utils import interactive_menu, text_input, confirm

DESCRIPTION = "Network diagnostic tools - ping, port check, and DNS lookup"


def main():
    print("🌐 Network Tools")
    print("=" * 50)
    
    # Define menu options
    menu_options = [
        {
            'name': '🏓 Ping a host',
            'value': 'ping',
            'description': 'Test connectivity to a host',
            'action': ping_host
        },
        {
            'name': '🔍 Check if a port is open', 
            'value': 'port',
            'description': 'Check if a specific port is accessible',
            'action': check_port
        },
        {
            'name': '🌐 DNS lookup',
            'value': 'dns', 
            'description': 'Resolve domain names to IP addresses',
            'action': dns_lookup
        },
        {
            'name': '📡 Show network interfaces',
            'value': 'interfaces',
            'description': 'Display network interface information', 
            'action': show_network_interfaces
        },
        {
            'name': '👋 Exit',
            'value': 'exit',
            'description': 'Quit the network tools',
            'action': None
        }
    ]
    
    while True:
        try:
            print("\n" + "=" * 50)
            selected = interactive_menu("Select a network tool:", menu_options)
            
            if not selected or selected['value'] == 'exit':
                print("👋 Goodbye!")
                break
                
            # Execute the selected action
            if selected['action']:
                print(f"\n🔧 Running: {selected['name']}")
                print("-" * 40)
                selected['action']()
                
                # Ask if user wants to continue
                if not confirm("\nWould you like to run another tool?", default=True):
                    print("👋 Goodbye!")
                    break
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            if not confirm("Would you like to continue?", default=True):
                break


def ping_host():
    """Ping a host to check connectivity"""
    host = text_input("Enter hostname or IP to ping:")
    if not host or not host.strip():
        print("❌ Please enter a valid hostname or IP")
        return
    
    host = host.strip()
    
    # Determine ping command based on OS
    param = "-n" if platform.system().lower() == "windows" else "-c"
    command = ["ping", param, "1", host]
    
    try:
        print(f"\n🏓 Pinging {host}...")
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"✅ {host} is reachable")
            # Show summary without full output
            lines = result.stdout.strip().split('\n')
            if lines and len(lines) > 1:
                # Show just the relevant stats line, not all output
                for line in lines[-3:]:
                    if 'time=' in line or 'packets transmitted' in line or 'packet loss' in line:
                        print(f"📊 {line.strip()}")
                        break
        else:
            print(f"❌ {host} is not reachable")
            
    except subprocess.TimeoutExpired:
        print(f"⏱️  Ping to {host} timed out")
    except Exception as e:
        print(f"❌ Error pinging {host}: {e}")


def check_port():
    """Check if a port is open on a host"""
    host = text_input("Enter hostname or IP:")
    if not host or not host.strip():
        print("❌ Please enter a valid hostname or IP")
        return
    
    host = host.strip()
    
    def validate_port(answers, current):
        try:
            port = int(current)
            if not 1 <= port <= 65535:
                raise ValueError("Port must be between 1 and 65535")
            return True
        except ValueError as e:
            raise ValueError(str(e))
    
    port_str = text_input("Enter port number (1-65535):", validate=validate_port)
    if not port_str:
        print("❌ Port number is required")
        return
    
    try:
        port = int(port_str.strip())
    except ValueError:
        print("❌ Please enter a valid port number")
        return
    
    try:
        print(f"\n🔍 Checking {host}:{port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Port {port} is open on {host}")
        else:
            print(f"❌ Port {port} is closed on {host}")
            
    except socket.gaierror:
        print(f"❌ Could not resolve hostname: {host}")
    except Exception as e:
        print(f"❌ Error checking port: {e}")


def dns_lookup():
    """Perform DNS lookup for a domain"""
    domain = text_input("Enter domain name:")
    if not domain or not domain.strip():
        print("❌ Please enter a valid domain name")
        return
    
    domain = domain.strip()
    
    try:
        print(f"\n🔍 Looking up {domain}...")
        ip_address = socket.gethostbyname(domain)
        print(f"✅ {domain} resolves to: {ip_address}")
        
        # Try reverse lookup
        try:
            hostname = socket.gethostbyaddr(ip_address)
            print(f"🔄 Reverse lookup: {hostname[0]}")
        except socket.herror:
            print("🔄 Reverse lookup: Not available")
            
    except socket.gaierror:
        print(f"❌ Could not resolve domain: {domain}")
    except Exception as e:
        print(f"❌ Error during DNS lookup: {e}")


def show_network_interfaces():
    """Show basic network interface information"""
    print("\n🌐 Network Interface Information")
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
        print(f"❌ Error getting network info: {e}")