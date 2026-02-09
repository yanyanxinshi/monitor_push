"""
日志管理模块
提供统一的日志记录功能
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from config import Config


def setup_logger(name: str = 'telegram_monitor') -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        配置好的日志记录器
    """
    # 创建日志目录
    log_file = Path(Config.LOG_FILE)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO))
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器（按日期轮转）
    file_handler = logging.FileHandler(
        log_file,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


# 创建全局日志记录器
logger = setup_logger()
