"""
Screenshot Helper Utilities

Advanced screenshot capabilities with comparison and annotation features.
"""

import os
import time
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import base64
from io import BytesIO


class ScreenshotHelper:
    """Helper class for advanced screenshot functionality."""
    
    def __init__(self, output_dir=None):
        self.output_dir = Path(output_dir) if output_dir else Path.home() / "automation_screenshots"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def take_full_page_screenshot(self, driver, filename=None):
        """Take full page screenshot including content below the fold."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"fullpage_{timestamp}.png"
        
        filepath = self.output_dir / filename
        
        try:
            # Get page dimensions
            total_height = driver.execute_script("return document.body.scrollHeight")
            viewport_height = driver.execute_script("return window.innerHeight")
            
            # Take screenshots of each viewport section
            screenshots = []
            current_position = 0
            
            while current_position < total_height:
                # Scroll to current position
                driver.execute_script(f"window.scrollTo(0, {current_position});")
                time.sleep(0.5)  # Wait for scroll to complete
                
                # Take screenshot
                screenshot = driver.get_screenshot_as_png()
                screenshots.append(Image.open(BytesIO(screenshot)))
                
                current_position += viewport_height
            
            # Reset scroll position
            driver.execute_script("window.scrollTo(0, 0);")
            
            # Stitch screenshots together
            if screenshots:
                total_width = screenshots[0].width
                combined_image = Image.new('RGB', (total_width, total_height))
                
                y_position = 0
                for i, screenshot in enumerate(screenshots):
                    # Calculate how much of this screenshot to use
                    remaining_height = total_height - y_position
                    crop_height = min(viewport_height, remaining_height)
                    
                    if crop_height < viewport_height:
                        screenshot = screenshot.crop((0, 0, total_width, crop_height))
                    
                    combined_image.paste(screenshot, (0, y_position))
                    y_position += crop_height
                
                combined_image.save(str(filepath))
                return str(filepath)
            
        except Exception as e:
            # Fallback to regular screenshot
            return self.take_screenshot(driver, filename)
        
        return None
    
    def take_screenshot(self, driver, filename=None):
        """Take regular viewport screenshot."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
        
        filepath = self.output_dir / filename
        
        try:
            driver.save_screenshot(str(filepath))
            return str(filepath)
        except Exception:
            return None
    
    def take_element_screenshot(self, driver, element, filename=None, padding=10):
        """Take screenshot of specific element with optional padding."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"element_{timestamp}.png"
        
        filepath = self.output_dir / filename
        
        try:
            # Get element location and size
            location = element.location
            size = element.size
            
            # Scroll element into view
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)
            
            # Take full page screenshot
            driver.save_screenshot(str(filepath))
            
            # Crop to element with padding
            image = Image.open(str(filepath))
            
            left = max(0, location['x'] - padding)
            top = max(0, location['y'] - padding)
            right = min(image.width, location['x'] + size['width'] + padding)
            bottom = min(image.height, location['y'] + size['height'] + padding)
            
            cropped = image.crop((left, top, right, bottom))
            cropped.save(str(filepath))
            
            return str(filepath)
            
        except Exception:
            return None
    
    def take_comparison_screenshot(self, driver, before_action, after_action, description=""):
        """Take before/after screenshots with comparison."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Take before screenshot
        before_path = self.take_screenshot(driver, f"before_{timestamp}.png")
        
        # Perform action
        if callable(before_action):
            before_action()
        
        # Take after screenshot
        after_path = self.take_screenshot(driver, f"after_{timestamp}.png")
        
        if callable(after_action):
            after_action()
        
        # Create comparison
        comparison_path = self.create_side_by_side_comparison(
            before_path, after_path, f"comparison_{timestamp}.png", description
        )
        
        return {
            'before': before_path,
            'after': after_path,
            'comparison': comparison_path
        }
    
    def create_side_by_side_comparison(self, image1_path, image2_path, output_filename, description=""):
        """Create side-by-side comparison of two screenshots."""
        if not image1_path or not image2_path:
            return None
        
        try:
            img1 = Image.open(image1_path)
            img2 = Image.open(image2_path)
            
            # Resize images to same height if needed
            max_height = max(img1.height, img2.height)
            
            if img1.height != max_height:
                img1 = img1.resize((int(img1.width * max_height / img1.height), max_height))
            if img2.height != max_height:
                img2 = img2.resize((int(img2.width * max_height / img2.height), max_height))
            
            # Create combined image
            total_width = img1.width + img2.width + 10  # 10px separator
            combined = Image.new('RGB', (total_width, max_height + 50), 'white')
            
            # Paste images
            combined.paste(img1, (0, 50))
            combined.paste(img2, (img1.width + 10, 50))
            
            # Add labels and description
            draw = ImageDraw.Draw(combined)
            
            try:
                font = ImageFont.truetype("arial.ttf", 16)
            except:
                font = ImageFont.load_default()
            
            draw.text((10, 10), "BEFORE", fill='black', font=font)
            draw.text((img1.width + 20, 10), "AFTER", fill='black', font=font)
            
            if description:
                draw.text((10, 30), description[:100], fill='gray', font=font)
            
            # Save comparison
            output_path = self.output_dir / output_filename
            combined.save(str(output_path))
            
            return str(output_path)
            
        except Exception:
            return None
    
    def annotate_screenshot(self, image_path, annotations, output_filename=None):
        """Add annotations to a screenshot."""
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"annotated_{timestamp}.png"
        
        try:
            image = Image.open(image_path)
            draw = ImageDraw.Draw(image)
            
            try:
                font = ImageFont.truetype("arial.ttf", 14)
            except:
                font = ImageFont.load_default()
            
            for annotation in annotations:
                x, y = annotation.get('position', (0, 0))
                text = annotation.get('text', '')
                color = annotation.get('color', 'red')
                
                # Draw circle at position
                draw.ellipse([x-5, y-5, x+5, y+5], fill=color)
                
                # Draw text with background
                bbox = draw.textbbox((x+10, y-10), text, font=font)
                draw.rectangle(bbox, fill='white', outline=color)
                draw.text((x+10, y-10), text, fill=color, font=font)
            
            output_path = self.output_dir / output_filename
            image.save(str(output_path))
            
            return str(output_path)
            
        except Exception:
            return None
    
    def create_html_report(self, screenshots_data, output_filename="screenshot_report.html"):
        """Create HTML report with screenshots and metadata."""
        output_path = self.output_dir / output_filename
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Automation Screenshot Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .screenshot {{ margin: 20px 0; padding: 10px; border: 1px solid #ccc; }}
                .screenshot img {{ max-width: 100%; height: auto; }}
                .metadata {{ background: #f5f5f5; padding: 10px; margin: 10px 0; }}
                .timestamp {{ color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <h1>Automation Screenshot Report</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """
        
        for data in screenshots_data:
            html_content += f"""
            <div class="screenshot">
                <h3>{data.get('title', 'Screenshot')}</h3>
                <div class="metadata">
                    <p><strong>URL:</strong> {data.get('url', 'N/A')}</p>
                    <p><strong>Description:</strong> {data.get('description', 'N/A')}</p>
                    <p class="timestamp">Timestamp: {data.get('timestamp', 'N/A')}</p>
                </div>
                <img src="{Path(data['path']).name}" alt="Screenshot">
            </div>
            """
        
        html_content += """
        </body>
        </html>
        """
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return str(output_path)
        except Exception:
            return None
    
    def get_screenshot_metadata(self, driver, screenshot_path):
        """Extract metadata from current page state."""
        try:
            return {
                'url': driver.current_url,
                'title': driver.title,
                'timestamp': datetime.now().isoformat(),
                'viewport_size': driver.execute_script("return {width: window.innerWidth, height: window.innerHeight};"),
                'page_size': driver.execute_script("return {width: document.body.scrollWidth, height: document.body.scrollHeight};"),
                'scroll_position': driver.execute_script("return {x: window.pageXOffset, y: window.pageYOffset};"),
                'user_agent': driver.execute_script("return navigator.userAgent;"),
                'path': screenshot_path
            }
        except Exception:
            return {
                'timestamp': datetime.now().isoformat(),
                'path': screenshot_path
            }
    
    def cleanup_old_screenshots(self, days_old=7):
        """Clean up screenshots older than specified days."""
        try:
            cutoff_time = time.time() - (days_old * 24 * 60 * 60)
            
            for file_path in self.output_dir.glob("*.png"):
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
            
            for file_path in self.output_dir.glob("*.html"):
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
            
            return True
            
        except Exception:
            return False