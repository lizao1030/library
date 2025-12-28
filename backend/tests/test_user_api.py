"""
用户 API 单元测试
"""
import pytest
from app.models.user import User


class TestUserRegistration:
    """用户注册 API 测试"""

    def test_register_success(self, client, db_session):
        """测试正常注册"""
        response = client.post('/api/auth/register', json={
            'username': 'testuser',
            'password': 'password123',
            'email': 'test@example.com'
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['message'] == '注册成功'
        assert data['user']['username'] == 'testuser'
        assert data['user']['role'] == 'reader'

    def test_register_duplicate_username(self, client, db_session):
        """测试重复用户名"""
        # 先注册一个用户
        client.post('/api/auth/register', json={
            'username': 'testuser',
            'password': 'password123',
            'email': 'test1@example.com'
        })
        
        # 尝试用相同用户名注册
        response = client.post('/api/auth/register', json={
            'username': 'testuser',
            'password': 'password456',
            'email': 'test2@example.com'
        })
        
        assert response.status_code == 409
        data = response.get_json()
        assert data['error']['code'] == 'USER_EXISTS'

    def test_register_invalid_email(self, client, db_session):
        """测试无效邮箱格式"""
        response = client.post('/api/auth/register', json={
            'username': 'testuser',
            'password': 'password123',
            'email': 'invalid-email'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error']['code'] == 'INVALID_EMAIL'


class TestUserLogin:
    """用户登录 API 测试"""

    def test_login_success(self, client, db_session):
        """测试正常登录"""
        # 先注册用户
        client.post('/api/auth/register', json={
            'username': 'testuser',
            'password': 'password123',
            'email': 'test@example.com'
        })
        
        # 登录
        response = client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'password123'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data
        assert data['user']['username'] == 'testuser'

    def test_login_wrong_password(self, client, db_session):
        """测试错误密码"""
        # 先注册用户
        client.post('/api/auth/register', json={
            'username': 'testuser',
            'password': 'password123',
            'email': 'test@example.com'
        })
        
        # 用错误密码登录
        response = client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['error']['code'] == 'INVALID_CREDENTIALS'

    def test_login_disabled_account(self, client, app, db_session):
        """测试禁用账户登录"""
        # 先注册用户
        client.post('/api/auth/register', json={
            'username': 'testuser',
            'password': 'password123',
            'email': 'test@example.com'
        })
        
        # 禁用账户
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            user.is_active = False
            db_session.commit()
        
        # 尝试登录
        response = client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'password123'
        })
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['error']['code'] == 'ACCOUNT_DISABLED'
