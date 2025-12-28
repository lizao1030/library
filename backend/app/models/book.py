"""
图书数据模型
"""
import re
from datetime import datetime
from app import db


class Book(db.Model):
    """图书模型"""
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    isbn = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    publisher = db.Column(db.String(100))
    location = db.Column(db.String(50))
    total_stock = db.Column(db.Integer, default=0, nullable=False)
    available_stock = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关联借阅记录
    borrows = db.relationship('Borrow', backref='book', lazy='dynamic')

    def __repr__(self):
        return f'<Book {self.title}>'

    @staticmethod
    def validate_isbn(isbn: str) -> bool:
        """
        验证 ISBN 格式是否有效
        支持 ISBN-10 和 ISBN-13 格式
        
        Args:
            isbn: ISBN 字符串
            
        Returns:
            是否为有效的 ISBN 格式
        """
        if not isbn or not isinstance(isbn, str):
            return False
        
        # 移除连字符和空格
        cleaned = isbn.replace('-', '').replace(' ', '')
        
        # ISBN-10 验证
        if len(cleaned) == 10:
            return Book._validate_isbn10(cleaned)
        
        # ISBN-13 验证
        if len(cleaned) == 13:
            return Book._validate_isbn13(cleaned)
        
        return False

    @staticmethod
    def _validate_isbn10(isbn: str) -> bool:
        """
        验证 ISBN-10 格式
        
        Args:
            isbn: 去除连字符后的 ISBN-10 字符串
            
        Returns:
            是否为有效的 ISBN-10
        """
        # 前9位必须是数字，最后一位可以是数字或X
        if not re.match(r'^\d{9}[\dXx]$', isbn):
            return False
        
        # 计算校验和
        total = 0
        for i in range(9):
            total += int(isbn[i]) * (10 - i)
        
        # 处理最后一位
        last_char = isbn[9].upper()
        if last_char == 'X':
            total += 10
        else:
            total += int(last_char)
        
        return total % 11 == 0

    @staticmethod
    def _validate_isbn13(isbn: str) -> bool:
        """
        验证 ISBN-13 格式
        
        Args:
            isbn: 去除连字符后的 ISBN-13 字符串
            
        Returns:
            是否为有效的 ISBN-13
        """
        # 必须全是数字
        if not isbn.isdigit():
            return False
        
        # 必须以 978 或 979 开头
        if not isbn.startswith(('978', '979')):
            return False
        
        # 计算校验和
        total = 0
        for i in range(12):
            if i % 2 == 0:
                total += int(isbn[i])
            else:
                total += int(isbn[i]) * 3
        
        check_digit = (10 - (total % 10)) % 10
        return check_digit == int(isbn[12])

    def to_dict(self) -> dict:
        """
        将图书对象转换为字典
        
        Returns:
            图书信息字典
        """
        return {
            'id': self.id,
            'isbn': self.isbn,
            'title': self.title,
            'author': self.author,
            'publisher': self.publisher,
            'location': self.location,
            'total_stock': self.total_stock,
            'available_stock': self.available_stock,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
