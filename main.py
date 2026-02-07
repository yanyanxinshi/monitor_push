"""
Telegram 私密群组消息转发器 - GitHub Actions 优化版
基于 Telethon (MTProto) 实现的消息监控与转发系统

功能特性：
1. 使用 StringSession 进行认证（无需本地 .session 文件）
2. 仅在北京时间 09:00-24:00 运行
3. 支持历史消息补发和实时监听
4. 自动保存最后处理的消息 ID
5. 轻量级轮询模式，每 10 分钟执行一次
6. 转发至钉钉/飞书/企业微信 Webhook（自动识别）
"""

import os
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pytz
import aiohttp
from telethon import TelegramClient, events
from telethon.tl.types import Message


# ==================== 配置读取 ====================
class Config:
    """从环境变量读取配置"""
    
    # Telegram 配置
    API_ID = int(os.getenv('API_ID', '0'))
    API_HASH = os.getenv('API_HASH', '')
    STRING_SESSION = os.getenv('STRING_SESSION', '')
    TG_CHAT_ID = int(os.getenv('TG_CHAT_ID', '0'))
    
    # Webhook 配置
    WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
    
    # 运行时配置
    TIMEZONE = pytz.timezone('Asia/Shanghai')
    WORK_START_HOUR = 9  # 工作时段开始（北京时间）
    WORK_END_HOUR = 24   # 工作时段结束（北京时间）
    
    # Webhook 频率限制（飞书/企微限制：20条/分钟）
    WEBHOOK_SEND_INTERVAL = 3.0  # 发送间隔（秒），3秒 = 20条/分钟
    
    # 文件路径
    LAST_ID_FILE = Path('last_id.txt')
    
    @classmethod
    def validate(cls) -> bool:
        """验证必需的配置是否存在"""
        if not cls.API_ID or cls.API_ID == 0:
            print("❌ 错误：未设置 API_ID 环境变量")
            return False
        if not cls.API_HASH:
            print("❌ 错误：未设置 API_HASH 环境变量")
            return False
        if not cls.STRING_SESSION:
            print("❌ 错误：未设置 STRING_SESSION 环境变量")
            return False
        if not cls.TG_CHAT_ID or cls.TG_CHAT_ID == 0:
            print("❌ 错误：未设置 TG_CHAT_ID 环境变量")
            return False
        if not cls.WEBHOOK_URL:
            print("❌ 错误：未设置 WEBHOOK_URL 环境变量")
            return False
        return True


# ==================== 时间检查 ====================
def check_work_hours() -> bool:
    """
    检查当前是否在工作时段（北京时间 09:00-24:00）
    
    Returns:
        bool: 在工作时段返回 True，否则返回 False
    """
    now = datetime.now(Config.TIMEZONE)
    current_hour = now.hour
    
    if Config.WORK_START_HOUR <= current_hour < Config.WORK_END_HOUR:
        print(f"✅ 当前时间：{now.strftime('%Y-%m-%d %H:%M:%S')} - 在工作时段内")
        return True
    else:
        print(f"⏰ 当前时间：{now.strftime('%Y-%m-%d %H:%M:%S')} - 不在工作时段（09:00-24:00），脚本退出")
        return False


# ==================== 消息 ID 管理 ====================
def read_last_message_id() -> int:
    """
    从文件读取最后处理的消息 ID
    
    Returns:
        int: 最后处理的消息 ID，如果文件不存在则返回 0
    """
    if Config.LAST_ID_FILE.exists():
        try:
            last_id = int(Config.LAST_ID_FILE.read_text().strip())
            print(f"📖 读取到上次处理的消息 ID: {last_id}")
            return last_id
        except (ValueError, IOError) as e:
            print(f"⚠️ 读取 last_id.txt 失败: {e}，将从头开始")
            return 0
    else:
        print("📝 last_id.txt 不存在，将从头开始")
        return 0


def save_last_message_id(message_id: int) -> None:
    """
    保存最后处理的消息 ID 到文件
    
    Args:
        message_id: 要保存的消息 ID
    """
    try:
        Config.LAST_ID_FILE.write_text(str(message_id))
        print(f"💾 已保存消息 ID: {message_id}")
    except IOError as e:
        print(f"⚠️ 保存 last_id.txt 失败: {e}")


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
        # 默认使用钉钉格式（最通用）
        return 'dingtalk'


