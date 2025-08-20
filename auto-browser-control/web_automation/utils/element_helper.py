"""
Element Helper Utilities

Advanced element finding and interaction utilities with robust fallback strategies.
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException


class ElementHelper:
    """Helper class for robust element finding and interactions."""
    
    @staticmethod
    def smart_find_element(driver, text=None, tag=None, attributes=None, contains_text=None, timeout=10):
        """
        Smart element finder with multiple strategies.
        
        Args:
            driver: WebDriver instance
            text: Exact text content to match
            tag: HTML tag name
            attributes: Dict of attributes to match
            contains_text: Partial text content to match
            timeout: Maximum wait time
        """
        selectors = []
        
        # Build CSS selectors
        if tag and attributes:
            css_selector = tag
            for attr, value in attributes.items():
                if attr == 'class':
                    css_selector += f".{value.replace(' ', '.')}"
                else:
                    css_selector += f"[{attr}='{value}']"
            selectors.append(css_selector)
        
        # Build XPath selectors
        xpath_conditions = []
        
        if tag:
            xpath_base = f"//{tag}"
        else:
            xpath_base = "//*"
        
        if text:
            xpath_conditions.append(f"text()='{text}'")
        
        if contains_text:
            xpath_conditions.append(f"contains(text(), '{contains_text}')")
        
        if attributes:
            for attr, value in attributes.items():
                xpath_conditions.append(f"@{attr}='{value}'")
        
        if xpath_conditions:
            xpath_selector = xpath_base + "[" + " and ".join(xpath_conditions) + "]"
            selectors.append(xpath_selector)
        
        # Try each selector
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
                return element
            except TimeoutException:
                continue
        
        return None
    
    @staticmethod
    def find_clickable_element(driver, selectors, timeout=10):
        """Find a clickable element using multiple selectors."""
        for selector in selectors:
            try:
                if selector.startswith("//"):
                    element = WebDriverWait(driver, timeout).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                else:
                    element = WebDriverWait(driver, timeout).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                return element
            except TimeoutException:
                continue
        return None
    
    @staticmethod
    def robust_click(driver, element, max_attempts=3):
        """Perform a robust click with multiple strategies."""
        for attempt in range(max_attempts):
            try:
                # Ensure element is in view
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.3)
                
                # Try standard click
                element.click()
                return True
                
            except Exception as e:
                if "element click intercepted" in str(e).lower():
                    # Try JavaScript click
                    try:
                        driver.execute_script("arguments[0].click();", element)
                        return True
                    except:
                        pass
                
                if "stale element reference" in str(e).lower():
                    # Element became stale, need to re-find it
                    return False
                
                if attempt < max_attempts - 1:
                    time.sleep(0.5)
        
        return False
    
    @staticmethod
    def smart_input(driver, element, text, clear_first=True, typing_delay=0.05):
        """Smart text input with human-like typing."""
        try:
            if clear_first:
                element.clear()
                time.sleep(0.1)
            
            # Type with small delays to simulate human typing
            for char in text:
                element.send_keys(char)
                if typing_delay > 0:
                    time.sleep(typing_delay)
            
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def wait_for_element_state(driver, element, state="visible", timeout=10):
        """Wait for element to reach a specific state."""
        states = {
            "visible": EC.visibility_of,
            "invisible": EC.invisibility_of_element,
            "clickable": EC.element_to_be_clickable,
            "selected": EC.element_to_be_selected
        }
        
        if state not in states:
            return False
        
        try:
            WebDriverWait(driver, timeout).until(states[state](element))
            return True
        except TimeoutException:
            return False
    
    @staticmethod
    def find_elements_by_partial_link_text(driver, partial_text, case_sensitive=False):
        """Find elements containing partial link text with case option."""
        if case_sensitive:
            xpath = f"//a[contains(text(), '{partial_text}')]"
        else:
            xpath = f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{partial_text.lower()}')]"
        
        try:
            return driver.find_elements(By.XPATH, xpath)
        except:
            return []
    
    @staticmethod
    def get_element_center(driver, element):
        """Get the center coordinates of an element."""
        try:
            location = element.location
            size = element.size
            center_x = location['x'] + size['width'] / 2
            center_y = location['y'] + size['height'] / 2
            return (center_x, center_y)
        except:
            return None
    
    @staticmethod
    def highlight_element(driver, element, duration=1.0):
        """Highlight an element temporarily for debugging."""
        try:
            # Save original style
            original_style = element.get_attribute("style")
            
            # Apply highlight style
            driver.execute_script(
                "arguments[0].style.border='3px solid red'; arguments[0].style.backgroundColor='yellow';",
                element
            )
            
            time.sleep(duration)
            
            # Restore original style
            driver.execute_script(f"arguments[0].style='{original_style}';", element)
            
        except:
            pass
    
    @staticmethod
    def is_element_in_viewport(driver, element):
        """Check if element is currently visible in viewport."""
        try:
            return driver.execute_script("""
                var elem = arguments[0];
                var rect = elem.getBoundingClientRect();
                return (
                    rect.top >= 0 &&
                    rect.left >= 0 &&
                    rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
                );
            """, element)
        except:
            return False
    
    @staticmethod
    def scroll_element_into_center(driver, element):
        """Scroll element to center of viewport."""
        try:
            driver.execute_script("""
                arguments[0].scrollIntoView({
                    behavior: 'smooth',
                    block: 'center',
                    inline: 'center'
                });
            """, element)
            time.sleep(0.5)
            return True
        except:
            return False
    
    @staticmethod
    def find_parent_with_attribute(driver, element, attribute, value=None):
        """Find parent element with specific attribute."""
        try:
            if value:
                xpath = f".//ancestor::*[@{attribute}='{value}'][1]"
            else:
                xpath = f".//ancestor::*[@{attribute}][1]"
            
            return element.find_element(By.XPATH, xpath)
        except:
            return None
    
    @staticmethod
    def get_element_attributes(element):
        """Get all attributes of an element."""
        try:
            return element.get_property("attributes")
        except:
            return {}
    
    @staticmethod
    def element_screenshot(driver, element, filename=None):
        """Take screenshot of specific element."""
        try:
            if filename is None:
                filename = f"element_{int(time.time())}.png"
            
            # Scroll element into view
            ElementHelper.scroll_element_into_center(driver, element)
            
            # Take element screenshot
            element.screenshot(filename)
            return filename
        except:
            return None