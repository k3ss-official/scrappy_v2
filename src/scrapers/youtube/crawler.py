"""
YouTube Scraper Module for Scrappy

This module handles the crawling and extraction of YouTube channel content
using crawl4ai as the primary scraping engine.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import YouTube transcript API for transcript extraction
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api.formatters import JSONFormatter
    from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
except ImportError:
    logging.warning("YouTube Transcript API not installed. Transcripts will not be available.")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('scrappy.scrapers.youtube')

class YouTubeScraper:
    """
    Scraper for YouTube channels and videos using crawl4ai.
    """
    
    def __init__(self, channel_url: str, output_dir: str):
        """
        Initialize the YouTube scraper.
        
        Args:
            channel_url: URL of the YouTube channel to scrape
            output_dir: Directory to save scraped data
        """
        self.channel_url = channel_url
        self.output_dir = output_dir
        
        # Extract channel handle from URL
        self.channel_handle = self._extract_channel_handle(channel_url)
        
        # Create channel directory
        self.channel_dir = os.path.join(output_dir, f"youtube_{self.channel_handle}")
        os.makedirs(self.channel_dir, exist_ok=True)
        os.makedirs(os.path.join(self.channel_dir, 'videos'), exist_ok=True)
        
        # Initialize crawl4ai
        try:
            from crawl4ai import Crawler
            self.crawler = Crawler()
            logger.info(f"Initialized crawl4ai for YouTube channel: {self.channel_handle}")
        except ImportError:
            logger.error("crawl4ai not installed. Please install it to use the YouTube scraper.")
            raise
    
    def _extract_channel_handle(self, url: str) -> str:
        """
        Extract channel handle from YouTube URL.
        
        Args:
            url: YouTube channel URL
            
        Returns:
            Channel handle or ID
        """
        if '@' in url:
            # Handle @username format
            handle = url.split('@')[1].split('/')[0]
            return handle
        elif 'channel/' in url:
            # Handle channel/ID format
            channel_id = url.split('channel/')[1].split('/')[0]
            return channel_id
        else:
            # Default to a sanitized version of the URL
            return url.replace('https://', '').replace('www.youtube.com/', '').replace('/', '_')
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """
        Extract video ID from YouTube URL.
        
        Args:
            url: YouTube video URL
            
        Returns:
            Video ID or None if extraction fails
        """
        if 'youtube.com/watch' in url and 'v=' in url:
            # Handle youtube.com/watch?v=VIDEO_ID format
            video_id = url.split('v=')[1].split('&')[0]
        elif 'youtu.be/' in url:
            # Handle youtu.be/VIDEO_ID format
            video_id = url.split('youtu.be/')[1].split('?')[0]
        else:
            logger.warning(f"Could not extract video ID from URL: {url}")
            return None
        
        return video_id
    
    def extract_video_urls(self) -> List[str]:
        """
        Extract all video URLs from the channel.
        
        Returns:
            List of video URLs
        """
        logger.info(f"Extracting video URLs from channel: {self.channel_url}")
        
        # Use crawl4ai to extract video URLs
        result = self.crawler.crawl(self.channel_url)
        video_urls = result.get_links(filter_by=lambda url: 'youtube.com/watch' in url or 'youtu.be/' in url)
        
        logger.info(f"Found {len(video_urls)} videos in channel")
        return video_urls
    
    def crawl_channel_metadata(self) -> Dict[str, Any]:
        """
        Crawl channel metadata.
        
        Returns:
            Dictionary containing channel metadata
        """
        logger.info(f"Crawling metadata for channel: {self.channel_url}")
        
        # Use crawl4ai to extract channel metadata
        result = self.crawler.crawl(self.channel_url)
        
        # Extract channel metadata
        channel_data = {
            'handle': self.channel_handle,
            'url': self.channel_url,
            'title': result.get_title() or f"Channel {self.channel_handle}",
            'description': result.get_description() or '',
            'metadata': result.get_metadata() or {},
            'crawl_date': datetime.now().isoformat()
        }
        
        # Save channel metadata
        metadata_path = os.path.join(self.channel_dir, 'channel_metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(channel_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Channel metadata saved to {metadata_path}")
        return channel_data
    
    def get_video_transcript(self, video_id: str) -> List[Dict[str, Any]]:
        """
        Get transcript for a video using youtube_transcript_api.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            List of transcript segments with text and timestamps
        """
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            logger.info(f"Successfully retrieved transcript for video {video_id}")
            return transcript_list
        except (TranscriptsDisabled, NoTranscriptFound) as e:
            logger.warning(f"No transcript available for video {video_id}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error retrieving transcript for video {video_id}: {str(e)}")
            return []
    
    def crawl_video_content(self, video_url: str) -> Dict[str, Any]:
        """
        Crawl video content including metadata, description, and transcript.
        
        Args:
            video_url: YouTube video URL
            
        Returns:
            Dictionary containing video data
        """
        video_id = self.extract_video_id(video_url)
        if not video_id:
            return {}
        
        logger.info(f"Crawling content for video ID: {video_id}")
        
        # Use crawl4ai to extract video content
        result = self.crawler.crawl(video_url)
        
        # Extract video metadata
        video_data = {
            'video_id': video_id,
            'url': video_url,
            'title': result.get_title() or f"Video {video_id}",
            'description': result.get_description() or '',
            'metadata': result.get_metadata() or {},
            'crawl_date': datetime.now().isoformat(),
            'transcript': self.get_video_transcript(video_id)
        }
        
        # Save video data
        video_dir = os.path.join(self.channel_dir, 'videos', video_id)
        os.makedirs(video_dir, exist_ok=True)
        
        video_path = os.path.join(video_dir, 'video_data.json')
        with open(video_path, 'w', encoding='utf-8') as f:
            json.dump(video_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Video data saved to {video_path}")
        return video_data
    
    def crawl_all_videos(self) -> List[Dict[str, Any]]:
        """
        Crawl all videos from the channel.
        
        Returns:
            List of video data dictionaries
        """
        video_urls = self.extract_video_urls()
        logger.info(f"Starting to crawl {len(video_urls)} videos")
        
        video_data_list = []
        for i, url in enumerate(video_urls):
            logger.info(f"Processing video {i+1}/{len(video_urls)}: {url}")
            video_data = self.crawl_video_content(url)
            if video_data:
                video_data_list.append(video_data)
        
        # Save summary of all videos
        summary_path = os.path.join(self.channel_dir, 'videos_summary.json')
        summary_data = [
            {
                'video_id': data['video_id'],
                'title': data['title'],
                'url': data['url'],
                'has_transcript': bool(data.get('transcript'))
            }
            for data in video_data_list
        ]
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Crawled {len(video_data_list)} videos, summary saved to {summary_path}")
        return video_data_list
    
    def crawl_channel(self) -> Dict[str, Any]:
        """
        Crawl the entire channel including metadata and all videos.
        
        Returns:
            Dictionary with channel metadata and video data
        """
        logger.info(f"Starting full crawl of channel {self.channel_handle}")
        
        # Get channel metadata
        channel_data = self.crawl_channel_metadata()
        
        # Crawl all videos
        video_data_list = self.crawl_all_videos()
        
        # Create full channel data
        full_data = {
            'channel': channel_data,
            'videos_count': len(video_data_list),
            'crawl_date': datetime.now().isoformat()
        }
        
        # Save full crawl summary
        summary_path = os.path.join(self.channel_dir, 'crawl_summary.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(full_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Channel crawl completed, summary saved to {summary_path}")
        return full_data
