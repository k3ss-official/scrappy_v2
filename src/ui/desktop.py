"""
Desktop GUI Application for Scrappy

This module provides a PyQt5-based desktop GUI for the Scrappy application,
allowing users to interact with the scraping functionality through a modern interface.
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import threading
import webbrowser

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QComboBox, QPushButton, QCheckBox, QTabWidget,
    QScrollArea, QFrame, QSplitter, QFileDialog, QMessageBox, QProgressBar,
    QStackedWidget, QListWidget, QListWidgetItem, QGroupBox
)
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal, QUrl, QSettings
from PyQt5.QtGui import QIcon, QPixmap, QFont, QColor, QPalette, QDesktopServices
from PyQt5.QtWebEngineWidgets import QWebEngineView

# Import Scrappy main class
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import Scrappy
from src.utils.crawl4ai_integration import Crawl4AIManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('scrappy.gui')

# Define colors
DARK_BG = "#1a1625"
DARKER_BG = "#141019"
ACCENT_COLOR = "#6a4c93"
TEXT_COLOR = "#f8f9fa"
BUTTON_COLOR = "#6a4c93"
BUTTON_HOVER = "#7d5ba6"
BORDER_COLOR = "#2c2235"

class ScrapeWorker(QThread):
    """
    Worker thread for scraping operations.
    """
    progress_update = pyqtSignal(str, int)
    scrape_complete = pyqtSignal(dict)
    scrape_error = pyqtSignal(str)
    
    def __init__(self, scraper_type: str, url: str, output_formats: List[str], options: Dict[str, Any] = None):
        """
        Initialize the scrape worker.
        
        Args:
            scraper_type: Type of scraper to use ('github', 'website', or 'youtube')
            url: URL to scrape
            output_formats: List of output formats to generate
            options: Additional options for the scraper
        """
        super().__init__()
        self.scraper_type = scraper_type
        self.url = url
        self.output_formats = output_formats
        self.options = options or {}
        self.scrappy = Scrappy()
    
    def run(self):
        """
        Run the scraping operation.
        """
        try:
            self.progress_update.emit("Initializing scraper...", 10)
            
            if self.scraper_type == 'github':
                self.progress_update.emit("Scraping GitHub repository...", 20)
                result = self.scrappy.scrape_github(self.url, self.output_formats)
            elif self.scraper_type == 'website':
                depth = self.options.get('depth', 1)
                self.progress_update.emit(f"Scraping website with depth {depth}...", 20)
                result = self.scrappy.scrape_website(self.url, depth, self.output_formats)
            elif self.scraper_type == 'youtube':
                self.progress_update.emit("Scraping YouTube channel...", 20)
                result = self.scrappy.scrape_youtube(self.url, self.output_formats)
            else:
                raise ValueError(f"Unknown scraper type: {self.scraper_type}")
            
            self.progress_update.emit("Processing results...", 80)
            self.scrape_complete.emit(result)
            
        except Exception as e:
            logger.error(f"Error in scrape worker: {str(e)}")
            self.scrape_error.emit(str(e))

class StyledButton(QPushButton):
    """
    Custom styled button for the Scrappy GUI.
    """
    def __init__(self, text, parent=None, primary=True):
        """
        Initialize the styled button.
        
        Args:
            text: Button text
            parent: Parent widget
            primary: Whether this is a primary button
        """
        super().__init__(text, parent)
        self.primary = primary
        self.setMinimumHeight(40)
        self.setCursor(Qt.PointingHandCursor)
        
        if primary:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {BUTTON_COLOR};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {BUTTON_HOVER};
                }}
                QPushButton:pressed {{
                    background-color: {ACCENT_COLOR};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {TEXT_COLOR};
                    border: 1px solid {BORDER_COLOR};
                    border-radius: 4px;
                    padding: 8px 16px;
                }}
                QPushButton:hover {{
                    background-color: rgba(255, 255, 255, 0.1);
                }}
                QPushButton:pressed {{
                    background-color: rgba(255, 255, 255, 0.05);
                }}
            """)

