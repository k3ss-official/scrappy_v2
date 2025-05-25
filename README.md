# Scrappy - Universal Scraping and Delivery System

Scrappy is a versatile data extraction tool with three core capabilities:
1. GitHub repository scraping
2. Website content scraping 
3. YouTube channel scraping (with AI-powered content analysis)

The system follows a simple "What-Where-How" workflow:
- **WHAT**: URL to scrape (GitHub repo, website, or YouTube channel)
- **WHERE**: Local folder destination
- **HOW**: Output format(s) - selectable via checkboxes for flexibility

![Scrappy Logo](src/ui/icons/scrappy_icon.png)

## Features

- **Modern Desktop GUI**: Clean, dark-themed interface with intuitive controls
- **Multiple Output Formats**: Export data in JSON, CSV, TXT, YAML, or XML formats
- **Local Storage**: All scraped data is stored locally for easy access and management
- **Multiple Interfaces**: Use the desktop GUI, web interface, or command line
- **Security-First Design**: Built with robust security practices from the ground up
- **Dependency Management**: Automated setup and dependency checking with visual interface
- **Cross-Platform**: Works on macOS, Windows, and Linux

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation Steps

1. Clone the repository:
```bash
git clone https://github.com/k3ss-official/scrappy_v2.git
cd scrappy_v2
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the setup script to configure crawl4ai:
```bash
python src/utils/setup.py
```

## Usage

### Desktop GUI

The recommended way to use Scrappy is through its desktop GUI:

```bash
python src/ui/desktop.py
```

This will open the Scrappy desktop application, where you can:
- Enter URLs to scrape
- Select source types (GitHub, Website, YouTube)
- Choose output formats
- Specify destination folders
- View and manage saved data

### Web Interface

Alternatively, you can use the web interface:

```bash
python src/ui/web.py
```

Then open your browser and navigate to `http://localhost:5000`

### Command Line Interface

For automation and scripting, Scrappy provides a command-line interface:

**GitHub Repository Scraping**:
```bash
python main.py github https://github.com/username/repository --formats json csv
```

**Website Scraping**:
```bash
python main.py website https://example.com --depth 2 --formats json txt
```

**YouTube Channel Scraping**:
```bash
python main.py youtube https://www.youtube.com/@ChannelName --formats json yaml
```

## macOS Application Bundle

For macOS users, Scrappy can be installed as a proper application bundle:

1. Run the bundling script:
```bash
python tools/build_macos_app.py
```

2. Move the resulting `Scrappy.app` to your Applications folder:
```bash
mv dist/Scrappy.app /Applications/
```

## Project Structure

```
scrappy_v2/
├── main.py                  # Main entry point for CLI
├── src/
│   ├── scrapers/            # Scraper modules
│   │   ├── github/          # GitHub repository scraper
│   │   ├── website/         # Website content scraper
│   │   └── youtube/         # YouTube channel scraper
│   ├── storage/             # Storage handling
│   ├── formatters/          # Output format conversion
│   ├── utils/               # Utility modules
│   │   ├── security.py      # Security utilities
│   │   ├── setup.py         # Dependency management
│   │   └── crawl4ai_integration.py  # crawl4ai integration
│   ├── ui/                  # User interfaces
│   │   ├── desktop.py       # Desktop GUI (PyQt5)
│   │   ├── web.py           # Web interface (Flask)
│   │   ├── icons/           # Application icons
│   │   └── templates/       # HTML templates
│   └── tests/               # Test modules
├── tools/                   # Build and deployment tools
├── docs/                    # Documentation
│   └── sample_configs.md    # Sample configuration files
└── LICENSE                  # MIT License
```

## Dependencies

- crawl4ai - Primary scraping engine
- PyQt5 - Desktop GUI framework
- flask - Web interface
- requests - HTTP requests
- pyyaml - YAML format support
- youtube_transcript_api - YouTube transcript extraction

## Security

Scrappy is built with security in mind:
- Input validation and sanitization
- URL and file path security checks
- Protection against common web vulnerabilities
- Secure headers for web interface
- Rate limiting to prevent abuse

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- crawl4ai for providing the core scraping engine
- YouTube Transcript API for transcript extraction capabilities
