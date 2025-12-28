"""
应用入口文件
"""
import os

# 加载 .env 文件
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from app import create_app, db
from config import config

# 获取配置环境
config_name = os.environ.get('FLASK_ENV') or 'development'
app = create_app(config[config_name])


@app.cli.command('init-db')
def init_db():
    """初始化数据库"""
    db.create_all()
    print('数据库初始化完成！')


@app.cli.command('drop-db')
def drop_db():
    """删除所有表"""
    db.drop_all()
    print('数据库表已删除！')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
