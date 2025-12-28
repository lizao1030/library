"""
用户管理路由
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from app import db
from app.models.user import User

users_bp = Blueprint('users', __name__)


def admin_required(fn):
    """管理员权限装饰器"""
    from functools import wraps
    
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'error': {'code': 'FORBIDDEN', 'message': '需要管理员权限'}}), 403
        return fn(*args, **kwargs)
    return wrapper


@users_bp.route('', methods=['GET'])
@admin_required
def get_users():
    """
    获取用户列表（管理员）
    
    查询参数:
    - page: 页码，默认1
    - per_page: 每页数量，默认10
    - role: 角色筛选（admin/reader）
    - is_active: 状态筛选（true/false）
    
    返回:
    - 200: 用户列表
    - 403: 权限不足
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    role = request.args.get('role')
    is_active = request.args.get('is_active')
    
    # 构建查询
    query = User.query
    
    if role and role in ('admin', 'reader'):
        query = query.filter_by(role=role)
    
    if is_active is not None:
        is_active_bool = is_active.lower() == 'true'
        query = query.filter_by(is_active=is_active_bool)
    
    # 分页查询
    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    users = [{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'is_active': user.is_active,
        'created_at': user.created_at.isoformat() if user.created_at else None
    } for user in pagination.items]
    
    return jsonify({
        'users': users,
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    }), 200


@users_bp.route('/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """
    更新用户状态（管理员）
    
    请求体:
    {
        "is_active": boolean,  // 可选，启用/禁用用户
        "role": "admin" | "reader"  // 可选，更改角色
    }
    
    返回:
    - 200: 更新成功
    - 400: 参数验证失败
    - 403: 权限不足
    - 404: 用户不存在
    """
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': {'code': 'USER_NOT_FOUND', 'message': '用户不存在'}}), 404
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': {'code': 'INVALID_REQUEST', 'message': '请求体不能为空'}}), 400
    
    # 更新启用/禁用状态
    if 'is_active' in data:
        if not isinstance(data['is_active'], bool):
            return jsonify({'error': {'code': 'INVALID_PARAM', 'message': 'is_active 必须是布尔值'}}), 400
        user.is_active = data['is_active']
    
    # 更新角色
    if 'role' in data:
        if data['role'] not in ('admin', 'reader'):
            return jsonify({'error': {'code': 'INVALID_PARAM', 'message': '角色必须是 admin 或 reader'}}), 400
        user.role = data['role']
    
    db.session.commit()
    
    return jsonify({
        'message': '更新成功',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'is_active': user.is_active
        }
    }), 200
