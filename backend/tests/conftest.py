"""
pytest 配置文件
"""
import pytest
from app import create_app, db
from config import TestingConfig


@pytest.fixture(scope='function')
def app():
    """创建测试应用实例"""
    app = create_app(TestingConfig)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """创建数据库会话"""
    with app.app_context():
        yield db.session
