"""
Telegram 私密群组消息转发器 - 服务器长连接版
基于 Telethon (MTProto) 实现的消息监控与转发系统

功能特性：
1. 使用 StringSession 进行认证（无需本地 .session 文件）
2. 长连接实时监听，消息即时转发
3. 支持历史消息补发
4. 自动保存最后处理的消息 ID
5. 转发至钉钉/飞书/企业微信 Webhook（自动识别）
6. 完善的日志系统和异常处理
7. 支持工作时段配置
"""

import asyncio
import signal
import sys
from datetime import datetime
from typing import Optional

import aiohttp
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import Message

from config import Config
from logger import logger


# ==================== 全局变量 ====================
client: Optional[TelegramClient] = None
running = True


# ==================== 工具函数 ====================
def check_work_hours() -> bool:
    """
    检查当前是否在工作时段
    
    Returns:
        bool: 在工作时段返回 True，否则返回 False
    """
    now = datetime.now(Config.TIMEZONE)
    current_hour = now.hour
    
    if Config.WORK_START_HOUR <= current_hour < Config.WORK_END_HOUR:
        return True
    return False


def read_last_message_id() -> int:
    """
    从文件读取最后处理的消息 ID
    
    Returns:
        int: 最后处理的消息 ID，如果文件不存在则返回 0
    """
    if Config.LAST_ID_FILE.exists():
        try:
            last_id = int(Config.LAST_ID_FILE.read_text().strip())
            logger.info(f"读取到上次处理的消息 ID: {last_id}")
            return last_id
        except (ValueError, IOError) as e:
            logger.warning(f"读取 last_id.txt 失败: {e}，将从头开始")
            return 0
    else:
        logger.info("last_id.txt 不存在，将从头开始")
        return 0


def save_last_message_id(message_id: int) -> None:
    """
    保存最后处理的消息 ID 到文件
    
    Args:
        message_id: 要保存的消息 ID
    """
    try:
        Config.LAST_ID_FILE.write_text(str(message_id))
        logger.debug(f"已保存消息 ID: {message_id}")
    except IOError as e:
        logger.error(f"保存 last_id.txt 失败: {e}")


# ==================== Webhook 转发 ====================
def detect_webhook_type(url: str) -> str:
    """
    根据 Webhook URL 自动检测平台类型
    
    Args:
        url: Webhook URL
        
    Returns:
        str: 'dingtalk', 'feishu', 'wecom' 之一
    """
    url_lower = url.lower()
    if 'dingtalk.com' in url_lower or 'oapi.dingtalk.com' in url_lower:
        return 'dingtalk'
    elif 'feishu.cn' in url_lower or 'open.feishu.cn' in url_lower:
        return 'feishu'
    elif 'qyapi.weixin.qq.com' in url_lower or 'weixin.qq.com' in url_lower:
        return 'wecom'
    else:
        return 'dingtalk'


async def send_to_webhook(sender_name: str, send_time: str, message_text: str, message_id: int) -> bool:
    """
    将消息转发至钉钉/飞书/企业微信 Webhook（异步版本）
    自动根据 URL 识别平台类型
    
    Args:
        sender_name: 发送者名称
        send_time: 发送时间
        message_text: 消息正文
        message_id: 消息 ID
        
    Returns:
        bool: 发送成功返回 True，否则返回 False
    """
    # 检测 Webhook 类型
    webhook_type = detect_webhook_type(Config.WEBHOOK_URL)
    
    # 根据不同平台构建消息格式
    if webhook_type == 'dingtalk':
        # 钉钉机器人 - Markdown 格式
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": "🔔 舒芙蕾Push",
                "text": f"### 🔔 舒芙蕾Push\n\n"
                        f"**发送者：** {sender_name}\n\n"
                        f"**时间：** {send_time}\n\n"
                        f"**消息ID：** {message_id}\n\n"
                        f"**内容：**\n\n{message_text}"
            }
        }
        
    elif webhook_type == 'feishu':
        # 飞书机器人 - Post 格式
        payload = {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_CN": {
                        "title": "🔔 舒芙蕾Push",
                        "content": [
                            [{"tag": "text", "text": f"【发送者】{sender_name}\n"}],
                            [{"tag": "text", "text": f"【时间】{send_time}\n"}],
                            [{"tag": "text", "text": f"【消息ID】{message_id}\n"}],
                            [{"tag": "text", "text": f"【内容】\n{message_text}"}]
                        ]
                    }
                }
            }
        }
        
    else:  # wecom
        # 企业微信机器人 - Markdown 格式
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": f"### 🔔 舒芙蕾Push\n"
                          f"**发送者：** {sender_name}\n"
                          f"**时间：** {send_time}\n"
                          f"**消息ID：** {message_id}\n"
                          f"**内容：**\n{message_text}"
            }
        }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                Config.WEBHOOK_URL,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    logger.info(f"消息 {message_id} 已转发至 {webhook_type.upper()} Webhook")
                    return True
                else:
                    logger.warning(f"Webhook 返回错误状态码: {response.status}, 响应: {response_text}")
                    return False
            
    except Exception as e:
        logger.error(f"发送至 Webhook 失败: {e}")
        return False


