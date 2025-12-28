"""
统计路由
"""
import csv
import io
from datetime import datetime, date
from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy import func, extract, desc
from app import db
from app.models import User, Book, Borrow, BorrowStatus

statistics_bp = Blueprint('statistics', __name__)


def require_admin():
    """检查是否为管理员"""
    claims = get_jwt()
    return claims.get('role') == 'admin'


@statistics_bp.route('/borrows', methods=['GET'])
@jwt_required()
def get_borrow_statistics():
    """
    获取借阅统计
    
    查询参数:
    - period: 统计周期 (month/quarter/year)，默认 month
    - year: 年份，默认当前年
    - limit: 排行榜数量限制，默认10
    
    返回:
    - 200: 统计数据
    - 403: 权限不足
    """
    if not require_admin():
        return jsonify({'error': {'code': 'FORBIDDEN', 'message': '权限不足，仅管理员可查看统计'}}), 403
    
    # 获取查询参数
    period = request.args.get('period', 'month').strip().lower()
    year = request.args.get('year', date.today().year, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    if period not in ['month', 'quarter', 'year']:
        period = 'month'
    
    # 借阅量统计（按时间周期）
    period_stats = get_borrow_period_stats(period, year)
    
    # 图书借阅排行榜
    book_ranking = get_book_ranking(year, limit)
    
    # 总体统计
    total_stats = get_total_stats(year)
    
    return jsonify({
        'period': period,
        'year': year,
        'period_stats': period_stats,
        'book_ranking': book_ranking,
        'total_stats': total_stats
    }), 200


def get_borrow_period_stats(period: str, year: int) -> list:
    """
    获取按周期统计的借阅量
    
    Args:
        period: 统计周期 (month/quarter/year)
        year: 年份
        
    Returns:
        统计数据列表
    """
    if period == 'month':
        # 按月统计
        stats = db.session.query(
            extract('month', Borrow.borrow_date).label('period'),
            func.count(Borrow.id).label('count')
        ).filter(
            extract('year', Borrow.borrow_date) == year
        ).group_by(
            extract('month', Borrow.borrow_date)
        ).order_by('period').all()
        
        # 填充所有月份
        result = []
        month_data = {int(s.period): s.count for s in stats}
        for month in range(1, 13):
            result.append({
                'period': month,
                'period_name': f'{month}月',
                'count': month_data.get(month, 0)
            })
        return result
        
    elif period == 'quarter':
        # 按季度统计
        stats = db.session.query(
            func.ceil(extract('month', Borrow.borrow_date) / 3).label('period'),
            func.count(Borrow.id).label('count')
        ).filter(
            extract('year', Borrow.borrow_date) == year
        ).group_by(
            func.ceil(extract('month', Borrow.borrow_date) / 3)
        ).order_by('period').all()
        
        # 填充所有季度
        result = []
        quarter_data = {int(s.period): s.count for s in stats}
        quarter_names = ['第一季度', '第二季度', '第三季度', '第四季度']
        for quarter in range(1, 5):
            result.append({
                'period': quarter,
                'period_name': quarter_names[quarter - 1],
                'count': quarter_data.get(quarter, 0)
            })
        return result
        
    else:  # year
        # 按年统计（最近5年）
        stats = db.session.query(
            extract('year', Borrow.borrow_date).label('period'),
            func.count(Borrow.id).label('count')
        ).filter(
            extract('year', Borrow.borrow_date) >= year - 4
        ).group_by(
            extract('year', Borrow.borrow_date)
        ).order_by('period').all()
        
        result = []
        year_data = {int(s.period): s.count for s in stats}
        for y in range(year - 4, year + 1):
            result.append({
                'period': y,
                'period_name': f'{y}年',
                'count': year_data.get(y, 0)
            })
        return result


def get_book_ranking(year: int, limit: int) -> list:
    """
    获取图书借阅排行榜
    
    Args:
        year: 年份
        limit: 排行榜数量限制
        
    Returns:
        排行榜数据列表
    """
    stats = db.session.query(
        Book.id,
        Book.title,
        Book.author,
        Book.isbn,
        func.count(Borrow.id).label('borrow_count')
    ).join(
        Borrow, Book.id == Borrow.book_id
    ).filter(
        extract('year', Borrow.borrow_date) == year
    ).group_by(
        Book.id, Book.title, Book.author, Book.isbn
    ).order_by(
        desc('borrow_count')
    ).limit(limit).all()
    
    return [{
        'rank': idx + 1,
        'book_id': s.id,
        'title': s.title,
        'author': s.author,
        'isbn': s.isbn,
        'borrow_count': s.borrow_count
    } for idx, s in enumerate(stats)]


def get_total_stats(year: int) -> dict:
    """
    获取总体统计数据
    
    Args:
        year: 年份
        
    Returns:
        总体统计数据
    """
    # 年度总借阅量
    total_borrows = Borrow.query.filter(
        extract('year', Borrow.borrow_date) == year
    ).count()
    
    # 年度归还量
    total_returns = Borrow.query.filter(
        extract('year', Borrow.borrow_date) == year,
        Borrow.status.in_([BorrowStatus.RETURNED.value, BorrowStatus.OVERDUE.value])
    ).count()
    
    # 年度逾期量
    total_overdue = Borrow.query.filter(
        extract('year', Borrow.borrow_date) == year,
        Borrow.status == BorrowStatus.OVERDUE.value
    ).count()
    
    # 当前借阅中
    current_borrowed = Borrow.query.filter(
        Borrow.status == BorrowStatus.BORROWED.value
    ).count()
    
    return {
        'total_borrows': total_borrows,
        'total_returns': total_returns,
        'total_overdue': total_overdue,
        'current_borrowed': current_borrowed,
        'overdue_rate': round(total_overdue / total_borrows * 100, 2) if total_borrows > 0 else 0
    }


@statistics_bp.route('/users', methods=['GET'])
@jwt_required()
def get_user_statistics():
    """
    获取用户统计
    
    查询参数:
    - year: 年份，默认当前年
    - limit: 排行榜数量限制，默认10
    
    返回:
    - 200: 统计数据
    - 403: 权限不足
    """
    if not require_admin():
        return jsonify({'error': {'code': 'FORBIDDEN', 'message': '权限不足，仅管理员可查看统计'}}), 403
    
    # 获取查询参数
    year = request.args.get('year', date.today().year, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    # 活跃用户排行榜
    user_ranking = get_user_ranking(year, limit)
    
    # 用户总体统计
    user_stats = get_user_stats()
    
    return jsonify({
        'year': year,
        'user_ranking': user_ranking,
        'user_stats': user_stats
    }), 200


def get_user_ranking(year: int, limit: int) -> list:
    """
    获取活跃用户排行榜
    
    Args:
        year: 年份
        limit: 排行榜数量限制
        
    Returns:
        排行榜数据列表
    """
    stats = db.session.query(
        User.id,
        User.username,
        User.email,
        func.count(Borrow.id).label('borrow_count')
    ).join(
        Borrow, User.id == Borrow.user_id
    ).filter(
        extract('year', Borrow.borrow_date) == year
    ).group_by(
        User.id, User.username, User.email
    ).order_by(
        desc('borrow_count')
    ).limit(limit).all()
    
    return [{
        'rank': idx + 1,
        'user_id': s.id,
        'username': s.username,
        'email': s.email,
        'borrow_count': s.borrow_count
    } for idx, s in enumerate(stats)]


def get_user_stats() -> dict:
    """
    获取用户总体统计数据
    
    Returns:
        用户统计数据
    """
    # 总用户数
    total_users = User.query.count()
    
    # 活跃用户数（账户启用）
    active_users = User.query.filter(User.is_active == True).count()
    
    # 管理员数量
    admin_count = User.query.filter(User.role == 'admin').count()
    
    # 读者数量
    reader_count = User.query.filter(User.role == 'reader').count()
    
    return {
        'total_users': total_users,
        'active_users': active_users,
        'admin_count': admin_count,
        'reader_count': reader_count
    }


@statistics_bp.route('/export/borrows', methods=['GET'])
@jwt_required()
def export_borrow_statistics():
    """
    导出借阅统计数据为 CSV
    
    查询参数:
    - year: 年份，默认当前年
    - format: 导出格式 (csv)，默认 csv
    
    返回:
    - 200: CSV 文件
    - 403: 权限不足
    """
    if not require_admin():
        return jsonify({'error': {'code': 'FORBIDDEN', 'message': '权限不足，仅管理员可导出数据'}}), 403
    
    year = request.args.get('year', date.today().year, type=int)
    
    # 获取借阅记录
    borrows = Borrow.query.filter(
        extract('year', Borrow.borrow_date) == year
    ).order_by(Borrow.borrow_date.desc()).all()
    
    # 生成 CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 写入表头
    writer.writerow([
        '借阅ID', '用户ID', '用户名', '图书ID', '书名', 'ISBN',
        '借阅日期', '应还日期', '归还日期', '状态', '逾期天数'
    ])
    
    # 写入数据
    for borrow in borrows:
        overdue_days = borrow.calculate_overdue_days() if borrow.return_date else 0
        writer.writerow([
            borrow.id,
            borrow.user_id,
            borrow.user.username if borrow.user else '',
            borrow.book_id,
            borrow.book.title if borrow.book else '',
            borrow.book.isbn if borrow.book else '',
            borrow.borrow_date.isoformat() if borrow.borrow_date else '',
            borrow.due_date.isoformat() if borrow.due_date else '',
            borrow.return_date.isoformat() if borrow.return_date else '',
            borrow.status,
            overdue_days if overdue_days > 0 else ''
        ])
    
    # 返回 CSV 响应
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=borrow_statistics_{year}.csv',
            'Content-Type': 'text/csv; charset=utf-8'
        }
    )


