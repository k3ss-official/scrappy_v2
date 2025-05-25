"""
Security Module for Scrappy

This module provides security utilities and middleware for the Scrappy application,
ensuring secure data handling, input validation, and protection against common vulnerabilities.
"""

import os
import re
import logging
import hashlib
import secrets
import json
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
import html

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('scrappy.security')

class SecurityManager:
    """
    Security manager for the Scrappy application.
    """
    
    def __init__(self):
        """
        Initialize the security manager.
        """
        # Generate a random secret key for the session
        self.secret_key = secrets.token_hex(32)
        
        # Initialize security settings
        self.max_request_size = 10 * 1024 * 1024  # 10 MB
        self.allowed_domains = []  # Empty list means all domains are allowed
        self.rate_limit = 10  # Requests per minute
        
        logger.info("Initialized security manager")
    
    def validate_url(self, url: str) -> bool:
        """
        Validate a URL for security concerns.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid and safe, False otherwise
        """
        # Check if URL is properly formatted
        try:
            parsed_url = urlparse(url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                logger.warning(f"Invalid URL format: {url}")
                return False
            
            # Ensure URL uses http or https
            if parsed_url.scheme not in ['http', 'https']:
                logger.warning(f"Unsupported URL scheme: {parsed_url.scheme}")
                return False
            
            # Check against allowed domains if specified
            if self.allowed_domains and parsed_url.netloc not in self.allowed_domains:
                logger.warning(f"Domain not in allowed list: {parsed_url.netloc}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating URL {url}: {str(e)}")
            return False
    
    def sanitize_input(self, input_str: str) -> str:
        """
        Sanitize input string to prevent injection attacks.
        
        Args:
            input_str: Input string to sanitize
            
        Returns:
            Sanitized string
        """
        if not input_str:
            return ""
        
        # HTML escape to prevent XSS
        sanitized = html.escape(input_str)
        
        # Remove potentially dangerous patterns
        sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'data:', '', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    def validate_file_path(self, file_path: str) -> bool:
        """
        Validate a file path for security concerns.
        
        Args:
            file_path: File path to validate
            
        Returns:
            True if file path is valid and safe, False otherwise
        """
        # Normalize path
        normalized_path = os.path.normpath(file_path)
        
        # Check for path traversal attempts
        if '..' in normalized_path:
            logger.warning(f"Path traversal attempt detected: {file_path}")
            return False
        
        # Check for absolute paths
        if os.path.isabs(normalized_path):
            # Ensure path is within allowed directories
            allowed_dirs = ['/tmp', '/var/tmp', os.getcwd()]
            if not any(normalized_path.startswith(allowed_dir) for allowed_dir in allowed_dirs):
                logger.warning(f"Path outside allowed directories: {file_path}")
                return False
        
        return True
    
    def hash_data(self, data: str) -> str:
        """
        Create a secure hash of data.
        
        Args:
            data: Data to hash
            
        Returns:
            Secure hash of data
        """
        return hashlib.sha256(data.encode()).hexdigest()
    
    def secure_filename(self, filename: str) -> str:
        """
        Secure a filename to prevent path traversal and other attacks.
        
        Args:
            filename: Filename to secure
            
        Returns:
            Secured filename
        """
        # Remove any directory components
        filename = os.path.basename(filename)
        
        # Remove potentially dangerous characters
        filename = re.sub(r'[^\w\.\-]', '_', filename)
        
        # Ensure filename is not empty
        if not filename:
            filename = 'unnamed_file'
        
        return filename
    
    def validate_output_format(self, format_name: str) -> bool:
        """
        Validate an output format name.
        
        Args:
            format_name: Format name to validate
            
        Returns:
            True if format is valid, False otherwise
        """
        allowed_formats = ['json', 'csv', 'txt', 'yaml', 'xml']
        return format_name.lower() in allowed_formats
    
    def secure_headers(self) -> Dict[str, str]:
        """
        Generate secure HTTP headers for web responses.
        
        Returns:
            Dictionary of secure HTTP headers
        """
        return {
            'Content-Security-Policy': "default-src 'self'; script-src 'self' https://cdn.jsdelivr.net; style-src 'self' https://cdn.jsdelivr.net; img-src 'self' data:;",
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'SAMEORIGIN',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
    
    def apply_rate_limiting(self, client_id: str, current_count: int) -> bool:
        """
        Apply rate limiting to prevent abuse.
        
        Args:
            client_id: Identifier for the client
            current_count: Current request count for the client
            
        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        return current_count <= self.rate_limit
    
    def validate_json_data(self, json_str: str) -> Optional[Dict[str, Any]]:
        """
        Validate and safely parse JSON data.
        
        Args:
            json_str: JSON string to validate
            
        Returns:
            Parsed JSON data or None if invalid
        """
        try:
            # Limit JSON size
            if len(json_str) > self.max_request_size:
                logger.warning(f"JSON data too large: {len(json_str)} bytes")
                return None
            
            # Parse JSON
            data = json.loads(json_str)
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON data: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error validating JSON data: {str(e)}")
            return None
