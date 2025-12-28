# 图书馆管理系统

一个基于 Flask + Vue 3 的轻量级图书馆管理系统，支持图书入库、借阅、归还、查询以及用户管理、借阅统计等功能。

## 技术栈

### 后端
- Python 3.11+
- Flask 3.0
- SQLAlchemy 2.0
- MySQL 8.0
- JWT 认证

### 前端
- Vue 3
- Element Plus
- Vue Router
- Pinia
- Axios

### 部署
- Docker & Docker Compose
- Nginx

## 项目结构

```
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── models/         # 数据模型
│   │   ├── routes/         # API 路由
│   │   └── services/       # 业务逻辑
│   ├── tests/              # 测试文件
│   ├── scripts/            # 数据库脚本
│   ├── config.py           # 配置文件
│   ├── requirements.txt    # Python 依赖
│   ├── Dockerfile          # 后端容器配置
│   └── run.py              # 启动入口
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── api/           # API 接口
│   │   ├── views/         # 页面组件
│   │   ├── stores/        # 状态管理
│   │   └── router/        # 路由配置
│   ├── package.json       # Node 依赖
│   ├── Dockerfile         # 前端容器配置
│   └── vite.config.js     # Vite 配置
├── docker-compose.yml      # Docker 编排配置
├── .env.docker             # 环境变量模板
└── README.md
```

## 快速开始

### 方式一：Docker 部署（推荐）

1. 确保已安装 [Docker](https://docs.docker.com/get-docker/) 和 Docker Compose

2. 配置环境变量
```bash
cp .env.docker .env
```

编辑 `.env` 文件，设置数据库密码：
```bash
MYSQL_ROOT_PASSWORD=your_secure_root_password
MYSQL_PASSWORD=your_secure_db_password
SECRET_KEY=your_random_secret_key
JWT_SECRET_KEY=your_random_jwt_secret
```

3. 启动服务
```bash
docker-compose up -d
```

4. 访问应用
   - 前端：http://localhost
   - 后端 API：http://localhost:5000

5. 默认管理员账户
   - 用户名：`admin`
   - 密码：`admin123`

### 方式二：本地开发

#### 环境要求
- Python 3.11+
- Node.js 18+
- MySQL 8.0+

#### 后端安装

```bash
cd backend

# 创建虚拟环境
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库连接

# 初始化数据库
python scripts/init_db.py all

# 启动服务
python run.py
```

后端服务：http://localhost:5000

#### 前端安装

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务：http://localhost:5173

## Docker 命令参考

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
docker-compose logs -f backend  # 仅后端日志

# 重新构建并启动
docker-compose up -d --build

# 停止服务
docker-compose down

# 停止并删除数据卷（清空数据库）
docker-compose down -v
```

## API 接口

### 认证模块
| 方法 | 路径 | 功能 |
|------|------|------|
| POST | /api/auth/register | 用户注册 |
| POST | /api/auth/login | 用户登录 |
| POST | /api/auth/logout | 用户登出 |

### 图书模块
| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/books | 查询图书列表 |
| POST | /api/books | 添加图书（管理员）|
| GET | /api/books/{id} | 获取图书详情 |
| PUT | /api/books/{id} | 更新图书（管理员）|
| DELETE | /api/books/{id} | 删除图书（管理员）|

### 借阅模块
| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/borrows | 查询借阅记录 |
| POST | /api/borrows | 借书 |
| PUT | /api/borrows/{id}/return | 还书 |

### 统计模块
| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/statistics/borrows | 借阅统计（管理员）|
| GET | /api/statistics/users | 用户统计（管理员）|
| GET | /api/statistics/export/borrows | 导出借阅数据 |
| GET | /api/statistics/export/users | 导出用户数据 |

### 用户管理
| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/users | 获取用户列表（管理员）|
| PUT | /api/users/{id} | 更新用户状态（管理员）|

## 测试

```bash
cd backend

# 运行所有测试
python -m pytest tests/ -v

# 运行属性测试
python -m pytest tests/test_*_properties.py -v

# 生成覆盖率报告
python -m pytest tests/ --cov=app --cov-report=html
```

## 功能特性

- ✅ 用户注册与登录
- ✅ 角色权限管理（管理员/读者）
- ✅ 图书入库与管理
- ✅ 图书搜索（支持书名、作者、ISBN）
- ✅ 借阅与归还
- ✅ 逾期检测与提醒
- ✅ 借阅统计报表
- ✅ 数据导出（CSV）
- ✅ Docker 一键部署

## 环境变量说明

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| MYSQL_ROOT_PASSWORD | MySQL root 密码 | - |
| MYSQL_DATABASE | 数据库名 | library_db |
| MYSQL_USER | 数据库用户 | library |
| MYSQL_PASSWORD | 数据库密码 | - |
| SECRET_KEY | Flask 密钥 | - |
| JWT_SECRET_KEY | JWT 密钥 | - |

## 许可证

MIT License
