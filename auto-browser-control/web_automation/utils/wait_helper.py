"""
Wait Helper Utilities

Smart waiting strategies for page loads, element states, and dynamic content.
"""

import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException


class WaitHelper:
    """Helper class for intelligent waiting strategies."""
    
    @staticmethod
    def wait_for_page_load(driver, timeout=30):
        """Wait for page to fully load including JavaScript."""
        try:
            # Wait for document ready state
            WebDriverWait(driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            # Wait for jQuery if present
            try:
                WebDriverWait(driver, 5).until(
                    lambda d: d.execute_script("return typeof jQuery === 'undefined' || jQuery.active === 0")
                )
            except:
                pass  # jQuery not present or timeout
            
            return True
        except TimeoutException:
            return False
    
    @staticmethod
    def wait_for_ajax_complete(driver, timeout=10):
        """Wait for AJAX requests to complete."""
        try:
            # Wait for jQuery AJAX
            WebDriverWait(driver, timeout).until(
                lambda d: d.execute_script("return typeof jQuery === 'undefined' || jQuery.active === 0")
            )
            
            # Wait for Angular if present
            try:
                WebDriverWait(driver, 5).until(
                    lambda d: d.execute_script(
                        "return typeof angular === 'undefined' || "
                        "angular.element(document).injector().get('$http').pendingRequests.length === 0"
                    )
                )
            except:
                pass
            
            return True
        except TimeoutException:
            return False
    
    @staticmethod
    def wait_for_element_text_change(driver, element, initial_text, timeout=10):
        """Wait for element text to change from initial value."""
        try:
            WebDriverWait(driver, timeout).until(
                lambda d: element.text != initial_text
            )
            return True
        except TimeoutException:
            return False
    
    @staticmethod
    def wait_for_element_attribute_change(driver, element, attribute, initial_value, timeout=10):
        """Wait for element attribute to change from initial value."""
        try:
            WebDriverWait(driver, timeout).until(
                lambda d: element.get_attribute(attribute) != initial_value
            )
            return True
        except TimeoutException:
            return False
    
    @staticmethod
    def wait_for_url_change(driver, initial_url, timeout=10):
        """Wait for URL to change from initial value."""
        try:
            WebDriverWait(driver, timeout).until(
                lambda d: d.current_url != initial_url
            )
            return True
        except TimeoutException:
            return False
    
    @staticmethod
    def wait_for_url_contains(driver, text, timeout=10):
        """Wait for URL to contain specific text."""
        try:
            WebDriverWait(driver, timeout).until(
                EC.url_contains(text)
            )
            return True
        except TimeoutException:
            return False
    
    @staticmethod
    def wait_for_title_change(driver, timeout=10):
        """Wait for page title to change."""
        initial_title = driver.title
        try:
            WebDriverWait(driver, timeout).until(
                lambda d: d.title != initial_title
            )
            return True
        except TimeoutException:
            return False
    
    @staticmethod
    def wait_for_element_count(driver, selector, expected_count, timeout=10):
        """Wait for specific number of elements to be present."""
        try:
            WebDriverWait(driver, timeout).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, selector)) == expected_count
            )
            return True
        except TimeoutException:
            return False
    
    @staticmethod
    def wait_for_element_count_greater_than(driver, selector, min_count, timeout=10):
        """Wait for element count to be greater than specified value."""
        try:
            WebDriverWait(driver, timeout).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, selector)) > min_count
            )
            return True
        except TimeoutException:
            return False
    
    @staticmethod
    def wait_for_loading_to_disappear(driver, timeout=30):
        """Wait for common loading indicators to disappear."""
        loading_selectors = [
            ".loading",
            ".spinner",
            ".loader",
            "[data-loading='true']",
            ".progress-bar",
            ".loading-overlay",
            ".sk-fading-circle",
            ".fa-spinner",
            ".spinner-border"
        ]
        
        for selector in loading_selectors:
            try:
                # Wait for loading indicator to appear first (optional)
                try:
                    WebDriverWait(driver, 2).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                except TimeoutException:
                    continue  # Loading indicator never appeared
                
                # Wait for it to disappear
                WebDriverWait(driver, timeout).until_not(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
            except TimeoutException:
                continue
        
        return True
    
    @staticmethod
    def wait_for_text_present(driver, text, timeout=10):
        """Wait for specific text to appear anywhere on the page."""
        try:
            WebDriverWait(driver, timeout).until(
                EC.text_to_be_present_in_element((By.TAG_NAME, "body"), text)
            )
            return True
        except TimeoutException:
            return False
    
    @staticmethod
    def wait_for_text_not_present(driver, text, timeout=10):
        """Wait for specific text to disappear from the page."""
        try:
            WebDriverWait(driver, timeout).until_not(
                EC.text_to_be_present_in_element((By.TAG_NAME, "body"), text)
            )
            return True
        except TimeoutException:
            return False
    
    @staticmethod
    def wait_with_polls(driver, condition_func, timeout=10, poll_frequency=0.5):
        """Wait with custom polling condition."""
        end_time = time.time() + timeout
        
        while time.time() < end_time:
            try:
                if condition_func(driver):
                    return True
            except Exception:
                pass
            time.sleep(poll_frequency)
        
        return False
    
    @staticmethod
    def smart_wait_for_element(driver, selectors, condition="presence", timeout=10):
        """Smart waiting for elements with multiple selectors and conditions."""
        conditions = {
            "presence": EC.presence_of_element_located,
            "visible": EC.visibility_of_element_located,
            "clickable": EC.element_to_be_clickable,
            "invisible": EC.invisibility_of_element_located
        }
        
        if condition not in conditions:
            condition = "presence"
        
        for selector in selectors:
            try:
                if selector.startswith("//"):
                    element = WebDriverWait(driver, timeout).until(
                        conditions[condition]((By.XPATH, selector))
                    )
                else:
                    element = WebDriverWait(driver, timeout).until(
                        conditions[condition]((By.CSS_SELECTOR, selector))
                    )
                return element
            except TimeoutException:
                continue
        
        return None
    
    @staticmethod
    def wait_for_stable_element(driver, selector, stability_time=1.0, timeout=10):
        """Wait for element position and size to stabilize."""
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            
            # Wait for element to stabilize
            stable_start = time.time()
            last_rect = None
            
            while time.time() - stable_start < stability_time:
                current_rect = driver.execute_script("""
                    var rect = arguments[0].getBoundingClientRect();
                    return {x: rect.x, y: rect.y, width: rect.width, height: rect.height};
                """, element)
                
                if last_rect and current_rect != last_rect:
                    stable_start = time.time()  # Reset stability timer
                
                last_rect = current_rect
                time.sleep(0.1)
            
            return element
            
        except TimeoutException:
            return None
    
    @staticmethod
    def wait_for_network_idle(driver, idle_time=2.0, timeout=30):
        """Wait for network activity to be idle."""
        try:
            # Enable performance logging if not already enabled
            driver.execute_cdp_cmd('Network.enable', {})
            
            end_time = time.time() + timeout
            last_activity = time.time()
            
            while time.time() < end_time:
                # Check for network activity
                logs = driver.get_log('performance')
                
                network_events = [log for log in logs if 
                                'Network.' in log['message']['method']]
                
                if network_events:
                    last_activity = time.time()
                
                # Check if we've been idle long enough
                if time.time() - last_activity >= idle_time:
                    return True
                
                time.sleep(0.2)
            
            return False
            
        except Exception:
            # Fallback to simple wait if CDP not available
            time.sleep(idle_time)
            return True