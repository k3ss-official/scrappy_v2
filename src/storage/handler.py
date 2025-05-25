"""
Storage Handler Module for Scrappy

This module handles the storage and retrieval of scraped data
in the local filesystem.
"""

import os
import json
import shutil
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('scrappy.storage')

class StorageHandler:
    """
    Handler for storing and retrieving scraped data.
    """
    
    def __init__(self, base_dir: str):
        """
        Initialize the storage handler.
        
        Args:
            base_dir: Base directory for storing data
        """
        self.base_dir = base_dir
        
        # Create base directory if it doesn't exist
        os.makedirs(base_dir, exist_ok=True)
        
        # Create subdirectories for different scraper types
        self.github_dir = os.path.join(base_dir, 'github')
        self.website_dir = os.path.join(base_dir, 'website')
        self.youtube_dir = os.path.join(base_dir, 'youtube')
        
        os.makedirs(self.github_dir, exist_ok=True)
        os.makedirs(self.website_dir, exist_ok=True)
        os.makedirs(self.youtube_dir, exist_ok=True)
        
        logger.info(f"Initialized storage handler with base directory: {base_dir}")
    
    def get_storage_path(self, scraper_type: str, identifier: str) -> str:
        """
        Get the storage path for a specific scraper type and identifier.
        
        Args:
            scraper_type: Type of scraper ('github', 'website', or 'youtube')
            identifier: Unique identifier for the scraped content
            
        Returns:
            Path to the storage directory
        """
        if scraper_type == 'github':
            return os.path.join(self.github_dir, identifier)
        elif scraper_type == 'website':
            return os.path.join(self.website_dir, identifier)
        elif scraper_type == 'youtube':
            return os.path.join(self.youtube_dir, identifier)
        else:
            raise ValueError(f"Unknown scraper type: {scraper_type}")
    
    def save_data(self, scraper_type: str, identifier: str, data: Dict[str, Any]) -> str:
        """
        Save data to storage.
        
        Args:
            scraper_type: Type of scraper ('github', 'website', or 'youtube')
            identifier: Unique identifier for the scraped content
            data: Data to save
            
        Returns:
            Path to the saved data
        """
        storage_path = self.get_storage_path(scraper_type, identifier)
        os.makedirs(storage_path, exist_ok=True)
        
        # Add timestamp to data
        data['saved_at'] = datetime.now().isoformat()
        
        # Save data to JSON file
        data_path = os.path.join(storage_path, 'data.json')
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Data saved to {data_path}")
        return data_path
    
    def load_data(self, scraper_type: str, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Load data from storage.
        
        Args:
            scraper_type: Type of scraper ('github', 'website', or 'youtube')
            identifier: Unique identifier for the scraped content
            
        Returns:
            Loaded data or None if not found
        """
        storage_path = self.get_storage_path(scraper_type, identifier)
        data_path = os.path.join(storage_path, 'data.json')
        
        if not os.path.exists(data_path):
            logger.warning(f"Data not found at {data_path}")
            return None
        
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Data loaded from {data_path}")
            return data
        except Exception as e:
            logger.error(f"Error loading data from {data_path}: {str(e)}")
            return None
    
    def list_saved_data(self, scraper_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all saved data.
        
        Args:
            scraper_type: Optional filter by scraper type
            
        Returns:
            List of saved data information
        """
        result = []
        
        if scraper_type:
            # List data for specific scraper type
            if scraper_type == 'github':
                base_dir = self.github_dir
            elif scraper_type == 'website':
                base_dir = self.website_dir
            elif scraper_type == 'youtube':
                base_dir = self.youtube_dir
            else:
                raise ValueError(f"Unknown scraper type: {scraper_type}")
            
            for identifier in os.listdir(base_dir):
                data_path = os.path.join(base_dir, identifier, 'data.json')
                if os.path.exists(data_path):
                    try:
                        with open(data_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        result.append({
                            'scraper_type': scraper_type,
                            'identifier': identifier,
                            'path': data_path,
                            'saved_at': data.get('saved_at', 'unknown'),
                            'summary': self._generate_summary(scraper_type, data)
                        })
                    except Exception as e:
                        logger.error(f"Error reading data from {data_path}: {str(e)}")
        else:
            # List data for all scraper types
            for scraper_type in ['github', 'website', 'youtube']:
                result.extend(self.list_saved_data(scraper_type))
        
        return result
    
    def _generate_summary(self, scraper_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary of the data.
        
        Args:
            scraper_type: Type of scraper
            data: Data to summarize
            
        Returns:
            Summary dictionary
        """
        summary = {}
        
        if scraper_type == 'github':
            # GitHub repository summary
            repo = data.get('repository', {})
            summary = {
                'name': repo.get('name', 'unknown'),
                'owner': repo.get('owner', 'unknown'),
                'files_count': data.get('files_count', 0),
                'issues_count': data.get('issues_count', 0)
            }
        elif scraper_type == 'website':
            # Website summary
            summary = {
                'domain': data.get('domain', 'unknown'),
                'pages_crawled': data.get('pages_crawled', 0),
                'assets_downloaded': data.get('assets_downloaded', 0)
            }
        elif scraper_type == 'youtube':
            # YouTube channel summary
            channel = data.get('channel', {})
            summary = {
                'handle': channel.get('handle', 'unknown'),
                'videos_count': data.get('videos_count', 0)
            }
        
        return summary
    
    def delete_data(self, scraper_type: str, identifier: str) -> bool:
        """
        Delete data from storage.
        
        Args:
            scraper_type: Type of scraper ('github', 'website', or 'youtube')
            identifier: Unique identifier for the scraped content
            
        Returns:
            True if deletion was successful, False otherwise
        """
        storage_path = self.get_storage_path(scraper_type, identifier)
        
        if not os.path.exists(storage_path):
            logger.warning(f"Data not found at {storage_path}")
            return False
        
        try:
            shutil.rmtree(storage_path)
            logger.info(f"Data deleted from {storage_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting data from {storage_path}: {str(e)}")
            return False
