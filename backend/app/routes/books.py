"""
图书路由
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt
from app import db
from app.models.book import Book

books_bp = Blueprint('books', __name__)


def admin_required():
    """检查是否为管理员"""
    claims = get_jwt()
    return claims.get('role') == 'admin'


@books_bp.route('', methods=['POST'])
@jwt_required()
def add_book():
    """
    添加图书（管理员）
    
    请求体:
    {
        "isbn": "string",
        "title": "string",
        "author": "string",
        "publisher": "string",
        "location": "string",
        "quantity": integer
    }
    
    返回:
    - 201: 创建成功
    - 200: ISBN已存在，更新数量
    - 400: 参数验证失败
    - 403: 权限不足
    """
    # 检查管理员权限
    if not admin_required():
        return jsonify({'error': {'code': 'FORBIDDEN', 'message': '权限不足，需要管理员权限'}}), 403
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': {'code': 'INVALID_REQUEST', 'message': '请求体不能为空'}}), 400
    
    isbn = data.get('isbn', '').strip()
    title = data.get('title', '').strip()
    author = data.get('author', '').strip()
    publisher = data.get('publisher', '').strip()
    location = data.get('location', '').strip()
    quantity = data.get('quantity', 1)
    
    # 验证必填字段
    if not isbn:
        return jsonify({'error': {'code': 'INVALID_ISBN', 'message': 'ISBN不能为空'}}), 400
    
    # 验证 ISBN 格式
    if not Book.validate_isbn(isbn):
        return jsonify({'error': {'code': 'INVALID_ISBN', 'message': 'ISBN格式无效'}}), 400
    
    if not title:
        return jsonify({'error': {'code': 'INVALID_TITLE', 'message': '书名不能为空'}}), 400
    
    if not author:
        return jsonify({'error': {'code': 'INVALID_AUTHOR', 'message': '作者不能为空'}}), 400
    
    # 验证数量
    if not isinstance(quantity, int) or quantity < 1:
        return jsonify({'error': {'code': 'INVALID_QUANTITY', 'message': '数量必须为正整数'}}), 400
    
    # 检查 ISBN 是否已存在
    existing_book = Book.query.filter_by(isbn=isbn).first()
    
    if existing_book:
        # ISBN 已存在，更新数量
        existing_book.total_stock += quantity
        existing_book.available_stock += quantity
        db.session.commit()
        
        return jsonify({
            'message': 'ISBN已存在，已更新库存数量',
            'book': existing_book.to_dict()
        }), 200
    
    # 创建新图书
    book = Book(
        isbn=isbn,
        title=title,
        author=author,
        publisher=publisher,
        location=location,
        total_stock=quantity,
        available_stock=quantity
    )
    
    db.session.add(book)
    db.session.commit()
    
    return jsonify({
        'message': '图书添加成功',
        'book': book.to_dict()
    }), 201


@books_bp.route('', methods=['GET'])
def get_books():
    """
    查询图书列表
    
    查询参数:
    - keyword: 搜索关键词（书名、作者、ISBN）
    - title: 书名
    - author: 作者
    - isbn: ISBN
    - page: 页码（默认1）
    - per_page: 每页数量（默认10）
    
    返回:
    - 200: 查询成功
    """
    keyword = request.args.get('keyword', '').strip()
    title = request.args.get('title', '').strip()
    author = request.args.get('author', '').strip()
    isbn = request.args.get('isbn', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', current_app.config.get('ITEMS_PER_PAGE', 10), type=int)
    
    # 构建查询
    query = Book.query
    
    # 通用关键词搜索（书名、作者、ISBN）
    if keyword:
        keyword_filter = f'%{keyword}%'
        query = query.filter(
            db.or_(
                Book.title.ilike(keyword_filter),
                Book.author.ilike(keyword_filter),
                Book.isbn.ilike(keyword_filter)
            )
        )
    
    # 精确字段搜索
    if title:
        query = query.filter(Book.title.ilike(f'%{title}%'))
    
    if author:
        query = query.filter(Book.author.ilike(f'%{author}%'))
    
    if isbn:
        query = query.filter(Book.isbn.ilike(f'%{isbn}%'))
    
    # 分页
    pagination = query.order_by(Book.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    books = [book.to_dict() for book in pagination.items]
    
    # 添加可借状态
    for book in books:
        book['available'] = book['available_stock'] > 0
    
    return jsonify({
        'books': books,
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    }), 200


@books_bp.route('/<int:book_id>', methods=['GET'])
def get_book(book_id):
    """
    获取图书详情
    
    返回:
    - 200: 查询成功
    - 404: 图书不存在
    """
    book = Book.query.get(book_id)
    
    if not book:
        return jsonify({'error': {'code': 'BOOK_NOT_FOUND', 'message': '图书不存在'}}), 404
    
    book_dict = book.to_dict()
    book_dict['available'] = book.available_stock > 0
    
    return jsonify({'book': book_dict}), 200


@books_bp.route('/<int:book_id>', methods=['PUT'])
@jwt_required()
def update_book(book_id):
    """
    更新图书信息（管理员）
    
    请求体:
    {
        "title": "string",
        "author": "string",
        "publisher": "string",
        "location": "string",
        "total_stock": integer
    }
    
    返回:
    - 200: 更新成功
    - 400: 参数验证失败
    - 403: 权限不足
    - 404: 图书不存在
    """
    # 检查管理员权限
    if not admin_required():
        return jsonify({'error': {'code': 'FORBIDDEN', 'message': '权限不足，需要管理员权限'}}), 403
    
    book = Book.query.get(book_id)
    
    if not book:
        return jsonify({'error': {'code': 'BOOK_NOT_FOUND', 'message': '图书不存在'}}), 404
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': {'code': 'INVALID_REQUEST', 'message': '请求体不能为空'}}), 400
    
    # 更新字段
    if 'title' in data:
        title = data['title'].strip()
        if not title:
            return jsonify({'error': {'code': 'INVALID_TITLE', 'message': '书名不能为空'}}), 400
        book.title = title
    
    if 'author' in data:
        author = data['author'].strip()
        if not author:
            return jsonify({'error': {'code': 'INVALID_AUTHOR', 'message': '作者不能为空'}}), 400
        book.author = author
    
    if 'publisher' in data:
        book.publisher = data['publisher'].strip()
    
    if 'location' in data:
        book.location = data['location'].strip()
    
    if 'total_stock' in data:
        new_total = data['total_stock']
        if not isinstance(new_total, int) or new_total < 0:
            return jsonify({'error': {'code': 'INVALID_STOCK', 'message': '库存必须为非负整数'}}), 400
        
        # 计算已借出数量
        borrowed = book.total_stock - book.available_stock
        if new_total < borrowed:
            return jsonify({'error': {'code': 'INVALID_STOCK', 'message': f'库存不能小于已借出数量({borrowed})'}}), 400
        
        book.available_stock = new_total - borrowed
        book.total_stock = new_total
    
    db.session.commit()
    
    return jsonify({
        'message': '图书更新成功',
        'book': book.to_dict()
    }), 200


@books_bp.route('/<int:book_id>', methods=['DELETE'])
@jwt_required()
def delete_book(book_id):
    """
    删除图书（管理员）
    
    返回:
    - 200: 删除成功
    - 403: 权限不足
    - 404: 图书不存在
    - 409: 图书有未归还的借阅记录
    """
    # 检查管理员权限
    if not admin_required():
        return jsonify({'error': {'code': 'FORBIDDEN', 'message': '权限不足，需要管理员权限'}}), 403
    
    book = Book.query.get(book_id)
    
    if not book:
        return jsonify({'error': {'code': 'BOOK_NOT_FOUND', 'message': '图书不存在'}}), 404
    
    # 检查是否有未归还的借阅记录
    if book.total_stock != book.available_stock:
        return jsonify({'error': {'code': 'HAS_BORROWED', 'message': '该图书有未归还的借阅记录，无法删除'}}), 409
    
    db.session.delete(book)
    db.session.commit()
    
    return jsonify({'message': '图书删除成功'}), 200
