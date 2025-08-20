"""
Gmail Service for Web Automation

Automates Gmail interactions including sending emails and reading inbox.
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from ..core.error_handler import ErrorHandler


class GmailService:
    """Service for automating Gmail interactions."""
    
    def __init__(self, browser_manager):
        self.browser_manager = browser_manager
        self.error_handler = ErrorHandler()
        self.base_url = "https://mail.google.com"
    
    def navigate_to_gmail(self, driver):
        """Navigate to Gmail and wait for interface to load."""
        self.error_handler.log_info("Navigating to Gmail...")
        
        driver.get(self.base_url)
        
        try:
            # Wait for Gmail interface to load
            WebDriverWait(driver, 20).until(
                EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-tooltip='Compose']")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='button'][aria-label*='Compose']")),
                    EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Compose')]"))
                )
            )
            self.error_handler.log_info("Gmail loaded successfully")
            return True
        except TimeoutException:
            # Check if we need to sign in
            if "accounts.google.com" in driver.current_url:
                self.error_handler.log_warning("Gmail requires authentication")
                return False
            else:
                self.error_handler.log_error("Gmail interface not found")
                return False
    
    def start_compose(self, driver):
        """Start composing a new email."""
        # Try different selectors for the compose button
        compose_selectors = [
            "[data-tooltip='Compose']",
            "div[role='button'][aria-label*='Compose']",
            "//div[contains(text(), 'Compose')]",
            ".T-I.T-I-KE.L3"  # Gmail's compose button class
        ]
        
        for selector in compose_selectors:
            try:
                if selector.startswith("//"):
                    compose_btn = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                else:
                    compose_btn = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                
                self.browser_manager.safe_click(driver, compose_btn)
                self.error_handler.log_info("Compose window opened")
                return True
                
            except TimeoutException:
                continue
        
        raise Exception("Could not find compose button")
    
    def fill_email_fields(self, driver, to_email, subject, body):
        """Fill in email fields in the compose window."""
        try:
            # Wait for compose window to appear
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='to'], textarea[name='to']"))
            )
            
            # Fill TO field
            to_field = driver.find_element(By.CSS_SELECTOR, "input[name='to'], textarea[name='to']")
            to_field.clear()
            to_field.send_keys(to_email)
            time.sleep(1)
            
            # Fill Subject field
            subject_field = driver.find_element(By.CSS_SELECTOR, "input[name='subjectbox'], input[placeholder*='Subject']")
            subject_field.clear()
            subject_field.send_keys(subject)
            time.sleep(1)
            
            # Fill Body field
            body_selectors = [
                "div[role='textbox'][aria-label*='Message']",
                "div[contenteditable='true']",
                "textarea[aria-label*='Message']"
            ]
            
            body_field = None
            for selector in body_selectors:
                try:
                    body_field = driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not body_field:
                raise Exception("Could not find email body field")
            
            body_field.clear()
            body_field.send_keys(body)
            time.sleep(1)
            
            self.error_handler.log_info("Email fields filled successfully")
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, "Filling email fields")
            return False
    
    def send_email(self, driver):
        """Send the composed email."""
        try:
            # Find send button
            send_selectors = [
                "div[role='button'][data-tooltip*='Send']",
                "div[role='button'][aria-label*='Send']",
                "//div[contains(text(), 'Send')]",
                ".T-I.J-J5-Ji.aoO.v7.T-I-atl.L3"  # Gmail send button class
            ]
            
            for selector in send_selectors:
                try:
                    if selector.startswith("//"):
                        send_btn = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        send_btn = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    
                    self.browser_manager.safe_click(driver, send_btn)
                    self.error_handler.log_info("Email sent successfully")
                    return True
                    
                except TimeoutException:
                    continue
            
            # Fallback: try keyboard shortcut
            body_field = driver.find_element(By.CSS_SELECTOR, "div[contenteditable='true']")
            body_field.send_keys(Keys.CONTROL + Keys.RETURN)
            self.error_handler.log_info("Email sent using keyboard shortcut")
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, "Sending email")
            return False
    
    def send_email_complete(self, to_email, subject, body, driver=None):
        """Complete email sending workflow."""
        if driver is None:
            with self.browser_manager.connect() as browser:
                return self._send_email_with_browser(browser, to_email, subject, body)
        else:
            return self._send_email_with_browser(driver, to_email, subject, body)
    
    def _send_email_with_browser(self, driver, to_email, subject, body):
        """Internal method to send email with provided driver."""
        try:
            # Navigate to Gmail
            if not self.navigate_to_gmail(driver):
                raise Exception("Failed to navigate to Gmail")
            
            # Start compose
            if not self.start_compose(driver):
                raise Exception("Failed to start compose")
            
            # Fill fields
            if not self.fill_email_fields(driver, to_email, subject, body):
                raise Exception("Failed to fill email fields")
            
            # Send email
            if not self.send_email(driver):
                raise Exception("Failed to send email")
            
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, "Sending email")
            return False
    
    def get_inbox_emails(self, driver=None, limit=10):
        """Get recent emails from inbox."""
        if driver is None:
            with self.browser_manager.connect() as browser:
                return self._get_inbox_with_browser(browser, limit)
        else:
            return self._get_inbox_with_browser(driver, limit)
    
    def _get_inbox_with_browser(self, driver, limit):
        """Internal method to get inbox emails with provided driver."""
        try:
            # Navigate to Gmail
            if not self.navigate_to_gmail(driver):
                raise Exception("Failed to navigate to Gmail")
            
            # Wait for inbox to load
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "tr[class*='zA']"))
            )
            
            # Get email rows
            email_rows = driver.find_elements(By.CSS_SELECTOR, "tr[class*='zA']")[:limit]
            
            emails = []
            for row in email_rows:
                try:
                    # Extract email info
                    sender_elem = row.find_element(By.CSS_SELECTOR, "span[email], .go span")
                    subject_elem = row.find_element(By.CSS_SELECTOR, ".bog, .y6 span")
                    date_elem = row.find_element(By.CSS_SELECTOR, ".xY span")
                    
                    email_info = {
                        'sender': sender_elem.get_attribute('email') or sender_elem.text,
                        'subject': subject_elem.text,
                        'date': date_elem.text,
                        'read': 'zE' not in row.get_attribute('class')  # Unread emails have 'zE' class
                    }
                    
                    emails.append(email_info)
                    
                except Exception as e:
                    self.error_handler.log_warning(f"Failed to extract email info: {str(e)}")
                    continue
            
            self.error_handler.log_info(f"Retrieved {len(emails)} emails from inbox")
            return emails
            
        except Exception as e:
            self.error_handler.handle_error(e, "Getting inbox emails")
            return []
    
    def search_emails(self, query, driver=None):
        """Search for emails matching a query."""
        if driver is None:
            with self.browser_manager.connect() as browser:
                return self._search_emails_with_browser(browser, query)
        else:
            return self._search_emails_with_browser(driver, query)
    
    def _search_emails_with_browser(self, driver, query):
        """Internal method to search emails with provided driver."""
        try:
            # Navigate to Gmail
            if not self.navigate_to_gmail(driver):
                raise Exception("Failed to navigate to Gmail")
            
            # Find search box
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[aria-label*='Search']"))
            )
            
            # Enter search query
            search_box.clear()
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)
            
            # Wait for search results
            time.sleep(3)
            
            # Get search results using same method as inbox
            return self._get_inbox_with_browser(driver, limit=20)
            
        except Exception as e:
            self.error_handler.handle_error(e, f"Searching emails for: {query}")
            return []