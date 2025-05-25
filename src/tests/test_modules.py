"""
Test Module for Scrappy

This module provides testing utilities for verifying the functionality
of the Scrappy application and its components.
"""

import os
import sys
import json
import logging
import unittest
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('scrappy.tests')

# Import Scrappy modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import Scrappy
from src.scrapers.github.crawler import GitHubScraper
from src.scrapers.website.crawler import WebsiteScraper
from src.scrapers.youtube.crawler import YouTubeScraper
from src.storage.handler import StorageHandler
from src.formatters.converter import FormatConverter
from src.utils.security import SecurityManager

class TestGitHubScraper(unittest.TestCase):
    """
    Test cases for the GitHub scraper.
    """
    
    def setUp(self):
        """
        Set up test environment.
        """
        self.test_dir = os.path.join(os.getcwd(), 'test_data')
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Test repository URL
        self.repo_url = "https://github.com/k3ss-official/scrappy_v2"
        
        # Initialize scraper
        self.scraper = GitHubScraper(self.repo_url, self.test_dir)
    
    def tearDown(self):
        """
        Clean up test environment.
        """
        # Remove test directory
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_extract_repo_info(self):
        """
        Test extraction of repository owner and name.
        """
        owner, name = self.scraper._extract_repo_info(self.repo_url)
        self.assertEqual(owner, "k3ss-official")
        self.assertEqual(name, "scrappy_v2")
    
    def test_crawl_repo_metadata(self):
        """
        Test crawling of repository metadata.
        """
        # Mock the crawler for testing
        self.scraper.crawler.crawl = lambda url: MockCrawlResult(
            title="scrappy_v2",
            description="Universal Scraping and Delivery System",
            text="This is a test repository",
            metadata={"stars": 10, "forks": 5}
        )
        
        # Crawl metadata
        metadata = self.scraper.crawl_repo_metadata()
        
        # Verify metadata
        self.assertEqual(metadata['owner'], "k3ss-official")
        self.assertEqual(metadata['name'], "scrappy_v2")
        self.assertEqual(metadata['title'], "scrappy_v2")
        self.assertEqual(metadata['description'], "Universal Scraping and Delivery System")
        self.assertIn('crawl_date', metadata)

class TestWebsiteScraper(unittest.TestCase):
    """
    Test cases for the website scraper.
    """
    
    def setUp(self):
        """
        Set up test environment.
        """
        self.test_dir = os.path.join(os.getcwd(), 'test_data')
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Test website URL
        self.website_url = "https://example.com"
        
        # Initialize scraper
        self.scraper = WebsiteScraper(self.website_url, self.test_dir)
    
    def tearDown(self):
        """
        Clean up test environment.
        """
        # Remove test directory
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_extract_domain(self):
        """
        Test extraction of domain from URL.
        """
        domain = self.scraper._extract_domain(self.website_url)
        self.assertEqual(domain, "example.com")
        
        # Test with www prefix
        domain = self.scraper._extract_domain("https://www.example.com")
        self.assertEqual(domain, "example.com")
    
    def test_sanitize_url_to_filename(self):
        """
        Test sanitization of URL to filename.
        """
        filename = self.scraper._sanitize_url_to_filename("https://example.com/path/to/page")
        self.assertEqual(filename, "path_to_page")
        
        # Test with query parameters
        filename = self.scraper._sanitize_url_to_filename("https://example.com/search?q=test&page=1")
        self.assertEqual(filename, "search_q_test_page_1")
        
        # Test with empty path
        filename = self.scraper._sanitize_url_to_filename("https://example.com")
        self.assertEqual(filename, "index")

