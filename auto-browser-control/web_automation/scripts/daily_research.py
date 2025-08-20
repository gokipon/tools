#!/usr/bin/env python3
"""
Daily Research Automation Script

CLI script for automated daily research using Perplexity.ai with Obsidian integration.
Designed to be run via cron for daily automated research.
"""

import argparse
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from web_automation import WebAutomation
from web_automation.config.settings import get_settings
from web_automation.core.error_handler import ErrorHandler


def setup_logging(log_level='INFO'):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                Path.home() / 'automation_results' / 'daily_research.log'
            )
        ]
    )
    return logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Automated daily research using Perplexity.ai with Obsidian integration'
    )
    
    parser.add_argument(
        '--date',
        type=str,
        help='Date for diary entry (YYYY-MM-DD format). Defaults to yesterday.'
    )
    
    parser.add_argument(
        '--vault-path',
        type=str,
        help='Path to Obsidian vault. Overrides config setting.'
    )
    
    parser.add_argument(
        '--template-path',
        type=str,
        help='Path to research template file.'
    )
    
    parser.add_argument(
        '--diary-path',
        type=str,
        help='Specific path to diary file. If not provided, will auto-detect based on date.'
    )
    
    parser.add_argument(
        '--question',
        type=str,
        help='Specific research question. If not provided, will build from template and diary.'
    )
    
    parser.add_argument(
        '--output-file',
        type=str,
        help='Specific output filename. If not provided, will use timestamp.'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file.'
    )
    
    parser.add_argument(
        '--chrome-port',
        type=int,
        default=9222,
        help='Chrome remote debugging port (default: 9222).'
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run Chrome in headless mode.'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=60,
        help='Timeout for Perplexity response in seconds (default: 60).'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without executing.'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging.'
    )
    
    parser.add_argument(
        '--save-screenshot',
        action='store_true',
        help='Save screenshot after research.'
    )
    
    return parser.parse_args()


def get_diary_path(settings, vault_path, date):
    """Get the path to the diary file for the specified date."""
    if not vault_path:
        vault_path = settings.get('obsidian', 'vault_path', default='~/Documents/Obsidian Vault')
    
    vault_path = Path(vault_path).expanduser().resolve()
    
    # Format date
    if isinstance(date, str):
        date = datetime.strptime(date, '%Y-%m-%d')
    
    date_format = settings.get('obsidian', 'daily_notes_format', default='%Y-%m-%d')
    date_string = date.strftime(date_format)
    
    # Try common daily notes locations
    daily_notes_path = settings.get('obsidian', 'daily_notes_path', default='daily')
    possible_paths = [
        vault_path / daily_notes_path / f"{date_string}.md",
        vault_path / "Daily Notes" / f"{date_string}.md",
        vault_path / f"{date_string}.md",
        vault_path / "journal" / f"{date_string}.md",
        vault_path / "diary" / f"{date_string}.md"
    ]
    
    # Return the first existing path
    for path in possible_paths:
        if path.exists():
            return str(path)
    
    # Return the default location even if it doesn't exist
    return str(possible_paths[0])


def get_template_path(settings, vault_path, template_path=None):
    """Get the path to the research template file."""
    if template_path:
        return str(Path(template_path).expanduser().resolve())
    
    if not vault_path:
        vault_path = settings.get('obsidian', 'vault_path', default='~/Documents/Obsidian Vault')
    
    vault_path = Path(vault_path).expanduser().resolve()
    templates_path = settings.get('obsidian', 'templates_path', default='templates')
    
    # Try common template locations
    possible_paths = [
        vault_path / templates_path / "daily_research.md",
        vault_path / templates_path / "research.md",
        vault_path / "Templates" / "daily_research.md",
        vault_path / "templates" / "research_template.md"
    ]
    
    # Return the first existing path
    for path in possible_paths:
        if path.exists():
            return str(path)
    
    # Return None if no template found
    return None


def create_default_template(settings, vault_path):
    """Create a default research template if none exists."""
    if not vault_path:
        vault_path = settings.get('obsidian', 'vault_path', default='~/Documents/Obsidian Vault')
    
    vault_path = Path(vault_path).expanduser().resolve()
    templates_path = settings.get('obsidian', 'templates_path', default='templates')
    
    template_dir = vault_path / templates_path
    template_dir.mkdir(parents=True, exist_ok=True)
    
    template_file = template_dir / "daily_research.md"
    
    default_template = """# Daily Research Query

Based on my recent notes and thoughts, I would like to research and explore the following:

## Context from Recent Notes
{{diary_thoughts}}

## Current Goals and Interests  
{{diary_goals}}

## Research Question
Please provide insights, analysis, and actionable information related to the themes and interests mentioned above. Focus on:

1. Practical applications and next steps
2. Recent developments or trends
3. Resources for deeper learning
4. Potential challenges or considerations

Keep the response comprehensive but actionable, with specific recommendations where possible.

---
*Auto-generated research prompt based on diary entry from {{date}}*
"""
    
    try:
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(default_template)
        return str(template_file)
    except Exception:
        return None


