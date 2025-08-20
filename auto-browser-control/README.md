# Auto-Browser-Control

A comprehensive web automation library for browser control using Chrome Remote Debugging Protocol, designed for Obsidian integration and automated research workflows.

## 🚀 Features

- **Chrome Remote Debugging Integration**: Connect to existing Chrome instances
- **Obsidian Integration**: Seamless integration with Obsidian notes and templates
- **Service Modules**: Pre-built automation for Perplexity.ai, Gmail, and GitHub
- **Daily Research Automation**: CLI script for automated daily research
- **Advanced Error Handling**: Robust retry logic and error recovery
- **Screenshot Capabilities**: Full page and element-specific screenshots
- **Configurable Settings**: JSON and environment variable configuration

## 📦 Installation

### Prerequisites
- Python 3.7 or higher
- Chrome or Chromium browser
- pip package manager

### Install Dependencies
```bash
cd auto-browser-control
pip install -r requirements.txt
```

### Chrome Setup
Start Chrome with remote debugging enabled:

**macOS:**
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-selenium-debug
```

**Linux:**
```bash
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug
```

**Windows:**
```cmd
"C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --user-data-dir=C:\temp\chrome-debug
```

## 🎯 Quick Start

### Basic Usage
```python
from web_automation import WebAutomation

# Initialize automation
automation = WebAutomation(port=9222)

# Connect to browser and use Perplexity service
with automation.connect() as browser:
    perplexity = automation.service('perplexity')
    result = perplexity.ask_question("What are the latest developments in AI?")
    
    # Save result
    output_path = automation.save_result(result, "ai_research.md")
    print(f"Results saved to: {output_path}")
```

### Daily Research Automation
```bash
# Basic execution (uses previous day's diary)
python web_automation/scripts/daily_research.py

# With specific configuration
python web_automation/scripts/daily_research.py \
  --date 2024-01-15 \
  --vault-path ~/Documents/MyVault \
  --template-path ~/templates/research.md
```

## 🗂️ Project Structure

```
auto-browser-control/
├── web_automation/           # Main library package
│   ├── core/                # Core functionality
│   │   ├── browser_manager.py
│   │   ├── error_handler.py
│   │   └── prompt_builder.py
│   ├── services/            # Service-specific operations
│   │   ├── perplexity.py
│   │   ├── gmail.py
│   │   ├── github.py
│   │   └── generic.py
│   ├── utils/               # Helper utilities
│   │   ├── element_helper.py
│   │   ├── wait_helper.py
│   │   └── screenshot.py
│   ├── config/              # Configuration management
│   │   └── settings.py
│   └── scripts/             # Automation scripts
│       └── daily_research.py
├── README.md                # This file
├── requirements.txt         # Dependencies
├── requirement.md           # Detailed requirements
└── setup.py                # Installation script
```

## ⚙️ Configuration

### Configuration File
Create `auto_browser_config.json`:

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

### Environment Variables
```bash
export CHROME_DEBUG_PORT=9222
export OBSIDIAN_VAULT_PATH="~/Documents/MyVault"
export AUTOMATION_RESULTS_DIR="~/automation_results"
```

## 🤖 Services

### Perplexity.ai Service
```python
perplexity = automation.service('perplexity')
result = perplexity.ask_question("Research question here")
```

### Gmail Service
```python
gmail = automation.service('gmail')
gmail.send_email_complete(
    to_email="recipient@example.com",
    subject="Subject",
    body="Email body"
)
```

### GitHub Service
```python
github = automation.service('github')
issue_url = github.create_issue_complete(
    repo_path="username/repository",
    title="Issue title",
    body="Issue description"
)
```

## 📅 Daily Research Automation

### CLI Options
```bash
python web_automation/scripts/daily_research.py --help
```

Key options:
- `--date`: Specific date for research (YYYY-MM-DD)
- `--vault-path`: Obsidian vault path
- `--template-path`: Research template file
- `--question`: Direct research question
- `--dry-run`: Show what would be done without executing
- `--verbose`: Enable detailed logging

### Cron Job Setup
Add to your crontab for daily 5:30 AM execution:
```bash
30 5 * * * cd /path/to/auto-browser-control && python web_automation/scripts/daily_research.py
```

### Obsidian Template Example
Create `templates/daily_research.md`:
```markdown
# Daily Research Query

Based on my recent notes and thoughts:

## Context from Recent Notes
{{diary_thoughts}}

## Current Goals  
{{diary_goals}}

## Research Question
Please provide insights related to the themes above, focusing on:
1. Practical applications
2. Recent developments
3. Learning resources
4. Potential challenges
```

## 🛠️ Advanced Usage

### Custom Service Creation
```python
generic = automation.service('generic')

# Navigate to any website
generic.navigate_to_url(driver, "https://example.com")

# Fill forms
generic.fill_form(driver, {
    'username': 'myuser',
    'password': 'mypass'
})

# Extract table data
table_data = generic.extract_table_data(driver, ['table.data'])
```

### Screenshot Capabilities
```python
from web_automation.utils.screenshot import ScreenshotHelper

screenshot = ScreenshotHelper()

# Full page screenshot
full_page = screenshot.take_full_page_screenshot(driver)

# Element screenshot
element_shot = screenshot.take_element_screenshot(driver, element)

# Before/after comparison
comparison = screenshot.take_comparison_screenshot(
    driver, before_action, after_action, "Login process"
)
```

### Error Handling
```python
from web_automation.core.error_handler import ErrorHandler

handler = ErrorHandler()

@handler.retry_on_failure(max_retries=3, delay=2)
def my_automation_function():
    # Your automation code here
    pass

# Safe execution with default return
result = handler.safe_execute(
    risky_function, 
    default_return="fallback_value"
)
```

## 🧪 Testing

### Basic Test
```python
python example_usage.py
```

### Run Tests
```python
python test_basic.py
```

## 🔧 Troubleshooting

### Common Issues

**Chrome Connection Failed:**
- Ensure Chrome is running with `--remote-debugging-port=9222`
- Check if port 9222 is available
- Verify Chrome is not running in incognito mode

**Obsidian Files Not Found:**
- Check vault path configuration
- Verify daily notes path and format
- Ensure diary files exist for the specified date

**Service Automation Failures:**
- Ensure you're logged into services (Perplexity, Gmail, GitHub)
- Check internet connection
- Verify service websites haven't changed their UI

**Permission Issues:**
- Ensure output directories are writable
- Check file permissions for Obsidian vault

### Debug Mode
Enable verbose logging:
```bash
python web_automation/scripts/daily_research.py --verbose
```

## 📝 License

This project is open source. See LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues, feature requests, or questions:
- Create an issue in the repository
- Check existing documentation
- Review troubleshooting section

## 🔄 Version History

- **v1.0.0**: Initial release with core functionality
  - Chrome Remote Debugging integration
  - Obsidian integration
  - Perplexity, Gmail, GitHub services
  - Daily research automation
  - Comprehensive error handling
  - Advanced utilities and helpers

---

*Generated with auto-browser-control automation library*