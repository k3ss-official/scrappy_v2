"""
Security Module for Scrappy

This module provides security utilities for the Scrappy application,
including input sanitization, URL validation, and file path security.
"""

import os
import re
import html
import urllib.parse
from typing import Optional, List, Dict, Any


class SecurityManager:
    """
    Security manager for Scrappy application.
    
    Provides utilities for input validation, sanitization, and security checks.
    """
    
    def __init__(self):
        """Initialize the security manager."""
        # Patterns for security checks
        self.url_pattern = re.compile(
            r'^(?:http|https)://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or ipv4
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        # Allowed file extensions for output
        self.allowed_extensions = ['json', 'csv', 'txt', 'yaml', 'yml', 'xml']
        
        # Dangerous file paths to check
        self.dangerous_paths = ['/etc/passwd', '/etc/shadow', '/proc', '/sys', '/dev', 
                               '/boot', '/bin', '/sbin', '/usr/bin', '/usr/sbin']
    
    def sanitize_input(self, input_str: str) -> str:
        """
        Sanitize user input to prevent XSS and injection attacks.
        
        Args:
            input_str: User input string
            
        Returns:
            Sanitized string
        """
        if not input_str:
            return ""
        
        # HTML escape to prevent XSS
        return html.escape(input_str)
    
    def validate_url(self, url: str) -> bool:
        """
        Validate URL format and scheme.
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not url:
            return False
        
        # Check URL format
        if not self.url_pattern.match(url):
            return False
        
        # Check scheme
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ['http', 'https']:
            return False
        
        return True
    
    def secure_filename(self, filename: str) -> str:
        """
        Create a secure filename from user input.
        
        Args:
            filename: Original filename
            
        Returns:
            Secure filename
        """
        if not filename:
            return "unnamed_file"
        
        # Remove path components
        filename = os.path.basename(filename)
        
        # Remove dangerous characters
        filename = re.sub(r'[^\w\s.-]', '', filename)
        
        # Replace spaces with underscores
        filename = filename.replace(' ', '_')
        
        # Ensure it's not empty after sanitization
        if not filename:
            return "unnamed_file"
        
        return filename
    
    def validate_output_format(self, format_name: str) -> bool:
        """
        Validate output format.
        
        Args:
            format_name: Format name to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not format_name:
            return False
        
        return format_name.lower() in self.allowed_extensions
    
    def validate_path(self, path: str) -> bool:
        """
        Validate file path for security.
        
        Args:
            path: File path to validate
            
        Returns:
            True if safe, False otherwise
        """
        if not path:
            return False
        
        # Convert to absolute path
        abs_path = os.path.abspath(path)
        
        # Check for dangerous paths
        for dangerous in self.dangerous_paths:
            if abs_path == dangerous or abs_path.startswith(dangerous + os.sep):
                return False
        
        # Check for directory traversal attempts
        if '..' in path:
            return False
        
        return True
    
    def sanitize_path(self, path: str) -> str:
        """
        Sanitize file path for security.
        
        Args:
            path: File path to sanitize
            
        Returns:
            Sanitized path
        """
        if not path:
            return ""
        
        # Remove dangerous characters
        path = re.sub(r'[<>:"|?*]', '', path)
        
        # Replace spaces with underscores
        path = path.replace(' ', '_')
        
        return path