# ==================== 消息处理 ====================
async def process_message(message: Message) -> None:
    """
    处理单条消息并转发
    
    Args:
        message: Telegram 消息对象
    """
    try:
        # 检查工作时段
        if not check_work_hours():
            logger.debug(f"消息 {message.id} 不在工作时段，跳过")
            return
        
        # 获取发送者信息
        sender = await message.get_sender()
        sender_name = "未知用户"
        
        if sender:
            if hasattr(sender, 'first_name') and sender.first_name:
                sender_name = sender.first_name
                if hasattr(sender, 'last_name') and sender.last_name:
                    sender_name += f" {sender.last_name}"
            elif hasattr(sender, 'title') and sender.title:
                sender_name = sender.title
        
        # 获取消息时间（转换为北京时间）
        send_time = message.date.astimezone(Config.TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')
        
        # 获取消息文本
        message_text = message.text or "[非文本消息]"
        
        # 打印消息信息
        logger.info(f"新消息 ID: {message.id}, 发送者: {sender_name}, 时间: {send_time}")
        logger.debug(f"消息内容: {message_text[:100]}{'...' if len(message_text) > 100 else ''}")
        
        # 转发至 Webhook
        await send_to_webhook(sender_name, send_time, message_text, message.id)
        
        # 保存消息 ID
        save_last_message_id(message.id)
        
        # 频率限制
        await asyncio.sleep(Config.WEBHOOK_SEND_INTERVAL)
        
    except Exception as e:
        logger.error(f"处理消息 {message.id} 时发生错误: {e}", exc_info=True)


async def fetch_history_messages(client: TelegramClient, last_id: int) -> int:
    """
    获取并处理历史消息（从上次记录到现在）
    
    Args:
        client: Telegram 客户端实例
        last_id: 上次处理的消息 ID
        
    Returns:
        int: 最新处理的消息 ID
    """
    logger.info(f"开始获取历史消息（从 ID {last_id} 之后）...")
    
    try:
        all_messages = []
        offset_id = 0
        batch_size = 100
        
        # 分页获取所有历史消息
        while True:
            messages = await client.get_messages(
                Config.TG_CHAT_ID,
                min_id=last_id,
                limit=batch_size,
                offset_id=offset_id
            )
            
            if not messages:
                break
            
            all_messages.extend(messages)
            
            oldest_msg_id = min(msg.id for msg in messages)
            if oldest_msg_id <= last_id:
                break
            
            offset_id = oldest_msg_id
            
            if len(messages) < batch_size:
                break
            
            await asyncio.sleep(0.5)
        
        # 过滤掉 ID <= last_id 的消息
        new_messages = [msg for msg in all_messages if msg.id > last_id]
        
        if not new_messages:
            logger.info("没有新的历史消息")
            return last_id
        
        # 按时间顺序处理（从旧到新）
        new_messages.sort(key=lambda m: m.id)
        
        logger.info(f"共获取到 {len(new_messages)} 条新消息，开始处理...")
        
        latest_id = last_id
        for i, msg in enumerate(new_messages, 1):
            logger.info(f"[{i}/{len(new_messages)}] 处理历史消息 ID: {msg.id}")
            await process_message(msg)
            latest_id = msg.id
        
        logger.info(f"历史消息处理完成，最新 ID: {latest_id}")
        return latest_id
        
    except Exception as e:
        logger.error(f"获取历史消息失败: {e}", exc_info=True)
        return last_id


# ==================== 信号处理 ====================
def signal_handler(signum, frame):
    """处理退出信号"""
    global running
    logger.info(f"收到信号 {signum}，准备退出...")
    running = False


# ==================== 主程序 ====================
async def main():
    """主程序入口"""
    global client, running
    
    # 显示配置
    Config.display()
    
    # 验证配置
    is_valid, error_msg = Config.validate()
    if not is_valid:
        logger.error(f"配置验证失败: {error_msg}")
        sys.exit(1)
    
    # 读取上次处理的消息 ID
    last_message_id = read_last_message_id()
    
    # 创建 Telegram 客户端
    logger.info("正在连接 Telegram...")
    client = TelegramClient(
        StringSession(Config.STRING_SESSION),
        Config.API_ID,
        Config.API_HASH
    )
    
    try:
        # 启动客户端
        await client.start()
        logger.info("Telegram 连接成功")
        
        # 获取当前用户信息
        me = await client.get_me()
        logger.info(f"当前登录用户 ID: {me.id}")
        
        # 获取历史消息
        logger.info(f"开始检查群组 ID: {Config.TG_CHAT_ID}")
        last_message_id = await fetch_history_messages(client, last_message_id)
        
        # 注册新消息处理器
        @client.on(events.NewMessage(chats=Config.TG_CHAT_ID))
        async def handler(event):
            """实时消息处理器"""
            await process_message(event.message)
        
        logger.info("开始实时监听新消息...")
        logger.info("按 Ctrl+C 退出")
        
        # 保持运行
        while running:
            await asyncio.sleep(1)
        
        logger.info("程序正常退出")
        
    except KeyboardInterrupt:
        logger.info("收到键盘中断，退出程序")
    except Exception as e:
        logger.error(f"运行过程中发生错误: {e}", exc_info=True)
        sys.exit(1)
    finally:
        if client:
            await client.disconnect()
            logger.info("已断开 Telegram 连接")


if __name__ == '__main__':
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("=" * 60)
    logger.info("  Telegram 私密群组消息转发器 - 服务器长连接版")
    logger.info("  运行模式：实时监听，消息即时转发")
    logger.info("=" * 60)
    
    # 运行异步主程序
    asyncio.run(main())
