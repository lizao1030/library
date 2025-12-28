"""
借阅记录数据模型
"""
from datetime import datetime, date, timedelta
from enum import Enum as PyEnum
from app import db


class BorrowStatus(PyEnum):
    """借阅状态枚举"""
    BORROWED = 'borrowed'      # 借阅中
    RETURNED = 'returned'      # 已归还
    OVERDUE = 'overdue'        # 逾期归还


class Borrow(db.Model):
    """借阅记录模型"""
    __tablename__ = 'borrows'

    # 默认借阅天数
    DEFAULT_BORROW_DAYS = 30

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    borrow_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date, nullable=True)
    status = db.Column(
        db.Enum('borrowed', 'returned', 'overdue', name='borrow_status'),
        default='borrowed',
        nullable=False
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Borrow {self.id}>'

    @staticmethod
    def calculate_due_date(borrow_date: date, days: int = None) -> date:
        """
        计算应还日期
        
        Args:
            borrow_date: 借阅日期
            days: 借阅天数，默认30天
            
        Returns:
            应还日期
        """
        if days is None:
            days = Borrow.DEFAULT_BORROW_DAYS
        return borrow_date + timedelta(days=days)

    def calculate_overdue_days(self, return_date: date = None) -> int:
        """
        计算逾期天数
        
        Args:
            return_date: 归还日期，默认使用记录中的归还日期
            
        Returns:
            逾期天数，如果未逾期返回0
        """
        actual_return = return_date or self.return_date
        if not actual_return:
            # 如果还没归还，使用今天的日期计算
            actual_return = date.today()
        
        if actual_return <= self.due_date:
            return 0
        
        return (actual_return - self.due_date).days

    def is_overdue(self, check_date: date = None) -> bool:
        """
        检查是否逾期
        
        Args:
            check_date: 检查日期，默认为今天
            
        Returns:
            是否逾期
        """
        if check_date is None:
            check_date = date.today()
        
        # 已归还的记录不算逾期（除非状态已标记为overdue）
        if self.status == BorrowStatus.RETURNED.value:
            return False
        
        return check_date > self.due_date

    def get_remaining_days(self, check_date: date = None) -> int:
        """
        获取剩余借阅天数
        
        Args:
            check_date: 检查日期，默认为今天
            
        Returns:
            剩余天数，负数表示已逾期
        """
        if check_date is None:
            check_date = date.today()
        
        return (self.due_date - check_date).days

    def to_dict(self) -> dict:
        """
        将借阅记录转换为字典
        
        Returns:
            借阅记录信息字典
        """
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'book_id': self.book_id,
            'borrow_date': self.borrow_date.isoformat() if self.borrow_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'return_date': self.return_date.isoformat() if self.return_date else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'remaining_days': self.get_remaining_days() if self.status == BorrowStatus.BORROWED.value else None,
            'overdue_days': self.calculate_overdue_days() if self.return_date and self.status == BorrowStatus.OVERDUE.value else None
        }
        
        # 添加关联信息（如果已加载）
        if self.user:
            result['user'] = {
                'id': self.user.id,
                'username': self.user.username
            }
        
        if self.book:
            result['book'] = {
                'id': self.book.id,
                'title': self.book.title,
                'isbn': self.book.isbn
            }
        
        return result
