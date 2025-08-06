"""GitHub専用操作クラス"""

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


class GitHubService(BaseService):
    """GitHub専用操作"""
    
    def get_service_url(self) -> str:
        """GitHubのURL"""
        return "https://github.com"
    
    def __init__(self, browser_manager):
        super().__init__(browser_manager)
        self.element_helper = ElementHelper()
        self.wait_helper = WaitHelper()
    
    def create_issue(
        self, 
        repo_url: str, 
        title: str, 
        body: str,
        labels: Optional[List[str]] = None
    ) -> bool:
        """Issueを作成
        
        Args:
            repo_url: リポジトリURL
            title: Issue タイトル
            body: Issue 本文
            labels: ラベル一覧
            
        Returns:
            作成成功の可否
        """
        try:
            # Issueページに移動
            issues_url = f"{repo_url.rstrip('/')}/issues/new"
            self.driver.get(issues_url)
            time.sleep(3)
            
            # タイトル入力
            title_field = self.driver.find_element(By.ID, "issue_title")
            title_field.send_keys(title)
            
            # 本文入力
            body_field = self.driver.find_element(By.ID, "issue_body")
            body_field.send_keys(body)
            
            # ラベル追加（オプション）
            if labels:
                self._add_labels(labels)
            
            # Issue作成
            submit_button = self.driver.find_element(
                By.CSS_SELECTOR, 
                'button[type="submit"]:contains("Submit new issue")'
            )
            submit_button.click()
            
            time.sleep(3)
            logger.info(f"Issue作成完了: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Issue作成エラー: {e}")
            return False
    
    def _add_labels(self, labels: List[str]) -> None:
        """Issueにラベルを追加"""
        try:
            # ラベルボタンをクリック
            label_button = self.driver.find_element(
                By.CSS_SELECTOR, 
                'button[aria-label="Labels"]'
            )
            label_button.click()
            time.sleep(1)
            
            # 各ラベルを選択
            for label in labels:
                try:
                    label_checkbox = self.driver.find_element(
                        By.XPATH, 
                        f'//span[contains(text(), "{label}")]/preceding-sibling::input'
                    )
                    if not label_checkbox.is_selected():
                        label_checkbox.click()
                        time.sleep(0.5)
                except NoSuchElementException:
                    logger.warning(f"ラベルが見つかりません: {label}")
            
            # ラベルメニューを閉じる
            self.driver.find_element(By.TAG_NAME, "body").click()
            time.sleep(1)
            
        except Exception as e:
            logger.warning(f"ラベル追加エラー: {e}")
    
    def get_repository_info(self, repo_url: str) -> Dict[str, Any]:
        """リポジトリ情報を取得
        
        Args:
            repo_url: リポジトリURL
            
        Returns:
            リポジトリ情報
        """
        try:
            self.driver.get(repo_url)
            time.sleep(3)
            
            # 基本情報を取得
            info = {}
            
            # リポジトリ名
            try:
                repo_name = self.driver.find_element(
                    By.CSS_SELECTOR, 
                    'h1 strong a, [data-testid="AppHeader-context-item-label"]'
                ).text
                info['name'] = repo_name
            except NoSuchElementException:
                info['name'] = 'Unknown'
            
            # 説明
            try:
                description = self.driver.find_element(
                    By.CSS_SELECTOR,
                    '[data-testid="repository-description"], .f4'
                ).text
                info['description'] = description
            except NoSuchElementException:
                info['description'] = ''
            
            # スター数
            try:
                stars = self.driver.find_element(
                    By.CSS_SELECTOR,
                    '#repo-stars-counter-star, .starring-counter'
                ).text
                info['stars'] = stars
            except NoSuchElementException:
                info['stars'] = '0'
            
            # フォーク数
            try:
                forks = self.driver.find_element(
                    By.CSS_SELECTOR,
                    '#repo-network-counter, .social-count'
                ).text
                info['forks'] = forks
            except NoSuchElementException:
                info['forks'] = '0'
            
            logger.info(f"リポジトリ情報取得完了: {repo_name}")
            return info
            
        except Exception as e:
            logger.error(f"リポジトリ情報取得エラー: {e}")
            return {}
    
    def search_repositories(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """リポジトリを検索
        
        Args:
            query: 検索クエリ
            limit: 取得する件数
            
        Returns:
            リポジトリ情報のリスト
        """
        try:
            # 検索ページに移動
            search_url = f"https://github.com/search?q={query}&type=repositories"
            self.driver.get(search_url)
            time.sleep(3)
            
            repositories = []
            
            # 検索結果を取得
            repo_items = self.driver.find_elements(
                By.CSS_SELECTOR,
                '[data-testid="results-list"] > div'
            )[:limit]
            
            for item in repo_items:
                try:
                    repo_info = self._extract_repo_search_info(item)
                    if repo_info:
                        repositories.append(repo_info)
                except Exception as e:
                    logger.warning(f"リポジトリ情報抽出エラー: {e}")
                    continue
            
            logger.info(f"{len(repositories)}件のリポジトリを取得")
            return repositories
            
        except Exception as e:
            logger.error(f"リポジトリ検索エラー: {e}")
            return []
    
    def _extract_repo_search_info(self, item_element) -> Optional[Dict[str, Any]]:
        """検索結果からリポジトリ情報を抽出"""
        try:
            # リポジトリ名とURL
            name_link = item_element.find_element(By.CSS_SELECTOR, 'h3 a')
            name = name_link.text
            url = name_link.get_attribute('href')
            
            # 説明
            try:
                description = item_element.find_element(By.CSS_SELECTOR, 'p').text
            except NoSuchElementException:
                description = ''
            
            # 言語
            try:
                language = item_element.find_element(
                    By.CSS_SELECTOR, 
                    '[itemprop="programmingLanguage"]'
                ).text
            except NoSuchElementException:
                language = ''
            
            # スター数
            try:
                stars = item_element.find_element(
                    By.CSS_SELECTOR,
                    'a[href$="/stargazers"]'
                ).text
            except NoSuchElementException:
                stars = '0'
            
            return {
                'name': name,
                'url': url,
                'description': description,
                'language': language,
                'stars': stars
            }
            
        except NoSuchElementException:
            return None