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
            
            # Log version information
            logger.info(f"Using crawl4ai version: {crawl4ai.__version__}")
            
            # Load configuration if provided
            self.config = {}
            if config_path and os.path.exists(config_path):
                self._load_config(config_path)
            
            # Initialize crawler with configuration
            self.crawler = self._initialize_crawler()
            
            logger.info("Successfully initialized crawl4ai")
        except ImportError:
            logger.error("Failed to import crawl4ai. Please install it using 'pip install crawl4ai'")
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
            
            # Handle API changes between crawl4ai versions
            try:
                # For newer versions (0.6.x)
                crawler = self.crawl4ai.Crawler(**crawler_options)
            except TypeError:
                # For older versions with different API
                logger.info("Detected older crawl4ai version, adapting initialization parameters")
                # Adjust parameters for older versions if needed
                if 'follow_redirects' in crawler_options:
                    crawler_options['allow_redirects'] = crawler_options.pop('follow_redirects')
                crawler = self.crawl4ai.Crawler(**crawler_options)
            
            # Set additional options if available
            if 'headers' in self.config:
                try:
                    crawler.set_headers(self.config['headers'])
                except AttributeError:
                    # Handle older versions that might use a different method
                    crawler.headers.update(self.config['headers'])
            
            if 'cookies' in self.config:
                try:
                    crawler.set_cookies(self.config['cookies'])
                except AttributeError:
                    # Handle older versions
                    crawler.cookies.update(self.config['cookies'])
            
            if 'proxies' in self.config:
                try:
                    crawler.set_proxies(self.config['proxies'])
                except AttributeError:
                    # Handle older versions
                    crawler.proxies = self.config['proxies']
            
            return crawler
        except Exception as e:
            logger.error(f"Error initializing crawl4ai crawler: {str(e)}")
            # Fall back to default crawler with minimal options
            try:
                return self.crawl4ai.Crawler()
            except:
                # Last resort fallback for any version
                return self.crawl4ai.Crawler() if hasattr(self.crawl4ai, 'Crawler') else self.crawl4ai.create_crawler()
    
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
                try:
                    # For newer versions
                    temp_crawler = self.crawl4ai.Crawler(
                        user_agent=options.get('user_agent', getattr(self.crawler, 'user_agent', None)),
                        timeout=options.get('timeout', getattr(self.crawler, 'timeout', 30)),
                        max_retries=options.get('max_retries', getattr(self.crawler, 'max_retries', 3)),
                        follow_redirects=options.get('follow_redirects', getattr(self.crawler, 'follow_redirects', True)),
                        verify_ssl=options.get('verify_ssl', getattr(self.crawler, 'verify_ssl', True))
                    )
                except TypeError:
                    # For older versions
                    crawler_options = {
                        'user_agent': options.get('user_agent', getattr(self.crawler, 'user_agent', None)),
                        'timeout': options.get('timeout', getattr(self.crawler, 'timeout', 30)),
                        'max_retries': options.get('max_retries', getattr(self.crawler, 'max_retries', 3)),
                    }
                    if 'follow_redirects' in options:
                        crawler_options['allow_redirects'] = options['follow_redirects']
                    elif hasattr(self.crawler, 'allow_redirects'):
                        crawler_options['allow_redirects'] = getattr(self.crawler, 'allow_redirects', True)
                    
                    if 'verify_ssl' in options:
                        crawler_options['verify'] = options['verify_ssl']
                    elif hasattr(self.crawler, 'verify'):
                        crawler_options['verify'] = getattr(self.crawler, 'verify', True)
                    
                    temp_crawler = self.crawl4ai.Crawler(**crawler_options)
                
                # Set additional options if available
                if 'headers' in options:
                    try:
                        temp_crawler.set_headers(options['headers'])
                    except AttributeError:
                        temp_crawler.headers.update(options['headers'])
                
                if 'cookies' in options:
                    try:
                        temp_crawler.set_cookies(options['cookies'])
                    except AttributeError:
                        temp_crawler.cookies.update(options['cookies'])
                
                if 'proxies' in options:
                    try:
                        temp_crawler.set_proxies(options['proxies'])
                    except AttributeError:
                        temp_crawler.proxies = options['proxies']
                
                # Handle different crawl method signatures
                try:
                    result = temp_crawler.crawl(url)
                except TypeError:
                    # Try alternative method signatures
                    try:
                        result = temp_crawler.crawl(url=url)
                    except:
                        result = temp_crawler.fetch(url)
            else:
                # Use the default configured crawler
                try:
                    result = self.crawler.crawl(url)
                except TypeError:
                    # Try alternative method signatures
                    try:
                        result = self.crawler.crawl(url=url)
                    except:
                        result = self.crawler.fetch(url)
            
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
