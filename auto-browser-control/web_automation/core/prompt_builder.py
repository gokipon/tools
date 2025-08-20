"""
Prompt Builder for Obsidian Integration

Builds prompts by combining Obsidian template files with diary entries.
Supports automatic date-based path generation for research automation.
"""

import os
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

from .error_handler import ErrorHandler


class PromptBuilder:
    """Builds prompts from Obsidian template and diary files."""
    
    def __init__(self):
        self.error_handler = ErrorHandler()
        self.obsidian_vault_path = None
        self.template_patterns = {
            'daily_research': 'templates/daily_research.md',
            'question_template': 'templates/question.md',
            'analysis_template': 'templates/analysis.md'
        }
    
    def set_obsidian_vault_path(self, vault_path: str):
        """Set the path to the Obsidian vault."""
        self.obsidian_vault_path = Path(vault_path).expanduser().resolve()
        if not self.obsidian_vault_path.exists():
            raise FileNotFoundError(f"Obsidian vault not found at: {vault_path}")
    
    def get_daily_note_path(self, date: datetime = None, format_string: str = "%Y-%m-%d") -> Path:
        """Get the path to a daily note based on date."""
        if date is None:
            # Default to previous day for automated research
            date = datetime.now() - timedelta(days=1)
        
        date_string = date.strftime(format_string)
        
        # Common daily notes locations in Obsidian
        possible_paths = [
            Path("daily") / f"{date_string}.md",
            Path("Daily Notes") / f"{date_string}.md",
            Path(f"{date_string}.md"),
            Path("journal") / f"{date_string}.md",
            Path(f"diary/{date_string}.md")
        ]
        
        if self.obsidian_vault_path:
            for path in possible_paths:
                full_path = self.obsidian_vault_path / path
                if full_path.exists():
                    return full_path
        
        # Return the most common format as default
        return self.obsidian_vault_path / "daily" / f"{date_string}.md"
    
    def read_file(self, file_path: str or Path) -> str:
        """Read content from a file with error handling."""
        try:
            path = Path(file_path).expanduser().resolve()
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            self.error_handler.handle_error(e, f"Reading file {file_path}")
            return ""
    
    def extract_sections(self, content: str) -> Dict[str, str]:
        """Extract sections from markdown content based on headers."""
        sections = {}
        
        # Split by headers (# ## ### etc.)
        header_pattern = r'^(#{1,6})\s+(.+)$'
        lines = content.split('\n')
        
        current_section = "content"  # Default section
        current_content = []
        
        for line in lines:
            header_match = re.match(header_pattern, line, re.MULTILINE)
            
            if header_match:
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                section_name = header_match.group(2).lower().replace(' ', '_')
                current_section = section_name
                current_content = [line]  # Include the header
            else:
                current_content.append(line)
        
        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def extract_tags(self, content: str) -> list:
        """Extract tags from content."""
        tag_pattern = r'#(\w+)'
        tags = re.findall(tag_pattern, content)
        return list(set(tags))  # Remove duplicates
    
    def extract_links(self, content: str) -> list:
        """Extract Obsidian-style links [[link]] from content."""
        link_pattern = r'\[\[([^\]]+)\]\]'
        links = re.findall(link_pattern, content)
        return links
    
    def process_template_variables(self, template_content: str, variables: Dict[str, Any]) -> str:
        """Process template variables in the format {{variable_name}}."""
        processed_content = template_content
        
        # Add default variables
        now = datetime.now()
        default_vars = {
            'date': now.strftime('%Y-%m-%d'),
            'time': now.strftime('%H:%M'),
            'datetime': now.strftime('%Y-%m-%d %H:%M'),
            'timestamp': int(now.timestamp())
        }
        
        all_variables = {**default_vars, **variables}
        
        # Replace template variables
        for key, value in all_variables.items():
            pattern = f'{{{{{key}}}}}'
            processed_content = processed_content.replace(pattern, str(value))
        
        return processed_content
    
    def build_from_files(self, 
                        template_path: str or Path, 
                        diary_path: str or Path = None,
                        variables: Dict[str, Any] = None) -> str:
        """Build prompt from template and diary files."""
        variables = variables or {}
        
        # Read template
        template_content = self.read_file(template_path)
        if not template_content:
            return ""
        
        # Read diary if provided
        diary_content = ""
        if diary_path:
            diary_content = self.read_file(diary_path)
        elif self.obsidian_vault_path:
            # Auto-detect previous day's diary
            auto_diary_path = self.get_daily_note_path()
            diary_content = self.read_file(auto_diary_path)
        
        # Extract sections from diary
        diary_sections = self.extract_sections(diary_content)
        
        # Prepare variables for template processing
        template_variables = {
            **variables,
            'diary_content': diary_content,
            'diary_summary': diary_sections.get('summary', ''),
            'diary_thoughts': diary_sections.get('thoughts', diary_sections.get('reflection', '')),
            'diary_goals': diary_sections.get('goals', diary_sections.get('tomorrow', '')),
            'diary_tags': ', '.join(self.extract_tags(diary_content)),
            'diary_links': ', '.join(self.extract_links(diary_content))
        }
        
        # Process template
        final_prompt = self.process_template_variables(template_content, template_variables)
        
        return final_prompt
    
    def build_research_prompt(self, 
                            topic: str = None,
                            context: str = None,
                            diary_date: datetime = None) -> str:
        """Build a research prompt using the daily research template."""
        
        # Get diary content
        diary_path = self.get_daily_note_path(diary_date)
        diary_content = self.read_file(diary_path)
        
        # Extract relevant sections
        diary_sections = self.extract_sections(diary_content)
        
        # Build research prompt
        prompt_parts = []
        
        if topic:
            prompt_parts.append(f"Research Topic: {topic}")
        
        if context:
            prompt_parts.append(f"Context: {context}")
        
        if diary_content:
            prompt_parts.append("\\n--- Based on my recent notes ---\\n")
            
            # Add relevant diary sections
            if 'thoughts' in diary_sections or 'reflection' in diary_sections:
                thoughts = diary_sections.get('thoughts', diary_sections.get('reflection', ''))
                prompt_parts.append(f"Recent thoughts:\\n{thoughts}")
            
            if 'goals' in diary_sections or 'tomorrow' in diary_sections:
                goals = diary_sections.get('goals', diary_sections.get('tomorrow', ''))
                prompt_parts.append(f"Current goals:\\n{goals}")
            
            # Add tags for context
            tags = self.extract_tags(diary_content)
            if tags:
                prompt_parts.append(f"Related topics: {', '.join(tags)}")
        
        return "\\n\\n".join(prompt_parts)
    
    def save_result_with_context(self, 
                               result: str, 
                               original_prompt: str, 
                               filename: str = None) -> str:
        """Save research result with original prompt context."""
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"research_result_{timestamp}.md"
        
        # Ensure results directory exists
        results_dir = Path.home() / "automation_results"
        results_dir.mkdir(exist_ok=True)
        
        filepath = results_dir / filename
        
        # Create comprehensive result file
        result_content = f"""# Research Result - {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Original Prompt
{original_prompt}

## Result
{result}

---
*Generated by auto-browser-control at {datetime.now().isoformat()}*
"""
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(result_content)
            
            self.error_handler.log_info(f"Result saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.error_handler.handle_error(e, f"Saving result to {filepath}")
            return ""