class StyledLineEdit(QLineEdit):
    """
    Custom styled line edit for the Scrappy GUI.
    """
    def __init__(self, placeholder="", parent=None):
        """
        Initialize the styled line edit.
        
        Args:
            placeholder: Placeholder text
            parent: Parent widget
        """
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(40)
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {DARKER_BG};
                color: {TEXT_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 4px;
                padding: 8px 12px;
            }}
            QLineEdit:focus {{
                border: 1px solid {ACCENT_COLOR};
            }}
        """)

class StyledComboBox(QComboBox):
    """
    Custom styled combo box for the Scrappy GUI.
    """
    def __init__(self, parent=None):
        """
        Initialize the styled combo box.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setMinimumHeight(40)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QComboBox {{
                background-color: {DARKER_BG};
                color: {TEXT_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 4px;
                padding: 8px 12px;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: {BORDER_COLOR};
                border-left-style: solid;
            }}
            QComboBox QAbstractItemView {{
                background-color: {DARKER_BG};
                color: {TEXT_COLOR};
                selection-background-color: {ACCENT_COLOR};
            }}
        """)

class StyledCheckBox(QCheckBox):
    """
    Custom styled checkbox for the Scrappy GUI.
    """
    def __init__(self, text, parent=None):
        """
        Initialize the styled checkbox.
        
        Args:
            text: Checkbox text
            parent: Parent widget
        """
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QCheckBox {{
                color: {TEXT_COLOR};
                spacing: 5px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid {BORDER_COLOR};
                border-radius: 3px;
            }}
            QCheckBox::indicator:unchecked {{
                background-color: {DARKER_BG};
            }}
            QCheckBox::indicator:checked {{
                background-color: {ACCENT_COLOR};
                image: url(:/icons/check.png);
            }}
        """)

