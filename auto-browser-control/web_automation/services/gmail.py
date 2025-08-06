"""Gmail専用操作クラス"""

import time
import logging
from typing import List, Dict, Any, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .base_service import BaseService
from ..utils.element_helper import ElementHelper
from ..utils.wait_helper import WaitHelper

logger = logging.getLogger(__name__)


class GmailService(BaseService):
    """Gmail専用操作"""
    
    def get_service_url(self) -> str:
        """GmailのURL"""
        return "https://mail.google.com"
    
    def __init__(self, browser_manager):
        super().__init__(browser_manager)
        self.element_helper = ElementHelper()
        self.wait_helper = WaitHelper()
    
    def send_email(self, to: str, subject: str, body: str) -> bool:
        """メールを送信
        
        Args:
            to: 宛先
            subject: 件名
            body: 本文
            
        Returns:
            送信成功の可否
        """
        try:
            self.navigate_to_service()
            time.sleep(3)
            
            # 作成ボタンをクリック
            self._click_compose_button()
            
            # メール情報を入力
            self._fill_email_form(to, subject, body)
            
            # 送信
            self._send_email()
            
            logger.info(f"メール送信完了: {to}")
            return True
            
        except Exception as e:
            logger.error(f"Gmail送信エラー: {e}")
            return False
    
    def _click_compose_button(self) -> None:
        """作成ボタンをクリック"""
        compose_selectors = [
            '[data-tooltip="作成"]',
            '[aria-label*="作成"]',
            '[aria-label*="Compose"]',
            'div[role="button"]:contains("作成")'
        ]
        
        button = self.element_helper.find_element_with_fallbacks(
            self.driver, compose_selectors
        )
        
        if button:
            button.click()
            time.sleep(2)
        else:
            raise NoSuchElementException("作成ボタンが見つかりません")
    
    def _fill_email_form(self, to: str, subject: str, body: str) -> None:
        """メールフォームを入力"""
        # 宛先入力
        to_field = self.driver.find_element(By.CSS_SELECTOR, '[aria-label*="To"]')
        to_field.send_keys(to)
        time.sleep(1)
        
        # 件名入力
        subject_field = self.driver.find_element(By.CSS_SELECTOR, '[aria-label*="Subject"]')
        subject_field.send_keys(subject)
        time.sleep(1)
        
        # 本文入力
        body_field = self.driver.find_element(By.CSS_SELECTOR, '[aria-label*="Message Body"]')
        body_field.send_keys(body)
        time.sleep(1)
    
    def _send_email(self) -> None:
        """メールを送信"""
        send_selectors = [
            '[aria-label*="Send"]',
            '[data-tooltip*="Send"]',
            'div[role="button"]:contains("Send")'
        ]
        
        send_button = self.element_helper.find_element_with_fallbacks(
            self.driver, send_selectors
        )
        
        if send_button:
            send_button.click()
            time.sleep(3)
        else:
            # Ctrl+Enterで送信を試行
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.CONTROL + Keys.RETURN)
    
    def get_recent_emails(self, count: int = 5) -> List[Dict[str, Any]]:
        """最近のメールを取得
        
        Args:
            count: 取得するメール数
            
        Returns:
            メール情報のリスト
        """
        try:
            self.navigate_to_service()
            time.sleep(3)
            
            emails = []
            
            # メール行を取得
            email_rows = self.driver.find_elements(
                By.CSS_SELECTOR, 
                '[role="listitem"], tr[class*="zA"]'
            )[:count]
            
            for row in email_rows:
                try:
                    email_info = self._extract_email_info(row)
                    if email_info:
                        emails.append(email_info)
                except Exception as e:
                    logger.warning(f"メール情報抽出エラー: {e}")
                    continue
            
            logger.info(f"{len(emails)}件のメール情報を取得")
            return emails
            
        except Exception as e:
            logger.error(f"メール取得エラー: {e}")
            return []
    
    def _extract_email_info(self, row_element) -> Optional[Dict[str, Any]]:
        """メール行から情報を抽出"""
        try:
            # 送信者
            sender = row_element.find_element(
                By.CSS_SELECTOR, 
                '[email], .go span, .yW span'
            ).text
            
            # 件名
            subject = row_element.find_element(
                By.CSS_SELECTOR,
                '.bog, .y6 span, [data-thread-id] span'
            ).text
            
            # 日時
            date = row_element.find_element(
                By.CSS_SELECTOR,
                '.xY span, .xW, [title*=":"]'
            ).get_attribute('title') or row_element.find_element(
                By.CSS_SELECTOR,
                '.xY span, .xW'
            ).text
            
            return {
                'sender': sender,
                'subject': subject,
                'date': date
            }
            
        except NoSuchElementException:
            return None