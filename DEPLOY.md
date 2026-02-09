# 服务器部署快速指南

## 🚀 5 分钟快速部署

### 1. 准备工作

```bash
# 克隆或上传项目到服务器
cd /path/to/your/directory
git clone <your-repo-url> telegram_monitor
cd telegram_monitor

# 或者直接上传文件
scp -r telegram_monitor user@server:/path/to/directory/
```

### 2. 安装依赖

```bash
# 安装 Python 3.8+（如果还没有）
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置
nano .env
```

**必需填写的配置**：
```env
API_ID=你的API_ID
API_HASH=你的API_HASH
STRING_SESSION=你的STRING_SESSION
TG_CHAT_ID=-1001234567890
WEBHOOK_URL=你的Webhook地址
```

### 4. 生成 StringSession（如果还没有）

```bash
python gen_session.py
```

### 5. 测试运行

```bash
# 前台运行测试
python server_main.py

# 看到 "开始实时监听新消息..." 表示成功
# 按 Ctrl+C 停止
```

### 6. 后台运行

#### 方式 A：使用 nohup（最简单）

```bash
nohup python server_main.py > logs/output.log 2>&1 &

# 查看日志
tail -f logs/output.log

# 停止程序
ps aux | grep server_main.py
kill <PID>
```

#### 方式 B：使用 systemd（推荐）

```bash
# 1. 编辑服务文件
nano telegram-monitor.service

# 修改以下内容：
# User=你的用户名
# WorkingDirectory=/完整/路径/到/telegram_monitor
# Environment="PATH=/完整/路径/到/venv/bin"
# ExecStart=/完整/路径/到/venv/bin/python server_main.py

# 2. 安装服务
sudo cp telegram-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable telegram-monitor
sudo systemctl start telegram-monitor

# 3. 查看状态
sudo systemctl status telegram-monitor

# 4. 查看日志
sudo journalctl -u telegram-monitor -f
```

## ✅ 验证部署

### 检查清单

- [ ] 程序正常启动，无错误日志
- [ ] 日志显示"Telegram 连接成功"
- [ ] 日志显示"开始实时监听新消息"
- [ ] 在 TG 群组发送测试消息
- [ ] 钉钉/飞书/企微收到转发消息
- [ ] `last_id.txt` 文件正常更新

### 常用命令

```bash
# 查看进程
ps aux | grep server_main

# 查看日志
tail -f logs/telegram_monitor.log

# 重启服务（systemd）
sudo systemctl restart telegram-monitor

# 停止服务（systemd）
sudo systemctl stop telegram-monitor

# 查看服务状态（systemd）
sudo systemctl status telegram-monitor
```

## 🔧 故障排查

### 问题 1：连接失败

```bash
# 检查网络
ping telegram.org

# 检查配置
cat .env | grep -v "^#"

# 查看详细日志
tail -n 100 logs/telegram_monitor.log
```

### 问题 2：钉钉未收到消息

```bash
# 测试 Webhook
curl -X POST "你的WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "msgtype": "markdown",
    "markdown": {
      "title": "测试",
      "text": "### 舒芙蕾Push\n\n测试消息"
    }
  }'

# 检查钉钉机器人关键词设置
# 确保包含"舒芙蕾"或"Push"
```

### 问题 3：进程意外退出

```bash
# 查看系统日志
sudo journalctl -u telegram-monitor -n 100

# 查看应用日志
tail -n 100 logs/telegram_monitor.log

# 检查系统资源
free -h
df -h
```

## 📊 性能监控

### 查看资源占用

```bash
# CPU 和内存
top -p $(pgrep -f server_main.py)

# 详细信息
ps aux | grep server_main.py
```

### 日志大小管理

```bash
# 查看日志大小
du -sh logs/

# 清理旧日志（保留最近 7 天）
find logs/ -name "*.log" -mtime +7 -delete

# 或使用 logrotate（推荐）
sudo nano /etc/logrotate.d/telegram-monitor
```

logrotate 配置示例：
```
/path/to/telegram_monitor/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

## 🔐 安全建议

1. **文件权限**
```bash
chmod 600 .env
chmod 700 logs/
```

2. **防火墙**
```bash
# 只允许必要的出站连接
sudo ufw allow out 443/tcp
sudo ufw allow out 80/tcp
```

3. **定期更新**
```bash
# 更新系统
sudo apt-get update && sudo apt-get upgrade

# 更新 Python 依赖
pip install --upgrade -r requirements.txt
```

## 📞 获取帮助

- 查看完整文档：`README_SERVER.md`
- 查看日志：`logs/telegram_monitor.log`
- GitHub Issues：提交问题和建议

---

**部署完成！** 🎉

现在您的 Telegram 监控服务应该已经在服务器上稳定运行了。
