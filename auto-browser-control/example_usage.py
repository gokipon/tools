#!/usr/bin/env python3
"""
Example Usage Script for Auto-Browser-Control

Demonstrates various features and use cases of the web automation library.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add the web_automation module to path
sys.path.insert(0, str(Path(__file__).parent))

from web_automation import WebAutomation
from web_automation.config.settings import get_settings


def example_basic_usage():
    """Basic usage example with Perplexity service."""
    print("\\n=== Basic Usage Example ===")
    
    try:
        # Initialize automation
        automation = WebAutomation(port=9222)
        
        # Connect and use Perplexity service
        with automation.connect() as browser:
            print("Connected to browser successfully!")
            
            perplexity = automation.service('perplexity')
            question = "What are the key benefits of automation in daily workflows?"
            
            print(f"Asking question: {question}")
            result = perplexity.ask_question(question, browser, timeout=30)
            
            if result:
                print(f"\\nReceived answer ({len(result)} characters)")
                print(f"First 200 characters: {result[:200]}...")
                
                # Save result
                output_path = automation.save_result(result, "basic_example.md")
                print(f"Results saved to: {output_path}")
            else:
                print("No result received")
                
    except Exception as e:
        print(f"Error in basic usage example: {str(e)}")


def example_obsidian_integration():
    """Example demonstrating Obsidian integration."""
    print("\\n=== Obsidian Integration Example ===")
    
    try:
        # Get settings
        settings = get_settings()
        
        # Initialize automation
        automation = WebAutomation(port=9222)
        
        # Create sample template content
        sample_template = """# Research Query

## Context
Based on my recent thoughts and notes:

{{diary_content}}

## Question
Please provide insights about productivity and automation, focusing on:
1. Latest trends and tools
2. Practical implementation tips
3. Common challenges and solutions

Keep the response actionable and specific.
"""
        
        # Create sample diary content
        sample_diary = """# Daily Note - {date}

## Thoughts
- Been thinking about improving my daily workflow
- Want to learn more about automation tools
- Looking for ways to be more productive

