"""
Website Scraper Module for Scrappy

This module handles the crawling and extraction of website content
using crawl4ai as the primary scraping engine.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from urllib.parse import urlparse

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('scrappy.scrapers.website')

class WebsiteScraper:
    """
    Scraper for websites using crawl4ai.
    """
    
    def __init__(self, website_url: str, output_dir: str, depth: int = 1):
        """
        Initialize the website scraper.
        
        Args:
            website_url: URL of the website to scrape
            output_dir: Directory to save scraped data
            depth: Crawling depth (default: 1, just the provided URL)
        """
        self.website_url = website_url
        self.output_dir = output_dir
        self.depth = depth
        
        # Extract domain from URL
        self.domain = self._extract_domain(website_url)
        
        # Create website directory
        self.website_dir = os.path.join(output_dir, f"website_{self.domain}")
        os.makedirs(self.website_dir, exist_ok=True)
        os.makedirs(os.path.join(self.website_dir, 'pages'), exist_ok=True)
        os.makedirs(os.path.join(self.website_dir, 'assets'), exist_ok=True)
        
        # Initialize crawl4ai
        try:
            from crawl4ai import Crawler
            self.crawler = Crawler()
            logger.info(f"Initialized crawl4ai for website: {self.domain}")
        except ImportError:
            logger.error("crawl4ai not installed. Please install it to use the website scraper.")
            raise
    
    def _extract_domain(self, url: str) -> str:
        """
        Extract domain from URL.
        
        Args:
            url: Website URL
            
        Returns:
            Domain name
        """
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
            
        return domain
    
    def _sanitize_url_to_filename(self, url: str) -> str:
        """
        Convert URL to a valid filename.
        
        Args:
            url: URL to convert
            
        Returns:
            Sanitized filename
        """
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        # Remove leading and trailing slashes
        path = path.strip('/')
        
        # Replace slashes with underscores
        path = path.replace('/', '_')
        
        # If path is empty, use 'index'
        if not path:
            path = 'index'
            
        # Add query parameters if present
        if parsed_url.query:
            path += '_' + parsed_url.query.replace('&', '_').replace('=', '_')
            
        return path
    
    def crawl_page(self, url: str) -> Dict[str, Any]:
        """
        Crawl a single page.
        
        Args:
            url: URL to crawl
            
        Returns:
            Dictionary containing page data
        """
        logger.info(f"Crawling page: {url}")
        
        # Use crawl4ai to extract page content
        result = self.crawler.crawl(url)
        
        # Generate filename from URL
        filename = self._sanitize_url_to_filename(url)
        
        # Extract page content
        page_data = {
            'url': url,
            'title': result.get_title() or url,
            'description': result.get_description() or '',
            'text': result.get_text() or '',
            'html': result.get_html() or '',
            'links': result.get_links() or [],
            'images': result.get_images() or [],
            'metadata': result.get_metadata() or {},
            'crawl_date': datetime.now().isoformat()
        }
        
        # Save page data
        page_path = os.path.join(self.website_dir, 'pages', f"{filename}.json")
        with open(page_path, 'w', encoding='utf-8') as f:
            json.dump(page_data, f, ensure_ascii=False, indent=2)
        
        # Save HTML content separately
        html_path = os.path.join(self.website_dir, 'pages', f"{filename}.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(page_data['html'])
        
        logger.info(f"Page data saved to {page_path}")
        return page_data
    
    def extract_asset_urls(self, page_data: Dict[str, Any]) -> List[str]:
        """
        Extract asset URLs (images, CSS, JS) from page data.
        
        Args:
            page_data: Page data dictionary
            
        Returns:
            List of asset URLs
        """
        asset_urls = []
        
        # Extract image URLs
        asset_urls.extend(page_data.get('images', []))
        
        # Extract CSS and JS URLs from HTML
        # This is a simplified approach - in a real implementation,
        # we would parse the HTML and extract all asset URLs
        html = page_data.get('html', '')
        
        # Simple regex-like extraction for demonstration
        for asset_type in ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg']:
            start_idx = 0
            while True:
                idx = html.find(asset_type, start_idx)
                if idx == -1:
                    break
                    
                # Find the URL around this asset
                url_start = html.rfind('http', start_idx, idx)
                if url_start != -1:
                    url_end = html.find('"', url_start)
                    if url_end != -1:
                        asset_url = html[url_start:url_end]
                        asset_urls.append(asset_url)
                
                start_idx = idx + len(asset_type)
        
        return list(set(asset_urls))  # Remove duplicates
    
    def download_asset(self, asset_url: str) -> bool:
        """
        Download an asset from URL.
        
        Args:
            asset_url: URL of the asset to download
            
        Returns:
            True if download was successful, False otherwise
        """
        try:
            import requests
            from urllib.parse import urlparse
            
            logger.info(f"Downloading asset: {asset_url}")
            
            # Generate filename from URL
            parsed_url = urlparse(asset_url)
            filename = os.path.basename(parsed_url.path)
            
            # If filename is empty or invalid, generate a hash-based name
            if not filename or '.' not in filename:
                import hashlib
                filename = hashlib.md5(asset_url.encode()).hexdigest()
                
                # Try to determine file extension from URL
                if '.css' in asset_url:
                    filename += '.css'
                elif '.js' in asset_url:
                    filename += '.js'
                elif any(ext in asset_url.lower() for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg']):
                    for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg']:
                        if ext in asset_url.lower():
                            filename += ext
                            break
                else:
                    filename += '.bin'  # Generic binary file
            
            # Download the asset
            response = requests.get(asset_url, stream=True, timeout=10)
            response.raise_for_status()
            
            # Save the asset
            asset_path = os.path.join(self.website_dir, 'assets', filename)
            with open(asset_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Asset saved to {asset_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading asset {asset_url}: {str(e)}")
            return False
    
    def crawl_website(self) -> Dict[str, Any]:
        """
        Crawl the website starting from the initial URL.
        
        Returns:
            Dictionary with website data
        """
        logger.info(f"Starting crawl of website: {self.website_url}")
        
        # Crawl the initial page
        initial_page_data = self.crawl_page(self.website_url)
        
        # Extract links from the initial page
        links = initial_page_data.get('links', [])
        
        # Filter links to only include those from the same domain
        same_domain_links = [
            link for link in links 
            if self.domain in link and link != self.website_url
        ]
        
        # Limit the number of links to crawl based on depth
        links_to_crawl = same_domain_links[:min(len(same_domain_links), self.depth * 10)]
        
        # Crawl additional pages if depth > 1
        crawled_pages = [initial_page_data]
        if self.depth > 1:
            for link in links_to_crawl:
                page_data = self.crawl_page(link)
                crawled_pages.append(page_data)
        
        # Extract and download assets
        all_assets = []
        for page_data in crawled_pages:
            assets = self.extract_asset_urls(page_data)
            all_assets.extend(assets)
        
        # Remove duplicates
        unique_assets = list(set(all_assets))
        
        # Download assets
        downloaded_assets = []
        for asset_url in unique_assets:
            if self.download_asset(asset_url):
                downloaded_assets.append(asset_url)
        
        # Create website summary
        website_data = {
            'domain': self.domain,
            'url': self.website_url,
            'pages_crawled': len(crawled_pages),
            'assets_downloaded': len(downloaded_assets),
            'crawl_date': datetime.now().isoformat(),
            'page_urls': [page['url'] for page in crawled_pages],
            'asset_urls': downloaded_assets
        }
        
        # Save website summary
        summary_path = os.path.join(self.website_dir, 'website_summary.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(website_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Website crawl completed, summary saved to {summary_path}")
        return website_data