class TestYouTubeScraper(unittest.TestCase):
    """
    Test cases for the YouTube scraper.
    """
    
    def setUp(self):
        """
        Set up test environment.
        """
        self.test_dir = os.path.join(os.getcwd(), 'test_data')
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Test channel URL
        self.channel_url = "https://www.youtube.com/@ManuAGI"
        
        # Initialize scraper
        self.scraper = YouTubeScraper(self.channel_url, self.test_dir)
    
    def tearDown(self):
        """
        Clean up test environment.
        """
        # Remove test directory
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_extract_channel_handle(self):
        """
        Test extraction of channel handle from URL.
        """
        handle = self.scraper._extract_channel_handle(self.channel_url)
        self.assertEqual(handle, "ManuAGI")
        
        # Test with channel ID
        handle = self.scraper._extract_channel_handle("https://www.youtube.com/channel/UC1234567890")
        self.assertEqual(handle, "UC1234567890")
    
    def test_extract_video_id(self):
        """
        Test extraction of video ID from URL.
        """
        # Test youtube.com/watch format
        video_id = self.scraper.extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        self.assertEqual(video_id, "dQw4w9WgXcQ")
        
        # Test youtu.be format
        video_id = self.scraper.extract_video_id("https://youtu.be/dQw4w9WgXcQ")
        self.assertEqual(video_id, "dQw4w9WgXcQ")
        
        # Test invalid URL
        video_id = self.scraper.extract_video_id("https://example.com")
        self.assertIsNone(video_id)

class TestStorageHandler(unittest.TestCase):
    """
    Test cases for the storage handler.
    """
    
    def setUp(self):
        """
        Set up test environment.
        """
        self.test_dir = os.path.join(os.getcwd(), 'test_data')
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Initialize storage handler
        self.storage = StorageHandler(self.test_dir)
    
    def tearDown(self):
        """
        Clean up test environment.
        """
        # Remove test directory
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_save_and_load_data(self):
        """
        Test saving and loading data.
        """
        # Test data
        test_data = {
            'name': 'Test Data',
            'value': 42,
            'nested': {
                'key': 'value'
            }
        }
        
        # Save data
        self.storage.save_data('github', 'test_repo', test_data)
        
        # Load data
        loaded_data = self.storage.load_data('github', 'test_repo')
        
        # Verify data
        self.assertEqual(loaded_data['name'], test_data['name'])
        self.assertEqual(loaded_data['value'], test_data['value'])
        self.assertEqual(loaded_data['nested']['key'], test_data['nested']['key'])
        self.assertIn('saved_at', loaded_data)
    
    def test_list_saved_data(self):
        """
        Test listing saved data.
        """
        # Save test data
        self.storage.save_data('github', 'test_repo_1', {'name': 'Test Repo 1'})
        self.storage.save_data('github', 'test_repo_2', {'name': 'Test Repo 2'})
        self.storage.save_data('website', 'test_site', {'name': 'Test Site'})
        
        # List all data
        all_data = self.storage.list_saved_data()
        self.assertEqual(len(all_data), 3)
        
        # List github data
        github_data = self.storage.list_saved_data('github')
        self.assertEqual(len(github_data), 2)
        
        # List website data
        website_data = self.storage.list_saved_data('website')
        self.assertEqual(len(website_data), 1)
    
    def test_delete_data(self):
        """
        Test deleting data.
        """
        # Save test data
        self.storage.save_data('github', 'test_repo', {'name': 'Test Repo'})
        
        # Verify data exists
        self.assertTrue(self.storage.load_data('github', 'test_repo') is not None)
        
        # Delete data
        self.storage.delete_data('github', 'test_repo')
        
        # Verify data is deleted
        self.assertTrue(self.storage.load_data('github', 'test_repo') is None)

