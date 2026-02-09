#!/bin/bash
# Telegram Monitor 启动脚本

# 进入项目目录
cd "$(dirname "$0")"

# 激活虚拟环境（如果使用）
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "错误：未找到 .env 文件"
    echo "请复制 .env.example 为 .env 并填写配置"
    exit 1
fi

# 创建日志目录
mkdir -p logs

# 启动程序
echo "启动 Telegram Monitor..."
python main.py
