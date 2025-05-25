"""
Crawl4AI Integration Module for Scrappy

This module handles the integration with crawl4ai, the primary scraping engine
for the Scrappy application.
"""

import os
import logging
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('scrappy.crawl4ai_integration')

class Crawl4AIManager:
    """
    Manager for crawl4ai integration and configuration.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the crawl4ai manager.
        
        Args:
            config_path: Path to crawl4ai configuration file (optional)
        """
        try:
            # Import crawl4ai
            import crawl4ai
            self.crawl4ai = crawl4ai
            
            # Load configuration if provided
            self.config = {}
            if config_path and os.path.exists(config_path):
                self._load_config(config_path)
            
            # Initialize crawler with configuration
            self.crawler = self._initialize_crawler()
            
            logger.info("Successfully initialized crawl4ai")
        except ImportError:
            logger.error("Failed to import crawl4ai. Please install it using 'pip install crawl4ai==1.0.0'")
            raise
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load crawl4ai configuration from file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        try:
            import json
            with open(config_path, 'r') as f:
                self.config = json.load(f)
            logger.info(f"Loaded crawl4ai configuration from {config_path}")
            return self.config
        except Exception as e:
            logger.error(f"Error loading crawl4ai configuration: {str(e)}")
            return {}
    
    def _initialize_crawler(self) -> Any:
        """
        Initialize crawl4ai crawler with configuration.
        
        Returns:
            Initialized crawler instance
        """
        try:
            # Apply configuration options
            crawler_options = {
                'user_agent': self.config.get('user_agent', 'Scrappy/1.0 (+https://github.com/k3ss-official/scrappy_v2)'),
                'timeout': self.config.get('timeout', 30),
                'max_retries': self.config.get('max_retries', 3),
                'follow_redirects': self.config.get('follow_redirects', True),
                'verify_ssl': self.config.get('verify_ssl', True)
            }
            
            # Initialize crawler with options
            crawler = self.crawl4ai.Crawler(**crawler_options)
            
            # Set additional options if available
            if 'headers' in self.config:
                crawler.set_headers(self.config['headers'])
            
            if 'cookies' in self.config:
                crawler.set_cookies(self.config['cookies'])
            
            if 'proxies' in self.config:
                crawler.set_proxies(self.config['proxies'])
            
            return crawler
        except Exception as e:
            logger.error(f"Error initializing crawl4ai crawler: {str(e)}")
            # Fall back to default crawler
            return self.crawl4ai.Crawler()
    
    def crawl(self, url: str, options: Optional[Dict[str, Any]] = None) -> Any:
        """
        Crawl a URL using crawl4ai.
        
        Args:
            url: URL to crawl
            options: Additional options for this specific crawl (optional)
            
        Returns:
            Crawl result
        """
        try:
            logger.info(f"Crawling URL: {url}")
            
            # Apply per-request options if provided
            if options:
                # Create a copy of the crawler with these options
                temp_crawler = self.crawl4ai.Crawler(
                    user_agent=options.get('user_agent', self.crawler.user_agent),
                    timeout=options.get('timeout', self.crawler.timeout),
                    max_retries=options.get('max_retries', self.crawler.max_retries),
                    follow_redirects=options.get('follow_redirects', self.crawler.follow_redirects),
                    verify_ssl=options.get('verify_ssl', self.crawler.verify_ssl)
                )
                
                # Set additional options if available
                if 'headers' in options:
                    temp_crawler.set_headers(options['headers'])
                
                if 'cookies' in options:
                    temp_crawler.set_cookies(options['cookies'])
                
                if 'proxies' in options:
                    temp_crawler.set_proxies(options['proxies'])
                
                result = temp_crawler.crawl(url)
            else:
                # Use the default configured crawler
                result = self.crawler.crawl(url)
            
            logger.info(f"Successfully crawled URL: {url}")
            return result
        except Exception as e:
            logger.error(f"Error crawling URL {url}: {str(e)}")
            raise
    
    def get_default_config(self) -> Dict[str, Any]:
        """
        Get default crawl4ai configuration.
        
        Returns:
            Default configuration dictionary
        """
        return {
            'user_agent': 'Scrappy/1.0 (+https://github.com/k3ss-official/scrappy_v2)',
            'timeout': 30,
            'max_retries': 3,
            'follow_redirects': True,
            'verify_ssl': True,
            'headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5'
            },
            'cookies': {},
            'proxies': {}
        }
    
    def save_default_config(self, config_path: str) -> bool:
        """
        Save default configuration to file.
        
        Args:
            config_path: Path to save configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import json
            config = self.get_default_config()
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # Save configuration
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Saved default crawl4ai configuration to {config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving default crawl4ai configuration: {str(e)}")
            return False
