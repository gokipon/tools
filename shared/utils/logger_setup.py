#!/usr/bin/env python3
"""
統一ログ設定ユーティリティ

全ワークフローで一貫したログ設定を提供
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from ..config_loader import get_config


def setup_logger(name: str, 
                log_file: Optional[Path] = None,
                log_level: Optional[str] = None,
                format_string: Optional[str] = None) -> logging.Logger:
    """
    統一されたログ設定でロガーを作成
    
    Args:
        name: ロガー名（通常は__name__）
        log_file: ログファイルパス（Noneの場合はファイル出力なし）
        log_level: ログレベル（NoneならCONFIGから取得）
        format_string: フォーマット文字列（NoneならCONFIGから取得）
        
    Returns:
        設定されたロガーインスタンス
    """
    config = get_config()
    log_config = config.get_log_config()
    
    # パラメータのデフォルト値設定
    if log_level is None:
        log_level = log_config['level']
    if format_string is None:
        format_string = log_config['format']
    
    # ロガーを作成
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # 既存のハンドラーをクリア（重複防止）
    logger.handlers.clear()
    
    # フォーマッターを作成
    formatter = logging.Formatter(format_string)
    
    # コンソールハンドラーを追加
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # ファイルハンドラーを追加（指定された場合）
    if log_file:
        # ログディレクトリを作成
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_workflow_logger(workflow_name: str, create_log_file: bool = True) -> logging.Logger:
    """
    ワークフロー用のロガーを取得
    
    Args:
        workflow_name: ワークフロー名（'radio', 'research', 'get-myinfo'など）
        create_log_file: ログファイルを作成するか
        
    Returns:
        ワークフロー専用ロガー
    """
    config = get_config()
    
    log_file = None
    if create_log_file:
        log_dir = config.project_root / "logs"
        log_file = log_dir / f"{workflow_name}.log"
    
    return setup_logger(f"tools.{workflow_name}", log_file)


class LoggerMixin:
    """ロガー機能をクラスに追加するMixin"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = None
    
    @property
    def logger(self) -> logging.Logger:
        """ロガーインスタンスを遅延初期化で取得"""
        if self._logger is None:
            class_name = self.__class__.__name__
            module_name = self.__class__.__module__
            logger_name = f"{module_name}.{class_name}"
            
            # ワークフロー名を推測
            workflow_name = "unknown"
            if "radio" in module_name:
                workflow_name = "radio"
            elif "research" in module_name:
                workflow_name = "research"
            elif "get-myinfo" in module_name or "myinfo" in module_name:
                workflow_name = "get-myinfo"
            
            self._logger = get_workflow_logger(workflow_name)
        
        return self._logger