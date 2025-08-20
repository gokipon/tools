"""
Browser Manager for Chrome Remote Debugging

Handles connection management and browser automation through Chrome DevTools Protocol.
"""

import json
import time
import requests
import websocket
from contextlib import contextmanager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException

from .error_handler import ErrorHandler


class BrowserManager:
    """Manages Chrome browser connection using Remote Debugging Protocol."""
    
    def __init__(self, port=9222, headless=False, timeout=30):
        self.port = port
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        self.error_handler = ErrorHandler()
        
        # Chrome options for remote debugging
        self.chrome_options = Options()
        self.chrome_options.add_argument(f"--remote-debugging-port={port}")
        if headless:
            self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-gpu")
    
    def is_chrome_running(self):
        """Check if Chrome is running with remote debugging."""
        try:
            response = requests.get(f"http://localhost:{self.port}/json/version", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def get_tabs(self):
        """Get list of available browser tabs."""
        try:
            response = requests.get(f"http://localhost:{self.port}/json", timeout=5)
            if response.status_code == 200:
                return response.json()
            return []
        except requests.RequestException:
            return []
    
    def connect_to_existing_tab(self, url_pattern=None):
        """Connect to existing Chrome tab or create new one."""
        if not self.is_chrome_running():
            raise ConnectionError(
                f"Chrome not running with remote debugging on port {self.port}. "
                f"Start Chrome with: "
                f"google-chrome --remote-debugging-port={self.port} --user-data-dir=/tmp/chrome-debug"
            )
        
        try:
            # Try to connect to existing Chrome session
            self.chrome_options.add_experimental_option("debuggerAddress", f"localhost:{self.port}")
            self.driver = webdriver.Chrome(options=self.chrome_options)
            
            # If url_pattern specified, try to find matching tab
            if url_pattern:
                tabs = self.get_tabs()
                for tab in tabs:
                    if url_pattern in tab.get('url', ''):
                        self.driver.get(tab['url'])
                        break
            
            return self.driver
            
        except WebDriverException as e:
            raise ConnectionError(f"Failed to connect to Chrome: {str(e)}")
    
    @contextmanager
    def connect(self):
        """Context manager for browser connection."""
        try:
            driver = self.connect_to_existing_tab()
            yield driver
        except Exception as e:
            self.error_handler.handle_error(e, "Browser connection failed")
            raise
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
    
    def wait_for_element(self, driver, locator, timeout=None):
        """Wait for element to be present and return it."""
        timeout = timeout or self.timeout
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            return element
        except TimeoutException:
            return None
    
    def wait_for_clickable(self, driver, locator, timeout=None):
        """Wait for element to be clickable and return it."""
        timeout = timeout or self.timeout
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable(locator)
            )
            return element
        except TimeoutException:
            return None
    
    def safe_click(self, driver, element):
        """Safely click an element with retry logic."""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # Scroll element into view
                driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(0.5)
                
                # Try regular click
                element.click()
                return True
                
            except Exception as e:
                if attempt < max_attempts - 1:
                    # Try JavaScript click as fallback
                    try:
                        driver.execute_script("arguments[0].click();", element)
                        return True
                    except:
                        time.sleep(1)
                        continue
                else:
                    self.error_handler.log_error(f"Failed to click element after {max_attempts} attempts: {str(e)}")
                    return False
        
        return False
    
    def safe_send_keys(self, element, text, clear_first=True):
        """Safely send keys to an element."""
        try:
            if clear_first:
                element.clear()
            element.send_keys(text)
            return True
        except Exception as e:
            self.error_handler.log_error(f"Failed to send keys: {str(e)}")
            return False
    
    def take_screenshot(self, driver, filename=None):
        """Take a screenshot of current page."""
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
        
        try:
            driver.save_screenshot(filename)
            return filename
        except Exception as e:
            self.error_handler.log_error(f"Failed to take screenshot: {str(e)}")
            return None
    
    def get_page_source(self, driver):
        """Get current page source."""
        try:
            return driver.page_source
        except Exception as e:
            self.error_handler.log_error(f"Failed to get page source: {str(e)}")
            return None
    
    def execute_js(self, driver, script, *args):
        """Execute JavaScript in the browser."""
        try:
            return driver.execute_script(script, *args)
        except Exception as e:
            self.error_handler.log_error(f"Failed to execute JavaScript: {str(e)}")
            return None