"""ブラウザ接続管理モジュール"""

import subprocess
import time
import logging
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

from .error_handler import ErrorHandler

logger = logging.getLogger(__name__)


class BrowserManager:
    """Chrome Remote Debugging接続の管理"""
    
    def __init__(self, port: int = 9222, user_data_dir: Optional[str] = None):
        """
        Args:
            port: Chrome Remote Debuggingポート番号
            user_data_dir: Chromeのユーザーデータディレクトリ
        """
        self.port = port
        self.user_data_dir = user_data_dir or "/tmp/chrome-selenium-debug"
        self.error_handler = ErrorHandler()
        self._chrome_process = None
    
    def start_chrome_debug_mode(self) -> None:
        """Chrome Remote Debuggingモードで起動"""
        try:
            chrome_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "google-chrome"
            ]
            
            chrome_cmd = None
            for path in chrome_paths:
                try:
                    # パスの存在確認
                    subprocess.run([path, "--version"], capture_output=True, check=True)
                    chrome_cmd = path
                    break
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
            
            if not chrome_cmd:
                raise RuntimeError("Chromeが見つかりません")
            
            cmd = [
                chrome_cmd,
                f"--remote-debugging-port={self.port}",
                f"--user-data-dir={self.user_data_dir}",
                "--no-first-run",
                "--disable-default-apps"
            ]
            
            self._chrome_process = subprocess.Popen(
                cmd, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
            
            # Chrome起動待機
            time.sleep(3)
            logger.info(f"Chrome Debug Mode起動 (Port: {self.port})")
            
        except Exception as e:
            logger.error(f"Chrome起動失敗: {e}")
            raise
    
    def connect(self) -> webdriver.Chrome:
        """WebDriverでChrome接続"""
        return self.error_handler.retry_operation(self._connect_internal, max_retries=3)
    
    def _connect_internal(self) -> webdriver.Chrome:
        """内部接続処理"""
        try:
            options = Options()
            options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.port}")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            
            driver = webdriver.Chrome(options=options)
            driver.implicitly_wait(10)
            
            logger.info("WebDriver接続成功")
            return driver
            
        except WebDriverException as e:
            if "No such session" in str(e) or "cannot connect" in str(e).lower():
                # Chrome Debug Modeが起動していない場合、自動起動を試行
                logger.warning("Chrome Debug Mode未起動を検出、自動起動します")
                self.start_chrome_debug_mode()
                time.sleep(2)
                
                # 再度接続を試行
                options = Options()
                options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.port}")
                driver = webdriver.Chrome(options=options)
                driver.implicitly_wait(10)
                return driver
            else:
                raise e
    
    def disconnect(self, driver: webdriver.Chrome) -> None:
        """WebDriver接続終了"""
        try:
            if driver:
                driver.quit()
                logger.info("WebDriver接続終了")
        except Exception as e:
            logger.error(f"WebDriver終了エラー: {e}")
    
    def cleanup(self) -> None:
        """リソースのクリーンアップ"""
        try:
            if self._chrome_process and self._chrome_process.poll() is None:
                self._chrome_process.terminate()
                self._chrome_process.wait(timeout=5)
                logger.info("Chromeプロセス終了")
        except Exception as e:
            logger.error(f"クリーンアップエラー: {e}")