class ScrappyGUI(QMainWindow):
    """
    Main window for the Scrappy desktop GUI.
    """
    def __init__(self):
        """
        Initialize the main window.
        """
        super().__init__()
        
        # Initialize Scrappy
        self.scrappy = Scrappy()
        
        # Initialize crawl4ai manager
        self.crawl4ai_manager = Crawl4AIManager()
        
        # Set up the UI
        self.init_ui()
        
        # Load settings
        self.load_settings()
        
        logger.info("Initialized Scrappy GUI")
    
    def init_ui(self):
        """
        Initialize the user interface.
        """
        # Set window properties
        self.setWindowTitle("Scrappy")
        self.setMinimumSize(1000, 700)
        
        # Set window icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", "scrappy_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Set application style
        self.set_dark_theme()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Create content area
        content = self.create_content()
        main_layout.addWidget(content, 1)
        
        # Create status bar
        self.statusBar().setStyleSheet(f"background-color: {DARKER_BG}; color: {TEXT_COLOR};")
        self.statusBar().showMessage("Ready")
    
    def set_dark_theme(self):
        """
        Set dark theme for the application.
        """
        # Set application style
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {DARK_BG};
                color: {TEXT_COLOR};
            }}
            QTabWidget::pane {{
                border: 1px solid {BORDER_COLOR};
                background-color: {DARK_BG};
            }}
            QTabBar::tab {{
                background-color: {DARKER_BG};
                color: {TEXT_COLOR};
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {ACCENT_COLOR};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {BORDER_COLOR};
            }}
            QScrollArea {{
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {DARKER_BG};
                width: 12px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {BORDER_COLOR};
                min-height: 20px;
                border-radius: 6px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QProgressBar {{
                border: 1px solid {BORDER_COLOR};
                border-radius: 4px;
                text-align: center;
                background-color: {DARKER_BG};
            }}
            QProgressBar::chunk {{
                background-color: {ACCENT_COLOR};
                width: 1px;
            }}
        """)
    
    def create_header(self):
        """
        Create the header section.
        
        Returns:
            Header widget
        """
        header = QWidget()
        header.setStyleSheet(f"background-color: {DARK_BG};")
        header.setMinimumHeight(150)
        
        layout = QVBoxLayout(header)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("SCRAPPY")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 48px; font-weight: bold; color: #f8f9fa;")
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("what can I get for you?")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 24px; color: #f8f9fa;")
        layout.addWidget(subtitle)
        
        return header
    
    def create_content(self):
        """
        Create the main content area.
        
        Returns:
            Content widget
        """
        content = QWidget()
        
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Search bar
        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        self.search_input = StyledLineEdit("Let's find them")
        search_layout.addWidget(self.search_input, 1)
        
        find_button = StyledButton("Find", primary=True)
        find_button.clicked.connect(self.on_search)
        search_layout.addWidget(find_button)
        
        layout.addWidget(search_container)
        
        # Filter options
        filter_container = QWidget()
        filter_layout = QHBoxLayout(filter_container)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(10)
        
        # Source type
        source_container = QWidget()
        source_layout = QVBoxLayout(source_container)
        source_layout.setContentsMargins(0, 0, 0, 0)
        
        source_label = QLabel("Source")
        source_label.setStyleSheet(f"color: {TEXT_COLOR};")
        source_layout.addWidget(source_label)
        
        self.source_combo = StyledComboBox()
        self.source_combo.addItems(["GitHub", "Website", "YouTube"])
        source_layout.addWidget(self.source_combo)
        
        filter_layout.addWidget(source_container)
        
        # Options
        options_container = QWidget()
        options_layout = QVBoxLayout(options_container)
        options_layout.setContentsMargins(0, 0, 0, 0)
        
        options_label = QLabel("Options")
        options_label.setStyleSheet(f"color: {TEXT_COLOR};")
        options_layout.addWidget(options_label)
        
        self.options_combo = StyledComboBox()
        self.update_options_combo()
        options_layout.addWidget(self.options_combo)
        
        filter_layout.addWidget(options_container)
        
        # Output formats
        formats_container = QWidget()
        formats_layout = QVBoxLayout(formats_container)
        formats_layout.setContentsMargins(0, 0, 0, 0)
        
        formats_label = QLabel("Output Formats")
        formats_label.setStyleSheet(f"color: {TEXT_COLOR};")
        formats_layout.addWidget(formats_label)
        
        formats_widget = QWidget()
        formats_widget_layout = QHBoxLayout(formats_widget)
        formats_widget_layout.setContentsMargins(0, 0, 0, 0)
        formats_widget_layout.setSpacing(10)
        
        self.format_checkboxes = {}
        for fmt in ["JSON", "CSV", "TXT", "YAML", "XML"]:
            checkbox = StyledCheckBox(fmt)
            if fmt == "JSON":
                checkbox.setChecked(True)
            self.format_checkboxes[fmt.lower()] = checkbox
            formats_widget_layout.addWidget(checkbox)
        
        formats_layout.addWidget(formats_widget)
        
        filter_layout.addWidget(formats_container)
        
        # Output directory
        output_container = QWidget()
        output_layout = QVBoxLayout(output_container)
        output_layout.setContentsMargins(0, 0, 0, 0)
        
        output_label = QLabel("Output Directory")
        output_label.setStyleSheet(f"color: {TEXT_COLOR};")
        output_layout.addWidget(output_label)
        
        output_widget = QWidget()
        output_widget_layout = QHBoxLayout(output_widget)
        output_widget_layout.setContentsMargins(0, 0, 0, 0)
        output_widget_layout.setSpacing(10)
        
        self.output_dir_input = StyledLineEdit()
        output_widget_layout.addWidget(self.output_dir_input, 1)
        
        browse_button = StyledButton("Browse", primary=False)
        browse_button.clicked.connect(self.browse_output_dir)
        output_widget_layout.addWidget(browse_button)
        
        output_layout.addWidget(output_widget)
        
        filter_layout.addWidget(output_container)
        
        layout.addWidget(filter_container)
        
        # Tabs for different views
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {BORDER_COLOR};
                background-color: {DARK_BG};
            }}
        """)
        
        # Results tab
        self.results_tab = self.create_results_tab()
        self.tabs.addTab(self.results_tab, "Results")
        
        # Saved data tab
        self.saved_data_tab = self.create_saved_data_tab()
        self.tabs.addTab(self.saved_data_tab, "Saved Data")
        
        # Settings tab
        self.settings_tab = self.create_settings_tab()
        self.tabs.addTab(self.settings_tab, "Settings")
        
        layout.addWidget(self.tabs, 1)
        
        # Connect signals
        self.source_combo.currentIndexChanged.connect(self.update_options_combo)
        
        return content
    
    def create_results_tab(self):
        """
        Create the results tab.
        
        Returns:
            Results tab widget
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Results area
        self.results_stack = QStackedWidget()
        
        # Empty state
        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_layout.setAlignment(Qt.AlignCenter)
        
        empty_label = QLabel("No results yet")
        empty_label.setAlignment(Qt.AlignCenter)
        empty_label.setStyleSheet("font-size: 18px; color: #6c757d;")
        empty_layout.addWidget(empty_label)
        
        start_button = StyledButton("Start Scraping", primary=True)
        start_button.clicked.connect(self.on_search)
        empty_layout.addWidget(start_button, 0, Qt.AlignCenter)
        
        self.results_stack.addWidget(empty_widget)
        
        # Loading state
        loading_widget = QWidget()
        loading_layout = QVBoxLayout(loading_widget)
        loading_layout.setAlignment(Qt.AlignCenter)
        
        loading_label = QLabel("Scraping in progress...")
        loading_label.setAlignment(Qt.AlignCenter)
        loading_label.setStyleSheet("font-size: 18px;")
        loading_layout.addWidget(loading_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimumWidth(400)
        loading_layout.addWidget(self.progress_bar, 0, Qt.AlignCenter)
        
        self.progress_label = QLabel("Initializing...")
        self.progress_label.setAlignment(Qt.AlignCenter)
        loading_layout.addWidget(self.progress_label)
        
        cancel_button = StyledButton("Cancel", primary=False)
        cancel_button.clicked.connect(self.cancel_scraping)
        loading_layout.addWidget(cancel_button, 0, Qt.AlignCenter)
        
        self.results_stack.addWidget(loading_widget)
        
        # Results state
        self.results_widget = QWidget()
        results_layout = QVBoxLayout(self.results_widget)
        
        # Results header
        results_header = QWidget()
        results_header_layout = QHBoxLayout(results_header)
        results_header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.results_title = QLabel("Results")
        self.results_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        results_header_layout.addWidget(self.results_title, 1)
        
        export_button = StyledButton("Export", primary=False)
        export_button.clicked.connect(self.export_results)
        results_header_layout.addWidget(export_button)
        
        new_search_button = StyledButton("New Search", primary=True)
        new_search_button.clicked.connect(self.new_search)
        results_header_layout.addWidget(new_search_button)
        
        results_layout.addWidget(results_header)
        
        # Results content
        results_content = QScrollArea()
        results_content.setWidgetResizable(True)
        results_content.setFrameShape(QFrame.NoFrame)
        
        self.results_content_widget = QWidget()
        self.results_content_layout = QVBoxLayout(self.results_content_widget)
        self.results_content_layout.setAlignment(Qt.AlignTop)
        
        results_content.setWidget(self.results_content_widget)
        results_layout.addWidget(results_content, 1)
        
        self.results_stack.addWidget(self.results_widget)
        
        layout.addWidget(self.results_stack)
        
        return tab
    
    def create_saved_data_tab(self):
        """
        Create the saved data tab.
        
        Returns:
            Saved data tab widget
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Saved data list
        self.saved_data_list = QListWidget()
        self.saved_data_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {DARKER_BG};
                border: 1px solid {BORDER_COLOR};
                border-radius: 4px;
            }}
            QListWidget::item {{
                padding: 10px;
                border-bottom: 1px solid {BORDER_COLOR};
            }}
            QListWidget::item:selected {{
                background-color: {ACCENT_COLOR};
            }}
        """)
        self.saved_data_list.itemDoubleClicked.connect(self.view_saved_data)
        layout.addWidget(self.saved_data_list)
        
        # Buttons
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        refresh_button = StyledButton("Refresh", primary=False)
        refresh_button.clicked.connect(self.refresh_saved_data)
        buttons_layout.addWidget(refresh_button)
        
        view_button = StyledButton("View", primary=True)
        view_button.clicked.connect(lambda: self.view_saved_data(self.saved_data_list.currentItem()))
        buttons_layout.addWidget(view_button)
        
        delete_button = StyledButton("Delete", primary=False)
        delete_button.clicked.connect(self.delete_saved_data)
        buttons_layout.addWidget(delete_button)
        
        layout.addWidget(buttons_widget)
        
        # Load saved data
        self.refresh_saved_data()
        
        return tab
    
    def create_settings_tab(self):
        """
        Create the settings tab.
        
        Returns:
            Settings tab widget
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Crawl4AI settings
        crawl4ai_group = QGroupBox("Crawl4AI Settings")
        crawl4ai_group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {BORDER_COLOR};
                border-radius: 4px;
                margin-top: 1ex;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: {TEXT_COLOR};
            }}
        """)
        
        crawl4ai_layout = QVBoxLayout(crawl4ai_group)
        
        # User agent
        user_agent_widget = QWidget()
        user_agent_layout = QHBoxLayout(user_agent_widget)
        user_agent_layout.setContentsMargins(0, 0, 0, 0)
        
        user_agent_label = QLabel("User Agent:")
        user_agent_label.setMinimumWidth(100)
        user_agent_layout.addWidget(user_agent_label)
        
        self.user_agent_input = StyledLineEdit()
        self.user_agent_input.setText("Scrappy/1.0 (+https://github.com/k3ss-official/scrappy_v2)")
        user_agent_layout.addWidget(self.user_agent_input, 1)
        
        crawl4ai_layout.addWidget(user_agent_widget)
        
        # Timeout
        timeout_widget = QWidget()
        timeout_layout = QHBoxLayout(timeout_widget)
        timeout_layout.setContentsMargins(0, 0, 0, 0)
        
        timeout_label = QLabel("Timeout (seconds):")
        timeout_label.setMinimumWidth(100)
        timeout_layout.addWidget(timeout_label)
        
        self.timeout_combo = StyledComboBox()
        self.timeout_combo.addItems(["10", "20", "30", "60", "120"])
        self.timeout_combo.setCurrentText("30")
        timeout_layout.addWidget(self.timeout_combo, 1)
        
        crawl4ai_layout.addWidget(timeout_widget)
        
        # Max retries
        retries_widget = QWidget()
        retries_layout = QHBoxLayout(retries_widget)
        retries_layout.setContentsMargins(0, 0, 0, 0)
        
        retries_label = QLabel("Max Retries:")
        retries_label.setMinimumWidth(100)
        retries_layout.addWidget(retries_label)
        
        self.retries_combo = StyledComboBox()
        self.retries_combo.addItems(["1", "2", "3", "5", "10"])
        self.retries_combo.setCurrentText("3")
        retries_layout.addWidget(self.retries_combo, 1)
        
        crawl4ai_layout.addWidget(retries_widget)
        
        # Follow redirects
        redirects_widget = QWidget()
        redirects_layout = QHBoxLayout(redirects_widget)
        redirects_layout.setContentsMargins(0, 0, 0, 0)
        
        self.follow_redirects_checkbox = StyledCheckBox("Follow Redirects")
        self.follow_redirects_checkbox.setChecked(True)
        redirects_layout.addWidget(self.follow_redirects_checkbox)
        
        crawl4ai_layout.addWidget(redirects_widget)
        
        # Verify SSL
        ssl_widget = QWidget()
        ssl_layout = QHBoxLayout(ssl_widget)
        ssl_layout.setContentsMargins(0, 0, 0, 0)
        
        self.verify_ssl_checkbox = StyledCheckBox("Verify SSL Certificates")
        self.verify_ssl_checkbox.setChecked(True)
        ssl_layout.addWidget(self.verify_ssl_checkbox)
        
        crawl4ai_layout.addWidget(ssl_widget)
        
        layout.addWidget(crawl4ai_group)
        
        # Application settings
        app_group = QGroupBox("Application Settings")
        app_group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {BORDER_COLOR};
                border-radius: 4px;
                margin-top: 1ex;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: {TEXT_COLOR};
            }}
        """)
        
        app_layout = QVBoxLayout(app_group)
        
        # Default output directory
        output_dir_widget = QWidget()
        output_dir_layout = QHBoxLayout(output_dir_widget)
        output_dir_layout.setContentsMargins(0, 0, 0, 0)
        
        output_dir_label = QLabel("Default Output Directory:")
        output_dir_label.setMinimumWidth(150)
        output_dir_layout.addWidget(output_dir_label)
        
        self.default_output_dir_input = StyledLineEdit()
        self.default_output_dir_input.setText(os.path.join(os.path.expanduser("~"), "scrappy_data"))
        output_dir_layout.addWidget(self.default_output_dir_input, 1)
        
        browse_default_button = StyledButton("Browse", primary=False)
        browse_default_button.clicked.connect(self.browse_default_output_dir)
        output_dir_layout.addWidget(browse_default_button)
        
        app_layout.addWidget(output_dir_widget)
        
        # Default formats
        default_formats_widget = QWidget()
        default_formats_layout = QHBoxLayout(default_formats_widget)
        default_formats_layout.setContentsMargins(0, 0, 0, 0)
        
        default_formats_label = QLabel("Default Output Formats:")
        default_formats_label.setMinimumWidth(150)
        default_formats_layout.addWidget(default_formats_label)
        
        formats_widget = QWidget()
        formats_widget_layout = QHBoxLayout(formats_widget)
        formats_widget_layout.setContentsMargins(0, 0, 0, 0)
        formats_widget_layout.setSpacing(10)
        
        self.default_format_checkboxes = {}
        for fmt in ["JSON", "CSV", "TXT", "YAML", "XML"]:
            checkbox = StyledCheckBox(fmt)
            if fmt == "JSON":
                checkbox.setChecked(True)
            self.default_format_checkboxes[fmt.lower()] = checkbox
            formats_widget_layout.addWidget(checkbox)
        
        default_formats_layout.addWidget(formats_widget, 1)
        
        app_layout.addWidget(default_formats_widget)
        
        layout.addWidget(app_group)
        
        # Buttons
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        reset_button = StyledButton("Reset to Defaults", primary=False)
        reset_button.clicked.connect(self.reset_settings)
        buttons_layout.addWidget(reset_button)
        
        save_button = StyledButton("Save Settings", primary=True)
        save_button.clicked.connect(self.save_settings)
        buttons_layout.addWidget(save_button)
        
        layout.addWidget(buttons_widget)
        
        # Add spacer
        layout.addStretch()
        
        return tab
    
    def update_options_combo(self):
        """
        Update options combo box based on selected source type.
        """
        self.options_combo.clear()
        
        source_type = self.source_combo.currentText().lower()
        
        if source_type == "github":
            self.options_combo.addItems(["Include Issues", "Include Pull Requests", "Include Files"])
        elif source_type == "website":
            self.options_combo.addItems(["Depth: 1", "Depth: 2", "Depth: 3"])
        elif source_type == "youtube":
            self.options_combo.addItems(["Include Transcripts", "Include Comments", "Analyze Content"])
    
    def browse_output_dir(self):
        """
        Browse for output directory.
        """
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_dir_input.setText(directory)
    
    def browse_default_output_dir(self):
        """
        Browse for default output directory.
        """
        directory = QFileDialog.getExistingDirectory(self, "Select Default Output Directory")
        if directory:
            self.default_output_dir_input.setText(directory)
    
    def on_search(self):
        """
        Handle search button click.
        """
        # Get search parameters
        url = self.search_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Input Error", "Please enter a URL to scrape.")
            return
        
        # Get source type
        source_type = self.source_combo.currentText().lower()
        
        # Get options
        options = {}
        option_text = self.options_combo.currentText()
        
        if source_type == "website" and "Depth:" in option_text:
            depth = int(option_text.split(":")[1].strip())
            options["depth"] = depth
        
        # Get output formats
        output_formats = []
        for fmt, checkbox in self.format_checkboxes.items():
            if checkbox.isChecked():
                output_formats.append(fmt)
        
        if not output_formats:
            QMessageBox.warning(self, "Input Error", "Please select at least one output format.")
            return
        
        # Get output directory
        output_dir = self.output_dir_input.text().strip()
        if not output_dir:
            output_dir = os.path.join(os.path.expanduser("~"), "scrappy_data")
            self.output_dir_input.setText(output_dir)
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Update UI
        self.results_stack.setCurrentIndex(1)  # Show loading state
        self.progress_bar.setValue(0)
        self.progress_label.setText("Initializing...")
        
        # Start scraping in a separate thread
        self.scrape_worker = ScrapeWorker(source_type, url, output_formats, options)
        self.scrape_worker.progress_update.connect(self.update_progress)
        self.scrape_worker.scrape_complete.connect(self.on_scrape_complete)
        self.scrape_worker.scrape_error.connect(self.on_scrape_error)
        self.scrape_worker.start()
    
    def update_progress(self, message, progress):
        """
        Update progress bar and label.
        
        Args:
            message: Progress message
            progress: Progress value (0-100)
        """
        self.progress_label.setText(message)
        self.progress_bar.setValue(progress)
    
    def on_scrape_complete(self, result):
        """
        Handle scrape completion.
        
        Args:
            result: Scrape result
        """
        # Update UI
        self.results_stack.setCurrentIndex(2)  # Show results state
        
        # Clear previous results
        while self.results_content_layout.count():
            item = self.results_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Set results title
        scraper_type = result.get('scraper_type', 'unknown')
        identifier = result.get('identifier', 'unknown')
        self.results_title.setText(f"{scraper_type.capitalize()}: {identifier}")
        
        # Add result information
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.StyledPanel)
        info_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {DARKER_BG};
                border: 1px solid {BORDER_COLOR};
                border-radius: 4px;
                padding: 10px;
            }}
        """)
        
        info_layout = QVBoxLayout(info_frame)
        
        # Add basic information
        if scraper_type == 'github':
            repo_data = result.get('data', {}).get('repository', {})
            info_layout.addWidget(QLabel(f"<b>Repository:</b> {repo_data.get('name', 'Unknown')}"))
            info_layout.addWidget(QLabel(f"<b>Owner:</b> {repo_data.get('owner', 'Unknown')}"))
            info_layout.addWidget(QLabel(f"<b>Files:</b> {result.get('data', {}).get('files_count', 0)}"))
            info_layout.addWidget(QLabel(f"<b>Issues:</b> {result.get('data', {}).get('issues_count', 0)}"))
        elif scraper_type == 'website':
            website_data = result.get('data', {})
            info_layout.addWidget(QLabel(f"<b>Domain:</b> {website_data.get('domain', 'Unknown')}"))
            info_layout.addWidget(QLabel(f"<b>Pages Crawled:</b> {website_data.get('pages_crawled', 0)}"))
            info_layout.addWidget(QLabel(f"<b>Assets Downloaded:</b> {website_data.get('assets_downloaded', 0)}"))
        elif scraper_type == 'youtube':
            channel_data = result.get('data', {}).get('channel', {})
            info_layout.addWidget(QLabel(f"<b>Channel:</b> {channel_data.get('handle', 'Unknown')}"))
            info_layout.addWidget(QLabel(f"<b>Videos:</b> {result.get('data', {}).get('videos_count', 0)}"))
        
        # Add crawl date
        crawl_date = result.get('data', {}).get('crawl_date', 'Unknown')
        info_layout.addWidget(QLabel(f"<b>Crawl Date:</b> {crawl_date}"))
        
        self.results_content_layout.addWidget(info_frame)
        
        # Add output files
        files_frame = QFrame()
        files_frame.setFrameShape(QFrame.StyledPanel)
        files_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {DARKER_BG};
                border: 1px solid {BORDER_COLOR};
                border-radius: 4px;
                padding: 10px;
            }}
        """)
        
        files_layout = QVBoxLayout(files_frame)
        files_layout.addWidget(QLabel("<b>Output Files:</b>"))
        
        for fmt, path in result.get('output_files', {}).items():
            file_widget = QWidget()
            file_layout = QHBoxLayout(file_widget)
            file_layout.setContentsMargins(0, 0, 0, 0)
            
            file_label = QLabel(f"{fmt.upper()}: {os.path.basename(path)}")
            file_layout.addWidget(file_label, 1)
            
            open_button = StyledButton("Open", primary=False)
            open_button.clicked.connect(lambda checked, p=path: self.open_file(p))
            file_layout.addWidget(open_button)
            
            files_layout.addWidget(file_widget)
        
        self.results_content_layout.addWidget(files_frame)
        
        # Add spacer
        self.results_content_layout.addStretch()
        
        # Refresh saved data list
        self.refresh_saved_data()
        
        # Update status bar
        self.statusBar().showMessage(f"Scraping completed: {scraper_type}/{identifier}")
    
    def on_scrape_error(self, error_message):
        """
        Handle scrape error.
        
        Args:
            error_message: Error message
        """
        # Update UI
        self.results_stack.setCurrentIndex(0)  # Show empty state
        
        # Show error message
        QMessageBox.critical(self, "Scraping Error", f"An error occurred during scraping:\n\n{error_message}")
        
        # Update status bar
        self.statusBar().showMessage("Scraping failed")
    
    def cancel_scraping(self):
        """
        Cancel ongoing scraping operation.
        """
        if hasattr(self, 'scrape_worker') and self.scrape_worker.isRunning():
            self.scrape_worker.terminate()
            self.scrape_worker.wait()
            
            # Update UI
            self.results_stack.setCurrentIndex(0)  # Show empty state
            
            # Update status bar
            self.statusBar().showMessage("Scraping cancelled")
    
    def new_search(self):
        """
        Start a new search.
        """
        self.results_stack.setCurrentIndex(0)  # Show empty state
        self.search_input.clear()
        self.statusBar().showMessage("Ready for new search")
    
    def export_results(self):
        """
        Export results to a file.
        """
        # TODO: Implement export functionality
        QMessageBox.information(self, "Export", "Export functionality will be implemented in a future version.")
    
    def refresh_saved_data(self):
        """
        Refresh saved data list.
        """
        self.saved_data_list.clear()
        
        # Get saved data
        saved_data = self.scrappy.list_saved_data()
        
        for data in saved_data:
            scraper_type = data.get('scraper_type', 'unknown')
            identifier = data.get('identifier', 'unknown')
            saved_at = data.get('saved_at', 'unknown')
            
            item = QListWidgetItem(f"{scraper_type.capitalize()}: {identifier} (Saved: {saved_at})")
            item.setData(Qt.UserRole, data)
            self.saved_data_list.addItem(item)
    
    def view_saved_data(self, item):
        """
        View saved data.
        
        Args:
            item: List widget item
        """
        if not item:
            return
        
        data = item.data(Qt.UserRole)
        if not data:
            return
        
        scraper_type = data.get('scraper_type', 'unknown')
        identifier = data.get('identifier', 'unknown')
        
        # Load data
        loaded_data = self.scrappy.load_data(scraper_type, identifier)
        if not loaded_data:
            QMessageBox.warning(self, "Data Error", f"Failed to load data for {scraper_type}/{identifier}")
            return
        
        # Show data in a dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Saved Data: {scraper_type.capitalize()}/{identifier}")
        dialog.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        # Data content
        content = QTextEdit()
        content.setReadOnly(True)
        content.setStyleSheet(f"""
            QTextEdit {{
                background-color: {DARKER_BG};
                color: {TEXT_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 4px;
                padding: 10px;
                font-family: monospace;
            }}
        """)
        
        # Format data as JSON
        import json
        formatted_data = json.dumps(loaded_data, indent=2)
        content.setText(formatted_data)
        
        layout.addWidget(content)
        
        # Buttons
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        export_button = StyledButton("Export", primary=False)
        export_button.clicked.connect(lambda: self.export_data(scraper_type, identifier, loaded_data))
        buttons_layout.addWidget(export_button)
        
        close_button = StyledButton("Close", primary=True)
        close_button.clicked.connect(dialog.accept)
        buttons_layout.addWidget(close_button)
        
        layout.addWidget(buttons_widget)
        
        dialog.exec_()
    
    def delete_saved_data(self):
        """
        Delete saved data.
        """
        item = self.saved_data_list.currentItem()
        if not item:
            return
        
        data = item.data(Qt.UserRole)
        if not data:
            return
        
        scraper_type = data.get('scraper_type', 'unknown')
        identifier = data.get('identifier', 'unknown')
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete {scraper_type}/{identifier}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Delete data
            success = self.scrappy.delete_data(scraper_type, identifier)
            
            if success:
                # Remove item from list
                row = self.saved_data_list.row(item)
                self.saved_data_list.takeItem(row)
                
                # Update status bar
                self.statusBar().showMessage(f"Deleted {scraper_type}/{identifier}")
            else:
                QMessageBox.warning(self, "Deletion Error", f"Failed to delete {scraper_type}/{identifier}")
    
    def export_data(self, scraper_type, identifier, data):
        """
        Export data to a file.
        
        Args:
            scraper_type: Type of scraper
            identifier: Data identifier
            data: Data to export
        """
        # Get file path
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Data", f"{scraper_type}_{identifier}.json",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            # Write data to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            # Show success message
            QMessageBox.information(self, "Export Successful", f"Data exported to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export data: {str(e)}")
    
    def open_file(self, file_path):
        """
        Open a file with the default application.
        
        Args:
            file_path: Path to the file
        """
        if os.path.exists(file_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
        else:
            QMessageBox.warning(self, "File Error", f"File not found: {file_path}")
    
    def reset_settings(self):
        """
        Reset settings to defaults.
        """
        # Reset crawl4ai settings
        self.user_agent_input.setText("Scrappy/1.0 (+https://github.com/k3ss-official/scrappy_v2)")
        self.timeout_combo.setCurrentText("30")
        self.retries_combo.setCurrentText("3")
        self.follow_redirects_checkbox.setChecked(True)
        self.verify_ssl_checkbox.setChecked(True)
        
        # Reset application settings
        self.default_output_dir_input.setText(os.path.join(os.path.expanduser("~"), "scrappy_data"))
        
        for fmt, checkbox in self.default_format_checkboxes.items():
            checkbox.setChecked(fmt == "json")
        
        # Show message
        self.statusBar().showMessage("Settings reset to defaults")
    
    def save_settings(self):
        """
        Save settings.
        """
        # Create settings object
        settings = QSettings("k3ss-official", "Scrappy")
        
        # Save crawl4ai settings
        settings.setValue("crawl4ai/user_agent", self.user_agent_input.text())
        settings.setValue("crawl4ai/timeout", self.timeout_combo.currentText())
        settings.setValue("crawl4ai/max_retries", self.retries_combo.currentText())
        settings.setValue("crawl4ai/follow_redirects", self.follow_redirects_checkbox.isChecked())
        settings.setValue("crawl4ai/verify_ssl", self.verify_ssl_checkbox.isChecked())
        
        # Save application settings
        settings.setValue("app/default_output_dir", self.default_output_dir_input.text())
        
        default_formats = []
        for fmt, checkbox in self.default_format_checkboxes.items():
            if checkbox.isChecked():
                default_formats.append(fmt)
        
        settings.setValue("app/default_formats", default_formats)
        
        # Show message
        self.statusBar().showMessage("Settings saved")
        
        # Create crawl4ai config file
        config = {
            "user_agent": self.user_agent_input.text(),
            "timeout": int(self.timeout_combo.currentText()),
            "max_retries": int(self.retries_combo.currentText()),
            "follow_redirects": self.follow_redirects_checkbox.isChecked(),
            "verify_ssl": self.verify_ssl_checkbox.isChecked()
        }
        
        config_dir = os.path.join(os.path.expanduser("~"), ".scrappy")
        os.makedirs(config_dir, exist_ok=True)
        
        config_path = os.path.join(config_dir, "crawl4ai_config.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    
    def load_settings(self):
        """
        Load settings.
        """
        # Create settings object
        settings = QSettings("k3ss-official", "Scrappy")
        
        # Load crawl4ai settings
        self.user_agent_input.setText(settings.value("crawl4ai/user_agent", "Scrappy/1.0 (+https://github.com/k3ss-official/scrappy_v2)"))
        self.timeout_combo.setCurrentText(settings.value("crawl4ai/timeout", "30"))
        self.retries_combo.setCurrentText(settings.value("crawl4ai/max_retries", "3"))
        self.follow_redirects_checkbox.setChecked(settings.value("crawl4ai/follow_redirects", True, type=bool))
        self.verify_ssl_checkbox.setChecked(settings.value("crawl4ai/verify_ssl", True, type=bool))
        
        # Load application settings
        default_output_dir = settings.value("app/default_output_dir", os.path.join(os.path.expanduser("~"), "scrappy_data"))
        self.default_output_dir_input.setText(default_output_dir)
        self.output_dir_input.setText(default_output_dir)
        
        default_formats = settings.value("app/default_formats", ["json"])
        for fmt, checkbox in self.default_format_checkboxes.items():
            checkbox.setChecked(fmt in default_formats)
        
        for fmt, checkbox in self.format_checkboxes.items():
            checkbox.setChecked(fmt in default_formats)

def main():
    """
    Main function for running the desktop GUI.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrappy Desktop GUI')
    parser.add_argument('--output-dir', help='Base directory for storing data')
    
    args = parser.parse_args()
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Scrappy")
    app.setOrganizationName("k3ss-official")
    
    # Create main window
    window = ScrappyGUI()
    window.show()
    
    # Run application
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