async def send_to_webhook(sender_name: str, send_time: str, message_text: str) -> bool:
    """
    将消息转发至钉钉/飞书/企业微信 Webhook（异步版本）
    自动根据 URL 识别平台类型
    
    Args:
        sender_name: 发送者名称
        send_time: 发送时间
        message_text: 消息正文
        
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
                "title": "🔔 TG 群组监控告警",
                "text": f"### 🔔 TG 群组监控告警\n\n"
                        f"**发送者：** {sender_name}\n\n"
                        f"**时间：** {send_time}\n\n"
                        f"**内容：**\n\n{message_text}"
            }
        }
        print(f"📤 使用钉钉格式发送消息")
        
    elif webhook_type == 'feishu':
        # 飞书机器人 - Post 格式
        payload = {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_CN": {
                        "title": "🔔 TG 群组监控告警",
                        "content": [
                            [
                                {
                                    "tag": "text",
                                    "text": f"【发送者】{sender_name}\n"
                                }
                            ],
                            [
                                {
                                    "tag": "text",
                                    "text": f"【时间】{send_time}\n"
                                }
                            ],
                            [
                                {
                                    "tag": "text",
                                    "text": f"【内容】\n{message_text}"
                                }
                            ]
                        ]
                    }
                }
            }
        }
        print(f"📤 使用飞书格式发送消息")
        
    else:  # wecom
        # 企业微信机器人 - Markdown 格式
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": f"### 🔔 TG 群组监控告警\n"
                          f"**发送者：** {sender_name}\n"
                          f"**时间：** {send_time}\n"
                          f"**内容：**\n{message_text}"
            }
        }
        print(f"📤 使用企业微信格式发送消息")
    
    try:
        # 使用 aiohttp 进行异步 HTTP 请求，避免阻塞事件循环
        async with aiohttp.ClientSession() as session:
            async with session.post(
                Config.WEBHOOK_URL,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    print(f"✅ 消息已转发至 {webhook_type.upper()} Webhook")
                    return True
                else:
                    print(f"⚠️ Webhook 返回错误状态码: {response.status}")
                    print(f"   响应内容: {response_text}")
                    return False
            
    except aiohttp.ClientError as e:
        print(f"❌ 发送至 Webhook 失败（网络错误）: {e}")
        return False
    except asyncio.TimeoutError:
        print(f"❌ 发送至 Webhook 超时")
        return False
    except Exception as e:
        print(f"❌ 发送至 Webhook 失败（未知错误）: {e}")
        return False


# ==================== 消息处理 ====================
async def process_message(message: Message, client: TelegramClient) -> None:
    """
    处理单条消息并转发
    
    Args:
        message: Telegram 消息对象
        client: Telegram 客户端实例
    """
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
    print(f"\n{'='*60}")
    print(f"📨 新消息 ID: {message.id}")
    print(f"👤 发送者: {sender_name}")
    print(f"🕒 时间: {send_time}")
    print(f"📝 内容: {message_text[:100]}{'...' if len(message_text) > 100 else ''}")
    print(f"{'='*60}\n")
    
    # 转发至 Webhook（异步）
    await send_to_webhook(sender_name, send_time, message_text)
    
    # 保存消息 ID
    save_last_message_id(message.id)


async def fetch_history_messages(client: TelegramClient, last_id: int) -> int:
    """
    获取并处理历史消息（从上次记录到现在）- 支持分页获取
    
    Args:
        client: Telegram 客户端实例
        last_id: 上次处理的消息 ID
        
    Returns:
        int: 最新处理的消息 ID
    """
    print(f"\n🔍 开始获取历史消息（从 ID {last_id} 之后）...")
    
    try:
        all_messages = []
        offset_id = 0  # 用于分页
        batch_size = 100  # 每次获取 100 条
        
        # 分页获取所有历史消息
        while True:
            print(f"   正在获取第 {len(all_messages) // batch_size + 1} 批消息...")
            
            messages = await client.get_messages(
                Config.TG_CHAT_ID,
                min_id=last_id,
                limit=batch_size,
                offset_id=offset_id
            )
            
            if not messages:
                break  # 没有更多消息了
            
            all_messages.extend(messages)
            
            # 检查是否已经获取到最早的消息
            oldest_msg_id = min(msg.id for msg in messages)
            if oldest_msg_id <= last_id:
                break
            
            # 更新 offset_id 为当前批次最小的消息 ID
            offset_id = oldest_msg_id
            
            # 如果获取的消息数少于 batch_size，说明已经到底了
            if len(messages) < batch_size:
                break
            
            # 添加小延迟，避免触发 Telegram API 限流
            await asyncio.sleep(0.5)
        
        if not all_messages:
            print("✅ 没有新的历史消息")
            return last_id
        
        # 过滤掉 ID <= last_id 的消息
        new_messages = [msg for msg in all_messages if msg.id > last_id]
        
        if not new_messages:
            print("✅ 没有新的历史消息")
            return last_id
        
        # 按时间顺序处理（从旧到新）
        new_messages.sort(key=lambda m: m.id)
        
        print(f"📥 共获取到 {len(new_messages)} 条新消息，开始处理...")
        print(f"⚠️ 为避免 Webhook 限流（20条/分钟），将以 {Config.WEBHOOK_SEND_INTERVAL} 秒/条的速度发送")
        
        latest_id = last_id
        for i, msg in enumerate(new_messages, 1):
            print(f"\n[{i}/{len(new_messages)}] 处理消息 ID: {msg.id}")
            await process_message(msg, client)
            latest_id = msg.id
            
            # 严格控制发送频率：3 秒/条（符合 20条/分钟限制）
            if i < len(new_messages):  # 最后一条不需要等待
                print(f"   ⏳ 等待 {Config.WEBHOOK_SEND_INTERVAL} 秒（防止限流）...")
                await asyncio.sleep(Config.WEBHOOK_SEND_INTERVAL)
        
        print(f"\n✅ 历史消息处理完成，最新 ID: {latest_id}")
        print(f"   总耗时约: {len(new_messages) * Config.WEBHOOK_SEND_INTERVAL / 60:.1f} 分钟")
        return latest_id
        
    except Exception as e:
        print(f"❌ 获取历史消息失败: {e}")
        import traceback
        traceback.print_exc()
        return last_id


# ==================== 主程序 ====================
async def run_monitor():
    """
    主运行逻辑（轻量级轮询模式）
    
    执行流程：
    1. 验证配置
    2. 检查工作时段
    3. 连接 Telegram
    4. 抓取历史消息（自动对比 last_id）
    5. 断开连接并退出
    
    设计理念：
    - 每 10 分钟执行一次，单次运行 < 5 分钟
    - 不需要长连接监听，不需要信号处理
    - "抓完就走"，简洁高效
    """
    # 1. 验证配置
    if not Config.validate():
        sys.exit(1)
    
    # 2. 检查工作时段
    if not check_work_hours():
        sys.exit(0)
    
    # 3. 读取上次处理的消息 ID
    last_message_id = read_last_message_id()
    
    # 4. 创建 Telegram 客户端
    print("\n🚀 正在连接 Telegram...")
    client = TelegramClient(
        'monitor_session',
        Config.API_ID,
        Config.API_HASH
    )
    
    try:
        # 使用 StringSession 连接
        await client.start(string_session=Config.STRING_SESSION)
        print("✅ Telegram 连接成功")
        
        # 获取当前用户信息
        me = await client.get_me()
        print(f"👤 当前登录用户: {me.first_name} (@{me.username})")
        
        # 5. 抓取并处理历史消息（核心逻辑）
        print(f"\n� 开始检查群组 ID: {Config.TG_CHAT_ID}")
        last_message_id = await fetch_history_messages(
            client,
            last_message_id
        )
        
        print("\n✅ 本次轮询完成")
        
    except Exception as e:
        print(f"\n❌ 运行过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    finally:
        # 6. 断开连接
        if client:
            await client.disconnect()
            print("🔌 已断开 Telegram 连接")


# ==================== 入口点 ====================
async def main():
    """程序入口"""
    await run_monitor()


if __name__ == '__main__':
    print("=" * 60)
    print("  Telegram 私密群组消息转发器 - 轻量级轮询版")
    print("  运行模式：每 10 分钟执行一次，抓完即退出")
    print("=" * 60)
    
    # 运行异步主程序
    asyncio.run(main())
