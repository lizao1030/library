"""
图书馆管理系统后端应用
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import Config

db = SQLAlchemy()
jwt = JWTManager()


def create_app(config_class=Config):
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 初始化扩展
    db.init_app(app)
    jwt.init_app(app)
    CORS(app)

    # 注册蓝图
    from app.routes import auth_bp, books_bp, borrows_bp, users_bp, statistics_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(books_bp, url_prefix='/api/books')
    app.register_blueprint(borrows_bp, url_prefix='/api/borrows')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(statistics_bp, url_prefix='/api/statistics')

    return app
