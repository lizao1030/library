"""
路由模块
"""
from app.routes.auth import auth_bp
from app.routes.books import books_bp
from app.routes.borrows import borrows_bp
from app.routes.users import users_bp
from app.routes.statistics import statistics_bp

__all__ = ['auth_bp', 'books_bp', 'borrows_bp', 'users_bp', 'statistics_bp']
