#!/usr/bin/env python3
"""
macOS Client for Things3 URL Processing

This script polls the EC2 server for pending Things3 URLs and opens them locally.
It runs continuously, checking for new URLs every 10 seconds.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Setup logging
log_file = Path.home() / "things3_url_client.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
EC2_HOST = os.getenv("EC2_HOST", "51.20.1.114")
EC2_PORT = os.getenv("EC2_PORT", "5001")
API_KEY = os.getenv("THINGS_API_KEY", "things3-url-api-key-2024")
CHECK_INTERVAL = 10  # seconds
SERVER_URL = "http://{}:{}".format(EC2_HOST, EC2_PORT)

class Things3UrlClient:
    def __init__(self):
        self.processed_urls: set[str] = set()
        self.last_check_time = datetime.now()
    
    def fetchPendingUrls(self) -> List[Dict[str, Any]]:
        """Fetch pending URLs from the EC2 server."""
        try:
            url = "{}/api/pending_urls?api_key={}".format(SERVER_URL, API_KEY)
            
            request = urllib.request.Request(url)
            request.add_header('Authorization', 'Bearer {}'.format(API_KEY))
            
            with urllib.request.urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode())
                
            urls = data.get('urls', [])
            count = data.get('count', 0)
            
            if count > 0:
                logger.info("Fetched {} pending URLs from server".format(count))
            
            return urls
            
        except urllib.error.HTTPError as e:
            if e.code == 401:
                logger.error("Authentication failed. Check API key.")
            else:
                logger.error("HTTP error {}: {}".format(e.code, e.reason))
            return []
        except urllib.error.URLError as e:
            logger.error("Failed to connect to server: {}".format(e.reason))
            return []
        except Exception as e:
            logger.error("Failed to fetch URLs: {}".format(e))
            return []
    
    def checkServerStatus(self) -> bool:
        """Check if the server is accessible."""
        try:
            url = "{}/api/health".format(SERVER_URL)
            request = urllib.request.Request(url)
            
            with urllib.request.urlopen(request, timeout=5) as response:
                data = json.loads(response.read().decode())
                
            return data.get('status') == 'healthy'
            
        except Exception as e:
            logger.warning("Server health check failed: {}".format(e))
            return False
    
    def openThingsUrl(self, url: str, task_title: str) -> bool:
        """Open a Things3 URL on macOS."""
        try:
            logger.info("Opening Things3 URL for task: {}".format(task_title))
            logger.debug("URL: {}".format(url))
            
            # Use 'open' command on macOS to open the URL
            result = subprocess.run(
                ["open", url],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logger.info("✅ Successfully opened URL for: {}".format(task_title))
                return True
            else:
                logger.warning("⚠️ Failed to open URL for: {} (return code: {})".format(
                    task_title, result.returncode))
                if result.stderr:
                    logger.warning("Error: {}".format(result.stderr))
                return False
                
        except subprocess.TimeoutExpired:
            logger.warning("⚠️ URL open timed out for: {}".format(task_title))
            return False
        except Exception as e:
            logger.error("❌ Failed to open URL for '{}': {}".format(task_title, e))
            return False
    
    def processUrls(self, urls: List[Dict[str, Any]]) -> None:
        """Process a list of URLs by opening them in Things3."""
        successful = 0
        failed = 0
        
        for url_data in urls:
            url = url_data.get('url', '')
            task_title = url_data.get('task_title', 'Unknown Task')
            original_title = url_data.get('original_title', '')
            
            # Skip if already processed (shouldn't happen with server marking)
            if url in self.processed_urls:
                logger.warning("Skipping already processed URL: {}".format(task_title))
                continue
            
            # Open the URL
            if self.openThingsUrl(url, task_title):
                successful += 1
                self.processed_urls.add(url)
                
                # Log the original English title for reference
                if original_title:
                    logger.info("Original title: {}".format(original_title))
            else:
                failed += 1
            
            # Small delay between URLs to avoid overwhelming Things3
            time.sleep(0.5)
        
        if successful > 0 or failed > 0:
            logger.info("Processed {} URLs: {} successful, {} failed".format(
                successful + failed, successful, failed))
    
    def runSingleCycle(self) -> None:
        """Run a single polling cycle."""
        logger.debug("Starting polling cycle...")
        
        # Fetch pending URLs from server
        urls = self.fetchPendingUrls()
        
        if urls:
            self.processUrls(urls)
        else:
            logger.debug("No pending URLs found")
    
    def runContinuousPolling(self) -> None:
        """Run continuous polling for URLs."""
        logger.info("🚀 Starting Things3 URL client")
        logger.info("📡 Polling server at {}".format(SERVER_URL))
        logger.info("⏰ Checking every {} seconds".format(CHECK_INTERVAL))
        logger.info("🛑 Press Ctrl+C to stop")
        logger.info("=" * 60)
        
        # Initial server check
        if not self.checkServerStatus():
            logger.warning("⚠️ Server may be unavailable. Will keep trying...")
        
        try:
            while True:
                self.runSingleCycle()
                
                logger.debug("Waiting {} seconds before next check...".format(CHECK_INTERVAL))
                time.sleep(CHECK_INTERVAL)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Client stopped by user")
        except Exception as e:
            logger.error("❌ Client failed: {}".format(e))
            raise
        finally:
            logger.info("💤 Client shutting down. Goodbye!")

def validateSetup() -> bool:
    """Validate that the setup is correct."""
    logger.info("🔍 Validating setup...")
    
    # Check if running on macOS
    if sys.platform != "darwin":
        logger.error("❌ This client must run on macOS (detected: {})".format(sys.platform))
        return False
    
    # Check if Things3 is installed
    try:
        result = subprocess.run(
            ["osascript", "-e", 'id of application "Things3"'],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            logger.warning("⚠️ Things3 may not be installed")
    except Exception:
        logger.warning("⚠️ Could not verify Things3 installation")
    
    logger.info("✅ Setup validation passed")
    logger.info("Server: {}".format(SERVER_URL))
    return True

def main() -> None:
    """Main function."""
    # Validate setup
    if not validateSetup():
        logger.error("❌ Setup validation failed")
        sys.exit(1)
    
    # Create and run client
    client = Things3UrlClient()
    
    # Check if running in test mode
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        logger.info("🧪 Running in test mode (single cycle)")
        client.runSingleCycle()
    else:
        client.runContinuousPolling()

if __name__ == "__main__":
    main() 