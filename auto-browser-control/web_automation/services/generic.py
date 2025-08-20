"""
Generic Service for Web Automation

Provides universal web element operations and page automation capabilities.
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from ..core.error_handler import ErrorHandler


class GenericService:
    """Service for generic web automation operations."""
    
    def __init__(self, browser_manager):
        self.browser_manager = browser_manager
        self.error_handler = ErrorHandler()
    
    def navigate_to_url(self, driver, url):
        """Navigate to a specific URL and wait for page load."""
        self.error_handler.log_info(f"Navigating to: {url}")
        
        driver.get(url)
        
        try:
            # Wait for page to load (check for common indicators)
            WebDriverWait(driver, 15).until(
                EC.any_of(
                    EC.presence_of_element_located((By.TAG_NAME, "body")),
                    EC.presence_of_element_located((By.TAG_NAME, "main")),
                    EC.presence_of_element_located((By.TAG_NAME, "content"))
                )
            )
            
            # Additional wait for dynamic content
            time.sleep(2)
            
            self.error_handler.log_info("Page loaded successfully")
            return True
            
        except TimeoutException:
            self.error_handler.log_error("Page load timeout")
            return False
    
    def find_element_by_multiple_selectors(self, driver, selectors, timeout=10):
        """Try multiple selectors to find an element."""
        for selector in selectors:
            try:
                if selector.startswith("//"):
                    element = WebDriverWait(driver, timeout).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                else:
                    element = WebDriverWait(driver, timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                
                self.error_handler.log_info(f"Found element using selector: {selector}")
                return element
                
            except TimeoutException:
                continue
        
        return None
    
    def click_element(self, driver, selectors, timeout=10):
        """Click an element using multiple selector fallbacks."""
        element = self.find_element_by_multiple_selectors(driver, selectors, timeout)
        
        if element:
            return self.browser_manager.safe_click(driver, element)
        else:
            self.error_handler.log_error("Could not find element to click")
            return False
    
    def input_text(self, driver, selectors, text, clear_first=True, timeout=10):
        """Input text into an element using multiple selector fallbacks."""
        element = self.find_element_by_multiple_selectors(driver, selectors, timeout)
        
        if element:
            return self.browser_manager.safe_send_keys(element, text, clear_first)
        else:
            self.error_handler.log_error("Could not find element for text input")
            return False
    
    def get_element_text(self, driver, selectors, timeout=10):
        """Get text from an element using multiple selector fallbacks."""
        element = self.find_element_by_multiple_selectors(driver, selectors, timeout)
        
        if element:
            try:
                return element.text.strip()
            except Exception as e:
                self.error_handler.log_error(f"Failed to get element text: {str(e)}")
                return ""
        else:
            return ""
    
    def get_element_attribute(self, driver, selectors, attribute, timeout=10):
        """Get attribute value from an element."""
        element = self.find_element_by_multiple_selectors(driver, selectors, timeout)
        
        if element:
            try:
                return element.get_attribute(attribute)
            except Exception as e:
                self.error_handler.log_error(f"Failed to get element attribute: {str(e)}")
                return None
        else:
            return None
    
    def wait_for_text_to_appear(self, driver, text, timeout=30):
        """Wait for specific text to appear on the page."""
        try:
            WebDriverWait(driver, timeout).until(
                EC.text_to_be_present_in_element((By.TAG_NAME, "body"), text)
            )
            return True
        except TimeoutException:
            return False
    
    def wait_for_element_to_disappear(self, driver, selectors, timeout=10):
        """Wait for an element to disappear from the page."""
        try:
            for selector in selectors:
                if selector.startswith("//"):
                    WebDriverWait(driver, timeout).until_not(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                else:
                    WebDriverWait(driver, timeout).until_not(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
            return True
        except TimeoutException:
            return False
    
    def scroll_to_element(self, driver, selectors):
        """Scroll to an element on the page."""
        element = self.find_element_by_multiple_selectors(driver, selectors)
        
        if element:
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(0.5)
                return True
            except Exception as e:
                self.error_handler.log_error(f"Failed to scroll to element: {str(e)}")
                return False
        
        return False
    
    def hover_over_element(self, driver, selectors):
        """Hover over an element."""
        element = self.find_element_by_multiple_selectors(driver, selectors)
        
        if element:
            try:
                actions = ActionChains(driver)
                actions.move_to_element(element).perform()
                time.sleep(0.5)
                return True
            except Exception as e:
                self.error_handler.log_error(f"Failed to hover over element: {str(e)}")
                return False
        
        return False
    
    def select_dropdown_option(self, driver, dropdown_selectors, option_value):
        """Select an option from a dropdown."""
        dropdown = self.find_element_by_multiple_selectors(driver, dropdown_selectors)
        
        if dropdown:
            try:
                # Click to open dropdown
                self.browser_manager.safe_click(driver, dropdown)
                time.sleep(1)
                
                # Try to find and click the option
                option_selectors = [
                    f"option[value='{option_value}']",
                    f"//option[text()='{option_value}']",
                    f"//li[text()='{option_value}']",
                    f".option:contains('{option_value}')"
                ]
                
                option = self.find_element_by_multiple_selectors(driver, option_selectors)
                if option:
                    return self.browser_manager.safe_click(driver, option)
                else:
                    self.error_handler.log_error(f"Could not find dropdown option: {option_value}")
                    return False
                
            except Exception as e:
                self.error_handler.log_error(f"Failed to select dropdown option: {str(e)}")
                return False
        
        return False
    
    def fill_form(self, driver, form_data, form_selectors=None):
        """Fill out a form with the provided data."""
        success = True
        
        for field_name, field_value in form_data.items():
            field_selectors = [
                f"input[name='{field_name}']",
                f"textarea[name='{field_name}']",
                f"select[name='{field_name}']",
                f"#{field_name}",
                f".{field_name} input",
                f"[data-testid='{field_name}']"
            ]
            
            if not self.input_text(driver, field_selectors, str(field_value)):
                self.error_handler.log_error(f"Failed to fill field: {field_name}")
                success = False
        
        return success
    
    def extract_table_data(self, driver, table_selectors):
        """Extract data from a table."""
        table = self.find_element_by_multiple_selectors(driver, table_selectors)
        
        if not table:
            return []
        
        try:
            rows = table.find_elements(By.TAG_NAME, "tr")
            table_data = []
            
            for row in rows:
                cells = row.find_elements(By.CSS_SELECTOR, "td, th")
                row_data = [cell.text.strip() for cell in cells]
                if any(row_data):  # Only add non-empty rows
                    table_data.append(row_data)
            
            return table_data
            
        except Exception as e:
            self.error_handler.log_error(f"Failed to extract table data: {str(e)}")
            return []
    
    def take_screenshot_with_context(self, driver, filename_prefix="automation"):
        """Take a screenshot with contextual filename."""
        try:
            current_url = driver.current_url
            page_title = driver.title
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            
            # Create descriptive filename
            url_part = current_url.split("/")[-1][:20] if current_url else "page"
            filename = f"{filename_prefix}_{url_part}_{timestamp}.png"
            
            screenshot_path = self.browser_manager.take_screenshot(driver, filename)
            if screenshot_path:
                self.error_handler.log_info(f"Screenshot saved: {screenshot_path} (Title: {page_title})")
            
            return screenshot_path
            
        except Exception as e:
            self.error_handler.log_error(f"Failed to take contextual screenshot: {str(e)}")
            return None
    
    def execute_custom_script(self, driver, script, *args):
        """Execute custom JavaScript on the page."""
        try:
            result = driver.execute_script(script, *args)
            self.error_handler.log_info("Custom JavaScript executed successfully")
            return result
        except Exception as e:
            self.error_handler.log_error(f"Failed to execute custom script: {str(e)}")
            return None
    
    def wait_for_page_load_complete(self, driver, timeout=30):
        """Wait for page to completely load including AJAX calls."""
        try:
            # Wait for document ready state
            WebDriverWait(driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            # Additional wait for common AJAX indicators to disappear
            ajax_selectors = [
                ".loading",
                ".spinner",
                "[data-loading]",
                ".progress-bar",
                "//div[contains(@class, 'loading')]"
            ]
            
            # Wait a bit for AJAX to potentially start
            time.sleep(1)
            
            # Wait for loading indicators to disappear
            self.wait_for_element_to_disappear(driver, ajax_selectors, timeout=10)
            
            self.error_handler.log_info("Page load complete")
            return True
            
        except Exception as e:
            self.error_handler.log_warning(f"Page load check failed: {str(e)}")
            return False