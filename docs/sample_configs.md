# Sample Configurations for Scrappy

This directory contains sample configuration files for different scraper types.

## GitHub Repository Scraper

```json
{
  "scraper_type": "github",
  "url": "https://github.com/k3ss-official/scrappy_v2",
  "output_formats": ["json", "csv", "txt"],
  "output_dir": "/path/to/output",
  "options": {
    "include_issues": true,
    "include_pull_requests": true,
    "max_files": 100
  }
}
```

## Website Scraper

```json
{
  "scraper_type": "website",
  "url": "https://example.com",
  "output_formats": ["json", "html", "txt"],
  "output_dir": "/path/to/output",
  "options": {
    "depth": 2,
    "download_assets": true,
    "follow_external_links": false,
    "max_pages": 50
  }
}
```

## YouTube Channel Scraper

```json
{
  "scraper_type": "youtube",
  "url": "https://www.youtube.com/@ManuAGI",
  "output_formats": ["json", "txt", "csv"],
  "output_dir": "/path/to/output",
  "options": {
    "include_transcripts": true,
    "max_videos": 20,
    "include_comments": false,
    "analyze_content": true
  }
}
```

## Using Configuration Files

You can use these configuration files with the command-line interface:

```bash
python main.py --config /path/to/config.json
```

Or load them through the web interface by clicking the "Load Configuration" button.

## Creating Custom Configurations

1. Start with one of the sample configurations above
2. Modify the parameters to suit your needs
3. Save as a JSON file
4. Load using the CLI or web interface

## Configuration Parameters

### Common Parameters

- `scraper_type`: Type of scraper to use (`github`, `website`, or `youtube`)
- `url`: URL to scrape
- `output_formats`: List of output formats to generate
- `output_dir`: Directory to save output files

### GitHub Scraper Options

- `include_issues`: Whether to include repository issues
- `include_pull_requests`: Whether to include pull requests
- `max_files`: Maximum number of files to scrape

### Website Scraper Options

- `depth`: Crawling depth (1 = just the provided URL, 2 = URL and linked pages, etc.)
- `download_assets`: Whether to download assets (images, CSS, JS)
- `follow_external_links`: Whether to follow links to external domains
- `max_pages`: Maximum number of pages to scrape

### YouTube Scraper Options

- `include_transcripts`: Whether to include video transcripts
- `max_videos`: Maximum number of videos to scrape
- `include_comments`: Whether to include video comments
- `analyze_content`: Whether to perform content analysis
