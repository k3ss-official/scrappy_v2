"""
Setup and Dependency Management Module for Scrappy

This module handles the setup and dependency management for the Scrappy application.
It checks for required dependencies and provides a GUI for installing missing dependencies.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

class SetupManager:
    """Manages setup and dependencies for the Scrappy application."""
    
    def __init__(self):
        """Initialize the setup manager."""
        self.python_version = sys.version_info
        self.system = platform.system()
        self.required_packages = [
            'pyqt5',
            'requests',
            'beautifulsoup4',
            'crawl4ai',
            'pyyaml',
            'lxml',
            'markdown',
            'python-dateutil',
            'tqdm',
            'colorama'
        ]
        self.system_dependencies = {
            'Linux': ['python3-tk', 'python3-pyqt5'],
            'Darwin': ['python-tk', 'pyqt5'],
            'Windows': []  # Windows typically bundles tkinter with Python
        }
    
    def check_python_version(self):
        """Check if Python version is compatible."""
        required_version = (3, 8)
        
        if self.python_version < required_version:
            print(f"Error: Scrappy requires Python {required_version[0]}.{required_version[1]} or higher.")
            print(f"Current Python version: {self.python_version[0]}.{self.python_version[1]}.{self.python_version[2]}")
            return False
        
        return True
    
    def check_dependencies(self):
        """Check if required dependencies are installed."""
        missing_packages = []
        
        for package in self.required_packages:
            try:
                __import__(package.replace('-', '_').split('==')[0])
            except ImportError:
                missing_packages.append(package)
        
        return missing_packages
    
    def install_dependencies(self, packages):
        """Install required dependencies."""
        if not packages:
            return True
        
        print(f"Installing missing packages: {', '.join(packages)}")
        
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages)
            print("Dependencies installed successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error installing dependencies: {str(e)}")
            return False
    
    def check_system_dependencies(self):
        """Check if required system dependencies are installed."""
        if self.system not in self.system_dependencies:
            print(f"Unsupported operating system: {self.system}")
            return False
        
        missing_deps = []
        
        # For Linux, check with package manager
        if self.system == 'Linux':
            for dep in self.system_dependencies['Linux']:
                # Check if package is installed
                try:
                    # Try importing tkinter directly for the python3-tk package
                    if dep == 'python3-tk':
                        try:
                            import tkinter
                        except ImportError:
                            missing_deps.append(dep)
                    # For other packages, use dpkg or rpm to check
                    elif subprocess.call(['dpkg', '-s', dep], 
                                        stdout=subprocess.DEVNULL, 
                                        stderr=subprocess.DEVNULL) != 0:
                        missing_deps.append(dep)
                except:
                    # If dpkg is not available, assume package might be missing
                    missing_deps.append(dep)
        
        # For macOS, we can't easily check system packages
        # Just try importing tkinter
        elif self.system == 'Darwin':
            try:
                import tkinter
            except ImportError:
                missing_deps.append('python-tk')
        
        return missing_deps
    
    def install_system_dependencies(self, deps):
        """Provide instructions for installing system dependencies."""
        if not deps:
            return True
        
        print("\nSystem dependencies required:")
        
        if self.system == 'Linux':
            print("Please run the following command to install required system dependencies:")
            print(f"sudo apt-get install {' '.join(deps)}")
            
        elif self.system == 'Darwin':
            print("Please run the following command to install required system dependencies:")
            print("brew install python-tk")
            
        elif self.system == 'Windows':
            print("Please reinstall Python and ensure to check 'tcl/tk and IDLE' during installation.")
        
        return False
    
    def setup(self):
        """Run the setup process."""
        # Check Python version
        if not self.check_python_version():
            return False
        
        # Check system dependencies
        missing_sys_deps = self.check_system_dependencies()
        if missing_sys_deps:
            self.install_system_dependencies(missing_sys_deps)
            print("\nPlease restart the application after installing the required system dependencies.")
            return False
        
        # Check Python package dependencies
        missing_packages = self.check_dependencies()
        if missing_packages:
            if not self.install_dependencies(missing_packages):
                return False
        
        return True

# For command-line setup
if __name__ == "__main__":
    setup_manager = SetupManager()
    if setup_manager.setup():
        print("Setup completed successfully!")
    else:
        print("Setup failed. Please resolve the issues and try again.")
        sys.exit(1)
