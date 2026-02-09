# 项目结构说明

```
telegram_monitor/
├── .env.example              # 环境变量配置模板
├── .env                      # 环境变量配置文件（需自己创建，不提交到 Git）
├── .gitignore               # Git 忽略文件配置
├── requirements.txt         # Python 依赖列表
├── last_id.txt             # 最后处理的消息 ID（自动生成）
│
├── config.py               # 配置管理模块
├── logger.py               # 日志管理模块
├── gen_session.py          # StringSession 生成工具
├── main.py                 # 主程序（长连接实时监听）
│
├── start.sh                # 启动脚本
├── telegram-monitor.service # systemd 服务配置
│
├── README.md               # 完整部署文档
├── DEPLOY.md              # 快速部署指南
├── PROJECT_STRUCTURE.md   # 本文档
├── REFACTOR_SUMMARY.md    # 重构总结
│
└── logs/                   # 日志目录（自动创建）
    └── telegram_monitor.log
```

## 📁 文件说明

### 核心文件

| 文件 | 用途 |
|------|------|
| `main.py` | 主程序 - 长连接实时监听 |
| `config.py` | 配置管理 - 从 .env 读取配置 |
| `logger.py` | 日志管理 - 统一日志输出 |
| `gen_session.py` | Session 生成工具 - 首次配置时使用 |

### 配置文件

| 文件 | 说明 | 是否提交 Git |
|------|------|-------------|
| `.env.example` | 配置模板 | ✅ 提交 |
| `.env` | 实际配置（包含敏感信息） | ❌ 不提交 |
| `last_id.txt` | 消息 ID 状态 | ⚠️ 可选 |

### 部署文件

| 文件 | 用途 | 适用系统 |
|------|------|---------|
| `start.sh` | 启动脚本 | Linux/macOS |
| `telegram-monitor.service` | systemd 服务配置 | Linux |

### 文档文件

| 文件 | 说明 |
|------|------|
| `README.md` | 完整部署文档 |
| `DEPLOY.md` | 快速部署指南 |
| `PROJECT_STRUCTURE.md` | 本文档 |
| `REFACTOR_SUMMARY.md` | 重构总结 |

## 🚀 快速开始

### 1. 配置环境变量

```bash
cp .env.example .env
nano .env
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行程序

```bash
# 前台运行
python main.py

# 或使用启动脚本
./start.sh

# 或后台运行
nohup python main.py > logs/output.log 2>&1 &
```

## 📚 相关文档

- **快速部署**：`DEPLOY.md`
- **完整文档**：`README.md`
- **重构说明**：`REFACTOR_SUMMARY.md`
