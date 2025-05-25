"""
Main module for Scrappy - Universal Scraping and Delivery System

This module serves as the entry point for the Scrappy application,
integrating all components and providing the main functionality.
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, List, Any, Optional
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scrappy.log')
    ]
)
logger = logging.getLogger('scrappy')

# Import scraper modules
from src.scrapers.github.crawler import GitHubScraper
from src.scrapers.website.crawler import WebsiteScraper
from src.scrapers.youtube.crawler import YouTubeScraper

# Import storage handler
from src.storage.handler import StorageHandler

# Import format converter
from src.formatters.converter import FormatConverter

class Scrappy:
    """
    Main class for the Scrappy application.
    """
    
    def __init__(self, base_dir: str = None):
        """
        Initialize the Scrappy application.
        
        Args:
            base_dir: Base directory for storing data (default: current directory)
        """
        # Set base directory
        if base_dir is None:
            self.base_dir = os.path.join(os.getcwd(), 'scrappy_data')
        else:
            self.base_dir = base_dir
        
        # Create base directory if it doesn't exist
        os.makedirs(self.base_dir, exist_ok=True)
        
        # Initialize storage handler
        self.storage = StorageHandler(os.path.join(self.base_dir, 'storage'))
        
        # Initialize format converter
        self.converter = FormatConverter(os.path.join(self.base_dir, 'output'))
        
        logger.info(f"Initialized Scrappy with base directory: {self.base_dir}")
    
    def scrape_github(self, repo_url: str, output_formats: List[str] = None) -> Dict[str, Any]:
        """
        Scrape a GitHub repository.
        
        Args:
            repo_url: URL of the GitHub repository to scrape
            output_formats: List of output formats (default: ['json'])
            
        Returns:
            Dictionary with scraping results and output file paths
        """
        if output_formats is None:
            output_formats = ['json']
        
        logger.info(f"Scraping GitHub repository: {repo_url}")
        
        # Extract repository owner and name for identifier
        scraper = GitHubScraper(repo_url, os.path.join(self.base_dir, 'temp'))
        repo_owner, repo_name = scraper._extract_repo_info(repo_url)
        identifier = f"{repo_owner}_{repo_name}"
        
        # Scrape repository
        repo_data = scraper.crawl_repository()
        
        # Save data to storage
        self.storage.save_data('github', identifier, repo_data)
        
        # Convert to requested formats
        output_files = self.converter.convert(repo_data, output_formats, f"github_{identifier}")
        
        # Return results
        return {
            'scraper_type': 'github',
            'identifier': identifier,
            'data': repo_data,
            'output_files': output_files
        }
    
    def scrape_website(self, website_url: str, depth: int = 1, output_formats: List[str] = None) -> Dict[str, Any]:
        """
        Scrape a website.
        
        Args:
            website_url: URL of the website to scrape
            depth: Crawling depth (default: 1)
            output_formats: List of output formats (default: ['json'])
            
        Returns:
            Dictionary with scraping results and output file paths
        """
        if output_formats is None:
            output_formats = ['json']
        
        logger.info(f"Scraping website: {website_url} with depth {depth}")
        
        # Extract domain for identifier
        scraper = WebsiteScraper(website_url, os.path.join(self.base_dir, 'temp'), depth)
        domain = scraper._extract_domain(website_url)
        identifier = domain
        
        # Scrape website
        website_data = scraper.crawl_website()
        
        # Save data to storage
        self.storage.save_data('website', identifier, website_data)
        
        # Convert to requested formats
        output_files = self.converter.convert(website_data, output_formats, f"website_{identifier}")
        
        # Return results
        return {
            'scraper_type': 'website',
            'identifier': identifier,
            'data': website_data,
            'output_files': output_files
        }
    
    def scrape_youtube(self, channel_url: str, output_formats: List[str] = None) -> Dict[str, Any]:
        """
        Scrape a YouTube channel.
        
        Args:
            channel_url: URL of the YouTube channel to scrape
            output_formats: List of output formats (default: ['json'])
            
        Returns:
            Dictionary with scraping results and output file paths
        """
        if output_formats is None:
            output_formats = ['json']
        
        logger.info(f"Scraping YouTube channel: {channel_url}")
        
        # Extract channel handle for identifier
        scraper = YouTubeScraper(channel_url, os.path.join(self.base_dir, 'temp'))
        channel_handle = scraper._extract_channel_handle(channel_url)
        identifier = channel_handle
        
        # Scrape channel
        channel_data = scraper.crawl_channel()
        
        # Save data to storage
        self.storage.save_data('youtube', identifier, channel_data)
        
        # Convert to requested formats
        output_files = self.converter.convert(channel_data, output_formats, f"youtube_{identifier}")
        
        # Return results
        return {
            'scraper_type': 'youtube',
            'identifier': identifier,
            'data': channel_data,
            'output_files': output_files
        }
    
    def list_saved_data(self, scraper_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all saved data.
        
        Args:
            scraper_type: Optional filter by scraper type
            
        Returns:
            List of saved data information
        """
        return self.storage.list_saved_data(scraper_type)
    
    def load_data(self, scraper_type: str, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Load data from storage.
        
        Args:
            scraper_type: Type of scraper ('github', 'website', or 'youtube')
            identifier: Unique identifier for the scraped content
            
        Returns:
            Loaded data or None if not found
        """
        return self.storage.load_data(scraper_type, identifier)
    
    def delete_data(self, scraper_type: str, identifier: str) -> bool:
        """
        Delete data from storage.
        
        Args:
            scraper_type: Type of scraper ('github', 'website', or 'youtube')
            identifier: Unique identifier for the scraped content
            
        Returns:
            True if deletion was successful, False otherwise
        """
        return self.storage.delete_data(scraper_type, identifier)

def main():
    """
    Main function for command-line interface.
    """
    parser = argparse.ArgumentParser(description='Scrappy - Universal Scraping and Delivery System')
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # GitHub scraper command
    github_parser = subparsers.add_parser('github', help='Scrape a GitHub repository')
    github_parser.add_argument('url', help='URL of the GitHub repository to scrape')
    github_parser.add_argument('--output-dir', help='Output directory for scraped data')
    github_parser.add_argument('--formats', nargs='+', default=['json'], 
                              choices=['json', 'csv', 'txt', 'yaml', 'xml'],
                              help='Output formats (default: json)')
    
    # Website scraper command
    website_parser = subparsers.add_parser('website', help='Scrape a website')
    website_parser.add_argument('url', help='URL of the website to scrape')
    website_parser.add_argument('--depth', type=int, default=1, help='Crawling depth (default: 1)')
    website_parser.add_argument('--output-dir', help='Output directory for scraped data')
    website_parser.add_argument('--formats', nargs='+', default=['json'], 
                               choices=['json', 'csv', 'txt', 'yaml', 'xml'],
                               help='Output formats (default: json)')
    
    # YouTube scraper command
    youtube_parser = subparsers.add_parser('youtube', help='Scrape a YouTube channel')
    youtube_parser.add_argument('url', help='URL of the YouTube channel to scrape')
    youtube_parser.add_argument('--output-dir', help='Output directory for scraped data')
    youtube_parser.add_argument('--formats', nargs='+', default=['json'], 
                               choices=['json', 'csv', 'txt', 'yaml', 'xml'],
                               help='Output formats (default: json)')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List saved data')
    list_parser.add_argument('--type', choices=['github', 'website', 'youtube'],
                            help='Filter by scraper type')
    
    # Load command
    load_parser = subparsers.add_parser('load', help='Load saved data')
    load_parser.add_argument('type', choices=['github', 'website', 'youtube'],
                            help='Scraper type')
    load_parser.add_argument('identifier', help='Unique identifier for the scraped content')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete saved data')
    delete_parser.add_argument('type', choices=['github', 'website', 'youtube'],
                              help='Scraper type')
    delete_parser.add_argument('identifier', help='Unique identifier for the scraped content')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Initialize Scrappy
    scrappy = Scrappy(args.output_dir if hasattr(args, 'output_dir') and args.output_dir else None)
    
    # Execute command
    if args.command == 'github':
        result = scrappy.scrape_github(args.url, args.formats)
        print(f"GitHub repository scraped successfully: {result['identifier']}")
        print(f"Output files: {result['output_files']}")
    elif args.command == 'website':
        result = scrappy.scrape_website(args.url, args.depth, args.formats)
        print(f"Website scraped successfully: {result['identifier']}")
        print(f"Output files: {result['output_files']}")
    elif args.command == 'youtube':
        result = scrappy.scrape_youtube(args.url, args.formats)
        print(f"YouTube channel scraped successfully: {result['identifier']}")
        print(f"Output files: {result['output_files']}")
    elif args.command == 'list':
        results = scrappy.list_saved_data(args.type)
        print(f"Found {len(results)} saved data entries:")
        for result in results:
            print(f"- {result['scraper_type']}/{result['identifier']} (saved at {result['saved_at']})")
    elif args.command == 'load':
        data = scrappy.load_data(args.type, args.identifier)
        if data:
            print(f"Data loaded successfully: {args.type}/{args.identifier}")
            print(json.dumps(data, indent=2))
        else:
            print(f"Data not found: {args.type}/{args.identifier}")
    elif args.command == 'delete':
        success = scrappy.delete_data(args.type, args.identifier)
        if success:
            print(f"Data deleted successfully: {args.type}/{args.identifier}")
        else:
            print(f"Failed to delete data: {args.type}/{args.identifier}")
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
