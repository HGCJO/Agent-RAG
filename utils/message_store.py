import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from utils.logger_handler import logger

class MessageStore:
    """对话历史存储管理"""
    
    def __init__(self, storage_dir: str = "history"):
        """
        初始化消息存储
        
        Args:
            storage_dir: 历史文件存储目录
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"[消息存储] 初始化完毕，存储路径: {self.storage_dir}")
    
    def _get_user_history_file(self, user_id: str) -> Path:
        """获取用户历史文件路径"""
        return self.storage_dir / f"{user_id}_history.json"
    
    def save_message(self, user_id: str, role: str, content: str) -> bool:
        """
        保存单条消息
        
        Args:
            user_id: 用户 ID
            role: 消息角色 ("user" 或 "assistant")
            content: 消息内容
        
        Returns:
            是否保存成功
        """
        try:
            history_file = self._get_user_history_file(user_id)
            
            # 读取现有历史
            history = []
            if history_file.exists():
                with open(history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
            
            # 添加新消息
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            }
            history.append(message)
            
            # 保存回文件
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"[消息存储] 用户 {user_id} 消息已保存")
            return True
        
        except Exception as e:
            logger.error(f"[消息存储] 保存消息失败: {e}", exc_info=True)
            return False
    
    def save_messages(self, user_id: str, messages: List[Dict]) -> bool:
        """
        批量保存消息
        
        Args:
            user_id: 用户 ID
            messages: 消息列表 [{"role": "...", "content": "...", "timestamp": "..."}, ...]
        
        Returns:
            是否保存成功
        """
        try:
            history_file = self._get_user_history_file(user_id)
            
            # 添加时间戳
            for msg in messages:
                if "timestamp" not in msg:
                    msg["timestamp"] = datetime.now().isoformat()
            
            # 保存文件
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)
            
            logger.info(f"[消息存储] 用户 {user_id} 的 {len(messages)} 条消息已保存")
            return True
        
        except Exception as e:
            logger.error(f"[消息存储] 批量保存消息失败: {e}", exc_info=True)
            return False
    
    def load_messages(self, user_id: str, limit: Optional[int] = None) -> List[Dict]:
        """
        加载用户历史消息
        
        Args:
            user_id: 用户 ID
            limit: 最多加载多少条（None 为全部）
        
        Returns:
            消息列表
        """
        try:
            history_file = self._get_user_history_file(user_id)
            
            if not history_file.exists():
                logger.info(f"[消息存储] 用户 {user_id} 没有历史记录")
                return []
            
            with open(history_file, "r", encoding="utf-8") as f:
                messages = json.load(f)
            
            # 如果指定了限制，取最后 limit 条
            if limit:
                messages = messages[-limit:]
            
            logger.info(f"[消息存储] 加载用户 {user_id} 的 {len(messages)} 条消息")
            return messages
        
        except Exception as e:
            logger.error(f"[消息存储] 加载消息失败: {e}", exc_info=True)
            return []
    
    def clear_messages(self, user_id: str) -> bool:
        """
        清空用户历史消息
        
        Args:
            user_id: 用户 ID
        
        Returns:
            是否清空成功
        """
        try:
            history_file = self._get_user_history_file(user_id)
            if history_file.exists():
                history_file.unlink()
            logger.info(f"[消息存储] 用户 {user_id} 的历史消息已清空")
            return True
        
        except Exception as e:
            logger.error(f"[消息存储] 清空消息失败: {e}", exc_info=True)
            return False
    
    def get_user_stats(self, user_id: str) -> Dict:
        """获取用户的历史统计信息"""
        try:
            messages = self.load_messages(user_id)
            user_msgs = [m for m in messages if m["role"] == "user"]
            assistant_msgs = [m for m in messages if m["role"] == "assistant"]
            
            return {
                "user_id": user_id,
                "total_messages": len(messages),
                "user_messages": len(user_msgs),
                "assistant_messages": len(assistant_msgs),
                "first_message_time": messages[0]["timestamp"] if messages else None,
                "last_message_time": messages[-1]["timestamp"] if messages else None
            }
        
        except Exception as e:
            logger.error(f"[消息存储] 获取统计信息失败: {e}", exc_info=True)
            return {}