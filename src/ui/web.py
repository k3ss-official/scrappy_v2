"""
Web UI Module for Scrappy

This module provides a simple web interface for the Scrappy application,
allowing users to interact with the scraping functionality through a browser.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import threading
import webbrowser

from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('scrappy.ui')

# Import Scrappy main class
from main import Scrappy

class WebUI:
    """
    Web UI for the Scrappy application.
    """
    
    def __init__(self, base_dir: str = None, host: str = '0.0.0.0', port: int = 5000):
        """
        Initialize the Web UI.
        
        Args:
            base_dir: Base directory for storing data (default: current directory)
            host: Host to run the web server on (default: 0.0.0.0)
            port: Port to run the web server on (default: 5000)
        """
        self.host = host
        self.port = port
        
        # Initialize Scrappy
        self.scrappy = Scrappy(base_dir)
        
        # Initialize Flask app
        self.app = Flask(__name__, 
                         static_folder=os.path.join(os.path.dirname(__file__), 'static'),
                         template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
        
        # Configure routes
        self._configure_routes()
        
        logger.info(f"Initialized Web UI with host {host} and port {port}")
    
    def _configure_routes(self):
        """
        Configure Flask routes.
        """
        # Home page
        @self.app.route('/')
        def home():
            return render_template('index.html')
        
        # GitHub scraper
        @self.app.route('/scrape/github', methods=['GET', 'POST'])
        def scrape_github():
            if request.method == 'POST':
                # Get form data
                repo_url = request.form.get('repo_url')
                output_formats = request.form.getlist('output_formats')
                
                if not repo_url:
                    return jsonify({'error': 'Repository URL is required'}), 400
                
                if not output_formats:
                    output_formats = ['json']
                
                try:
                    # Scrape repository
                    result = self.scrappy.scrape_github(repo_url, output_formats)
                    
                    # Return result
                    return jsonify({
                        'success': True,
                        'message': f"GitHub repository scraped successfully: {result['identifier']}",
                        'result': result
                    })
                except Exception as e:
                    logger.error(f"Error scraping GitHub repository: {str(e)}")
                    return jsonify({'error': str(e)}), 500
            
            return render_template('github.html')
        
        # Website scraper
        @self.app.route('/scrape/website', methods=['GET', 'POST'])
        def scrape_website():
            if request.method == 'POST':
                # Get form data
                website_url = request.form.get('website_url')
                depth = int(request.form.get('depth', 1))
                output_formats = request.form.getlist('output_formats')
                
                if not website_url:
                    return jsonify({'error': 'Website URL is required'}), 400
                
                if not output_formats:
                    output_formats = ['json']
                
                try:
                    # Scrape website
                    result = self.scrappy.scrape_website(website_url, depth, output_formats)
                    
                    # Return result
                    return jsonify({
                        'success': True,
                        'message': f"Website scraped successfully: {result['identifier']}",
                        'result': result
                    })
                except Exception as e:
                    logger.error(f"Error scraping website: {str(e)}")
                    return jsonify({'error': str(e)}), 500
            
            return render_template('website.html')
        
        # YouTube scraper
        @self.app.route('/scrape/youtube', methods=['GET', 'POST'])
        def scrape_youtube():
            if request.method == 'POST':
                # Get form data
                channel_url = request.form.get('channel_url')
                output_formats = request.form.getlist('output_formats')
                
                if not channel_url:
                    return jsonify({'error': 'Channel URL is required'}), 400
                
                if not output_formats:
                    output_formats = ['json']
                
                try:
                    # Scrape channel
                    result = self.scrappy.scrape_youtube(channel_url, output_formats)
                    
                    # Return result
                    return jsonify({
                        'success': True,
                        'message': f"YouTube channel scraped successfully: {result['identifier']}",
                        'result': result
                    })
                except Exception as e:
                    logger.error(f"Error scraping YouTube channel: {str(e)}")
                    return jsonify({'error': str(e)}), 500
            
            return render_template('youtube.html')
        
        # List saved data
        @self.app.route('/data')
        def list_data():
            scraper_type = request.args.get('type')
            
            try:
                # List saved data
                results = self.scrappy.list_saved_data(scraper_type)
                
                return render_template('data.html', results=results)
            except Exception as e:
                logger.error(f"Error listing saved data: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        # View saved data
        @self.app.route('/data/<scraper_type>/<identifier>')
        def view_data(scraper_type, identifier):
            try:
                # Load data
                data = self.scrappy.load_data(scraper_type, identifier)
                
                if not data:
                    return jsonify({'error': f"Data not found: {scraper_type}/{identifier}"}), 404
                
                return render_template('view_data.html', 
                                      scraper_type=scraper_type, 
                                      identifier=identifier, 
                                      data=json.dumps(data, indent=2))
            except Exception as e:
                logger.error(f"Error viewing data: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        # Delete saved data
        @self.app.route('/data/<scraper_type>/<identifier>/delete', methods=['POST'])
        def delete_data(scraper_type, identifier):
            try:
                # Delete data
                success = self.scrappy.delete_data(scraper_type, identifier)
                
                if not success:
                    return jsonify({'error': f"Failed to delete data: {scraper_type}/{identifier}"}), 500
                
                return redirect(url_for('list_data'))
            except Exception as e:
                logger.error(f"Error deleting data: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        # Download output file
        @self.app.route('/output/<path:filename>')
        def download_file(filename):
            return send_from_directory(os.path.join(self.scrappy.base_dir, 'output'), filename)
    
    def run(self, open_browser: bool = True):
        """
        Run the web server.
        
        Args:
            open_browser: Whether to open a browser window (default: True)
        """
        if open_browser:
            # Open browser in a separate thread
            threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{self.port}")).start()
        
        # Run Flask app
        self.app.run(host=self.host, port=self.port, debug=False)

def main():
    """
    Main function for running the Web UI.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrappy Web UI')
    parser.add_argument('--host', default='0.0.0.0', help='Host to run the web server on')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the web server on')
    parser.add_argument('--no-browser', action='store_true', help='Do not open a browser window')
    parser.add_argument('--base-dir', help='Base directory for storing data')
    
    args = parser.parse_args()
    
    # Initialize and run Web UI
    ui = WebUI(args.base_dir, args.host, args.port)
    ui.run(not args.no_browser)

if __name__ == '__main__':
    main()
