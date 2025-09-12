#!/usr/bin/env python3
"""
ファイル操作共通ユーティリティ

ワークフロー間で共通するファイル操作の統一実装
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import Optional


def sanitize_filename(filename: str) -> str:
    """
    ファイル名をサニタイズ（特殊文字を除去・置換）
    
    Args:
        filename: 元のファイル名
        
    Returns:
        サニタイズされたファイル名
    """
    # 禁止文字を除去・置換
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = filename.replace(' ', '_')
    filename = filename.replace('　', '_')  # 全角スペースも置換
    
    # 先頭・末尾の空白やドットを除去
    filename = filename.strip(' .')
    
    # 空の場合のフォールバック
    if not filename:
        filename = 'untitled'
    
    return filename


def ensure_directory(path: Path) -> Path:
    """
    ディレクトリが存在しない場合は作成
    
    Args:
        path: ディレクトリパス
        
    Returns:
        作成されたディレクトリパス
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_file_safe(file_path: Path, encoding: str = 'utf-8') -> Optional[str]:
    """
    ファイルを安全に読み込み
    
    Args:
        file_path: ファイルパス
        encoding: エンコーディング
        
    Returns:
        ファイル内容（読み込めない場合はNone）
    """
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()
        
        if not content.strip():
            return None
        
        return content
    
    except Exception:
        return None


def write_file_safe(file_path: Path, content: str, encoding: str = 'utf-8') -> bool:
    """
    ファイルを安全に書き込み
    
    Args:
        file_path: ファイルパス
        content: 書き込み内容
        encoding: エンコーディング
        
    Returns:
        成功した場合True
    """
    try:
        # ディレクトリを確実に作成
        ensure_directory(file_path.parent)
        
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        
        return True
    
    except Exception:
        return False


def append_to_file_safe(file_path: Path, content: str, encoding: str = 'utf-8') -> bool:
    """
    ファイルに安全に追記
    
    Args:
        file_path: ファイルパス
        content: 追記内容
        encoding: エンコーディング
        
    Returns:
        成功した場合True
    """
    try:
        ensure_directory(file_path.parent)
        
        with open(file_path, 'a', encoding=encoding) as f:
            f.write(content)
        
        return True
    
    except Exception:
        return False


def format_date_for_path(date_obj: datetime) -> str:
    """
    日付をパス用文字列にフォーマット
    
    Args:
        date_obj: 日付オブジェクト
        
    Returns:
        YYYY-MM-DD形式の文字列
    """
    return date_obj.strftime('%Y-%m-%d')


def get_file_with_date_placeholder(path_template: str, date: str) -> Path:
    """
    日付プレースホルダーを含むパスを実際のパスに変換
    
    Args:
        path_template: {date}プレースホルダーを含むパステンプレート
        date: YYYY-MM-DD形式の日付文字列
        
    Returns:
        実際のファイルパス
    """
    return Path(path_template.format(date=date))


def create_markdown_with_metadata(title: str, content: str, 
                                 metadata: Optional[dict] = None) -> str:
    """
    メタデータ付きMarkdownファイルを作成
    
    Args:
        title: タイトル
        content: メイン内容
        metadata: 追加メタデータ
        
    Returns:
        フォーマットされたMarkdown文字列
    """
    result = f"# {title}\n\n"
    
    # メタデータセクション
    result += f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    if metadata:
        for key, value in metadata.items():
            result += f"{key}: {value}\n"
    
    result += "\n---\n\n"
    result += content
    
    return result