class TestFormatConverter(unittest.TestCase):
    """
    Test cases for the format converter.
    """
    
    def setUp(self):
        """
        Set up test environment.
        """
        self.test_dir = os.path.join(os.getcwd(), 'test_data')
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Initialize format converter
        self.converter = FormatConverter(self.test_dir)
        
        # Test data
        self.test_data = {
            'name': 'Test Data',
            'value': 42,
            'list': [1, 2, 3],
            'nested': {
                'key': 'value'
            }
        }
    
    def tearDown(self):
        """
        Clean up test environment.
        """
        # Remove test directory
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_convert_to_json(self):
        """
        Test conversion to JSON format.
        """
        # Convert to JSON
        json_path = self.converter._convert_to_json(self.test_data, 'test')
        
        # Verify file exists
        self.assertTrue(os.path.exists(json_path))
        
        # Verify content
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertEqual(data['name'], self.test_data['name'])
        self.assertEqual(data['value'], self.test_data['value'])
        self.assertEqual(data['list'], self.test_data['list'])
        self.assertEqual(data['nested']['key'], self.test_data['nested']['key'])
    
    def test_convert_to_multiple_formats(self):
        """
        Test conversion to multiple formats.
        """
        # Convert to multiple formats
        formats = ['json', 'csv', 'txt', 'yaml', 'xml']
        results = self.converter.convert(self.test_data, formats, 'test_multi')
        
        # Verify all formats are converted
        for fmt in formats:
            self.assertIn(fmt, results)
            self.assertTrue(os.path.exists(results[fmt]))

class TestSecurityManager(unittest.TestCase):
    """
    Test cases for the security manager.
    """
    
    def setUp(self):
        """
        Set up test environment.
        """
        # Initialize security manager
        self.security = SecurityManager()
    
    def test_validate_url(self):
        """
        Test URL validation.
        """
        # Valid URLs
        self.assertTrue(self.security.validate_url("https://example.com"))
        self.assertTrue(self.security.validate_url("http://example.com/path/to/page"))
        
        # Invalid URLs
        self.assertFalse(self.security.validate_url("ftp://example.com"))
        self.assertFalse(self.security.validate_url("not a url"))
    
    def test_sanitize_input(self):
        """
        Test input sanitization.
        """
        # Test HTML escaping
        sanitized = self.security.sanitize_input("<script>alert('XSS')</script>")
        self.assertEqual(sanitized, "&lt;script&gt;alert('XSS')&lt;/script&gt;")
        
        # Test dangerous pattern removal
        sanitized = self.security.sanitize_input("javascript:alert('XSS')")
        self.assertEqual(sanitized, ":alert('XSS')")
    
    def test_secure_filename(self):
        """
        Test filename security.
        """
        # Test path traversal prevention
        secure = self.security.secure_filename("../../../etc/passwd")
        self.assertEqual(secure, "etc_passwd")
        
        # Test character sanitization
        secure = self.security.secure_filename("file name with spaces.txt")
        self.assertEqual(secure, "file_name_with_spaces.txt")

class MockCrawlResult:
    """
    Mock crawl result for testing.
    """
    
    def __init__(self, title=None, description=None, text=None, html=None, links=None, images=None, metadata=None):
        self.title = title
        self.description = description
        self.text = text
        self.html = html
        self.links = links or []
        self.images = images or []
        self.metadata = metadata or {}
    
    def get_title(self):
        return self.title
    
    def get_description(self):
        return self.description
    
    def get_text(self):
        return self.text
    
    def get_html(self):
        return self.html
    
    def get_links(self, filter_by=None):
        if filter_by:
            return [link for link in self.links if filter_by(link)]
        return self.links
    
    def get_images(self):
        return self.images
    
    def get_metadata(self):
        return self.metadata

def run_tests():
    """
    Run all tests.
    """
    logger.info("Running Scrappy tests...")
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestGitHubScraper))
    suite.addTest(unittest.makeSuite(TestWebsiteScraper))
    suite.addTest(unittest.makeSuite(TestYouTubeScraper))
    suite.addTest(unittest.makeSuite(TestStorageHandler))
    suite.addTest(unittest.makeSuite(TestFormatConverter))
    suite.addTest(unittest.makeSuite(TestSecurityManager))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success status
    return result.wasSuccessful()

if __name__ == '__main__':
    run_tests()
