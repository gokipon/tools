"""スクリーンショット機能"""

import os
import time
import logging
from datetime import datetime
from typing import Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)


class ScreenshotHelper:
    """スクリーンショット撮影のヘルパークラス"""
    
    def __init__(self, output_dir: str = "screenshots"):
        """
        Args:
            output_dir: スクリーンショット保存ディレクトリ
        """
        self.output_dir = output_dir
        self._ensure_output_dir()
    
    def _ensure_output_dir(self) -> None:
        """出力ディレクトリを作成"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.debug(f"スクリーンショット保存ディレクトリ作成: {self.output_dir}")
    
    def take_full_screenshot(
        self, 
        driver: webdriver.Chrome,
        filename: Optional[str] = None,
        add_timestamp: bool = True
    ) -> str:
        """フルページスクリーンショットを撮影
        
        Args:
            driver: WebDriverインスタンス
            filename: ファイル名（指定しない場合は自動生成）
            add_timestamp: タイムスタンプを追加するか
            
        Returns:
            保存されたファイルのパス
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
            elif add_timestamp:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                name, ext = os.path.splitext(filename)
                filename = f"{name}_{timestamp}{ext}"
            
            filepath = os.path.join(self.output_dir, filename)
            
            # フルページスクリーンショット
            driver.save_screenshot(filepath)
            
            logger.info(f"フルスクリーンショット保存: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"スクリーンショット撮影エラー: {e}")
            return ""
    
    def take_element_screenshot(
        self,
        driver: webdriver.Chrome,
        element_selector: str,
        filename: Optional[str] = None,
        add_timestamp: bool = True
    ) -> str:
        """特定要素のスクリーンショットを撮影
        
        Args:
            driver: WebDriverインスタンス
            element_selector: 要素のセレクタ
            filename: ファイル名
            add_timestamp: タイムスタンプを追加するか
            
        Returns:
            保存されたファイルのパス
        """
        try:
            element = driver.find_element(By.CSS_SELECTOR, element_selector)
            
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"element_{timestamp}.png"
            elif add_timestamp:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                name, ext = os.path.splitext(filename)
                filename = f"{name}_{timestamp}{ext}"
            
            filepath = os.path.join(self.output_dir, filename)
            
            # 要素のスクリーンショット
            element.screenshot(filepath)
            
            logger.info(f"要素スクリーンショット保存: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"要素スクリーンショット撮影エラー: {e}")
            return ""
    
    def take_before_after_screenshot(
        self,
        driver: webdriver.Chrome,
        operation_name: str = "operation"
    ) -> Tuple[str, str]:
        """操作前後のスクリーンショットを撮影
        
        Args:
            driver: WebDriverインスタンス
            operation_name: 操作名
            
        Returns:
            (before_filepath, after_filepath)のタプル
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        before_path = self.take_full_screenshot(
            driver, 
            f"{operation_name}_before_{timestamp}.png",
            add_timestamp=False
        )
        
        return before_path, ""
    
    def complete_before_after_screenshot(
        self,
        driver: webdriver.Chrome,
        before_path: str,
        operation_name: str = "operation"
    ) -> Tuple[str, str]:
        """操作後のスクリーンショットを撮影（before_after_screenshotの完了版）
        
        Args:
            driver: WebDriverインスタンス
            before_path: 操作前のスクリーンショットパス
            operation_name: 操作名
            
        Returns:
            (before_filepath, after_filepath)のタプル
        """
        timestamp = before_path.split('_before_')[1].replace('.png', '') if '_before_' in before_path else datetime.now().strftime("%Y%m%d_%H%M%S")
        
        after_path = self.take_full_screenshot(
            driver,
            f"{operation_name}_after_{timestamp}.png",
            add_timestamp=False
        )
        
        return before_path, after_path
    
    def create_comparison_html(
        self,
        before_path: str,
        after_path: str,
        operation_name: str = "操作"
    ) -> str:
        """操作前後の比較HTMLを生成
        
        Args:
            before_path: 操作前スクリーンショットパス
            after_path: 操作後スクリーンショットパス
            operation_name: 操作名
            
        Returns:
            HTMLファイルのパス
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            html_filename = f"comparison_{timestamp}.html"
            html_filepath = os.path.join(self.output_dir, html_filename)
            
            before_filename = os.path.basename(before_path)
            after_filename = os.path.basename(after_path)
            
            html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{operation_name} - 比較結果</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .container {{ display: flex; gap: 20px; }}
        .screenshot {{ flex: 1; }}
        .screenshot img {{ width: 100%; border: 1px solid #ccc; }}
        .title {{ text-align: center; margin-bottom: 10px; font-weight: bold; }}
        h1 {{ text-align: center; }}
        .timestamp {{ text-align: center; color: #666; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <h1>{operation_name} - 比較結果</h1>
    <div class="timestamp">作成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
    
    <div class="container">
        <div class="screenshot">
            <div class="title">操作前</div>
            <img src="{before_filename}" alt="操作前">
        </div>
        <div class="screenshot">
            <div class="title">操作後</div>
            <img src="{after_filename}" alt="操作後">
        </div>
    </div>
</body>
</html>
"""
            
            with open(html_filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"比較HTML作成: {html_filepath}")
            return html_filepath
            
        except Exception as e:
            logger.error(f"比較HTML作成エラー: {e}")
            return ""
    
    def cleanup_old_screenshots(self, days: int = 7) -> None:
        """古いスクリーンショットを削除
        
        Args:
            days: 保持日数
        """
        try:
            current_time = time.time()
            cutoff_time = current_time - (days * 24 * 60 * 60)
            
            deleted_count = 0
            
            for filename in os.listdir(self.output_dir):
                filepath = os.path.join(self.output_dir, filename)
                
                if os.path.isfile(filepath):
                    file_time = os.path.getmtime(filepath)
                    
                    if file_time < cutoff_time:
                        os.remove(filepath)
                        deleted_count += 1
                        logger.debug(f"古いファイル削除: {filename}")
            
            if deleted_count > 0:
                logger.info(f"{deleted_count}個の古いスクリーンショットを削除しました")
            
        except Exception as e:
            logger.error(f"古いスクリーンショット削除エラー: {e}")