@statistics_bp.route('/export/users', methods=['GET'])
@jwt_required()
def export_user_statistics():
    """
    导出用户统计数据为 CSV
    
    查询参数:
    - year: 年份，默认当前年
    
    返回:
    - 200: CSV 文件
    - 403: 权限不足
    """
    if not require_admin():
        return jsonify({'error': {'code': 'FORBIDDEN', 'message': '权限不足，仅管理员可导出数据'}}), 403
    
    year = request.args.get('year', date.today().year, type=int)
    
    # 获取用户借阅统计
    user_stats = db.session.query(
        User.id,
        User.username,
        User.email,
        User.role,
        User.is_active,
        User.created_at,
        func.count(Borrow.id).label('borrow_count')
    ).outerjoin(
        Borrow, 
        (User.id == Borrow.user_id) & (extract('year', Borrow.borrow_date) == year)
    ).group_by(
        User.id, User.username, User.email, User.role, User.is_active, User.created_at
    ).order_by(desc('borrow_count')).all()
    
    # 生成 CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 写入表头
    writer.writerow([
        '用户ID', '用户名', '邮箱', '角色', '状态', '注册时间', f'{year}年借阅次数'
    ])
    
    # 写入数据
    for stat in user_stats:
        writer.writerow([
            stat.id,
            stat.username,
            stat.email,
            '管理员' if stat.role == 'admin' else '读者',
            '启用' if stat.is_active else '禁用',
            stat.created_at.strftime('%Y-%m-%d %H:%M:%S') if stat.created_at else '',
            stat.borrow_count
        ])
    
    # 返回 CSV 响应
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=user_statistics_{year}.csv',
            'Content-Type': 'text/csv; charset=utf-8'
        }
    )
