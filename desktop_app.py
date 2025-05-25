"""
Main entry point for Scrappy desktop application
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from src.ui.desktop import ScrappyDesktopApp

def main():
    """Main entry point for the desktop application."""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for better dark theme support
    
    window = ScrappyDesktopApp()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
