"""
Perplexity Service for Web Automation

Automates question submission and answer retrieval from Perplexity.ai.
Uses robust element detection and retry logic.
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from ..core.error_handler import ErrorHandler


class PerplexityService:
    """Service for automating Perplexity.ai interactions."""
    
    def __init__(self, browser_manager):
        self.browser_manager = browser_manager
        self.error_handler = ErrorHandler()
        self.base_url = "https://www.perplexity.ai"
    
    def get_element_selectors(self):
        """Get various selectors to try for Perplexity elements."""
        return {
            'search_input': [
                'textarea[placeholder*="Ask anything"]',
                'input[placeholder*="Ask anything"]',
                'textarea[name="q"]',
                'textarea[data-testid="search-input"]',
                '.search-input textarea',
                '[role="textbox"]',
                'textarea:first-of-type',
                'input[type="search"]'
            ],
            'submit_button': [
                'button[aria-label*="Submit"]',
                'button[type="submit"]',
                'button:has(svg)',
                '.submit-button',
                '[data-testid="submit-button"]',
                'button:last-of-type'
            ],
            'answer_container': [
                '[data-testid="answer"]',
                '.answer-container',
                '.response-container',
                '.main-content',
                'main article',
                '[role="main"] > div',
                '.prose'
            ]
        }
    
    def find_element_with_fallbacks(self, driver, element_type, timeout=10):
        """Try multiple selectors to find an element."""
        selectors = self.get_element_selectors()[element_type]
        
        for selector in selectors:
            try:
                element = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                self.error_handler.log_info(f"Found {element_type} using selector: {selector}")
                return element
            except TimeoutException:
                continue
        
        # If no CSS selectors work, try XPath fallbacks
        xpath_selectors = {
            'search_input': [
                "//textarea[contains(@placeholder, 'Ask') or contains(@placeholder, 'Search')]",
                "//input[contains(@placeholder, 'Ask') or contains(@placeholder, 'Search')]",
                "//textarea[1]",
                "//input[@type='search']"
            ],
            'submit_button': [
                "//button[contains(@aria-label, 'Submit') or contains(@title, 'Submit')]",
                "//button[@type='submit']",
                "//button[contains(., 'Search') or contains(., 'Ask')]",
                "//button[svg]"
            ],
            'answer_container': [
                "//*[contains(@class, 'answer') or contains(@class, 'response')]",
                "//main//article",
                "//div[contains(@class, 'prose') or contains(@class, 'content')]"
            ]
        }
        
        if element_type in xpath_selectors:
            for xpath in xpath_selectors[element_type]:
                try:
                    element = WebDriverWait(driver, timeout).until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
                    self.error_handler.log_info(f"Found {element_type} using XPath: {xpath}")
                    return element
                except TimeoutException:
                    continue
        
        return None
    
    @ErrorHandler().retry_on_failure(max_retries=2, delay=3)
    def navigate_to_perplexity(self, driver):
        """Navigate to Perplexity.ai and wait for page load."""
        self.error_handler.log_info("Navigating to Perplexity.ai...")
        
        driver.get(self.base_url)
        
        # Wait for page to load
        try:
            WebDriverWait(driver, 15).until(
                EC.any_of(
                    EC.presence_of_element_located((By.TAG_NAME, "textarea")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='search']")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[role='textbox']"))
                )
            )
            self.error_handler.log_info("Page loaded successfully")
            return True
        except TimeoutException:
            self.error_handler.log_error("Page load timeout")
            return False
    
    @ErrorHandler().retry_on_failure(max_retries=3, delay=2)
    def submit_question(self, driver, question):
        """Submit a question to Perplexity."""
        self.error_handler.log_info(f"Submitting question: {question[:100]}...")
        
        # Find search input
        search_input = self.find_element_with_fallbacks(driver, 'search_input', timeout=15)
        if not search_input:
            raise Exception("Could not find search input field")
        
        # Clear and enter question
        search_input.clear()
        time.sleep(0.5)
        search_input.send_keys(question)
        time.sleep(1)
        
        # Try to submit via Enter key first
        try:
            search_input.send_keys(Keys.RETURN)
            self.error_handler.log_info("Submitted question using Enter key")
            return True
        except:
            pass
        
        # Fallback: try to find and click submit button
        submit_button = self.find_element_with_fallbacks(driver, 'submit_button', timeout=5)
        if submit_button:
            if self.browser_manager.safe_click(driver, submit_button):
                self.error_handler.log_info("Submitted question using submit button")
                return True
        
        # Last resort: try JavaScript submission
        try:
            driver.execute_script("""
                var forms = document.querySelectorAll('form');
                if (forms.length > 0) {
                    forms[0].submit();
                }
            """)
            self.error_handler.log_info("Submitted question using JavaScript")
            return True
        except:
            pass
        
        raise Exception("Failed to submit question")
    
    def wait_for_response(self, driver, timeout=60):
        """Wait for Perplexity to generate a response."""
        self.error_handler.log_info("Waiting for response...")
        
        # Wait for loading to start (if there's a loading indicator)
        time.sleep(2)
        
        # Wait for response to appear
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check for answer content
            answer_element = self.find_element_with_fallbacks(driver, 'answer_container', timeout=2)
            
            if answer_element:
                # Check if content is substantial (not just loading text)
                content = answer_element.text.strip()
                if len(content) > 50 and not any(loading_text in content.lower() 
                    for loading_text in ['loading', 'searching', 'thinking', 'generating']):
                    self.error_handler.log_info(f"Response received ({len(content)} characters)")
                    return answer_element
            
            # Check for any main content that might contain the answer
            try:
                main_content = driver.find_element(By.TAG_NAME, "main")
                if main_content and len(main_content.text.strip()) > 100:
                    return main_content
            except NoSuchElementException:
                pass
            
            time.sleep(2)
        
        raise TimeoutException("Timeout waiting for response")
    
    def extract_response_text(self, response_element, driver):
        """Extract clean text from response element."""
        try:
            # Get the text content
            response_text = response_element.text.strip()
            
            # Try to get better formatted content if available
            try:
                # Look for markdown or formatted content
                formatted_elements = driver.find_elements(By.CSS_SELECTOR, 
                    ".prose, .markdown, .answer-content, [data-testid='answer']")
                
                if formatted_elements:
                    formatted_text = "\\n\\n".join([elem.text.strip() for elem in formatted_elements if elem.text.strip()])
                    if len(formatted_text) > len(response_text):
                        response_text = formatted_text
            except:
                pass
            
            # Clean up the text
            lines = response_text.split('\\n')
            cleaned_lines = []
            
            for line in lines:
                line = line.strip()
                if line and not line.lower().startswith(('loading', 'searching', 'generating')):
                    cleaned_lines.append(line)
            
            return '\\n'.join(cleaned_lines)
            
        except Exception as e:
            self.error_handler.handle_error(e, "Extracting response text")
            return response_element.text if response_element else ""
    
    def ask_question(self, question, driver=None, timeout=60):
        """Ask a question and get the response."""
        if driver is None:
            # Use context manager to handle browser connection
            with self.browser_manager.connect() as browser:
                return self._ask_question_with_browser(browser, question, timeout)
        else:
            return self._ask_question_with_browser(driver, question, timeout)
    
    def _ask_question_with_browser(self, driver, question, timeout):
        """Internal method to ask question with provided driver."""
        try:
            # Navigate to Perplexity
            if not self.navigate_to_perplexity(driver):
                raise Exception("Failed to navigate to Perplexity")
            
            # Submit question
            if not self.submit_question(driver, question):
                raise Exception("Failed to submit question")
            
            # Wait for response
            response_element = self.wait_for_response(driver, timeout)
            
            # Extract response text
            response_text = self.extract_response_text(response_element, driver)
            
            if not response_text:
                raise Exception("No response text extracted")
            
            self.error_handler.log_info(f"Successfully retrieved response ({len(response_text)} characters)")
            return response_text
            
        except Exception as e:
            self.error_handler.handle_error(e, "Asking question on Perplexity")
            
            # Take screenshot for debugging
            try:
                screenshot_path = self.browser_manager.take_screenshot(driver)
                if screenshot_path:
                    self.error_handler.log_info(f"Debug screenshot saved: {screenshot_path}")
            except:
                pass
            
            raise
    
    def batch_questions(self, questions, delay_between=5):
        """Ask multiple questions with delay between them."""
        results = []
        
        with self.browser_manager.connect() as driver:
            for i, question in enumerate(questions):
                self.error_handler.log_info(f"Processing question {i+1}/{len(questions)}")
                
                try:
                    result = self._ask_question_with_browser(driver, question)
                    results.append({
                        'question': question,
                        'answer': result,
                        'success': True
                    })
                except Exception as e:
                    results.append({
                        'question': question,
                        'answer': str(e),
                        'success': False
                    })
                
                # Delay between questions to be respectful
                if i < len(questions) - 1:
                    time.sleep(delay_between)
        
        return results