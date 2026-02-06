"""
Telegram StringSession 生成工具

用途：在本地生成 StringSession 字符串，用于 GitHub Actions 部署

使用步骤：
1. 确保已安装 telethon: pip install telethon
2. 准备好你的 API_ID 和 API_HASH（从 https://my.telegram.org 获取）
3. 运行此脚本: python gen_session.py
4. 按提示输入手机号、验证码等信息
5. 复制生成的 StringSession 字符串到 GitHub Secrets
"""

import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession


async def generate_session():
    """生成 StringSession 的交互式流程"""
    
    print("=" * 60)
    print("  Telegram StringSession 生成工具")
    print("=" * 60)
    print()
    
    # 获取 API 凭据
    print("📝 请输入你的 Telegram API 凭据")
    print("   （从 https://my.telegram.org/apps 获取）")
    print()
    
    api_id = input("请输入 API_ID: ").strip()
    api_hash = input("请输入 API_HASH: ").strip()
    
    if not api_id or not api_hash:
        print("\n❌ API_ID 和 API_HASH 不能为空！")
        return
    
    try:
        api_id = int(api_id)
    except ValueError:
        print("\n❌ API_ID 必须是数字！")
        return
    
    print("\n🔐 开始生成 StringSession...")
    print("   接下来需要登录你的 Telegram 账号")
    print()
    
    # 创建客户端（使用 StringSession）
    async with TelegramClient(StringSession(), api_id, api_hash) as client:
        # 登录流程（会自动提示输入手机号、验证码等）
        await client.start()
        
        # 获取 StringSession
        session_string = client.session.save()
        
        # 获取当前用户信息
        me = await client.get_me()
        
        print("\n" + "=" * 60)
        print("✅ StringSession 生成成功！")
        print("=" * 60)
        print()
        print(f"👤 登录账号: {me.first_name} (@{me.username})")
        print(f"📱 手机号: {me.phone}")
        print()
        print("🔑 你的 StringSession（请妥善保管）:")
        print("-" * 60)
        print(session_string)
        print("-" * 60)
        print()
        print("📋 后续步骤:")
        print("   1. 复制上面的 StringSession 字符串")
        print("   2. 在 GitHub 仓库中进入 Settings > Secrets and variables > Actions")
        print("   3. 点击 'New repository secret'")
        print("   4. Name 填写: STRING_SESSION")
        print("   5. Secret 粘贴上面的字符串")
        print("   6. 点击 'Add secret' 保存")
        print()
        print("⚠️ 安全提示:")
        print("   - StringSession 等同于你的账号密码，请勿泄露！")
        print("   - 不要将其提交到 Git 仓库或公开分享")
        print("   - 如果泄露，请立即在 Telegram 中登出所有会话")
        print()


def main():
    """主函数"""
    try:
        asyncio.run(generate_session())
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户取消操作")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