## Goals
- Implement better note-taking system
- Automate repetitive tasks
- Research productivity methodologies
""".format(date=datetime.now().strftime('%Y-%m-%d'))
        
        # Create temporary files
        temp_dir = Path("/tmp/obsidian_example")
        temp_dir.mkdir(exist_ok=True)
        
        template_path = temp_dir / "template.md"
        diary_path = temp_dir / "diary.md"
        
        with open(template_path, 'w') as f:
            f.write(sample_template)
        
        with open(diary_path, 'w') as f:
            f.write(sample_diary)
        
        print(f"Created temporary template: {template_path}")
        print(f"Created temporary diary: {diary_path}")
        
        # Build prompt from template and diary
        prompt = automation.build_prompt(str(template_path), str(diary_path))
        
        print(f"\\nBuilt prompt from template and diary:")
        print(f"Prompt length: {len(prompt)} characters")
        print(f"First 300 characters:\\n{prompt[:300]}...")
        
        # Clean up temp files
        template_path.unlink()
        diary_path.unlink()
        temp_dir.rmdir()
        
    except Exception as e:
        print(f"Error in Obsidian integration example: {str(e)}")


def example_gmail_service():
    """Example demonstrating Gmail service (requires authentication)."""
    print("\\n=== Gmail Service Example ===")
    print("Note: This requires you to be logged into Gmail in the browser")
    
    try:
        automation = WebAutomation(port=9222)
        
        # This is a demo - don't actually send emails in examples
        print("Demo: Would send email with Gmail service")
        print("Actual usage:")
        print("""
        gmail = automation.service('gmail')
        success = gmail.send_email_complete(
            to_email="recipient@example.com",
            subject="Test Email from Automation",
            body="This email was sent using auto-browser-control!"
        )
        """)
        
        # Example of getting inbox instead (safer for demo)
        with automation.connect() as browser:
            gmail = automation.service('gmail')
            
            # Navigate to Gmail to check if accessible
            if gmail.navigate_to_gmail(browser):
                print("Successfully navigated to Gmail")
                print("Gmail service is ready for email operations")
            else:
                print("Gmail navigation failed - may need authentication")
                
    except Exception as e:
        print(f"Error in Gmail service example: {str(e)}")


def example_github_service():
    """Example demonstrating GitHub service."""
    print("\\n=== GitHub Service Example ===")
    
    try:
        automation = WebAutomation(port=9222)
        
        with automation.connect() as browser:
            github = automation.service('github')
            
            # Get repository information
            repo_info = github.get_repository_info(browser, "microsoft/vscode")
            
            if repo_info:
                print("Retrieved repository information:")
                for key, value in repo_info.items():
                    print(f"  {key}: {value}")
            else:
                print("Could not retrieve repository information")
            
            # Search repositories
            search_results = github.search_repositories(
                browser, 
                "python automation", 
                language="python"
            )
            
            if search_results:
                print(f"\\nFound {len(search_results)} repositories:")
                for i, repo in enumerate(search_results[:3]):  # Show first 3
                    print(f"  {i+1}. {repo.get('name', 'Unknown')}")
                    print(f"     {repo.get('description', 'No description')[:100]}...")
            
    except Exception as e:
        print(f"Error in GitHub service example: {str(e)}")


def example_generic_service():
    """Example demonstrating generic service capabilities."""
    print("\\n=== Generic Service Example ===")
    
    try:
        automation = WebAutomation(port=9222)
        
        with automation.connect() as browser:
            generic = automation.service('generic')
            
            # Navigate to a simple website
            if generic.navigate_to_url(browser, "https://httpbin.org"):
                print("Successfully navigated to httpbin.org")
                
                # Get page title
                title = browser.title
                print(f"Page title: {title}")
                
                # Take screenshot
                screenshot_path = generic.take_screenshot_with_context(
                    browser, "generic_example"
                )
                if screenshot_path:
                    print(f"Screenshot saved: {screenshot_path}")
                
                # Wait for page load complete
                if generic.wait_for_page_load_complete(browser):
                    print("Page load completed successfully")
                
            else:
                print("Navigation failed")
                
    except Exception as e:
        print(f"Error in generic service example: {str(e)}")


def example_screenshot_utilities():
    """Example demonstrating screenshot utilities."""
    print("\\n=== Screenshot Utilities Example ===")
    
    try:
        from web_automation.utils.screenshot import ScreenshotHelper
        
        automation = WebAutomation(port=9222)
        screenshot_helper = ScreenshotHelper()
        
        with automation.connect() as browser:
            # Navigate to a page
            browser.get("https://www.example.com")
            
            # Take regular screenshot
            regular_shot = screenshot_helper.take_screenshot(browser, "example_regular.png")
            print(f"Regular screenshot: {regular_shot}")
            
            # Take full page screenshot
            full_shot = screenshot_helper.take_full_page_screenshot(browser, "example_full.png")
            print(f"Full page screenshot: {full_shot}")
            
            # Get screenshot metadata
            metadata = screenshot_helper.get_screenshot_metadata(browser, regular_shot)
            print(f"Screenshot metadata: {metadata}")
            
    except Exception as e:
        print(f"Error in screenshot utilities example: {str(e)}")


def example_configuration():
    """Example demonstrating configuration management."""
    print("\\n=== Configuration Management Example ===")
    
    try:
        # Get default settings
        settings = get_settings()
        
        print("Current configuration:")
        print(f"  Chrome port: {settings.get('browser', 'port')}")
        print(f"  Obsidian vault: {settings.get('obsidian', 'vault_path')}")
        print(f"  Results directory: {settings.get('automation', 'results_dir')}")
        print(f"  Max retries: {settings.get('automation', 'max_retries')}")
        
        # Get specific config sections
        chrome_config = settings.get_chrome_options()
        obsidian_config = settings.get_obsidian_config()
        
        print(f"\\nChrome options: {chrome_config}")
        print(f"Obsidian config: {obsidian_config}")
        
        # Create sample config file
        sample_config_path = settings.create_sample_config("sample_config.json")
        if sample_config_path:
            print(f"\\nSample config created: {sample_config_path}")
        
    except Exception as e:
        print(f"Error in configuration example: {str(e)}")


def example_error_handling():
    """Example demonstrating error handling capabilities."""
    print("\\n=== Error Handling Example ===")
    
    try:
        from web_automation.core.error_handler import ErrorHandler
        
        handler = ErrorHandler()
        
        # Example of retry decorator
        @handler.retry_on_failure(max_retries=2, delay=1)
        def potentially_failing_function():
            import random
            if random.random() < 0.7:  # 70% chance of failure
                raise Exception("Simulated failure")
            return "Success!"
        
        # Test retry mechanism
        try:
            result = potentially_failing_function()
            print(f"Function result: {result}")
        except Exception as e:
            print(f"Function failed after retries: {str(e)}")
        
        # Example of safe execution
        def risky_function():
            raise ValueError("This always fails")
        
        result = handler.safe_execute(
            risky_function, 
            default_return="Safe fallback value",
            context="Safe execution example"
        )
        print(f"Safe execution result: {result}")
        
    except Exception as e:
        print(f"Error in error handling example: {str(e)}")


def main():
    """Run all examples."""
    print("Auto-Browser-Control Example Usage")
    print("==================================")
    print("\\nMake sure Chrome is running with:")
    print("google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug")
    
    # Check if Chrome is accessible
    try:
        import requests
        response = requests.get("http://localhost:9222/json/version", timeout=5)
        if response.status_code == 200:
            print(f"✓ Chrome debugging accessible on port 9222")
        else:
            print("✗ Chrome debugging not accessible")
            return
    except Exception:
        print("✗ Chrome debugging not accessible - please start Chrome first")
        return
    
    # Run examples
    examples = [
        example_configuration,
        example_error_handling,
        example_obsidian_integration,
        example_screenshot_utilities,
        example_generic_service,
        example_github_service,
        example_gmail_service,
        example_basic_usage,
    ]
    
    for example_func in examples:
        try:
            example_func()
        except KeyboardInterrupt:
            print("\\nExamples interrupted by user")
            break
        except Exception as e:
            print(f"\\nExample {example_func.__name__} failed: {str(e)}")
        
        input("\\nPress Enter to continue to next example...")
    
    print("\\n=== Examples Complete ===")
    print("Check the output directories for generated files:")
    print("  ~/automation_results/ - Saved results")
    print("  ~/automation_screenshots/ - Screenshots")


if __name__ == "__main__":
    main()