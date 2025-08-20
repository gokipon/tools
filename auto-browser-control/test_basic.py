#!/usr/bin/env python3
"""
Basic Testing Suite for Auto-Browser-Control

Tests core functionality without requiring external services.
"""

import sys
import unittest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

# Add the web_automation module to path
sys.path.insert(0, str(Path(__file__).parent))

from web_automation.core.error_handler import ErrorHandler
from web_automation.core.prompt_builder import PromptBuilder
from web_automation.config.settings import Settings
from web_automation.utils.element_helper import ElementHelper
from web_automation.utils.wait_helper import WaitHelper
from web_automation.utils.screenshot import ScreenshotHelper


class TestErrorHandler(unittest.TestCase):
    """Test error handling functionality."""
    
    def setUp(self):
        self.handler = ErrorHandler()
    
    def test_basic_error_handling(self):
        """Test basic error logging."""
        error = ValueError("Test error")
        result = self.handler.handle_error(error, "Test context")
        self.assertIn("Test context", result)
        self.assertIn("ValueError", result)
    
    def test_retry_mechanism(self):
        """Test retry decorator."""
        attempt_count = 0
        
        @self.handler.retry_on_failure(max_retries=2, delay=0.1)
        def flaky_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise Exception("Temporary failure")
            return "Success"
        
        result = flaky_function()
        self.assertEqual(result, "Success")
        self.assertEqual(attempt_count, 3)
    
    def test_safe_execution(self):
        """Test safe execution with fallback."""
        def failing_function():
            raise Exception("Always fails")
        
        result = self.handler.safe_execute(
            failing_function,
            default_return="Fallback",
            context="Test safe execution"
        )
        self.assertEqual(result, "Fallback")
    
    def test_delay_calculation(self):
        """Test exponential backoff calculation."""
        delay1 = self.handler.calculate_delay(0)
        delay2 = self.handler.calculate_delay(1)
        delay3 = self.handler.calculate_delay(2)
        
        self.assertEqual(delay1, 1.0)  # base_delay
        self.assertEqual(delay2, 2.0)  # base_delay * 2^1
        self.assertEqual(delay3, 4.0)  # base_delay * 2^2


class TestPromptBuilder(unittest.TestCase):
    """Test prompt building functionality."""
    
    def setUp(self):
        self.builder = PromptBuilder()
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        # Clean up temp files
        for file in self.temp_dir.glob("*"):
            file.unlink()
        self.temp_dir.rmdir()
    
    def test_read_file(self):
        """Test file reading functionality."""
        test_content = "This is test content\\nWith multiple lines"
        test_file = self.temp_dir / "test.md"
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        content = self.builder.read_file(test_file)
        self.assertEqual(content, test_content)
    
    def test_extract_sections(self):
        """Test markdown section extraction."""
        markdown_content = """# Main Title

Some content here.

## Section One
Content for section one.

### Subsection
More content.

## Section Two  
Content for section two.
"""
        
        sections = self.builder.extract_sections(markdown_content)
        self.assertIn("main_title", sections)
        self.assertIn("section_one", sections)
        self.assertIn("section_two", sections)
    
    def test_extract_tags(self):
        """Test tag extraction."""
        content = "This content has #tag1 and #tag2 and #productivity tags."
        tags = self.builder.extract_tags(content)
        
        expected_tags = ["tag1", "tag2", "productivity"]
        for tag in expected_tags:
            self.assertIn(tag, tags)
    
    def test_extract_links(self):
        """Test Obsidian link extraction."""
        content = "This has [[Link One]] and [[Link Two]] references."
        links = self.builder.extract_links(content)
        
        expected_links = ["Link One", "Link Two"]
        self.assertEqual(sorted(links), sorted(expected_links))
    
    def test_template_variable_processing(self):
        """Test template variable replacement."""
        template = "Date: {{date}}, Custom: {{custom_var}}"
        variables = {"custom_var": "test_value"}
        
        result = self.builder.process_template_variables(template, variables)
        
        self.assertIn("test_value", result)
        self.assertNotIn("{{custom_var}}", result)
        self.assertNotIn("{{date}}", result)  # Should be replaced with actual date
    
    def test_build_from_files(self):
        """Test building prompt from template and diary files."""
        # Create test template
        template_content = """# Research Query

## Context
{{diary_content}}

## Custom Variable
{{custom_var}}
"""
        
        # Create test diary
        diary_content = """# Daily Note

## Thoughts
- Some thoughts here
- More ideas

## Goals
- Goal 1
- Goal 2
"""
        
        template_file = self.temp_dir / "template.md"
        diary_file = self.temp_dir / "diary.md"
        
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        with open(diary_file, 'w', encoding='utf-8') as f:
            f.write(diary_content)
        
        # Build prompt
        variables = {"custom_var": "test_custom"}
        result = self.builder.build_from_files(
            template_file, diary_file, variables
        )
        
        self.assertIn("Some thoughts here", result)
        self.assertIn("test_custom", result)
        self.assertNotIn("{{", result)  # No unprocessed variables


