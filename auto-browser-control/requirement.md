# Auto-Browser-Control Requirements Document

## Project Overview

Auto-browser-control is a comprehensive web automation library designed for browser control using Chrome Remote Debugging Protocol. The library specializes in Obsidian integration and automated research workflows, with a focus on daily research automation using services like Perplexity.ai.

## Core Requirements

### 1. Browser Management
- **Chrome Remote Debugging Integration**: Connect to existing Chrome instances via remote debugging protocol
- **Connection Management**: Robust connection handling with automatic retry and error recovery
- **Multi-tab Support**: Ability to work with multiple browser tabs and windows
- **Screenshot Capabilities**: Full page and element-specific screenshot functionality
- **Element Interaction**: Safe clicking, text input, and form filling with fallback strategies

### 2. Obsidian Integration
- **File Reading**: Read and parse Obsidian markdown files including daily notes and templates
- **Template Processing**: Process template variables and combine template files with diary entries
- **Date-based Path Generation**: Automatically generate paths to daily notes based on date patterns
- **Section Extraction**: Parse markdown sections, tags, and links from Obsidian files
- **Result Saving**: Save automation results in markdown format with proper timestamps

### 3. Service Modules

#### Perplexity.ai Service
- **Question Submission**: Submit questions to Perplexity with robust element detection
- **Answer Retrieval**: Extract comprehensive answers with proper formatting
- **Response Waiting**: Smart waiting for AI response generation with timeout handling
- **Batch Processing**: Support for multiple questions with appropriate delays

#### Gmail Service
- **Email Composition**: Automated email creation with recipient, subject, and body
- **Email Sending**: Send emails through Gmail web interface
- **Inbox Reading**: Retrieve and parse recent emails from inbox
- **Search Functionality**: Search emails by keywords and criteria

#### GitHub Service
- **Issue Creation**: Create GitHub issues with title, body, and labels
- **Repository Information**: Extract repository metadata and statistics
- **Repository Search**: Search for repositories by various criteria

#### Generic Service
- **Universal Operations**: Generic web element operations for any website
- **Form Filling**: Automated form completion with field detection
- **Table Extraction**: Extract data from HTML tables
- **Custom JavaScript**: Execute custom scripts on web pages

### 4. Daily Research Automation
- **CLI Script**: Command-line interface for automated daily research
- **Cron Compatibility**: Designed to run via cron jobs for daily automation
- **Template-based Prompts**: Build research prompts from Obsidian templates and diary entries
- **Result Management**: Save research results with context and timestamps
- **Configuration Support**: Flexible configuration via JSON files and environment variables

### 5. Error Handling and Reliability
- **Retry Logic**: Exponential backoff retry mechanism for failed operations
- **Error Logging**: Comprehensive logging with configurable levels
- **Graceful Degradation**: Fallback strategies when primary methods fail
- **Timeout Management**: Configurable timeouts for all operations
- **Screenshot Debugging**: Automatic screenshots on errors for debugging

### 6. Utilities and Helpers
- **Element Helper**: Advanced element finding with multiple selector strategies
- **Wait Helper**: Smart waiting for page loads, AJAX completion, and element states
- **Screenshot Helper**: Advanced screenshot capabilities including comparisons and annotations
- **Configuration Manager**: Settings management with file and environment variable support

## Technical Architecture

### Core Components
1. **BrowserManager**: Chrome Remote Debugging connection and browser control
2. **PromptBuilder**: Obsidian file integration and template processing
3. **ErrorHandler**: Comprehensive error handling and retry logic
4. **Settings**: Configuration management and settings loading

### Service Layer
- **PerplexityService**: Perplexity.ai automation
- **GmailService**: Gmail automation
- **GitHubService**: GitHub automation
- **GenericService**: Universal web automation

### Utility Layer
- **ElementHelper**: Advanced element interaction utilities
- **WaitHelper**: Smart waiting strategies
- **ScreenshotHelper**: Screenshot and comparison utilities

### Scripts Layer
- **daily_research.py**: CLI script for daily research automation

## Installation and Setup

### Dependencies
- Python 3.7+
- Selenium WebDriver
- Chrome/Chromium browser
- PIL (Pillow) for image processing
- Additional Python packages as specified in requirements.txt

### Chrome Setup
```bash
# Start Chrome with remote debugging
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug
```

### Python Installation
```bash
cd auto-browser-control
pip install -r requirements.txt
```

## Usage Examples

### Basic Usage
```python
from web_automation import WebAutomation

automation = WebAutomation(port=9222)

with automation.connect() as browser:
    perplexity = automation.service('perplexity')
    result = perplexity.ask_question("What are the latest AI developments?")
    automation.save_result(result, "ai_research.md")
```

### Daily Research Automation
```bash
# Basic execution (uses previous day's diary)
python web_automation/scripts/daily_research.py

# With specific date and template
python web_automation/scripts/daily_research.py --date 2024-01-15 --template-path ~/templates/research.md

# Cron setup for daily 5:30 AM execution
30 5 * * * cd /path/to/auto-browser-control && python web_automation/scripts/daily_research.py
```

### Configuration
```json
{
  "browser": {
    "port": 9222,
    "headless": false,
    "timeout": 30
  },
  "obsidian": {
    "vault_path": "~/Documents/Obsidian Vault",
    "daily_notes_format": "%Y-%m-%d",
    "daily_notes_path": "daily"
  },
  "automation": {
    "results_dir": "~/automation_results",
    "max_retries": 3
  }
}
```

## Acceptance Criteria

### Phase 1 - Core Functionality
- [x] Chrome Remote Debugging connection established
- [x] Basic browser automation (navigation, clicking, text input)
- [x] Perplexity.ai service integration
- [x] Obsidian file reading and template processing
- [x] Error handling with retry logic

### Phase 2 - Advanced Features
- [x] Daily research automation script
- [x] Gmail and GitHub service modules
- [x] Advanced screenshot capabilities
- [x] Configuration management system
- [x] Comprehensive utility helpers

### Phase 3 - Production Readiness
- [x] CLI script with full argument support
- [x] Cron job compatibility
- [x] Comprehensive error handling
- [x] Documentation and examples
- [x] Testing suite

## Constraints and Considerations

### Technical Constraints
- Requires Chrome browser with remote debugging enabled
- Dependent on web service UI stability (Perplexity, Gmail, GitHub)
- Limited by network connectivity and service availability

### Security Considerations
- Uses existing browser sessions (relies on user authentication)
- No credential storage in the automation system
- Screenshots may contain sensitive information

### Performance Considerations
- Designed for periodic automation, not high-frequency operations
- Includes respectful delays between requests
- Configurable timeouts and retry limits

## Future Enhancements

### Potential Additions
- Support for additional services (Twitter, LinkedIn, etc.)
- Enhanced natural language processing for prompt generation
- Integration with other note-taking applications
- Web scraping capabilities for research augmentation
- API integrations as alternatives to web automation

### Scalability Considerations
- Multi-browser support for parallel operations
- Distributed execution capabilities
- Enhanced monitoring and alerting
- Performance optimization for large-scale usage

## Success Metrics

### Functionality Metrics
- Successful automation of daily research workflow
- Reliable service integration with <5% failure rate
- Comprehensive error recovery and logging

### Usability Metrics
- Simple CLI interface requiring minimal configuration
- Clear documentation and examples
- Easy installation and setup process

### Reliability Metrics
- Stable operation in cron job environment
- Graceful handling of service outages
- Consistent results across different environments