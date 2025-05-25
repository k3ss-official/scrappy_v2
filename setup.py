"""
Setup script for Scrappy desktop application
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    required_version = (3, 8)
    current_version = sys.version_info
    
    if current_version < required_version:
        print(f"Error: Scrappy requires Python {required_version[0]}.{required_version[1]} or higher.")
        print(f"Current Python version: {current_version[0]}.{current_version[1]}.{current_version[2]}")
        return False
    
    return True

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import PyQt5
        import flask
        import requests
        # Try to import crawl4ai
        try:
            import crawl4ai
            print("crawl4ai is installed.")
        except ImportError:
            print("Warning: crawl4ai is not installed. Will attempt to install it.")
            return False
        
        return True
    except ImportError as e:
        print(f"Error: Missing dependency - {str(e)}")
        return False

def install_dependencies():
    """Install required dependencies."""
    print("Installing dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {str(e)}")
        return False

def create_desktop_shortcut():
    """Create desktop shortcut for the application."""
    system = platform.system()
    
    if system == "Windows":
        create_windows_shortcut()
    elif system == "Darwin":  # macOS
        create_macos_app()
    elif system == "Linux":
        create_linux_shortcut()
    else:
        print(f"Unsupported operating system: {system}")
        return False
    
    return True

def create_windows_shortcut():
    """Create Windows desktop shortcut."""
    try:
        import winshell
        from win32com.client import Dispatch
        
        desktop = winshell.desktop()
        path = os.path.join(desktop, "Scrappy.lnk")
        
        target = os.path.abspath("desktop_app.py")
        wdir = os.path.abspath(".")
        icon = os.path.abspath(os.path.join("src", "ui", "icons", "scrappy_icon.png"))
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = sys.executable
        shortcut.Arguments = target
        shortcut.WorkingDirectory = wdir
        shortcut.IconLocation = icon
        shortcut.save()
        
        print(f"Windows shortcut created at: {path}")
        return True
    except Exception as e:
        print(f"Error creating Windows shortcut: {str(e)}")
        return False

def create_macos_app():
    """Create macOS .app bundle."""
    try:
        # Create app structure
        app_path = os.path.expanduser("~/Applications/Scrappy.app")
        os.makedirs(os.path.join(app_path, "Contents", "MacOS"), exist_ok=True)
        os.makedirs(os.path.join(app_path, "Contents", "Resources"), exist_ok=True)
        
        # Create Info.plist
        info_plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>Scrappy</string>
    <key>CFBundleIconFile</key>
    <string>scrappy_icon.icns</string>
    <key>CFBundleIdentifier</key>
    <string>com.k3ss.scrappy</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>Scrappy</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
"""
        with open(os.path.join(app_path, "Contents", "Info.plist"), "w") as f:
            f.write(info_plist)
        
        # Create launcher script
        launcher = f"""#!/bin/bash
cd "{os.path.abspath(".")}"
"{sys.executable}" "{os.path.abspath("desktop_app.py")}"
"""
        launcher_path = os.path.join(app_path, "Contents", "MacOS", "Scrappy")
        with open(launcher_path, "w") as f:
            f.write(launcher)
        
        # Make launcher executable
        os.chmod(launcher_path, 0o755)
        
        # Copy icon
        icon_source = os.path.abspath(os.path.join("src", "ui", "icons", "scrappy_icon.png"))
        icon_dest = os.path.join(app_path, "Contents", "Resources", "scrappy_icon.icns")
        
        # In a real implementation, we would convert PNG to ICNS
        # For now, just copy the PNG as a placeholder
        import shutil
        shutil.copy2(icon_source, icon_dest)
        
        print(f"macOS app bundle created at: {app_path}")
        return True
    except Exception as e:
        print(f"Error creating macOS app bundle: {str(e)}")
        return False

def create_linux_shortcut():
    """Create Linux desktop shortcut."""
    try:
        desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        shortcut_path = os.path.join(desktop_dir, "Scrappy.desktop")
        
        shortcut_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Scrappy
Comment=Universal Scraping and Delivery System
Exec={sys.executable} {os.path.abspath("desktop_app.py")}
Icon={os.path.abspath(os.path.join("src", "ui", "icons", "scrappy_icon.png"))}
Path={os.path.abspath(".")}
Terminal=false
Categories=Utility;Development;
"""
        with open(shortcut_path, "w") as f:
            f.write(shortcut_content)
        
        # Make executable
        os.chmod(shortcut_path, 0o755)
        
        print(f"Linux desktop shortcut created at: {shortcut_path}")
        return True
    except Exception as e:
        print(f"Error creating Linux desktop shortcut: {str(e)}")
        return False

def main():
    """Main setup function."""
    print("Scrappy Setup")
    print("=============")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        print("Installing missing dependencies...")
        if not install_dependencies():
            print("Failed to install dependencies. Please install them manually.")
            sys.exit(1)
    
    # Create desktop shortcut
    print("Creating desktop shortcut...")
    create_desktop_shortcut()
    
    print("\nSetup completed successfully!")
    print("You can now run Scrappy using:")
    print(f"  {sys.executable} desktop_app.py")
    
    # Offer to run the application
    run_now = input("Would you like to run Scrappy now? (y/n): ")
    if run_now.lower() in ["y", "yes"]:
        subprocess.Popen([sys.executable, "desktop_app.py"])

if __name__ == "__main__":
    main()
