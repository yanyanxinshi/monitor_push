# Telegram Monitor - 服务器部署版

基于 MTProto 协议的 Telegram 消息监控系统，支持服务器长连接部署，可将私密群组消息实时转发至钉钉/飞书/企业微信。

## ✨ 核心特性

- 🔐 **StringSession 认证**：无需本地 `.session` 文件
- ⚡ **实时监听**：长连接模式，消息即时转发
- 📨 **历史补发**：启动时自动补发未处理的消息
- 💾 **状态持久化**：自动保存最后处理的消息 ID
- 🔄 **自动重连**：网络断开自动重连
- 📊 **完善日志**：支持控制台和文件双输出
- 🌐 **多平台支持**：自动识别钉钉/飞书/企微 Webhook
- ⚙️ **灵活配置**：通过 `.env` 文件管理所有配置
- 🛡️ **进程守护**：支持 systemd 服务管理

## 📋 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制配置文件模板
cp .env.example .env

# 编辑配置文件
nano .env  # 或使用其他编辑器
```

填写以下必需配置：

```env
# Telegram API 配置（从 https://my.telegram.org/apps 获取）
API_ID=12345678
API_HASH=your_api_hash_here

# StringSession（使用 gen_session.py 生成）
STRING_SESSION=your_string_session_here

# 监控的群组 ID（负数，如 -1001234567890）
TG_CHAT_ID=-1001234567890

# Webhook URL
WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=xxx
```

### 3. 生成 StringSession

```bash
python gen_session.py
```

按提示输入：
- API_ID 和 API_HASH
- 手机号（国际格式，如 +8613800138000）
- 验证码
- 两步验证密码（如果启用了）

将生成的 StringSession 填入 `.env` 文件。

### 4. 运行程序

#### 方式 1：直接运行

```bash
python server_main.py
```

#### 方式 2：使用启动脚本

```bash
chmod +x start.sh
./start.sh
```

#### 方式 3：后台运行（nohup）

```bash
nohup python server_main.py > logs/output.log 2>&1 &
```

#### 方式 4：使用 screen/tmux

```bash
# 使用 screen
screen -S telegram-monitor
python server_main.py
# 按 Ctrl+A+D 退出 screen

# 恢复 screen
screen -r telegram-monitor

# 使用 tmux
tmux new -s telegram-monitor
python server_main.py
# 按 Ctrl+B+D 退出 tmux

# 恢复 tmux
tmux attach -t telegram-monitor
```

## 🚀 生产环境部署

### 使用 systemd（推荐）

1. **编辑服务配置文件**

```bash
sudo nano telegram-monitor.service
```

修改以下内容：
- `User=your_username` → 你的用户名
- `WorkingDirectory=/path/to/telegram_monitor` → 项目路径
- `Environment="PATH=/path/to/venv/bin"` → 虚拟环境路径
- `ExecStart=/path/to/venv/bin/python server_main.py` → 完整路径

2. **安装服务**

```bash
# 复制服务文件
sudo cp telegram-monitor.service /etc/systemd/system/

# 重新加载 systemd
sudo systemctl daemon-reload

# 启用服务（开机自启）
sudo systemctl enable telegram-monitor

# 启动服务
sudo systemctl start telegram-monitor
```

3. **管理服务**

```bash
# 查看状态
sudo systemctl status telegram-monitor

# 查看日志
sudo journalctl -u telegram-monitor -f

# 重启服务
sudo systemctl restart telegram-monitor

# 停止服务
sudo systemctl stop telegram-monitor
```

### 使用 Supervisor

1. **安装 Supervisor**

```bash
sudo apt-get install supervisor  # Debian/Ubuntu
sudo yum install supervisor      # CentOS/RHEL
```

2. **创建配置文件**

```bash
sudo nano /etc/supervisor/conf.d/telegram-monitor.conf
```

内容：

```ini
[program:telegram-monitor]
command=/path/to/venv/bin/python /path/to/telegram_monitor/server_main.py
directory=/path/to/telegram_monitor
user=your_username
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/path/to/telegram_monitor/logs/supervisor.log
```

3. **启动服务**

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start telegram-monitor
```

## 📊 配置说明

### 必需配置

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `API_ID` | Telegram API ID | `12345678` |
| `API_HASH` | Telegram API Hash | `abcdef1234567890` |
| `STRING_SESSION` | 认证会话字符串 | `1AQAOMTQ5LjE1NC4x...` |
| `TG_CHAT_ID` | 目标群组 ID | `-1001234567890` |
| `WEBHOOK_URL` | Webhook 地址 | `https://oapi.dingtalk.com/...` |

### 可选配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `WORK_START_HOUR` | 工作时段开始（24小时制） | `0` |
| `WORK_END_HOUR` | 工作时段结束（24小时制） | `24` |
| `WEBHOOK_SEND_INTERVAL` | 发送间隔（秒） | `3.0` |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `LOG_FILE` | 日志文件路径 | `logs/telegram_monitor.log` |

## 📝 日志管理

### 日志位置

- **控制台输出**：实时显示 INFO 级别日志
- **文件输出**：`logs/telegram_monitor.log`（包含 DEBUG 级别）

### 日志级别

- `DEBUG`：详细调试信息
- `INFO`：一般信息（默认）
- `WARNING`：警告信息
- `ERROR`：错误信息

### 查看日志

```bash
# 实时查看日志
tail -f logs/telegram_monitor.log

# 查看最近 100 行
tail -n 100 logs/telegram_monitor.log

# 搜索错误
grep ERROR logs/telegram_monitor.log
```

## 🔧 故障排查

### 1. 连接失败

**症状**：无法连接到 Telegram

**解决方案**：
- 检查网络连接
- 确认 `STRING_SESSION` 未过期
- 尝试重新生成 StringSession
- 检查防火墙设置

### 2. 消息未转发

**症状**：程序运行正常，但钉钉未收到消息

**解决方案**：
- 检查 `WEBHOOK_URL` 是否正确
- 确认钉钉机器人关键词包含"舒芙蕾"或"Push"
- 查看日志中的 Webhook 响应
- 手动测试 Webhook URL

### 3. 进程意外退出

**症状**：程序运行一段时间后自动退出

**解决方案**：
- 查看日志文件中的错误信息
- 使用 systemd 或 supervisor 自动重启
- 检查系统资源（内存、CPU）
- 确认 `STRING_SESSION` 有效

### 4. 重复消息

**症状**：同一条消息被转发多次

**解决方案**：
- 确认只有一个进程在运行
- 检查 `last_id.txt` 是否正常更新
- 停止所有进程后重新启动

## ⚠️ 注意事项

### 安全性

1. **保护 .env 文件**
   - 不要提交到 Git 仓库
   - 设置适当的文件权限：`chmod 600 .env`
   - 定期更换敏感凭据

2. **STRING_SESSION 安全**
   - 如果泄露，立即在 Telegram 中登出所有会话
   - 重新生成新的 StringSession

3. **服务器安全**
   - 使用防火墙限制访问
   - 定期更新系统和依赖
   - 使用非 root 用户运行

### 性能优化

1. **Webhook 频率限制**
   - 钉钉：20条/分钟
   - 飞书：20条/分钟
   - 企微：20条/分钟
   - 已内置 3 秒/条的保护机制

2. **资源占用**
   - 内存：约 50-100MB
   - CPU：空闲时 <1%
   - 网络：取决于消息频率

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题，请在 GitHub Issues 中提出。
