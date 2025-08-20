"""
GitHub Service for Web Automation

Automates GitHub interactions including issue creation and repository operations.
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from ..core.error_handler import ErrorHandler


class GitHubService:
    """Service for automating GitHub interactions."""
    
    def __init__(self, browser_manager):
        self.browser_manager = browser_manager
        self.error_handler = ErrorHandler()
        self.base_url = "https://github.com"
    
    def navigate_to_repo(self, driver, repo_path):
        """Navigate to a specific GitHub repository."""
        repo_url = f"{self.base_url}/{repo_path}"
        self.error_handler.log_info(f"Navigating to repository: {repo_url}")
        
        driver.get(repo_url)
        
        try:
            # Wait for repository page to load
            WebDriverWait(driver, 15).until(
                EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='repository-name']")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1[itemprop='name']")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".js-repo-nav"))
                )
            )
            self.error_handler.log_info("Repository page loaded successfully")
            return True
        except TimeoutException:
            self.error_handler.log_error("Repository page load timeout")
            return False
    
    def create_issue(self, driver, repo_path, title, body, labels=None):
        """Create a new issue in the specified repository."""
        try:
            # Navigate to repository
            if not self.navigate_to_repo(driver, repo_path):
                raise Exception("Failed to navigate to repository")
            
            # Click on Issues tab
            issues_selectors = [
                "a[data-content='Issues']",
                "a[href*='/issues']",
                "#issues-tab",
                "//a[contains(text(), 'Issues')]"
            ]
            
            issues_tab = None
            for selector in issues_selectors:
                try:
                    if selector.startswith("//"):
                        issues_tab = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        issues_tab = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    break
                except TimeoutException:
                    continue
            
            if not issues_tab:
                raise Exception("Could not find Issues tab")
            
            self.browser_manager.safe_click(driver, issues_tab)
            time.sleep(2)
            
            # Click "New issue" button
            new_issue_selectors = [
                "a[data-testid='new-issue-button']",
                ".btn-primary[href*='issues/new']",
                "//a[contains(text(), 'New issue')]",
                ".btn[href$='/issues/new']"
            ]
            
            new_issue_btn = None
            for selector in new_issue_selectors:
                try:
                    if selector.startswith("//"):
                        new_issue_btn = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        new_issue_btn = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    break
                except TimeoutException:
                    continue
            
            if not new_issue_btn:
                raise Exception("Could not find New Issue button")
            
            self.browser_manager.safe_click(driver, new_issue_btn)
            
            # Wait for new issue form
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='issue[title]'], #issue_title"))
            )
            
            # Fill title
            title_field = driver.find_element(By.CSS_SELECTOR, "input[name='issue[title]'], #issue_title")
            title_field.clear()
            title_field.send_keys(title)
            time.sleep(1)
            
            # Fill body
            body_selectors = [
                "textarea[name='issue[body]']",
                "#issue_body",
                ".js-comment-field-placeholder textarea"
            ]
            
            body_field = None
            for selector in body_selectors:
                try:
                    body_field = driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not body_field:
                raise Exception("Could not find issue body field")
            
            body_field.clear()
            body_field.send_keys(body)
            time.sleep(1)
            
            # Add labels if specified
            if labels:
                self._add_labels_to_issue(driver, labels)
            
            # Submit issue
            submit_selectors = [
                ".btn-primary[type='submit']",
                "button[data-testid='submit-new-issue-button']",
                ".btn-primary:contains('Submit new issue')",
                "//button[contains(text(), 'Submit')]"
            ]
            
            submit_btn = None
            for selector in submit_selectors:
                try:
                    if selector.startswith("//"):
                        submit_btn = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        submit_btn = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    break
                except TimeoutException:
                    continue
            
            if not submit_btn:
                raise Exception("Could not find submit button")
            
            self.browser_manager.safe_click(driver, submit_btn)
            
            # Wait for issue creation confirmation
            time.sleep(3)
            
            # Get issue URL
            current_url = driver.current_url
            if "/issues/" in current_url:
                self.error_handler.log_info(f"Issue created successfully: {current_url}")
                return current_url
            else:
                raise Exception("Issue creation may have failed")
            
        except Exception as e:
            self.error_handler.handle_error(e, f"Creating issue in {repo_path}")
            return None
    
    def _add_labels_to_issue(self, driver, labels):
        """Add labels to an issue during creation."""
        try:
            # Click on Labels gear icon
            labels_gear = driver.find_element(By.CSS_SELECTOR, ".sidebar-labels .octicon-gear")
            self.browser_manager.safe_click(driver, labels_gear)
            
            # Wait for labels dropdown
            time.sleep(1)
            
            # Add each label
            for label in labels:
                try:
                    label_checkbox = driver.find_element(By.XPATH, f"//span[text()='{label}']/../..//input[@type='checkbox']")
                    if not label_checkbox.is_selected():
                        self.browser_manager.safe_click(driver, label_checkbox)
                except NoSuchElementException:
                    self.error_handler.log_warning(f"Label '{label}' not found")
            
            # Click outside to close dropdown
            title_field = driver.find_element(By.CSS_SELECTOR, "input[name='issue[title]']")
            self.browser_manager.safe_click(driver, title_field)
            
        except Exception as e:
            self.error_handler.log_warning(f"Failed to add labels: {str(e)}")
    
    def get_repository_info(self, driver, repo_path):
        """Get basic information about a repository."""
        try:
            if not self.navigate_to_repo(driver, repo_path):
                raise Exception("Failed to navigate to repository")
            
            repo_info = {}
            
            # Get repository name and description
            try:
                repo_name = driver.find_element(By.CSS_SELECTOR, "[data-testid='repository-name'], h1[itemprop='name']").text
                repo_info['name'] = repo_name
            except NoSuchElementException:
                pass
            
            try:
                description = driver.find_element(By.CSS_SELECTOR, "[data-testid='repository-description'], p[itemprop='about']").text
                repo_info['description'] = description
            except NoSuchElementException:
                pass
            
            # Get stats
            try:
                stats_elements = driver.find_elements(By.CSS_SELECTOR, ".Counter")
                if len(stats_elements) >= 3:
                    repo_info['stars'] = stats_elements[0].text
                    repo_info['forks'] = stats_elements[1].text
            except:
                pass
            
            # Get language
            try:
                language = driver.find_element(By.CSS_SELECTOR, "[data-testid='repository-language'], .ml-0[itemprop='programmingLanguage']").text
                repo_info['language'] = language
            except NoSuchElementException:
                pass
            
            return repo_info
            
        except Exception as e:
            self.error_handler.handle_error(e, f"Getting repository info for {repo_path}")
            return {}
    
    def search_repositories(self, driver, query, language=None, sort="best-match"):
        """Search for repositories on GitHub."""
        try:
            # Build search URL
            search_url = f"{self.base_url}/search?q={query.replace(' ', '+')}"
            if language:
                search_url += f"+language:{language}"
            search_url += f"&type=Repositories&s={sort}"
            
            self.error_handler.log_info(f"Searching repositories: {search_url}")
            driver.get(search_url)
            
            # Wait for search results
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".repo-list-item, [data-testid='results-list']"))
            )
            
            # Extract repository results
            repo_elements = driver.find_elements(By.CSS_SELECTOR, ".repo-list-item")[:10]  # Limit to first 10
            
            repositories = []
            for repo_elem in repo_elements:
                try:
                    repo_info = {}
                    
                    # Get repository name and URL
                    name_link = repo_elem.find_element(By.CSS_SELECTOR, ".f4 a")
                    repo_info['name'] = name_link.text
                    repo_info['url'] = name_link.get_attribute('href')
                    
                    # Get description
                    try:
                        description = repo_elem.find_element(By.CSS_SELECTOR, ".mb-1 p").text
                        repo_info['description'] = description
                    except NoSuchElementException:
                        repo_info['description'] = ""
                    
                    # Get language and stars
                    try:
                        metadata = repo_elem.find_elements(By.CSS_SELECTOR, ".f6 .ml-0, .f6 .muted-link")
                        for elem in metadata:
                            text = elem.text.strip()
                            if text and not text.startswith("Updated"):
                                if "★" in text or "star" in text.lower():
                                    repo_info['stars'] = text
                                else:
                                    repo_info['language'] = text
                    except:
                        pass
                    
                    repositories.append(repo_info)
                    
                except Exception as e:
                    self.error_handler.log_warning(f"Failed to extract repository info: {str(e)}")
                    continue
            
            self.error_handler.log_info(f"Found {len(repositories)} repositories")
            return repositories
            
        except Exception as e:
            self.error_handler.handle_error(e, f"Searching repositories for: {query}")
            return []
    
    def create_issue_complete(self, repo_path, title, body, labels=None, driver=None):
        """Complete workflow to create an issue."""
        if driver is None:
            with self.browser_manager.connect() as browser:
                return self.create_issue(browser, repo_path, title, body, labels)
        else:
            return self.create_issue(driver, repo_path, title, body, labels)