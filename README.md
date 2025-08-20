# 用户登陆登出系统（后端重构版，分支 `1`）

本分支只重构**后端结构**，功能保持不变（注册 / 登录 / 登出 / 控制台）。从单文件改为标准的 **Flask 应用工厂 + Blueprints + 迁移体系**，并补充环境配置与运行说明。

## 技术栈
Flask · Flask-SQLAlchemy · Flask-Login · Flask-Migrate · SQLite

## 快速开始
```bash
# 1) 创建虚拟环境
python -m venv .venv
source .venv/bin/activate         # Windows: .\.venv\Scripts\Activate.ps1

# 2) 安装依赖
pip install -U pip
pip install -r requirements.txt

# 3) 配置环境变量
cp .env.example .env              # 修改 SECRET_KEY / DATABASE_URL 如需自定义

# 4) 初始化数据库（首次）
export FLASK_APP=wsgi.py          # Windows: set / $env:
python -m flask db upgrade

# 5) 启动服务
python -m flask --app wsgi.py run -p 5001 --debug
