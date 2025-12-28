"""
认证路由
"""
import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from app.models.user import User

auth_bp = Blueprint('auth', __name__)


def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    用户注册
    
    请求体:
    {
        "username": "string",
        "password": "string",
        "email": "string"
    }
    
    返回:
    - 201: 注册成功
    - 400: 参数验证失败
    - 409: 用户名或邮箱已存在
    """
    data = request.get_json()
    
    # 验证必填字段
    if not data:
        return jsonify({'error': {'code': 'INVALID_REQUEST', 'message': '请求体不能为空'}}), 400
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    email = data.get('email', '').strip()
    
    # 验证用户名
    if not username:
        return jsonify({'error': {'code': 'INVALID_USERNAME', 'message': '用户名不能为空'}}), 400
    if len(username) < 2 or len(username) > 50:
        return jsonify({'error': {'code': 'INVALID_USERNAME', 'message': '用户名长度应在2-50个字符之间'}}), 400
    
    # 验证密码
    if not password:
        return jsonify({'error': {'code': 'INVALID_PASSWORD', 'message': '密码不能为空'}}), 400
    if len(password) < 6:
        return jsonify({'error': {'code': 'INVALID_PASSWORD', 'message': '密码长度至少6个字符'}}), 400
    
    # 验证邮箱格式
    if not email:
        return jsonify({'error': {'code': 'INVALID_EMAIL', 'message': '邮箱不能为空'}}), 400
    if not validate_email(email):
        return jsonify({'error': {'code': 'INVALID_EMAIL', 'message': '邮箱格式无效'}}), 400
    
    # 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify({'error': {'code': 'USER_EXISTS', 'message': '用户名已存在'}}), 409
    
    # 检查邮箱是否已存在
    if User.query.filter_by(email=email).first():
        return jsonify({'error': {'code': 'EMAIL_EXISTS', 'message': '邮箱已被注册'}}), 409
    
    # 创建新用户
    user = User(
        username=username,
        email=email,
        role='reader',
        is_active=True,
        password_hash=''
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'message': '注册成功',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        }
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录
    
    请求体:
    {
        "username": "string",
        "password": "string"
    }
    
    返回:
    - 200: 登录成功，返回 JWT token
    - 400: 参数验证失败
    - 401: 用户名或密码错误
    - 403: 账户已被禁用
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': {'code': 'INVALID_REQUEST', 'message': '请求体不能为空'}}), 400
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'error': {'code': 'INVALID_CREDENTIALS', 'message': '用户名和密码不能为空'}}), 400
    
    # 查找用户
    user = User.query.filter_by(username=username).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': {'code': 'INVALID_CREDENTIALS', 'message': '用户名或密码错误'}}), 401
    
    # 检查账户是否被禁用
    if not user.is_active:
        return jsonify({'error': {'code': 'ACCOUNT_DISABLED', 'message': '账户已被禁用'}}), 403
    
    # 生成 JWT token，包含用户角色信息
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            'username': user.username,
            'role': user.role,
            'email': user.email
        }
    )
    
    # 根据角色返回不同的重定向路径
    redirect_path = '/admin/dashboard' if user.role == 'admin' else '/reader/dashboard'
    
    return jsonify({
        'message': '登录成功',
        'access_token': access_token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        },
        'redirect': redirect_path
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    用户登出
    
    返回:
    - 200: 登出成功
    """
    # JWT 是无状态的，客户端只需删除 token 即可
    # 这里可以添加 token 黑名单逻辑（如果需要）
    return jsonify({'message': '登出成功'}), 200
