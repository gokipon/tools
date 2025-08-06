"""待機処理ヘルパー"""

import time
import logging
from typing import List, Optional, Union, Callable
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)


class WaitHelper:
    """待機処理のヘルパークラス"""
    
    @staticmethod
    def wait_for_element_appear(
        driver: webdriver.Chrome,
        selectors: Union[str, List[str]],
        timeout: int = 10
    ) -> Optional[WebElement]:
        """要素の出現を待機
        
        Args:
            driver: WebDriverインスタンス
            selectors: セレクタ（文字列 or リスト）
            timeout: 待機タイムアウト
            
        Returns:
            見つかった要素（見つからない場合はNone）
        """
        if isinstance(selectors, str):
            selectors = [selectors]
        
        for selector in selectors:
            try:
                element = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                if element and element.is_displayed():
                    logger.debug(f"要素出現確認: {selector}")
                    return element
            except TimeoutException:
                continue
        
        logger.warning(f"要素が出現しませんでした（セレクタ: {selectors}）")
        return None
    
    @staticmethod
    def wait_for_element_clickable(
        driver: webdriver.Chrome,
        selector: str,
        timeout: int = 10
    ) -> Optional[WebElement]:
        """要素がクリック可能になるまで待機
        
        Args:
            driver: WebDriverインスタンス
            selector: セレクタ
            timeout: 待機タイムアウト
            
        Returns:
            クリック可能になった要素（タイムアウトの場合はNone）
        """
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            logger.debug(f"要素がクリック可能になりました: {selector}")
            return element
            
        except TimeoutException:
            logger.warning(f"要素がクリック可能になりませんでした: {selector}")
            return None
    
    @staticmethod
    def wait_for_text_present(
        driver: webdriver.Chrome,
        selector: str,
        text: str,
        timeout: int = 10
    ) -> bool:
        """要素に特定のテキストが現れるまで待機
        
        Args:
            driver: WebDriverインスタンス
            selector: セレクタ
            text: 待機するテキスト
            timeout: 待機タイムアウト
            
        Returns:
            テキストが現れたかどうか
        """
        try:
            WebDriverWait(driver, timeout).until(
                EC.text_to_be_present_in_element((By.CSS_SELECTOR, selector), text)
            )
            logger.debug(f"テキスト出現確認: '{text}' in {selector}")
            return True
            
        except TimeoutException:
            logger.warning(f"テキストが現れませんでした: '{text}' in {selector}")
            return False
    
    @staticmethod
    def wait_for_element_disappear(
        driver: webdriver.Chrome,
        selector: str,
        timeout: int = 10
    ) -> bool:
        """要素の消失を待機
        
        Args:
            driver: WebDriverインスタンス
            selector: セレクタ
            timeout: 待機タイムアウト
            
        Returns:
            要素が消失したかどうか
        """
        try:
            WebDriverWait(driver, timeout).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, selector))
            )
            logger.debug(f"要素消失確認: {selector}")
            return True
            
        except TimeoutException:
            logger.warning(f"要素が消失しませんでした: {selector}")
            return False
    
    @staticmethod
    def wait_for_page_load(
        driver: webdriver.Chrome,
        timeout: int = 30
    ) -> bool:
        """ページの読み込み完了を待機
        
        Args:
            driver: WebDriverインスタンス
            timeout: 待機タイムアウト
            
        Returns:
            ページが読み込まれたかどうか
        """
        try:
            WebDriverWait(driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            # 追加でAJAXリクエストの完了も待機（jQuery使用サイト用）
            try:
                WebDriverWait(driver, 5).until(
                    lambda d: d.execute_script("return typeof jQuery !== 'undefined' ? jQuery.active == 0 : true")
                )
            except:
                pass  # jQueryがない場合は無視
            
            logger.debug("ページ読み込み完了")
            return True
            
        except TimeoutException:
            logger.warning("ページ読み込みがタイムアウトしました")
            return False
    
    @staticmethod
    def wait_for_condition(
        condition: Callable,
        timeout: int = 10,
        check_interval: float = 0.5
    ) -> bool:
        """カスタム条件の成立を待機
        
        Args:
            condition: 条件関数（戻り値がTrueになるまで待機）
            timeout: 待機タイムアウト
            check_interval: チェック間隔
            
        Returns:
            条件が成立したかどうか
        """
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    if condition():
                        logger.debug("カスタム条件成立")
                        return True
                except Exception as e:
                    logger.debug(f"条件チェックエラー: {e}")
                
                time.sleep(check_interval)
            
            logger.warning("カスタム条件がタイムアウトしました")
            return False
            
        except Exception as e:
            logger.error(f"条件待機エラー: {e}")
            return False
    
    @staticmethod
    def wait_for_url_change(
        driver: webdriver.Chrome,
        current_url: str,
        timeout: int = 10
    ) -> bool:
        """URLの変更を待機
        
        Args:
            driver: WebDriverインスタンス
            current_url: 現在のURL
            timeout: 待機タイムアウト
            
        Returns:
            URLが変更されたかどうか
        """
        try:
            WebDriverWait(driver, timeout).until(
                lambda d: d.current_url != current_url
            )
            logger.debug(f"URL変更確認: {current_url} -> {driver.current_url}")
            return True
            
        except TimeoutException:
            logger.warning(f"URL変更がタイムアウトしました: {current_url}")
            return False
    
    @staticmethod
    def smart_wait(
        driver: webdriver.Chrome,
        base_wait: float = 2.0,
        max_wait: float = 10.0
    ) -> None:
        """ページの状態に応じたスマート待機
        
        Args:
            driver: WebDriverインスタンス  
            base_wait: 基本待機時間
            max_wait: 最大待機時間
        """
        try:
            # 基本待機
            time.sleep(base_wait)
            
            # ローディングインジケータがあれば待機
            loading_selectors = [
                '.loading', '.spinner', '.loader',
                '[data-loading="true"]', '.animate-spin',
                '.fa-spinner', '.fa-circle-o-notch'
            ]
            
            for selector in loading_selectors:
                try:
                    if driver.find_elements(By.CSS_SELECTOR, selector):
                        WaitHelper.wait_for_element_disappear(driver, selector, timeout=int(max_wait))
                        break
                except:
                    continue
            
            # ページ読み込み完了確認
            WaitHelper.wait_for_page_load(driver, timeout=int(max_wait))
            
            logger.debug("スマート待機完了")
            
        except Exception as e:
            logger.debug(f"スマート待機エラー: {e}")
            time.sleep(base_wait)  # フォールバック