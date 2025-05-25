"""
Desktop GUI Application for Scrappy

This module implements the PyQt5-based desktop GUI for Scrappy,
following the 'What-Where-How' workflow pattern.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QFileDialog,
    QCheckBox, QTabWidget, QScrollArea, QFrame, QSplitter,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QStatusBar, QToolBar, QAction, QMenu, QSystemTrayIcon
)
from PyQt5.QtGui import QIcon, QPixmap, QFont, QColor, QPalette, QCursor
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal, QTimer, QSettings

# Import scraper modules
from src.scrapers.github.crawler import GitHubScraper
from src.scrapers.website.crawler import WebsiteScraper
from src.scrapers.youtube.crawler import YouTubeScraper
from src.utils.security import SecurityManager
from src.utils.setup import SetupManager
from src.formatters.converter import FormatConverter
from src.storage.handler import StorageHandler

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('scrappy.ui.desktop')

# Constants
DARK_BG = "#1a1b26"
DARKER_BG = "#16161e"
ACCENT_COLOR = "#7aa2f7"
SUCCESS_COLOR = "#9ece6a"
WARNING_COLOR = "#e0af68"
ERROR_COLOR = "#f7768e"
TEXT_COLOR = "#c0caf5"
SECONDARY_TEXT_COLOR = "#a9b1d6"

class ScrapingWorker(QThread):
    """Worker thread for running scraping tasks."""
    
    progress_signal = pyqtSignal(str, int)
    finished_signal = pyqtSignal(dict, bool)
    
    def __init__(self, scrape_type: str, url: str, output_dir: str, formats: List[str]):
        """Initialize the worker thread."""
        super().__init__()
        self.scrape_type = scrape_type
        self.url = url
        self.output_dir = output_dir
        self.formats = formats
        self.security = SecurityManager()
    
    def run(self):
        """Run the scraping task."""
        try:
            # Validate inputs
            if not self.security.validate_url(self.url):
                self.finished_signal.emit({"error": "Invalid URL format"}, False)
                return
            
            if not self.security.validate_path(self.output_dir):
                self.finished_signal.emit({"error": "Invalid output directory"}, False)
                return
            
            # Create output directory if it doesn't exist
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Initialize appropriate scraper
            self.progress_signal.emit("Initializing scraper...", 10)
            
            if self.scrape_type == "github" or (self.scrape_type == "auto" and "github.com" in self.url):
                scraper = GitHubScraper(self.url, self.output_dir)
                self.progress_signal.emit("GitHub scraper initialized", 20)
            
            elif self.scrape_type == "website" or (self.scrape_type == "auto" and not any(x in self.url for x in ["github.com", "youtube.com"])):
                scraper = WebsiteScraper(self.url, self.output_dir)
                self.progress_signal.emit("Website scraper initialized", 20)
            
            elif self.scrape_type == "youtube" or (self.scrape_type == "auto" and "youtube.com" in self.url):
                scraper = YouTubeScraper(self.url, self.output_dir)
                self.progress_signal.emit("YouTube scraper initialized", 20)
            
            else:
                self.finished_signal.emit({"error": "Invalid scraper type"}, False)
                return
            
            # Run scraping
            self.progress_signal.emit("Starting scraping process...", 30)
            result = scraper.scrape()
            self.progress_signal.emit("Scraping completed", 70)
            
            # Convert to requested formats
            self.progress_signal.emit("Converting to requested formats...", 80)
            converter = FormatConverter()
            
            output_files = []
            for fmt in self.formats:
                if fmt.lower() == "json":
                    # JSON is the default format, already saved
                    continue
                
                output_file = converter.convert(result, fmt.lower(), self.output_dir)
                output_files.append(output_file)
            
            self.progress_signal.emit("Conversion completed", 90)
            
            # Prepare result summary
            summary = {
                "url": self.url,
                "type": self.scrape_type,
                "output_dir": self.output_dir,
                "formats": self.formats,
                "timestamp": datetime.now().isoformat(),
                "output_files": output_files
            }
            
            # Signal completion
            self.progress_signal.emit("Task completed successfully", 100)
            self.finished_signal.emit(summary, True)
        
        except Exception as e:
            logger.error(f"Error in scraping worker: {str(e)}")
            self.finished_signal.emit({"error": str(e)}, False)


class ScrappyDesktopApp(QMainWindow):
    """Main desktop application window for Scrappy."""
    
    def __init__(self):
        """Initialize the application window."""
        super().__init__()
        
        # Initialize managers
        self.security = SecurityManager()
        self.setup_manager = SetupManager()
        self.storage = StorageHandler()
        
        # Initialize UI
        self.init_ui()
        
        # Load settings and history
        self.load_settings()
        self.load_history()
        
        # Check dependencies
        self.check_dependencies()
    
    def init_ui(self):
        """Initialize the user interface."""
        # Set window properties
        self.setWindowTitle("Scrappy - Universal Scraping and Delivery System")
        self.setMinimumSize(1000, 700)
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "scrappy_icon.png")))
        
        # Set dark theme
        self.set_dark_theme()
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Create content area
        content = QSplitter(Qt.Horizontal)
        
        # Create sidebar
        sidebar = self.create_sidebar()
        content.addWidget(sidebar)
        
        # Create tab widget for main content
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #1a1b26;
            }
            QTabBar::tab {
                background-color: #16161e;
                color: #a9b1d6;
                padding: 8px 16px;
                border: none;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background-color: #1a1b26;
                color: #c0caf5;
                border-bottom: 2px solid #7aa2f7;
            }
        """)
        
        # Create dashboard tab
        dashboard_tab = self.create_dashboard_tab()
        self.tab_widget.addTab(dashboard_tab, "Dashboard")
        
        # Create new scrape tab
        new_scrape_tab = self.create_new_scrape_tab()
        self.tab_widget.addTab(new_scrape_tab, "New Scrape")
        
        # Create history tab
        history_tab = self.create_history_tab()
        self.tab_widget.addTab(history_tab, "History")
        
        # Create settings tab
        settings_tab = self.create_settings_tab()
        self.tab_widget.addTab(settings_tab, "Settings")
        
        content.addWidget(self.tab_widget)
        
        # Set stretch factors
        content.setStretchFactor(0, 1)  # Sidebar
        content.setStretchFactor(1, 4)  # Main content
        
        main_layout.addWidget(content)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(f"background-color: {DARKER_BG}; color: {SECONDARY_TEXT_COLOR};")
        self.setStatusBar(self.status_bar)
        
        # Set initial status
        self.status_bar.showMessage("Ready")
        
        # Create system tray icon
        self.create_tray_icon()
    
    def set_dark_theme(self):
        """Set dark theme for the application."""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(DARK_BG))
        palette.setColor(QPalette.WindowText, QColor(TEXT_COLOR))
        palette.setColor(QPalette.Base, QColor(DARKER_BG))
        palette.setColor(QPalette.AlternateBase, QColor(DARK_BG))
        palette.setColor(QPalette.ToolTipBase, QColor(DARK_BG))
        palette.setColor(QPalette.ToolTipText, QColor(TEXT_COLOR))
        palette.setColor(QPalette.Text, QColor(TEXT_COLOR))
        palette.setColor(QPalette.Button, QColor(DARK_BG))
        palette.setColor(QPalette.ButtonText, QColor(TEXT_COLOR))
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(ACCENT_COLOR))
        palette.setColor(QPalette.Highlight, QColor(ACCENT_COLOR))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        
        self.setPalette(palette)
        
        # Set stylesheet for widgets
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {DARK_BG};
                color: {TEXT_COLOR};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            
            QLineEdit, QComboBox, QSpinBox, QTextEdit, QPlainTextEdit {{
                background-color: {DARKER_BG};
                border: 1px solid #414868;
                border-radius: 4px;
                padding: 8px;
                color: {TEXT_COLOR};
            }}
            
            QPushButton {{
                background-color: {ACCENT_COLOR};
                color: #16161e;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            
            QPushButton:hover {{
                background-color: #91b4f9;
            }}
            
            QPushButton:pressed {{
                background-color: #6a8fd7;
            }}
            
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid #414868;
                border-radius: 3px;
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {ACCENT_COLOR};
                border: 1px solid {ACCENT_COLOR};
            }}
        """)
    
    def create_header(self):
        """Create the application header."""
        header = QFrame()
        header.setStyleSheet(f"background-color: {DARKER_BG}; border-bottom: 1px solid #414868;")
        header.setFixedHeight(60)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 0, 16, 0)
        
        # Logo and title
        logo_label = QLabel()
        logo_pixmap = QPixmap(os.path.join(os.path.dirname(__file__), "icons", "scrappy_icon.png"))
        logo_label.setPixmap(logo_pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(logo_label)
        
        title_label = QLabel("Scrappy")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #c0caf5;")
        layout.addWidget(title_label)
        
        version_label = QLabel("v1.0")
        version_label.setStyleSheet(f"background-color: {ACCENT_COLOR}; color: #16161e; padding: 2px 6px; border-radius: 4px; font-size: 12px; font-weight: bold;")
        layout.addWidget(version_label)
        
        layout.addStretch()
        
        # System status
        status_icon = QLabel()
        status_icon.setStyleSheet("background-color: #9ece6a; border-radius: 5px; min-width: 10px; min-height: 10px; max-width: 10px; max-height: 10px;")
        layout.addWidget(status_icon)
        
        status_label = QLabel("System Online")
        status_label.setStyleSheet("color: #a9b1d6;")
        layout.addWidget(status_label)
        
        # Current time
        self.time_label = QLabel(datetime.now().strftime("%I:%M:%S %p"))
        self.time_label.setStyleSheet("color: #a9b1d6;")
        layout.addWidget(self.time_label)
        
        # Update time every second
        timer = QTimer(self)
        timer.timeout.connect(self.update_time)
        timer.start(1000)
        
        return header
    
    def create_sidebar(self):
        """Create the sidebar navigation."""
        sidebar = QFrame()
        sidebar.setStyleSheet(f"background-color: {DARKER_BG};")
        sidebar.setFixedWidth(200)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Dashboard button
        dashboard_btn = QPushButton("  Dashboard")
        dashboard_btn.setIcon(QIcon.fromTheme("dashboard", QIcon.fromTheme("view-grid")))
        dashboard_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #3b4261;
                color: {TEXT_COLOR};
                border: none;
                border-radius: 0;
                padding: 16px;
                text-align: left;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #414868;
            }}
        """)
        dashboard_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(0))
        layout.addWidget(dashboard_btn)
        
        # New Scrape button
        new_scrape_btn = QPushButton("  New Scrape")
        new_scrape_btn.setIcon(QIcon.fromTheme("document-new", QIcon.fromTheme("list-add")))
        new_scrape_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DARKER_BG};
                color: {TEXT_COLOR};
                border: none;
                border-radius: 0;
                padding: 16px;
                text-align: left;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #414868;
            }}
        """)
        new_scrape_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(1))
        layout.addWidget(new_scrape_btn)
        
        # History button
        history_btn = QPushButton("  History")
        history_btn.setIcon(QIcon.fromTheme("document-open-recent", QIcon.fromTheme("appointment-soon")))
        history_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DARKER_BG};
                color: {TEXT_COLOR};
                border: none;
                border-radius: 0;
                padding: 16px;
                text-align: left;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #414868;
            }}
        """)
        history_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(2))
        layout.addWidget(history_btn)
        
        # Settings button
        settings_btn = QPushButton("  Settings")
        settings_btn.setIcon(QIcon.fromTheme("preferences-system", QIcon.fromTheme("configure")))
        settings_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DARKER_BG};
                color: {TEXT_COLOR};
                border: none;
                border-radius: 0;
                padding: 16px;
                text-align: left;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #414868;
            }}
        """)
        settings_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(3))
        layout.addWidget(settings_btn)
        
        layout.addStretch()
        
        return sidebar
    
    def create_dashboard_tab(self):
        """Create the dashboard tab."""
        dashboard = QWidget()
        layout = QVBoxLayout(dashboard)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        # Dashboard title
        title = QLabel("Dashboard Overview")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #c0caf5;")
        layout.addWidget(title)
        
        # Metrics section
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(16)
        
        # Total Scrapes
        total_scrapes = self.create_metric_card(
            "Total Scrapes",
            "0",
            "download",
            "#7aa2f7"
        )
        metrics_layout.addWidget(total_scrapes)
        
        # Files Generated
        files_generated = self.create_metric_card(
            "Files Generated",
            "0",
            "file",
            "#9ece6a"
        )
        metrics_layout.addWidget(files_generated)
        
        # Data Processed
        data_processed = self.create_metric_card(
            "Data Processed",
            "0 MB",
            "database",
            "#bb9af7"
        )
        metrics_layout.addWidget(data_processed)
        
        # Success Rate
        success_rate = self.create_metric_card(
            "Success Rate",
            "0%",
            "chart-line",
            "#e0af68"
        )
        metrics_layout.addWidget(success_rate)
        
        layout.addLayout(metrics_layout)
        
        # New Scraping Task section
        task_frame = QFrame()
        task_frame.setStyleSheet(f"background-color: {DARKER_BG}; border-radius: 8px;")
        task_layout = QVBoxLayout(task_frame)
        task_layout.setContentsMargins(24, 24, 24, 24)
        task_layout.setSpacing(16)
        
        task_title = QLabel("New Scraping Task")
        task_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #c0caf5;")
        task_layout.addWidget(task_title)
        
        # WHAT to scrape
        what_layout = QVBoxLayout()
        what_label = QLabel("WHAT to scrape?")
        what_label.setStyleSheet("font-weight: bold; color: #7aa2f7;")
        what_layout.addWidget(what_label)
        
        what_input_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholder("https://github.com/user/repo or https://example.com or @YouTubeChannel")
        what_input_layout.addWidget(self.url_input)
        
        self.source_type = QComboBox()
        self.source_type.addItems(["Auto-detect", "GitHub", "Website", "YouTube"])
        what_input_layout.addWidget(self.source_type)
        
        what_layout.addLayout(what_input_layout)
        task_layout.addLayout(what_layout)
        
        # WHERE to save
        where_layout = QVBoxLayout()
        where_label = QLabel("WHERE to save?")
        where_label.setStyleSheet("font-weight: bold; color: #9ece6a;")
        where_layout.addWidget(where_label)
        
        where_input_layout = QHBoxLayout()
        self.output_dir = QLineEdit()
        self.output_dir.setPlaceholder("/path/to/output/directory")
        where_input_layout.addWidget(self.output_dir)
        
        browse_btn = QPushButton("Browse")
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #9ece6a;
                color: #16161e;
            }
            QPushButton:hover {
                background-color: #aad97a;
            }
        """)
        browse_btn.clicked.connect(self.browse_output_dir)
        where_input_layout.addWidget(browse_btn)
        
        where_layout.addLayout(where_input_layout)
        task_layout.addLayout(where_layout)
        
        # HOW to format output
        how_layout = QVBoxLayout()
        how_label = QLabel("HOW to format output?")
        how_label.setStyleSheet("font-weight: bold; color: #e0af68;")
        how_layout.addWidget(how_label)
        
        formats_layout = QHBoxLayout()
        
        self.json_checkbox = QCheckBox("JSON")
        self.json_checkbox.setChecked(True)
        formats_layout.addWidget(self.json_checkbox)
        
        self.csv_checkbox = QCheckBox("CSV")
        formats_layout.addWidget(self.csv_checkbox)
        
        self.txt_checkbox = QCheckBox("TXT")
        formats_layout.addWidget(self.txt_checkbox)
        
        self.html_checkbox = QCheckBox("HTML")
        formats_layout.addWidget(self.html_checkbox)
        
        self.md_checkbox = QCheckBox("Markdown")
        formats_layout.addWidget(self.md_checkbox)
        
        formats_layout.addStretch()
        how_layout.addLayout(formats_layout)
        task_layout.addLayout(how_layout)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        start_btn = QPushButton("Start Scraping")
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #7aa2f7;
                color: #16161e;
                font-weight: bold;
                padding: 12px 24px;
            }
            QPushButton:hover {
                background-color: #91b4f9;
            }
        """)
        start_btn.clicked.connect(self.start_scraping)
        buttons_layout.addWidget(start_btn)
        
        save_template_btn = QPushButton("Save as Template")
        save_template_btn.setStyleSheet("""
            QPushButton {
                background-color: #414868;
                color: #c0caf5;
                font-weight: bold;
                padding: 12px 24px;
            }
            QPushButton:hover {
                background-color: #545c7e;
            }
        """)
        save_template_btn.clicked.connect(self.save_template)
        buttons_layout.addWidget(save_template_btn)
        
        buttons_layout.addStretch()
        task_layout.addLayout(buttons_layout)
        
        layout.addWidget(task_frame)
        
        # Recent Activity section
        activity_frame = QFrame()
        activity_frame.setStyleSheet(f"background-color: {DARKER_BG}; border-radius: 8px;")
        activity_layout = QVBoxLayout(activity_frame)
        activity_layout.setContentsMargins(24, 24, 24, 24)
        activity_layout.setSpacing(16)
        
        activity_title = QLabel("Recent Activity")
        activity_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #c0caf5;")
        activity_layout.addWidget(activity_title)
        
        # Activity list will be populated from history
        self.activity_list = QTableWidget(0, 4)
        self.activity_list.setHorizontalHeaderLabels(["Type", "URL", "Time", "Status"])
        self.activity_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.activity_list.setStyleSheet(f"""
            QTableWidget {{
                background-color: {DARKER_BG};
                border: none;
            }}
            QHeaderView::section {{
                background-color: {DARKER_BG};
                color: {SECONDARY_TEXT_COLOR};
                border: none;
                padding: 8px;
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid #414868;
            }}
        """)
        activity_layout.addWidget(self.activity_list)
        
        layout.addWidget(activity_frame)
        
        return dashboard
    
    def create_metric_card(self, title, value, icon_name, color):
        """Create a metric card for the dashboard."""
        card = QFrame()
        card.setStyleSheet(f"background-color: {DARKER_BG}; border-radius: 8px;")
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {SECONDARY_TEXT_COLOR}; font-size: 14px;")
        layout.addWidget(title_label)
        
        value_layout = QHBoxLayout()
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {TEXT_COLOR}; font-size: 24px; font-weight: bold;")
        value_layout.addWidget(value_label)
        
        value_layout.addStretch()
        
        icon_label = QLabel()
        icon_label.setStyleSheet(f"color: {color};")
        # In a real implementation, we would set an actual icon here
        icon_label.setText("📊")
        value_layout.addWidget(icon_label)
        
        layout.addLayout(value_layout)
        
        return card
    
    def create_new_scrape_tab(self):
        """Create the new scrape tab."""
        # This is essentially the same as the task section in the dashboard
        # In a real implementation, we would refactor this to avoid duplication
        new_scrape = QWidget()
        layout = QVBoxLayout(new_scrape)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        # New Scrape title
        title = QLabel("New Scraping Task")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #c0caf5;")
        layout.addWidget(title)
        
        # Task form
        task_frame = QFrame()
        task_frame.setStyleSheet(f"background-color: {DARKER_BG}; border-radius: 8px;")
        task_layout = QVBoxLayout(task_frame)
        task_layout.setContentsMargins(24, 24, 24, 24)
        task_layout.setSpacing(24)
        
        # WHAT to scrape
        what_layout = QVBoxLayout()
        what_label = QLabel("WHAT to scrape?")
        what_label.setStyleSheet("font-weight: bold; color: #7aa2f7; font-size: 16px;")
        what_layout.addWidget(what_label)
        
        what_input_layout = QHBoxLayout()
        self.url_input_tab = QLineEdit()
        self.url_input_tab.setPlaceholder("https://github.com/user/repo or https://example.com or @YouTubeChannel")
        what_input_layout.addWidget(self.url_input_tab)
        
        self.source_type_tab = QComboBox()
        self.source_type_tab.addItems(["Auto-detect", "GitHub", "Website", "YouTube"])
        what_input_layout.addWidget(self.source_type_tab)
        
        what_layout.addLayout(what_input_layout)
        task_layout.addLayout(what_layout)
        
        # WHERE to save
        where_layout = QVBoxLayout()
        where_label = QLabel("WHERE to save?")
        where_label.setStyleSheet("font-weight: bold; color: #9ece6a; font-size: 16px;")
        where_layout.addWidget(where_label)
        
        where_input_layout = QHBoxLayout()
        self.output_dir_tab = QLineEdit()
        self.output_dir_tab.setPlaceholder("/path/to/output/directory")
        where_input_layout.addWidget(self.output_dir_tab)
        
        browse_btn = QPushButton("Browse")
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #9ece6a;
                color: #16161e;
            }
            QPushButton:hover {
                background-color: #aad97a;
            }
        """)
        browse_btn.clicked.connect(self.browse_output_dir_tab)
        where_input_layout.addWidget(browse_btn)
        
        where_layout.addLayout(where_input_layout)
        task_layout.addLayout(where_layout)
        
        # HOW to format output
        how_layout = QVBoxLayout()
        how_label = QLabel("HOW to format output?")
        how_label.setStyleSheet("font-weight: bold; color: #e0af68; font-size: 16px;")
        how_layout.addWidget(how_label)
        
        formats_layout = QHBoxLayout()
        
        self.json_checkbox_tab = QCheckBox("JSON")
        self.json_checkbox_tab.setChecked(True)
        formats_layout.addWidget(self.json_checkbox_tab)
        
        self.csv_checkbox_tab = QCheckBox("CSV")
        formats_layout.addWidget(self.csv_checkbox_tab)
        
        self.txt_checkbox_tab = QCheckBox("TXT")
        formats_layout.addWidget(self.txt_checkbox_tab)
        
        self.html_checkbox_tab = QCheckBox("HTML")
        formats_layout.addWidget(self.html_checkbox_tab)
        
        self.md_checkbox_tab = QCheckBox("Markdown")
        formats_layout.addWidget(self.md_checkbox_tab)
        
        formats_layout.addStretch()
        how_layout.addLayout(formats_layout)
        task_layout.addLayout(how_layout)
        
        # Advanced options (collapsible)
        advanced_layout = QVBoxLayout()
        advanced_label = QLabel("Advanced Options")
        advanced_label.setStyleSheet("font-weight: bold; color: #bb9af7; font-size: 16px;")
        advanced_layout.addWidget(advanced_label)
        
        # Add advanced options here
        # ...
        
        task_layout.addLayout(advanced_layout)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        start_btn = QPushButton("Start Scraping")
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #7aa2f7;
                color: #16161e;
                font-weight: bold;
                padding: 12px 24px;
            }
            QPushButton:hover {
                background-color: #91b4f9;
            }
        """)
        start_btn.clicked.connect(self.start_scraping_tab)
        buttons_layout.addWidget(start_btn)
        
        save_template_btn = QPushButton("Save as Template")
        save_template_btn.setStyleSheet("""
            QPushButton {
                background-color: #414868;
                color: #c0caf5;
                font-weight: bold;
                padding: 12px 24px;
            }
            QPushButton:hover {
                background-color: #545c7e;
            }
        """)
        save_template_btn.clicked.connect(self.save_template_tab)
        buttons_layout.addWidget(save_template_btn)
        
        buttons_layout.addStretch()
        task_layout.addLayout(buttons_layout)
        
        layout.addWidget(task_frame)
        layout.addStretch()
        
        return new_scrape
    
    def create_history_tab(self):
        """Create the history tab."""
        history = QWidget()
        layout = QVBoxLayout(history)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        # History title
        title = QLabel("Scraping History")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #c0caf5;")
        layout.addWidget(title)
        
        # History table
        self.history_table = QTableWidget(0, 5)
        self.history_table.setHorizontalHeaderLabels(["Type", "URL", "Time", "Formats", "Status"])
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.history_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {DARKER_BG};
                border: none;
                border-radius: 8px;
            }}
            QHeaderView::section {{
                background-color: {DARKER_BG};
                color: {SECONDARY_TEXT_COLOR};
                border: none;
                padding: 8px;
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid #414868;
            }}
        """)
        layout.addWidget(self.history_table)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        clear_btn = QPushButton("Clear History")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #f7768e;
                color: #16161e;
                font-weight: bold;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #ff8c9e;
            }
        """)
        clear_btn.clicked.connect(self.clear_history)
        buttons_layout.addWidget(clear_btn)
        
        export_btn = QPushButton("Export History")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #414868;
                color: #c0caf5;
                font-weight: bold;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #545c7e;
            }
        """)
        export_btn.clicked.connect(self.export_history)
        buttons_layout.addWidget(export_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        return history
    
    def create_settings_tab(self):
        """Create the settings tab."""
        settings = QWidget()
        layout = QVBoxLayout(settings)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        # Settings title
        title = QLabel("Settings")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #c0caf5;")
        layout.addWidget(title)
        
        # Settings sections
        settings_frame = QFrame()
        settings_frame.setStyleSheet(f"background-color: {DARKER_BG}; border-radius: 8px;")
        settings_layout = QVBoxLayout(settings_frame)
        settings_layout.setContentsMargins(24, 24, 24, 24)
        settings_layout.setSpacing(24)
        
        # General settings
        general_label = QLabel("General Settings")
        general_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #c0caf5;")
        settings_layout.addWidget(general_label)
        
        # Default output directory
        default_dir_layout = QHBoxLayout()
        default_dir_label = QLabel("Default Output Directory:")
        default_dir_layout.addWidget(default_dir_label)
        
        self.default_dir_input = QLineEdit()
        default_dir_layout.addWidget(self.default_dir_input)
        
        default_dir_browse = QPushButton("Browse")
        default_dir_browse.clicked.connect(self.browse_default_dir)
        default_dir_layout.addWidget(default_dir_browse)
        
        settings_layout.addLayout(default_dir_layout)
        
        # Default output formats
        default_formats_layout = QVBoxLayout()
        default_formats_label = QLabel("Default Output Formats:")
        default_formats_layout.addWidget(default_formats_label)
        
        formats_options = QHBoxLayout()
        
        self.default_json = QCheckBox("JSON")
        self.default_json.setChecked(True)
        formats_options.addWidget(self.default_json)
        
        self.default_csv = QCheckBox("CSV")
        formats_options.addWidget(self.default_csv)
        
        self.default_txt = QCheckBox("TXT")
        formats_options.addWidget(self.default_txt)
        
        self.default_html = QCheckBox("HTML")
        formats_options.addWidget(self.default_html)
        
        self.default_md = QCheckBox("Markdown")
        formats_options.addWidget(self.default_md)
        
        formats_options.addStretch()
        default_formats_layout.addLayout(formats_options)
        
        settings_layout.addLayout(default_formats_layout)
        
        # Advanced settings
        advanced_label = QLabel("Advanced Settings")
        advanced_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #c0caf5; margin-top: 16px;")
        settings_layout.addWidget(advanced_label)
        
        # Concurrent scraping tasks
        concurrent_layout = QHBoxLayout()
        concurrent_label = QLabel("Max Concurrent Tasks:")
        concurrent_layout.addWidget(concurrent_label)
        
        self.concurrent_input = QComboBox()
        self.concurrent_input.addItems(["1", "2", "3", "4", "5"])
        concurrent_layout.addWidget(self.concurrent_input)
        
        concurrent_layout.addStretch()
        settings_layout.addLayout(concurrent_layout)
        
        # Request timeout
        timeout_layout = QHBoxLayout()
        timeout_label = QLabel("Request Timeout (seconds):")
        timeout_layout.addWidget(timeout_label)
        
        self.timeout_input = QComboBox()
        self.timeout_input.addItems(["10", "20", "30", "60", "120"])
        self.timeout_input.setCurrentIndex(2)  # Default to 30 seconds
        timeout_layout.addWidget(self.timeout_input)
        
        timeout_layout.addStretch()
        settings_layout.addLayout(timeout_layout)
        
        # User agent
        user_agent_layout = QHBoxLayout()
        user_agent_label = QLabel("User Agent:")
        user_agent_layout.addWidget(user_agent_label)
        
        self.user_agent_input = QLineEdit("Scrappy/1.0 (+https://github.com/k3ss-official/scrappy_v2)")
        user_agent_layout.addWidget(self.user_agent_input)
        
        settings_layout.addLayout(user_agent_layout)
        
        settings_layout.addStretch()
        
        # Save settings button
        save_settings_btn = QPushButton("Save Settings")
        save_settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #7aa2f7;
                color: #16161e;
                font-weight: bold;
                padding: 12px 24px;
            }
            QPushButton:hover {
                background-color: #91b4f9;
            }
        """)
        save_settings_btn.clicked.connect(self.save_settings)
        settings_layout.addWidget(save_settings_btn)
        
        layout.addWidget(settings_frame)
        
        return settings
    
    def create_tray_icon(self):
        """Create system tray icon."""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "scrappy_icon.png")))
        
        # Create tray menu
        tray_menu = QMenu()
        
        show_action = QAction("Show Scrappy", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        new_scrape_action = QAction("New Scrape", self)
        new_scrape_action.triggered.connect(lambda: self.show() or self.tab_widget.setCurrentIndex(1))
        tray_menu.addAction(new_scrape_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
    
    def update_time(self):
        """Update the time display in the header."""
        self.time_label.setText(datetime.now().strftime("%I:%M:%S %p"))
    
    def browse_output_dir(self):
        """Open file dialog to select output directory."""
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_dir.setText(directory)
    
    def browse_output_dir_tab(self):
        """Open file dialog to select output directory (for tab)."""
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_dir_tab.setText(directory)
    
    def browse_default_dir(self):
        """Open file dialog to select default output directory."""
        directory = QFileDialog.getExistingDirectory(self, "Select Default Output Directory")
        if directory:
            self.default_dir_input.setText(directory)
    
    def start_scraping(self):
        """Start the scraping process from dashboard."""
        url = self.url_input.text()
        output_dir = self.output_dir.text()
        
        if not url:
            QMessageBox.warning(self, "Input Error", "Please enter a URL to scrape.")
            return
        
        if not output_dir:
            QMessageBox.warning(self, "Input Error", "Please select an output directory.")
            return
        
        # Get selected formats
        formats = []
        if self.json_checkbox.isChecked():
            formats.append("json")
        if self.csv_checkbox.isChecked():
            formats.append("csv")
        if self.txt_checkbox.isChecked():
            formats.append("txt")
        if self.html_checkbox.isChecked():
            formats.append("html")
        if self.md_checkbox.isChecked():
            formats.append("md")
        
        if not formats:
            QMessageBox.warning(self, "Input Error", "Please select at least one output format.")
            return
        
        # Get source type
        source_type = self.source_type.currentText().lower()
        if source_type == "auto-detect":
            source_type = "auto"
        
        # Create and start worker thread
        self.worker = ScrapingWorker(source_type, url, output_dir, formats)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.scraping_finished)
        self.worker.start()
        
        # Show progress dialog
        self.show_progress_dialog()
    
    def start_scraping_tab(self):
        """Start the scraping process from tab."""
        url = self.url_input_tab.text()
        output_dir = self.output_dir_tab.text()
        
        if not url:
            QMessageBox.warning(self, "Input Error", "Please enter a URL to scrape.")
            return
        
        if not output_dir:
            QMessageBox.warning(self, "Input Error", "Please select an output directory.")
            return
        
        # Get selected formats
        formats = []
        if self.json_checkbox_tab.isChecked():
            formats.append("json")
        if self.csv_checkbox_tab.isChecked():
            formats.append("csv")
        if self.txt_checkbox_tab.isChecked():
            formats.append("txt")
        if self.html_checkbox_tab.isChecked():
            formats.append("html")
        if self.md_checkbox_tab.isChecked():
            formats.append("md")
        
        if not formats:
            QMessageBox.warning(self, "Input Error", "Please select at least one output format.")
            return
        
        # Get source type
        source_type = self.source_type_tab.currentText().lower()
        if source_type == "auto-detect":
            source_type = "auto"
        
        # Create and start worker thread
        self.worker = ScrapingWorker(source_type, url, output_dir, formats)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.scraping_finished)
        self.worker.start()
        
        # Show progress dialog
        self.show_progress_dialog()
    
    def show_progress_dialog(self):
        """Show progress dialog for scraping task."""
        self.progress_dialog = QMessageBox(self)
        self.progress_dialog.setWindowTitle("Scraping in Progress")
        self.progress_dialog.setText("Initializing scraper...")
        self.progress_dialog.setStandardButtons(QMessageBox.Cancel)
        self.progress_dialog.buttonClicked.connect(self.cancel_scraping)
        self.progress_dialog.show()
    
    def update_progress(self, message, progress):
        """Update progress dialog."""
        if hasattr(self, 'progress_dialog') and self.progress_dialog.isVisible():
            self.progress_dialog.setText(message)
    
    def cancel_scraping(self):
        """Cancel the scraping process."""
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.terminate()
            self.status_bar.showMessage("Scraping cancelled")
    
    def scraping_finished(self, result, success):
        """Handle scraping completion."""
        if hasattr(self, 'progress_dialog') and self.progress_dialog.isVisible():
            self.progress_dialog.close()
        
        if success:
            QMessageBox.information(self, "Scraping Complete", "Scraping task completed successfully.")
            self.status_bar.showMessage("Scraping completed successfully")
            
            # Add to history
            self.add_to_history(result)
            
            # Update dashboard metrics
            self.update_metrics()
        else:
            error_message = result.get("error", "Unknown error")
            QMessageBox.critical(self, "Scraping Failed", f"Scraping task failed: {error_message}")
            self.status_bar.showMessage(f"Scraping failed: {error_message}")
    
    def add_to_history(self, result):
        """Add scraping result to history."""
        # Add to history data structure
        if not hasattr(self, 'history_data'):
            self.history_data = []
        
        self.history_data.append(result)
        
        # Save history to file
        self.save_history()
        
        # Update history table
        self.update_history_table()
        
        # Update recent activity in dashboard
        self.update_activity_list()
    
    def update_history_table(self):
        """Update the history table with current data."""
        if not hasattr(self, 'history_data'):
            return
        
        self.history_table.setRowCount(0)
        
        for i, item in enumerate(reversed(self.history_data)):
            self.history_table.insertRow(i)
            
            # Type
            type_item = QTableWidgetItem(item.get("type", "Unknown"))
            self.history_table.setItem(i, 0, type_item)
            
            # URL
            url_item = QTableWidgetItem(item.get("url", ""))
            self.history_table.setItem(i, 1, url_item)
            
            # Time
            timestamp = item.get("timestamp", "")
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    time_str = timestamp
            else:
                time_str = ""
            
            time_item = QTableWidgetItem(time_str)
            self.history_table.setItem(i, 2, time_item)
            
            # Formats
            formats = item.get("formats", [])
            formats_str = ", ".join(formats)
            formats_item = QTableWidgetItem(formats_str)
            self.history_table.setItem(i, 3, formats_item)
            
            # Status
            status_item = QTableWidgetItem("Success")
            status_item.setForeground(QColor(SUCCESS_COLOR))
            self.history_table.setItem(i, 4, status_item)
    
    def update_activity_list(self):
        """Update the recent activity list in dashboard."""
        if not hasattr(self, 'history_data') or not hasattr(self, 'activity_list'):
            return
        
        self.activity_list.setRowCount(0)
        
        # Show only the 5 most recent items
        recent_items = self.history_data[-5:] if len(self.history_data) > 5 else self.history_data
        
        for i, item in enumerate(reversed(recent_items)):
            self.activity_list.insertRow(i)
            
            # Type
            type_item = QTableWidgetItem(item.get("type", "Unknown"))
            self.activity_list.setItem(i, 0, type_item)
            
            # URL
            url_item = QTableWidgetItem(item.get("url", ""))
            self.activity_list.setItem(i, 1, url_item)
            
            # Time
            timestamp = item.get("timestamp", "")
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    time_str = timestamp
            else:
                time_str = ""
            
            time_item = QTableWidgetItem(time_str)
            self.activity_list.setItem(i, 2, time_item)
            
            # Status
            status_item = QTableWidgetItem("Success")
            status_item.setForeground(QColor(SUCCESS_COLOR))
            self.activity_list.setItem(i, 3, status_item)
    
    def update_metrics(self):
        """Update dashboard metrics based on history."""
        if not hasattr(self, 'history_data'):
            return
        
        # Count metrics
        total_scrapes = len(self.history_data)
        
        # Count files
        files_generated = 0
        for item in self.history_data:
            formats = item.get("formats", [])
            files_generated += len(formats)
        
        # Estimate data processed (placeholder)
        data_processed = total_scrapes * 0.5  # Rough estimate: 0.5 MB per scrape
        
        # Success rate (placeholder)
        success_rate = 100  # Assuming all successful for now
        
        # Update UI elements (placeholder)
        # In a real implementation, we would update the actual metric cards
        self.status_bar.showMessage(f"Metrics updated: {total_scrapes} scrapes, {files_generated} files, {data_processed:.1f} MB, {success_rate}% success")
    
    def save_template(self):
        """Save current scraping configuration as a template."""
        url = self.url_input.text()
        output_dir = self.output_dir.text()
        
        if not url and not output_dir:
            QMessageBox.warning(self, "Template Error", "Please enter at least a URL or output directory to save as template.")
            return
        
        # Get selected formats
        formats = []
        if self.json_checkbox.isChecked():
            formats.append("json")
        if self.csv_checkbox.isChecked():
            formats.append("csv")
        if self.txt_checkbox.isChecked():
            formats.append("txt")
        if self.html_checkbox.isChecked():
            formats.append("html")
        if self.md_checkbox.isChecked():
            formats.append("md")
        
        # Get source type
        source_type = self.source_type.currentText().lower()
        if source_type == "auto-detect":
            source_type = "auto"
        
        # Create template
        template = {
            "url": url,
            "output_dir": output_dir,
            "formats": formats,
            "type": source_type,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save template
        if not hasattr(self, 'templates'):
            self.templates = []
        
        self.templates.append(template)
        self.save_templates()
        
        QMessageBox.information(self, "Template Saved", "Scraping configuration saved as template.")
    
    def save_template_tab(self):
        """Save current scraping configuration as a template (from tab)."""
        url = self.url_input_tab.text()
        output_dir = self.output_dir_tab.text()
        
        if not url and not output_dir:
            QMessageBox.warning(self, "Template Error", "Please enter at least a URL or output directory to save as template.")
            return
        
        # Get selected formats
        formats = []
        if self.json_checkbox_tab.isChecked():
            formats.append("json")
        if self.csv_checkbox_tab.isChecked():
            formats.append("csv")
        if self.txt_checkbox_tab.isChecked():
            formats.append("txt")
        if self.html_checkbox_tab.isChecked():
            formats.append("html")
        if self.md_checkbox_tab.isChecked():
            formats.append("md")
        
        # Get source type
        source_type = self.source_type_tab.currentText().lower()
        if source_type == "auto-detect":
            source_type = "auto"
        
        # Create template
        template = {
            "url": url,
            "output_dir": output_dir,
            "formats": formats,
            "type": source_type,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save template
        if not hasattr(self, 'templates'):
            self.templates = []
        
        self.templates.append(template)
        self.save_templates()
        
        QMessageBox.information(self, "Template Saved", "Scraping configuration saved as template.")
    
    def clear_history(self):
        """Clear scraping history."""
        reply = QMessageBox.question(
            self, "Clear History",
            "Are you sure you want to clear all scraping history?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.history_data = []
            self.save_history()
            self.update_history_table()
            self.update_activity_list()
            self.update_metrics()
            self.status_bar.showMessage("History cleared")
    
    def export_history(self):
        """Export scraping history to file."""
        if not hasattr(self, 'history_data') or not self.history_data:
            QMessageBox.warning(self, "Export Error", "No history data to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export History", "", "JSON Files (*.json);;CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            if file_path.endswith(".json"):
                with open(file_path, 'w') as f:
                    json.dump(self.history_data, f, indent=2)
            elif file_path.endswith(".csv"):
                import csv
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Type", "URL", "Time", "Formats", "Status"])
                    
                    for item in self.history_data:
                        writer.writerow([
                            item.get("type", "Unknown"),
                            item.get("url", ""),
                            item.get("timestamp", ""),
                            ", ".join(item.get("formats", [])),
                            "Success"
                        ])
            else:
                with open(file_path, 'w') as f:
                    json.dump(self.history_data, f, indent=2)
            
            QMessageBox.information(self, "Export Complete", f"History exported to {file_path}")
            self.status_bar.showMessage(f"History exported to {file_path}")
        
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export history: {str(e)}")
    
    def save_settings(self):
        """Save application settings."""
        settings = QSettings("Scrappy", "ScrappyApp")
        
        # Save general settings
        settings.setValue("default_dir", self.default_dir_input.text())
        
        # Save default formats
        settings.setValue("default_json", self.default_json.isChecked())
        settings.setValue("default_csv", self.default_csv.isChecked())
        settings.setValue("default_txt", self.default_txt.isChecked())
        settings.setValue("default_html", self.default_html.isChecked())
        settings.setValue("default_md", self.default_md.isChecked())
        
        # Save advanced settings
        settings.setValue("concurrent_tasks", self.concurrent_input.currentText())
        settings.setValue("timeout", self.timeout_input.currentText())
        settings.setValue("user_agent", self.user_agent_input.text())
        
        settings.sync()
        
        QMessageBox.information(self, "Settings Saved", "Application settings have been saved.")
        self.status_bar.showMessage("Settings saved")
    
    def load_settings(self):
        """Load application settings."""
        settings = QSettings("Scrappy", "ScrappyApp")
        
        # Load general settings
        default_dir = settings.value("default_dir", "")
        if hasattr(self, 'default_dir_input'):
            self.default_dir_input.setText(default_dir)
        
        # Load default formats
        if hasattr(self, 'default_json'):
            self.default_json.setChecked(settings.value("default_json", True, type=bool))
        if hasattr(self, 'default_csv'):
            self.default_csv.setChecked(settings.value("default_csv", False, type=bool))
        if hasattr(self, 'default_txt'):
            self.default_txt.setChecked(settings.value("default_txt", False, type=bool))
        if hasattr(self, 'default_html'):
            self.default_html.setChecked(settings.value("default_html", False, type=bool))
        if hasattr(self, 'default_md'):
            self.default_md.setChecked(settings.value("default_md", False, type=bool))
        
        # Load advanced settings
        concurrent_tasks = settings.value("concurrent_tasks", "1")
        if hasattr(self, 'concurrent_input'):
            index = self.concurrent_input.findText(concurrent_tasks)
            if index >= 0:
                self.concurrent_input.setCurrentIndex(index)
        
        timeout = settings.value("timeout", "30")
        if hasattr(self, 'timeout_input'):
            index = self.timeout_input.findText(timeout)
            if index >= 0:
                self.timeout_input.setCurrentIndex(index)
        
        user_agent = settings.value("user_agent", "Scrappy/1.0 (+https://github.com/k3ss-official/scrappy_v2)")
        if hasattr(self, 'user_agent_input'):
            self.user_agent_input.setText(user_agent)
    
    def save_history(self):
        """Save scraping history to file."""
        if not hasattr(self, 'history_data'):
            return
        
        try:
            history_dir = os.path.join(os.path.expanduser("~"), ".scrappy")
            os.makedirs(history_dir, exist_ok=True)
            
            history_file = os.path.join(history_dir, "history.json")
            
            with open(history_file, 'w') as f:
                json.dump(self.history_data, f, indent=2)
        
        except Exception as e:
            logger.error(f"Failed to save history: {str(e)}")
    
    def load_history(self):
        """Load scraping history from file."""
        try:
            history_file = os.path.join(os.path.expanduser("~"), ".scrappy", "history.json")
            
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    self.history_data = json.load(f)
                
                # Update UI
                self.update_history_table()
                self.update_activity_list()
                self.update_metrics()
            else:
                self.history_data = []
        
        except Exception as e:
            logger.error(f"Failed to load history: {str(e)}")
            self.history_data = []
    
    def save_templates(self):
        """Save templates to file."""
        if not hasattr(self, 'templates'):
            return
        
        try:
            templates_dir = os.path.join(os.path.expanduser("~"), ".scrappy")
            os.makedirs(templates_dir, exist_ok=True)
            
            templates_file = os.path.join(templates_dir, "templates.json")
            
            with open(templates_file, 'w') as f:
                json.dump(self.templates, f, indent=2)
        
        except Exception as e:
            logger.error(f"Failed to save templates: {str(e)}")
    
    def load_templates(self):
        """Load templates from file."""
        try:
            templates_file = os.path.join(os.path.expanduser("~"), ".scrappy", "templates.json")
            
            if os.path.exists(templates_file):
                with open(templates_file, 'r') as f:
                    self.templates = json.load(f)
            else:
                self.templates = []
        
        except Exception as e:
            logger.error(f"Failed to load templates: {str(e)}")
            self.templates = []
    
    def check_dependencies(self):
        """Check if all required dependencies are installed."""
        missing_deps = self.setup_manager.check_dependencies()
        
        if missing_deps:
            reply = QMessageBox.question(
                self, "Missing Dependencies",
                f"The following dependencies are missing: {', '.join(missing_deps)}\n\nWould you like to install them now?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.install_dependencies(missing_deps)
    
    def install_dependencies(self, dependencies):
        """Install missing dependencies."""
        # Show progress dialog
        progress_dialog = QMessageBox(self)
        progress_dialog.setWindowTitle("Installing Dependencies")
        progress_dialog.setText("Installing dependencies, please wait...")
        progress_dialog.setStandardButtons(QMessageBox.NoButton)
        progress_dialog.show()
        
        # Install dependencies
        try:
            self.setup_manager.install_dependencies(dependencies)
            progress_dialog.close()
            QMessageBox.information(self, "Installation Complete", "Dependencies installed successfully.")
        except Exception as e:
            progress_dialog.close()
            QMessageBox.critical(self, "Installation Failed", f"Failed to install dependencies: {str(e)}")
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Minimize to tray instead of closing
        if self.tray_icon.isVisible():
            QMessageBox.information(self, "Scrappy", "Scrappy will continue running in the system tray.")
            self.hide()
            event.ignore()
        else:
            event.accept()


def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for better dark theme support
    
    window = ScrappyDesktopApp()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
