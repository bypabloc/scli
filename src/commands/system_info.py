#!/usr/bin/env python3
"""
System Info Command - Display comprehensive system information
"""

import os
import platform
import sys
from datetime import datetime

# Add the src directory to path to import scli modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.base_command import SimpleCommand

DESCRIPTION = "Display system information"


class SystemInfoCommand(SimpleCommand):
    """System information display command"""
    
    def __init__(self):
        super().__init__(name="system_info", description=DESCRIPTION)
    
    def execute(self, *args, **kwargs) -> bool:
        """Execute the system info command"""
        try:
            # Gather system information
            info = self._collect_system_info()
            
            # Display information
            self._display_system_info(info)
            
            # Store results
            for key, value in info.items():
                self.set_result(key, value)
            
            return True
        
        except Exception as e:
            self.print_error(f"Failed to collect system information: {e}")
            return False
    
    def _collect_system_info(self) -> dict:
        """Collect comprehensive system information"""
        info = {}
        
        # Basic system info
        info['hostname'] = platform.node()
        info['platform'] = platform.platform()
        info['system'] = platform.system()
        info['release'] = platform.release()
        info['version'] = platform.version()
        info['machine'] = platform.machine()
        info['processor'] = platform.processor()
        info['architecture'] = platform.architecture()[0]
        
        # Python info
        info['python_version'] = platform.python_version()
        info['python_implementation'] = platform.python_implementation()
        info['python_executable'] = sys.executable
        
        # Time info
        now = datetime.now()
        info['current_time'] = now.strftime("%Y-%m-%d %H:%M:%S")
        info['timezone'] = now.astimezone().tzname()
        
        # Directory info
        info['current_directory'] = os.getcwd()
        info['home_directory'] = os.path.expanduser("~")
        
        # Environment info
        info['path_separator'] = os.pathsep
        info['line_separator'] = repr(os.linesep)
        
        # User info
        info['username'] = os.getlogin() if hasattr(os, 'getlogin') else os.environ.get('USER', 'Unknown')
        
        return info
    
    def _display_system_info(self, info: dict):
        """Display system information in a formatted way"""
        self.print_success("System Information")
        print("=" * 50)
        
        # System Information
        print("\n🖥️  System:")
        print(f"  Hostname: {info['hostname']}")
        print(f"  Platform: {info['platform']}")
        print(f"  System: {info['system']}")
        print(f"  Release: {info['release']}")
        print(f"  Architecture: {info['architecture']}")
        print(f"  Machine: {info['machine']}")
        print(f"  Processor: {info['processor']}")
        
        # Python Information
        print("\n🐍 Python:")
        print(f"  Version: {info['python_version']}")
        print(f"  Implementation: {info['python_implementation']}")
        print(f"  Executable: {info['python_executable']}")
        
        # Time Information
        print("\n⏰ Time:")
        print(f"  Current Time: {info['current_time']}")
        print(f"  Timezone: {info['timezone']}")
        
        # Directory Information
        print("\n📁 Directories:")
        print(f"  Current: {info['current_directory']}")
        print(f"  Home: {info['home_directory']}")
        
        # User Information
        print("\n👤 User:")
        print(f"  Username: {info['username']}")
        
        # Environment
        print("\n🌍 Environment:")
        print(f"  Path Separator: {info['path_separator']}")
        print(f"  Line Separator: {info['line_separator']}")
        
        print("\n" + "=" * 50)


# Create command instance for the new system
command_instance = SystemInfoCommand()


