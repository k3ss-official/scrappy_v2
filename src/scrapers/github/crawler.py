"""
GitHub Scraper Module for Scrappy

This module handles the crawling and extraction of GitHub repository content
using crawl4ai as the primary scraping engine.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('scrappy.scrapers.github')

class GitHubScraper:
    """
    Scraper for GitHub repositories using crawl4ai.
    """
    
    def __init__(self, repo_url: str, output_dir: str):
        """
        Initialize the GitHub scraper.
        
        Args:
            repo_url: URL of the GitHub repository to scrape
            output_dir: Directory to save scraped data
        """
        self.repo_url = repo_url
        self.output_dir = output_dir
        
        # Extract repo owner and name from URL
        self.repo_owner, self.repo_name = self._extract_repo_info(repo_url)
        
        # Create repo directory
        self.repo_dir = os.path.join(output_dir, f"github_{self.repo_owner}_{self.repo_name}")
        os.makedirs(self.repo_dir, exist_ok=True)
        os.makedirs(os.path.join(self.repo_dir, 'files'), exist_ok=True)
        os.makedirs(os.path.join(self.repo_dir, 'issues'), exist_ok=True)
        
        # Initialize crawl4ai
        try:
            from crawl4ai import Crawler
            self.crawler = Crawler()
            logger.info(f"Initialized crawl4ai for GitHub repository: {self.repo_owner}/{self.repo_name}")
        except ImportError:
            logger.error("crawl4ai not installed. Please install it to use the GitHub scraper.")
            raise
    
    def _extract_repo_info(self, url: str) -> tuple:
        """
        Extract repository owner and name from GitHub URL.
        
        Args:
            url: GitHub repository URL
            
        Returns:
            Tuple of (owner, repo_name)
        """
        # Remove trailing slashes and .git extension
        clean_url = url.rstrip('/')
        if clean_url.endswith('.git'):
            clean_url = clean_url[:-4]
        
        # Extract owner and repo name
        parts = clean_url.split('/')
        if 'github.com' in parts:
            github_index = parts.index('github.com')
            if len(parts) >= github_index + 3:
                owner = parts[github_index + 1]
                repo_name = parts[github_index + 2]
                return owner, repo_name
        
        # Fallback to a default naming if parsing fails
        logger.warning(f"Could not extract owner and repo name from URL: {url}")
        return "unknown", "unknown"
    
    def crawl_repo_metadata(self) -> Dict[str, Any]:
        """
        Crawl repository metadata.
        
        Returns:
            Dictionary containing repository metadata
        """
        logger.info(f"Crawling metadata for repository: {self.repo_url}")
        
        # Use crawl4ai to extract repository metadata
        result = self.crawler.crawl(self.repo_url)
        
        # Extract repository metadata
        repo_data = {
            'owner': self.repo_owner,
            'name': self.repo_name,
            'url': self.repo_url,
            'title': result.get_title() or f"{self.repo_owner}/{self.repo_name}",
            'description': result.get_description() or '',
            'metadata': result.get_metadata() or {},
            'crawl_date': datetime.now().isoformat()
        }
        
        # Save repository metadata
        metadata_path = os.path.join(self.repo_dir, 'repo_metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(repo_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Repository metadata saved to {metadata_path}")
        return repo_data
    
    def extract_file_urls(self) -> List[str]:
        """
        Extract all file URLs from the repository.
        
        Returns:
            List of file URLs
        """
        logger.info(f"Extracting file URLs from repository: {self.repo_url}")
        
        # Use crawl4ai to extract file URLs
        result = self.crawler.crawl(self.repo_url)
        
        # Filter for blob URLs which contain actual file content
        file_urls = result.get_links(filter_by=lambda url: 'blob' in url and self.repo_owner in url and self.repo_name in url)
        
        logger.info(f"Found {len(file_urls)} files in repository")
        return file_urls
    
    def crawl_file_content(self, file_url: str) -> Dict[str, Any]:
        """
        Crawl file content.
        
        Args:
            file_url: GitHub file URL
            
        Returns:
            Dictionary containing file data
        """
        logger.info(f"Crawling content for file: {file_url}")
        
        # Use crawl4ai to extract file content
        result = self.crawler.crawl(file_url)
        
        # Extract file path from URL
        file_path = file_url.split(f"{self.repo_owner}/{self.repo_name}/blob/")[1].split('?')[0]
        file_name = os.path.basename(file_path)
        
        # Extract file content
        file_data = {
            'path': file_path,
            'name': file_name,
            'url': file_url,
            'content': result.get_text() or '',
            'crawl_date': datetime.now().isoformat()
        }
        
        # Save file data
        file_dir = os.path.join(self.repo_dir, 'files', os.path.dirname(file_path).replace('/', '_'))
        os.makedirs(file_dir, exist_ok=True)
        
        file_data_path = os.path.join(file_dir, f"{file_name}.json")
        with open(file_data_path, 'w', encoding='utf-8') as f:
            json.dump(file_data, f, ensure_ascii=False, indent=2)
        
        # Also save raw content
        file_content_path = os.path.join(file_dir, file_name)
        with open(file_content_path, 'w', encoding='utf-8') as f:
            f.write(file_data['content'])
        
        logger.info(f"File data saved to {file_data_path}")
        return file_data
    
    def extract_issue_urls(self) -> List[str]:
        """
        Extract all issue URLs from the repository.
        
        Returns:
            List of issue URLs
        """
        logger.info(f"Extracting issue URLs from repository: {self.repo_url}")
        
        # Use crawl4ai to extract issue URLs
        issues_url = f"{self.repo_url}/issues"
        result = self.crawler.crawl(issues_url)
        
        # Filter for issue URLs
        issue_urls = result.get_links(filter_by=lambda url: '/issues/' in url and self.repo_owner in url and self.repo_name in url)
        
        logger.info(f"Found {len(issue_urls)} issues in repository")
        return issue_urls
    
    def crawl_issue_content(self, issue_url: str) -> Dict[str, Any]:
        """
        Crawl issue content.
        
        Args:
            issue_url: GitHub issue URL
            
        Returns:
            Dictionary containing issue data
        """
        logger.info(f"Crawling content for issue: {issue_url}")
        
        # Use crawl4ai to extract issue content
        result = self.crawler.crawl(issue_url)
        
        # Extract issue number from URL
        issue_number = issue_url.split('/issues/')[1].split('/')[0]
        
        # Extract issue content
        issue_data = {
            'number': issue_number,
            'url': issue_url,
            'title': result.get_title() or f"Issue #{issue_number}",
            'content': result.get_text() or '',
            'metadata': result.get_metadata() or {},
            'crawl_date': datetime.now().isoformat()
        }
        
        # Save issue data
        issue_path = os.path.join(self.repo_dir, 'issues', f"issue_{issue_number}.json")
        with open(issue_path, 'w', encoding='utf-8') as f:
            json.dump(issue_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Issue data saved to {issue_path}")
        return issue_data
    
    def crawl_all_files(self) -> List[Dict[str, Any]]:
        """
        Crawl all files from the repository.
        
        Returns:
            List of file data dictionaries
        """
        file_urls = self.extract_file_urls()
        logger.info(f"Starting to crawl {len(file_urls)} files")
        
        file_data_list = []
        for i, url in enumerate(file_urls):
            logger.info(f"Processing file {i+1}/{len(file_urls)}: {url}")
            file_data = self.crawl_file_content(url)
            if file_data:
                file_data_list.append(file_data)
        
        # Save summary of all files
        summary_path = os.path.join(self.repo_dir, 'files_summary.json')
        summary_data = [
            {
                'path': data['path'],
                'name': data['name'],
                'url': data['url']
            }
            for data in file_data_list
        ]
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Crawled {len(file_data_list)} files, summary saved to {summary_path}")
        return file_data_list
    
    def crawl_all_issues(self) -> List[Dict[str, Any]]:
        """
        Crawl all issues from the repository.
        
        Returns:
            List of issue data dictionaries
        """
        issue_urls = self.extract_issue_urls()
        logger.info(f"Starting to crawl {len(issue_urls)} issues")
        
        issue_data_list = []
        for i, url in enumerate(issue_urls):
            logger.info(f"Processing issue {i+1}/{len(issue_urls)}: {url}")
            issue_data = self.crawl_issue_content(url)
            if issue_data:
                issue_data_list.append(issue_data)
        
        # Save summary of all issues
        summary_path = os.path.join(self.repo_dir, 'issues_summary.json')
        summary_data = [
            {
                'number': data['number'],
                'title': data['title'],
                'url': data['url']
            }
            for data in issue_data_list
        ]
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Crawled {len(issue_data_list)} issues, summary saved to {summary_path}")
        return issue_data_list
    
    def crawl_repository(self) -> Dict[str, Any]:
        """
        Crawl the entire repository including metadata, files, and issues.
        
        Returns:
            Dictionary with repository metadata, files, and issues
        """
        logger.info(f"Starting full crawl of repository {self.repo_owner}/{self.repo_name}")
        
        # Get repository metadata
        repo_data = self.crawl_repo_metadata()
        
        # Crawl all files
        file_data_list = self.crawl_all_files()
        
        # Crawl all issues
        issue_data_list = self.crawl_all_issues()
        
        # Create full repository data
        full_data = {
            'repository': repo_data,
            'files_count': len(file_data_list),
            'issues_count': len(issue_data_list),
            'crawl_date': datetime.now().isoformat()
        }
        
        # Save full crawl summary
        summary_path = os.path.join(self.repo_dir, 'crawl_summary.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(full_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Repository crawl completed, summary saved to {summary_path}")
        return full_data
