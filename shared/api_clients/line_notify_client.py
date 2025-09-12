#!/usr/bin/env python3
"""
LINE Notify 統一クライアント

全ワークフローで共有されるLINE Notify APIクライアント
"""

from typing import Optional
import requests

from ..config_loader import get_config
from ..utils.logger_setup import LoggerMixin


class LineNotifyClient(LoggerMixin):
    """LINE Notify API統一クライアント"""
    
    def __init__(self, custom_config: Optional[dict] = None):
        """
        クライアントを初期化
        
        Args:
            custom_config: カスタム設定（Noneの場合は共通設定を使用）
        """
        super().__init__()
        config = get_config()
        
        if custom_config:
            self.config = custom_config
        else:
            self.config = config.get_line_config()
        
        self.token = self.config.get('token')
        self.api_url = self.config['api_url']
        
        if not self.token:
            self.logger.warning("LINE Notify token not configured - notifications will be disabled")
    
    def send_message(self, message: str, 
                    sticker_package_id: Optional[int] = None,
                    sticker_id: Optional[int] = None) -> bool:
        """
        LINE Notifyでメッセージを送信
        
        Args:
            message: 送信するメッセージ
            sticker_package_id: スタンプパッケージID（オプション）
            sticker_id: スタンプID（オプション）
            
        Returns:
            送信成功時True
        """
        if not self.token:
            self.logger.warning("LINE Notify token not available - skipping notification")
            return False
        
        try:
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {'message': message}
            
            # スタンプが指定された場合は追加
            if sticker_package_id and sticker_id:
                data['stickerPackageId'] = sticker_package_id
                data['stickerId'] = sticker_id
            
            response = requests.post(
                self.api_url,
                headers=headers,
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info("LINE notification sent successfully")
                return True
            else:
                self.logger.error(f"LINE notification failed: HTTP {response.status_code}")
                self.logger.debug(f"Response: {response.text}")
                return False
        
        except Exception as e:
            self.logger.error(f"Failed to send LINE notification: {e}")
            return False
    
    def send_success_message(self, title: str, details: str = "") -> bool:
        """
        成功通知メッセージを送信
        
        Args:
            title: 成功したタスクのタイトル
            details: 詳細情報（オプション）
            
        Returns:
            送信成功時True
        """
        message = f"✅ {title}\n"
        if details:
            message += f"\n{details}"
        
        # 成功スタンプを追加（LINE公式スタンプ）
        return self.send_message(message, sticker_package_id=446, sticker_id=1988)
    
    def send_error_message(self, title: str, error_details: str = "") -> bool:
        """
        エラー通知メッセージを送信
        
        Args:
            title: エラーが発生したタスクのタイトル
            error_details: エラー詳細（オプション）
            
        Returns:
            送信成功時True
        """
        message = f"❌ {title}\n"
        if error_details:
            message += f"\nエラー詳細: {error_details}"
        
        # エラースタンプを追加
        return self.send_message(message, sticker_package_id=446, sticker_id=1989)
    
    def send_workflow_completion(self, workflow_name: str, 
                               items_processed: int = 0,
                               output_path: str = "",
                               execution_time: Optional[str] = None) -> bool:
        """
        ワークフロー完了通知を送信
        
        Args:
            workflow_name: ワークフロー名
            items_processed: 処理したアイテム数
            output_path: 出力先パス
            execution_time: 実行時間
            
        Returns:
            送信成功時True
        """
        message = f"🎉 {workflow_name} 完了\n"
        
        if items_processed > 0:
            message += f"処理件数: {items_processed}\n"
        
        if output_path:
            message += f"出力先: {output_path}\n"
        
        if execution_time:
            message += f"実行時間: {execution_time}\n"
        
        return self.send_success_message(workflow_name, message.strip())
    
    def test_connection(self) -> bool:
        """
        LINE Notify APIへの接続テスト
        
        Returns:
            接続成功時True
        """
        return self.send_message("📡 LINE Notify 接続テスト")


# よく使われる便利関数
def create_line_client() -> LineNotifyClient:
    """デフォルト設定でLINE Notifyクライアントを作成"""
    return LineNotifyClient()


def send_radio_completion_notice(chapters_count: int, output_dir: str, date: str) -> bool:
    """ラジオ台本生成完了通知"""
    client = create_line_client()
    
    message = f"""📻 ラジオ台本生成完了

日付: {date}
章数: {chapters_count}
出力先: {output_dir}
"""
    
    return client.send_success_message("ラジオ台本生成", message.strip())


def send_research_completion_notice(query: str, output_file: str) -> bool:
    """リサーチ完了通知"""
    client = create_line_client()
    
    message = f"""🔍 自動リサーチ完了

クエリ: {query}
出力: {output_file}
"""
    
    return client.send_success_message("自動リサーチ", message.strip())


def send_error_notice(workflow_name: str, error_message: str) -> bool:
    """エラー通知"""
    client = create_line_client()
    return client.send_error_message(f"{workflow_name} エラー", error_message)