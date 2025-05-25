"""
Setup and Dependency Manager for Scrappy

This module handles the setup, dependency checking, and installation
for the Scrappy application, ensuring all required components are available.
"""

import os
import sys
import logging
import subprocess
import pkg_resources
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('scrappy.setup')

class DependencyManager:
    """
    Manager for checking and installing dependencies.
    """
    
    def __init__(self):
        """
        Initialize the dependency manager.
        """
        # Define required packages
        self.required_packages = {
            'crawl4ai': '1.0.0',  # Minimum version
            'flask': '2.0.0',
            'requests': '2.25.0',
            'pyyaml': '5.4.0',
            'youtube_transcript_api': '0.4.0'
        }
        
        # Define optional packages
        self.optional_packages = {
            'pandas': '1.3.0',  # For advanced data processing
            'matplotlib': '3.4.0',  # For data visualization
            'nltk': '3.6.0'  # For NLP capabilities
        }
        
        logger.info("Initialized dependency manager")
    
    def check_dependencies(self) -> Dict[str, bool]:
        """
        Check if required dependencies are installed.
        
        Returns:
            Dictionary mapping package names to installation status
        """
        status = {}
        
        # Check required packages
        for package, min_version in self.required_packages.items():
            status[package] = self._check_package(package, min_version)
        
        return status
    
    def _check_package(self, package: str, min_version: str) -> bool:
        """
        Check if a package is installed with the minimum required version.
        
        Args:
            package: Package name
            min_version: Minimum required version
            
        Returns:
            True if package is installed with required version, False otherwise
        """
        try:
            installed = pkg_resources.get_distribution(package)
            installed_version = installed.version
            
            # Compare versions
            if pkg_resources.parse_version(installed_version) < pkg_resources.parse_version(min_version):
                logger.warning(f"Package {package} version {installed_version} is below required {min_version}")
                return False
            
            logger.info(f"Package {package} version {installed_version} is installed")
            return True
        except pkg_resources.DistributionNotFound:
            logger.warning(f"Package {package} is not installed")
            return False
    
    def install_package(self, package: str, version: str = None) -> bool:
        """
        Install a package using pip.
        
        Args:
            package: Package name
            version: Specific version to install (optional)
            
        Returns:
            True if installation was successful, False otherwise
        """
        try:
            # Construct installation command
            cmd = [sys.executable, '-m', 'pip', 'install', '--no-cache-dir', '--force-reinstall']
            
            if version:
                cmd.append(f"{package}=={version}")
            else:
                cmd.append(package)
            
            # Execute installation
            logger.info(f"Installing {package}{f' version {version}' if version else ''}...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Successfully installed {package}")
                return True
            else:
                logger.error(f"Failed to install {package}: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error installing {package}: {str(e)}")
            return False
    
    def show_dependency_gui(self):
        """
        Show a GUI for managing dependencies.
        """
        # Create root window
        root = tk.Tk()
        root.title("Scrappy - Dependency Manager")
        root.geometry("600x500")
        
        # Check dependencies
        status = self.check_dependencies()
        
        # Create main frame
        main_frame = ttk.Frame(root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        ttk.Label(main_frame, text="Scrappy Dependency Manager", font=("Arial", 16, "bold")).pack(pady=(0, 20))
        
        # Required packages frame
        req_frame = ttk.LabelFrame(main_frame, text="Required Packages", padding=10)
        req_frame.pack(fill=tk.X, pady=10)
        
        # Create checkboxes for required packages
        req_vars = {}
        for package, min_version in self.required_packages.items():
            var = tk.BooleanVar(value=status.get(package, False))
            req_vars[package] = var
            
            frame = ttk.Frame(req_frame)
            frame.pack(fill=tk.X, pady=2)
            
            ttk.Checkbutton(frame, variable=var, state="disabled").pack(side=tk.LEFT)
            ttk.Label(frame, text=f"{package} (>= {min_version})").pack(side=tk.LEFT, padx=5)
            
            if not status.get(package, False):
                ttk.Button(frame, text="Install", 
                          command=lambda p=package, v=min_version: self._install_and_update(p, v, req_vars)).pack(side=tk.RIGHT)
        
        # Optional packages frame
        opt_frame = ttk.LabelFrame(main_frame, text="Optional Packages", padding=10)
        opt_frame.pack(fill=tk.X, pady=10)
        
        # Check optional packages
        opt_status = {}
        for package, min_version in self.optional_packages.items():
            opt_status[package] = self._check_package(package, min_version)
        
        # Create checkboxes for optional packages
        opt_vars = {}
        for package, min_version in self.optional_packages.items():
            var = tk.BooleanVar(value=opt_status.get(package, False))
            opt_vars[package] = var
            
            frame = ttk.Frame(opt_frame)
            frame.pack(fill=tk.X, pady=2)
            
            ttk.Checkbutton(frame, variable=var, state="disabled").pack(side=tk.LEFT)
            ttk.Label(frame, text=f"{package} (>= {min_version})").pack(side=tk.LEFT, padx=5)
            
            if not opt_status.get(package, False):
                ttk.Button(frame, text="Install", 
                          command=lambda p=package, v=min_version: self._install_and_update(p, v, opt_vars)).pack(side=tk.RIGHT)
        
        # Action buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(btn_frame, text="Install All Missing", 
                  command=lambda: self._install_all_missing(req_vars, opt_vars)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="Refresh Status", 
                  command=lambda: self._refresh_status(req_vars, opt_vars)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="Close", 
                  command=root.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Status label
        status_label = ttk.Label(main_frame, text="Ready")
        status_label.pack(pady=10)
        
        # Store status label for updates
        self.status_label = status_label
        
        # Start GUI
        root.mainloop()
    
    def _install_and_update(self, package: str, version: str, var_dict: Dict[str, tk.BooleanVar]):
        """
        Install a package and update its status in the GUI.
        
        Args:
            package: Package name
            version: Package version
            var_dict: Dictionary of BooleanVars for checkboxes
        """
        self.status_label.config(text=f"Installing {package}...")
        
        # Install package
        success = self.install_package(package, version)
        
        if success:
            # Update checkbox
            var_dict[package].set(True)
            self.status_label.config(text=f"Successfully installed {package}")
        else:
            self.status_label.config(text=f"Failed to install {package}")
            messagebox.showerror("Installation Error", f"Failed to install {package}. Check logs for details.")
    
    def _install_all_missing(self, req_vars: Dict[str, tk.BooleanVar], opt_vars: Dict[str, tk.BooleanVar]):
        """
        Install all missing packages.
        
        Args:
            req_vars: Dictionary of BooleanVars for required packages
            opt_vars: Dictionary of BooleanVars for optional packages
        """
        # Install missing required packages
        for package, var in req_vars.items():
            if not var.get():
                self._install_and_update(package, self.required_packages[package], req_vars)
        
        # Install missing optional packages
        for package, var in opt_vars.items():
            if not var.get():
                self._install_and_update(package, self.optional_packages[package], opt_vars)
        
        self.status_label.config(text="All missing packages installed")
    
    def _refresh_status(self, req_vars: Dict[str, tk.BooleanVar], opt_vars: Dict[str, tk.BooleanVar]):
        """
        Refresh package status in the GUI.
        
        Args:
            req_vars: Dictionary of BooleanVars for required packages
            opt_vars: Dictionary of BooleanVars for optional packages
        """
        # Check required packages
        for package, var in req_vars.items():
            status = self._check_package(package, self.required_packages[package])
            var.set(status)
        
        # Check optional packages
        for package, var in opt_vars.items():
            status = self._check_package(package, self.optional_packages[package])
            var.set(status)
        
        self.status_label.config(text="Status refreshed")

def setup():
    """
    Perform initial setup for the Scrappy application.
    """
    logger.info("Starting Scrappy setup...")
    
    # Check dependencies
    dep_manager = DependencyManager()
    status = dep_manager.check_dependencies()
    
    # Check if all required dependencies are installed
    all_installed = all(status.values())
    
    if not all_installed:
        logger.warning("Some required dependencies are missing")
        
        # Show GUI for dependency management
        dep_manager.show_dependency_gui()
    else:
        logger.info("All required dependencies are installed")
    
    # Create necessary directories
    base_dir = os.path.join(os.getcwd(), 'scrappy_data')
    os.makedirs(os.path.join(base_dir, 'storage'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'output'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'temp'), exist_ok=True)
    
    logger.info("Setup completed successfully")
    return all_installed

if __name__ == '__main__':
    setup()
