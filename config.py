"""
配置管理模块
从 .env 文件读取配置
"""

import os
from pathlib import Path
from typing import Optional
import pytz
from dotenv import load_dotenv

# 加载 .env 文件
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """配置类 - 从环境变量读取所有配置"""
    
    # ==================== Telegram 配置 ====================
    API_ID: int = int(os.getenv('API_ID', '0'))
    API_HASH: str = os.getenv('API_HASH', '')
    STRING_SESSION: str = os.getenv('STRING_SESSION', '')
    TG_CHAT_ID: int = int(os.getenv('TG_CHAT_ID', '0'))
    
    # ==================== Webhook 配置 ====================
    WEBHOOK_URL: str = os.getenv('WEBHOOK_URL', '')
    WEBHOOK_SEND_INTERVAL: float = float(os.getenv('WEBHOOK_SEND_INTERVAL', '3.0'))
    
    # ==================== 运行时配置 ====================
    TIMEZONE = pytz.timezone('Asia/Shanghai')
    WORK_START_HOUR: int = int(os.getenv('WORK_START_HOUR', '0'))
    WORK_END_HOUR: int = int(os.getenv('WORK_END_HOUR', '24'))
    
    # ==================== 日志配置 ====================
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.getenv('LOG_FILE', 'logs/telegram_monitor.log')
    
    # ==================== 文件路径 ====================
    LAST_ID_FILE: Path = Path('last_id.txt')
    
    @classmethod
    def validate(cls) -> tuple[bool, Optional[str]]:
        """
        验证必需的配置是否存在
        
        Returns:
            (是否有效, 错误信息)
        """
        if not cls.API_ID or cls.API_ID == 0:
            return False, "未设置 API_ID 环境变量"
        
        if not cls.API_HASH:
            return False, "未设置 API_HASH 环境变量"
        
        if not cls.STRING_SESSION:
            return False, "未设置 STRING_SESSION 环境变量"
        
        if not cls.TG_CHAT_ID or cls.TG_CHAT_ID == 0:
            return False, "未设置 TG_CHAT_ID 环境变量"
        
        if not cls.WEBHOOK_URL:
            return False, "未设置 WEBHOOK_URL 环境变量"
        
        return True, None
    
    @classmethod
    def display(cls) -> None:
        """显示当前配置（隐藏敏感信息）"""
        print("\n" + "=" * 60)
        print("  当前配置")
        print("=" * 60)
        print(f"API_ID: {cls.API_ID}")
        print(f"API_HASH: {'*' * 8}...{cls.API_HASH[-4:] if cls.API_HASH else 'N/A'}")
        print(f"STRING_SESSION: {'已配置' if cls.STRING_SESSION else '未配置'}")
        print(f"TG_CHAT_ID: {cls.TG_CHAT_ID}")
        print(f"WEBHOOK_URL: {cls.WEBHOOK_URL[:50]}..." if len(cls.WEBHOOK_URL) > 50 else f"WEBHOOK_URL: {cls.WEBHOOK_URL}")
        print(f"工作时段: {cls.WORK_START_HOUR:02d}:00 - {cls.WORK_END_HOUR:02d}:00")
        print(f"Webhook 间隔: {cls.WEBHOOK_SEND_INTERVAL} 秒")
        print(f"日志级别: {cls.LOG_LEVEL}")
        print(f"日志文件: {cls.LOG_FILE}")
        print("=" * 60 + "\n")
