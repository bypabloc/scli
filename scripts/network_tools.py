import subprocess
import socket
import platform
from urllib.parse import urlparse

DESCRIPTION = "Network diagnostic tools - ping, port check, and DNS lookup"


def main():
    print("🌐 Network Tools")
    print("=" * 50)
    
    while True:
        print("\nSelect a network tool:")
        print("1. Ping a host")
        print("2. Check if a port is open")
        print("3. DNS lookup")
        print("4. Show network interfaces")
        print("5. Exit")
        
        try:
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == "1":
                ping_host()
            elif choice == "2":
                check_port()
            elif choice == "3":
                dns_lookup()
            elif choice == "4":
                show_network_interfaces()
            elif choice == "5":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1-5.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def ping_host():
    """Ping a host to check connectivity"""
    host = input("Enter hostname or IP to ping: ").strip()
    if not host:
        print("❌ Please enter a valid hostname or IP")
        return
    
    # Determine ping command based on OS
    param = "-n" if platform.system().lower() == "windows" else "-c"
    command = ["ping", param, "4", host]
    
    try:
        print(f"\n🏓 Pinging {host}...")
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"✅ {host} is reachable")
            # Show last line of ping output (summary)
            lines = result.stdout.strip().split('\n')
            if lines:
                print(f"📊 {lines[-1]}")
        else:
            print(f"❌ {host} is not reachable")
            
    except subprocess.TimeoutExpired:
        print(f"⏱️  Ping to {host} timed out")
    except Exception as e:
        print(f"❌ Error pinging {host}: {e}")


def check_port():
    """Check if a port is open on a host"""
    host = input("Enter hostname or IP: ").strip()
    if not host:
        print("❌ Please enter a valid hostname or IP")
        return
    
    try:
        port = int(input("Enter port number: ").strip())
        if not 1 <= port <= 65535:
            print("❌ Port must be between 1 and 65535")
            return
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
    domain = input("Enter domain name: ").strip()
    if not domain:
        print("❌ Please enter a valid domain name")
        return
    
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