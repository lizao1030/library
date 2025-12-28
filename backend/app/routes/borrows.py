"""
借阅路由
"""
from datetime import date
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app import db
from app.models import User, Book, Borrow, BorrowStatus

borrows_bp = Blueprint('borrows', __name__)


def get_current_user():
    """获取当前登录用户"""
    user_id = get_jwt_identity()
    return User.query.get(int(user_id))


def check_user_has_overdue(user_id: int) -> bool:
    """
    检查用户是否有逾期未还的图书
    
    Args:
        user_id: 用户ID
        
    Returns:
        是否有逾期未还图书
    """
    today = date.today()
    overdue_count = Borrow.query.filter(
        Borrow.user_id == user_id,
        Borrow.status == BorrowStatus.BORROWED.value,
        Borrow.due_date < today
    ).count()
    return overdue_count > 0


@borrows_bp.route('', methods=['POST'])
@jwt_required()
def borrow_book():
    """
    借书
    
    请求体:
    {
        "book_id": integer,
        "user_id": integer (可选，管理员可为其他用户借书)
    }
    
    返回:
    - 201: 借阅成功
    - 400: 参数验证失败
    - 403: 有逾期未还图书
    - 404: 图书不存在
    - 409: 库存不足
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': {'code': 'INVALID_REQUEST', 'message': '请求体不能为空'}}), 400
    
    book_id = data.get('book_id')
    
    if not book_id:
        return jsonify({'error': {'code': 'INVALID_BOOK_ID', 'message': '图书ID不能为空'}}), 400
    
    # 确定借阅用户
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())
    
    # 管理员可以为其他用户借书
    if claims.get('role') == 'admin' and data.get('user_id'):
        borrower_id = data.get('user_id')
        borrower = User.query.get(borrower_id)
        if not borrower:
            return jsonify({'error': {'code': 'USER_NOT_FOUND', 'message': '用户不存在'}}), 404
    else:
        borrower_id = current_user_id
        borrower = User.query.get(borrower_id)
    
    # 检查用户是否被禁用
    if not borrower.is_active:
        return jsonify({'error': {'code': 'USER_DISABLED', 'message': '用户账户已被禁用'}}), 403
    
    # 检查用户是否有逾期未还的图书
    if check_user_has_overdue(borrower_id):
        return jsonify({'error': {'code': 'HAS_OVERDUE', 'message': '有逾期未还图书，请先归还后再借阅'}}), 403
    
    # 检查图书是否存在
    book = Book.query.get(book_id)
    if not book:
        return jsonify({'error': {'code': 'BOOK_NOT_FOUND', 'message': '图书不存在'}}), 404
    
    # 检查库存
    if book.available_stock <= 0:
        return jsonify({'error': {'code': 'OUT_OF_STOCK', 'message': '库存不足'}}), 409
    
    # 创建借阅记录
    today = date.today()
    due_date = Borrow.calculate_due_date(today)
    
    borrow = Borrow(
        user_id=borrower_id,
        book_id=book_id,
        borrow_date=today,
        due_date=due_date,
        status=BorrowStatus.BORROWED.value
    )
    
    # 减少库存
    book.available_stock -= 1
    
    db.session.add(borrow)
    db.session.commit()
    
    return jsonify({
        'message': '借阅成功',
        'borrow': borrow.to_dict()
    }), 201


@borrows_bp.route('', methods=['GET'])
@jwt_required()
def get_borrows():
    """
    获取借阅记录
    
    查询参数:
    - user_id: 用户ID（管理员可查看所有用户）
    - status: 借阅状态 (borrowed/returned/overdue)
    - page: 页码（默认1）
    - per_page: 每页数量（默认10）
    
    返回:
    - 200: 查询成功
    """
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())
    is_admin = claims.get('role') == 'admin'
    
    # 获取查询参数
    user_id = request.args.get('user_id', type=int)
    status = request.args.get('status', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', current_app.config.get('ITEMS_PER_PAGE', 10), type=int)
    
    # 构建查询
    query = Borrow.query
    
    # 非管理员只能查看自己的借阅记录
    if is_admin and user_id:
        query = query.filter(Borrow.user_id == user_id)
    elif not is_admin:
        query = query.filter(Borrow.user_id == current_user_id)
    
    # 状态筛选
    if status and status in [s.value for s in BorrowStatus]:
        query = query.filter(Borrow.status == status)
    
    # 分页
    pagination = query.order_by(Borrow.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    borrows = [borrow.to_dict() for borrow in pagination.items]
    
    # 标记逾期记录
    today = date.today()
    for borrow_dict in borrows:
        if borrow_dict['status'] == BorrowStatus.BORROWED.value:
            due_date = date.fromisoformat(borrow_dict['due_date'])
            borrow_dict['is_overdue'] = today > due_date
    
    return jsonify({
        'borrows': borrows,
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    }), 200


@borrows_bp.route('/<int:borrow_id>/return', methods=['PUT'])
@jwt_required()
def return_book(borrow_id):
    """
    还书
    
    返回:
    - 200: 归还成功
    - 403: 权限不足
    - 404: 借阅记录不存在
    - 409: 图书已归还
    """
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())
    is_admin = claims.get('role') == 'admin'
    
    # 查找借阅记录
    borrow = Borrow.query.get(borrow_id)
    
    if not borrow:
        return jsonify({'error': {'code': 'BORROW_NOT_FOUND', 'message': '借阅记录不存在'}}), 404
    
    # 检查权限（只有本人或管理员可以还书）
    if not is_admin and borrow.user_id != current_user_id:
        return jsonify({'error': {'code': 'FORBIDDEN', 'message': '权限不足'}}), 403
    
    # 检查是否已归还
    if borrow.status in [BorrowStatus.RETURNED.value, BorrowStatus.OVERDUE.value]:
        return jsonify({'error': {'code': 'ALREADY_RETURNED', 'message': '图书已归还'}}), 409
    
    # 更新借阅记录
    today = date.today()
    borrow.return_date = today
    
    # 判断是否逾期
    if today > borrow.due_date:
        borrow.status = BorrowStatus.OVERDUE.value
        overdue_days = borrow.calculate_overdue_days(today)
    else:
        borrow.status = BorrowStatus.RETURNED.value
        overdue_days = 0
    
    # 恢复库存
    book = Book.query.get(borrow.book_id)
    if book:
        book.available_stock += 1
    
    db.session.commit()
    
    response_data = {
        'message': '归还成功',
        'borrow': borrow.to_dict()
    }
    
    if overdue_days > 0:
        response_data['message'] = f'归还成功，逾期 {overdue_days} 天'
        response_data['overdue_days'] = overdue_days
    
    return jsonify(response_data), 200