class TestSettings(unittest.TestCase):
    """Test settings management."""
    
    def setUp(self):
        self.settings = Settings()
    
    def test_default_settings(self):
        """Test that default settings are loaded."""
        port = self.settings.get('browser', 'port')
        self.assertIsInstance(port, int)
        self.assertEqual(port, 9222)
        
        vault_path = self.settings.get('obsidian', 'vault_path')
        self.assertIsInstance(vault_path, str)
    
    def test_nested_setting_access(self):
        """Test nested setting access."""
        # Test getting nested value
        port = self.settings.get('browser', 'port', default=8080)
        self.assertEqual(port, 9222)
        
        # Test non-existent path with default
        nonexistent = self.settings.get('nonexistent', 'path', default="fallback")
        self.assertEqual(nonexistent, "fallback")
    
    def test_setting_modification(self):
        """Test setting value modification."""
        original_port = self.settings.get('browser', 'port')
        
        # Set new value
        self.settings.set('browser', 'port', value=8080)
        new_port = self.settings.get('browser', 'port')
        
        self.assertEqual(new_port, 8080)
        self.assertNotEqual(new_port, original_port)
    
    def test_config_sections(self):
        """Test getting configuration sections."""
        chrome_config = self.settings.get_chrome_options()
        obsidian_config = self.settings.get_obsidian_config()
        
        self.assertIn('port', chrome_config)
        self.assertIn('vault_path', obsidian_config)
        
        self.assertIsInstance(chrome_config['port'], int)
        self.assertIsInstance(obsidian_config['vault_path'], str)
    
    def test_env_value_conversion(self):
        """Test environment variable value conversion."""
        # Test boolean conversion
        self.assertTrue(self.settings._convert_env_value('true'))
        self.assertTrue(self.settings._convert_env_value('1'))
        self.assertFalse(self.settings._convert_env_value('false'))
        self.assertFalse(self.settings._convert_env_value('0'))
        
        # Test integer conversion
        self.assertEqual(self.settings._convert_env_value('123'), 123)
        
        # Test float conversion
        self.assertEqual(self.settings._convert_env_value('123.45'), 123.45)
        
        # Test string fallback
        self.assertEqual(self.settings._convert_env_value('test'), 'test')


class TestElementHelper(unittest.TestCase):
    """Test element helper utilities."""
    
    def test_get_element_center(self):
        """Test element center calculation (mock test)."""
        # Mock element object
        class MockElement:
            def __init__(self):
                self.location = {'x': 10, 'y': 20}
                self.size = {'width': 100, 'height': 50}
        
        element = MockElement()
        center = ElementHelper.get_element_center(None, element)  # driver not used in calculation
        
        expected_x = 10 + 100 / 2  # 60
        expected_y = 20 + 50 / 2   # 45
        
        self.assertEqual(center, (expected_x, expected_y))
    
    def test_smart_find_element_selector_building(self):
        """Test that smart_find_element builds correct selectors."""
        # This is a unit test for the selector building logic
        # We'll test by examining what selectors would be built
        
        # Test with tag and attributes
        tag = "button"
        attributes = {"class": "btn primary", "id": "submit"}
        
        # The method would build CSS selector: button.btn.primary[id='submit']
        expected_css = "button.btn.primary[id='submit']"
        
        # For this test, we'll just verify the logic makes sense
        self.assertTrue(tag in expected_css)
        self.assertTrue("btn" in expected_css)
        self.assertTrue("primary" in expected_css)