def main():
    """Main function for daily research automation."""
    args = parse_arguments()
    
    # Setup logging
    log_level = 'DEBUG' if args.verbose else 'INFO'
    logger = setup_logging(log_level)
    
    logger.info("Starting daily research automation")
    
    try:
        # Load settings
        settings = get_settings(args.config)
        
        # Determine date
        if args.date:
            research_date = datetime.strptime(args.date, '%Y-%m-%d')
        else:
            # Default to yesterday for automated runs
            research_date = datetime.now() - timedelta(days=1)
        
        logger.info(f"Research date: {research_date.strftime('%Y-%m-%d')}")
        
        # Get paths
        vault_path = args.vault_path or settings.get('obsidian', 'vault_path')
        diary_path = args.diary_path or get_diary_path(settings, vault_path, research_date)
        template_path = get_template_path(settings, vault_path, args.template_path)
        
        # Create default template if none exists
        if not template_path:
            template_path = create_default_template(settings, vault_path)
            if template_path:
                logger.info(f"Created default template: {template_path}")
            else:
                logger.warning("Could not create default template")
        
        logger.info(f"Vault path: {vault_path}")
        logger.info(f"Diary path: {diary_path}")
        logger.info(f"Template path: {template_path}")
        
        # Check if diary file exists
        if not Path(diary_path).exists():
            logger.warning(f"Diary file not found: {diary_path}")
            if not args.dry_run:
                print(f"Warning: Diary file not found: {diary_path}")
                print("Research will proceed without diary context.")
        
        # Initialize automation
        automation = WebAutomation(
            port=args.chrome_port,
            headless=args.headless
        )
        
        # Set Obsidian vault path
        automation.prompt_builder.set_obsidian_vault_path(vault_path)
        
        # Build research prompt
        if args.question:
            research_prompt = args.question
            logger.info("Using provided research question")
        elif template_path:
            research_prompt = automation.build_prompt(template_path, diary_path)
            logger.info("Built research prompt from template and diary")
        else:
            # Fallback: create basic research prompt
            research_prompt = automation.prompt_builder.build_research_prompt(
                context="Daily research based on recent notes",
                diary_date=research_date
            )
            logger.info("Built basic research prompt")
        
        if args.dry_run:
            print(f"\\nDRY RUN MODE\\n")
            print(f"Date: {research_date.strftime('%Y-%m-%d')}")
            print(f"Vault: {vault_path}")
            print(f"Diary: {diary_path} (exists: {Path(diary_path).exists()})")
            print(f"Template: {template_path} (exists: {Path(template_path).exists() if template_path else False})")
            print(f"\\nResearch Prompt (first 200 chars):")
            print(f"{research_prompt[:200]}...")
            return
        
        if not research_prompt.strip():
            logger.error("Empty research prompt generated")
            print("Error: Could not generate research prompt")
            return 1
        
        logger.info(f"Research prompt generated ({len(research_prompt)} characters)")
        
        # Execute research on Perplexity
        logger.info("Connecting to Perplexity...")
        
        with automation.connect() as browser:
            perplexity = automation.service('perplexity')
            
            logger.info("Submitting research question...")
            result = perplexity.ask_question(research_prompt, browser, timeout=args.timeout)
            
            if result:
                logger.info(f"Research completed ({len(result)} characters)")
                
                # Save screenshot if requested
                if args.save_screenshot:
                    screenshot_path = automation.browser_manager.take_screenshot(browser)
                    if screenshot_path:
                        logger.info(f"Screenshot saved: {screenshot_path}")
                
                # Save result
                if args.output_file:
                    output_path = automation.prompt_builder.save_result_with_context(
                        result, research_prompt, args.output_file
                    )
                else:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"daily_research_{research_date.strftime('%Y-%m-%d')}_{timestamp}.md"
                    output_path = automation.prompt_builder.save_result_with_context(
                        result, research_prompt, filename
                    )
                
                if output_path:
                    logger.info(f"Results saved to: {output_path}")
                    print(f"Research completed successfully!")
                    print(f"Results saved to: {output_path}")
                else:
                    logger.error("Failed to save results")
                    print("Error: Failed to save results")
                    return 1
            else:
                logger.error("No result received from Perplexity")
                print("Error: No result received from Perplexity")
                return 1
    
    except KeyboardInterrupt:
        logger.info("Research interrupted by user")
        print("\\nResearch interrupted by user")
        return 1
    
    except Exception as e:
        logger.error(f"Research failed: {str(e)}", exc_info=True)
        print(f"Error: Research failed - {str(e)}")
        return 1
    
    logger.info("Daily research automation completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())