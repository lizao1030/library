#!/bin/bash
set -e

echo "等待数据库就绪..."

# 从环境变量获取数据库配置
DB_USER=${DB_USER:-library}
DB_PASSWORD=${DB_PASSWORD:-library123}
DB_NAME=${DB_NAME:-library_db}

# 等待 MySQL 可用
until python -c "
import os
import pymysql
conn = pymysql.connect(
    host='db',
    user=os.environ.get('DB_USER', 'library'),
    password=os.environ.get('DB_PASSWORD', 'library123'),
    database=os.environ.get('DB_NAME', 'library_db')
)
conn.close()
print('连接成功')
" 2>&1; do
    echo "数据库未就绪，等待中..."
    sleep 2
done

echo "数据库已就绪！"

# 初始化数据库表和管理员账户
echo "初始化数据库..."
python scripts/init_db.py all || echo "数据库已初始化"

echo "启动应用..."
exec python run.py
