"""
配置测试
"""
import pytest
from app import create_app, db
from config import TestingConfig, DevelopmentConfig


def test_testing_config():
    """测试测试环境配置"""
    app = create_app(TestingConfig)
    assert app.config['TESTING'] is True
    assert 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']


def test_development_config():
    """测试开发环境配置"""
    app = create_app(DevelopmentConfig)
    assert app.config['DEBUG'] is True


def test_database_connection(app):
    """测试数据库连接"""
    with app.app_context():
        # 尝试创建表
        db.create_all()
        # 验证表已创建
        assert db.engine is not None
