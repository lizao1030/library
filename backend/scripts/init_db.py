"""
数据库初始化脚本
"""
import sys
import os

# 添加项目根目录到路径
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

# 加载 .env 文件
from dotenv import load_dotenv
load_dotenv(os.path.join(backend_dir, '.env'))

from app import create_app, db
from app.models import User, Book, Borrow
from config import config
import bcrypt


def get_config():
    """获取当前环境配置"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['development'])


def init_database():
    """初始化数据库表"""
    app = create_app(get_config())
    with app.app_context():
        # 创建所有表
        db.create_all()
        print('数据库表创建成功！')


def create_admin_user():
    """创建默认管理员用户"""
    app = create_app(get_config())
    with app.app_context():
        # 检查是否已存在管理员
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print('管理员用户已存在')
            return
        
        # 创建管理员用户
        password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
        admin = User(
            username='admin',
            password_hash=password_hash.decode('utf-8'),
            email='admin@library.com',
            role='admin',
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        print('管理员用户创建成功！')
        print('用户名: admin')
        print('密码: admin123')


def create_sample_data():
    """创建示例数据"""
    app = create_app(get_config())
    with app.app_context():
        # 检查是否已有图书数据
        if Book.query.first():
            print('示例数据已存在')
            return
        
        # 创建示例图书
        books = [
            Book(
                isbn='978-7-111-42036-8',
                title='Python编程：从入门到实践',
                author='Eric Matthes',
                publisher='人民邮电出版社',
                location='A区-01-01',
                total_stock=5,
                available_stock=5
            ),
            Book(
                isbn='978-7-115-42802-8',
                title='JavaScript高级程序设计',
                author='Nicholas C. Zakas',
                publisher='人民邮电出版社',
                location='A区-01-02',
                total_stock=3,
                available_stock=3
            ),
            Book(
                isbn='978-7-111-40701-0',
                title='算法导论',
                author='Thomas H. Cormen',
                publisher='机械工业出版社',
                location='B区-02-01',
                total_stock=2,
                available_stock=2
            )
        ]
        
        for book in books:
            db.session.add(book)
        
        db.session.commit()
        print(f'成功创建 {len(books)} 本示例图书！')


def drop_all_tables():
    """删除所有表"""
    app = create_app(get_config())
    with app.app_context():
        db.drop_all()
        print('所有表已删除！')


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='数据库管理脚本')
    parser.add_argument('command', choices=['init', 'admin', 'sample', 'drop', 'all'],
                        help='执行的命令: init-初始化表, admin-创建管理员, sample-创建示例数据, drop-删除所有表, all-执行所有初始化')
    
    args = parser.parse_args()
    
    if args.command == 'init':
        init_database()
    elif args.command == 'admin':
        create_admin_user()
    elif args.command == 'sample':
        create_sample_data()
    elif args.command == 'drop':
        drop_all_tables()
    elif args.command == 'all':
        init_database()
        create_admin_user()
        create_sample_data()