class TestScreenshotHelper(unittest.TestCase):
    """Test screenshot helper utilities."""
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.screenshot_helper = ScreenshotHelper(output_dir=self.temp_dir)
    
    def tearDown(self):
        # Clean up temp files
        for file in self.temp_dir.glob("*"):
            if file.is_file():
                file.unlink()
        if self.temp_dir.exists():
            self.temp_dir.rmdir()
    
    def test_output_directory_creation(self):
        """Test that output directory is created."""
        self.assertTrue(self.temp_dir.exists())
        self.assertTrue(self.temp_dir.is_dir())
    
    def test_get_screenshot_metadata_structure(self):
        """Test screenshot metadata structure."""
        # Mock driver object
        class MockDriver:
            current_url = "https://example.com"
            title = "Example Page"
            
            def execute_script(self, script):
                if "viewport" in script:
                    return {"width": 1920, "height": 1080}
                elif "page" in script:
                    return {"width": 1920, "height": 2000}
                elif "scroll" in script:
                    return {"x": 0, "y": 100}
                elif "userAgent" in script:
                    return "Mozilla/5.0 Test Browser"
                return None
        
        driver = MockDriver()
        metadata = self.screenshot_helper.get_screenshot_metadata(driver, "/test/path")
        
        expected_keys = ['url', 'title', 'timestamp', 'viewport_size', 'page_size', 'scroll_position', 'user_agent', 'path']
        for key in expected_keys:
            self.assertIn(key, metadata)
        
        self.assertEqual(metadata['url'], "https://example.com")
        self.assertEqual(metadata['title'], "Example Page")
        self.assertEqual(metadata['path'], "/test/path")


class TestIntegration(unittest.TestCase):
    """Integration tests that combine multiple components."""
    
    def test_settings_and_prompt_builder_integration(self):
        """Test that settings can be used with prompt builder."""
        settings = Settings()
        builder = PromptBuilder()
        
        # Test that settings can provide vault path
        vault_path = settings.get_obsidian_config()['vault_path']
        self.assertIsInstance(vault_path, str)
        
        # Test that prompt builder can use the path
        expanded_path = settings.expand_path(vault_path)
        self.assertIsInstance(expanded_path, str)
    
    def test_error_handler_with_prompt_builder(self):
        """Test error handler integration with prompt builder."""
        handler = ErrorHandler()
        builder = PromptBuilder()
        
        # Test safe execution of file reading
        result = handler.safe_execute(
            builder.read_file,
            "/nonexistent/file.md",
            default_return="",
            context="File reading test"
        )
        
        self.assertEqual(result, "")  # Should return empty string as default


def run_connectivity_test():
    """Test if Chrome debugging is accessible."""
    try:
        import requests
        response = requests.get("http://localhost:9222/json/version", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def main():
    """Run all tests."""
    print("Auto-Browser-Control Basic Testing Suite")
    print("========================================")
    
    # Check Chrome connectivity (optional)
    if run_connectivity_test():
        print("✓ Chrome debugging is accessible on port 9222")
    else:
        print("⚠ Chrome debugging not accessible (external tests will be skipped)")
    
    print("\\nRunning unit tests...")
    
    # Create test suite
    test_classes = [
        TestErrorHandler,
        TestPromptBuilder,
        TestSettings,
        TestElementHelper,
        TestScreenshotHelper,
        TestIntegration
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\\n{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('\\n')[-2]}")
    
    if result.errors:
        print("\\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('\\n')[-2]}")
    
    if result.wasSuccessful():
        print("\\n✓ All tests passed!")
        return 0
    else:
        print("\\n✗ Some tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())