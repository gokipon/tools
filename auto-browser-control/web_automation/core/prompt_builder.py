"""プロンプト構築モジュール"""

import os
import logging
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Obsidianファイルを読み込んでプロンプト生成"""
    
    def build_prompt(self, template_path: str, diary_path: str) -> str:
        """プロンプトを構築
        
        Args:
            template_path: テンプレートファイルのパス
            diary_path: 日記ファイルのパス
            
        Returns:
            結合されたプロンプト文字列
        """
        try:
            # テンプレートファイル読み込み
            template_content = self._read_file(template_path)
            if not template_content:
                logger.warning(f"テンプレートファイルが空または見つかりません: {template_path}")
                template_content = "# デイリーリサーチ\n\n"
            
            # 日記ファイル読み込み
            diary_content = self._read_file(diary_path)
            if not diary_content:
                logger.warning(f"日記ファイルが見つかりません: {diary_path}")
                diary_content = "前日の日記はありません。"
            
            # プロンプト結合
            prompt = self._combine_content(template_content, diary_content)
            
            logger.info("プロンプト構築完了")
            return prompt
            
        except Exception as e:
            logger.error(f"プロンプト構築エラー: {e}")
            raise
    
    def _read_file(self, file_path: str) -> str:
        """ファイルを読み込み
        
        Args:
            file_path: ファイルパス
            
        Returns:
            ファイル内容
        """
        try:
            if not os.path.exists(file_path):
                logger.warning(f"ファイルが存在しません: {file_path}")
                return ""
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
            logger.debug(f"ファイル読み込み成功: {file_path}")
            return content
            
        except Exception as e:
            logger.error(f"ファイル読み込みエラー ({file_path}): {e}")
            return ""
    
    def _combine_content(self, template: str, diary: str) -> str:
        """テンプレートと日記を結合
        
        Args:
            template: テンプレート内容
            diary: 日記内容
            
        Returns:
            結合されたプロンプト
        """
        separator = "\n\n---\n\n"
        
        prompt = template + separator + "## 前日の振り返り\n\n" + diary
        
        return prompt
    
    def generate_diary_path(
        self, 
        base_path: str, 
        date: Optional[datetime] = None
    ) -> str:
        """日記ファイルのパスを自動生成
        
        Args:
            base_path: 基本パス (Obsidianのdiaryディレクトリ)
            date: 日付 (Noneの場合は前日)
            
        Returns:
            日記ファイルのパス
        """
        if date is None:
            date = datetime.now() - timedelta(days=1)
        
        diary_path = os.path.join(
            base_path,
            str(date.year),
            f"{date.month:02d}",
            f"{date.strftime('%Y-%m-%d')}.md"
        )
        
        logger.debug(f"日記パス生成: {diary_path}")
        return diary_path
    
    def validate_paths(self, template_path: str, diary_path: str) -> dict:
        """パスの検証
        
        Args:
            template_path: テンプレートパス
            diary_path: 日記パス
            
        Returns:
            検証結果辞書
        """
        result = {
            "template_exists": os.path.exists(template_path),
            "diary_exists": os.path.exists(diary_path),
            "template_readable": False,
            "diary_readable": False
        }
        
        if result["template_exists"]:
            try:
                with open(template_path, 'r', encoding='utf-8'):
                    result["template_readable"] = True
            except Exception:
                pass
        
        if result["diary_exists"]:
            try:
                with open(diary_path, 'r', encoding='utf-8'):
                    result["diary_readable"] = True
            except Exception:
                pass
        
        return result