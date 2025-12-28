"""
用户数据模型
"""
from datetime import datetime
import bcrypt
from app import db


class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.Enum('admin', 'reader'), default='reader', nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关联借阅记录
    borrows = db.relationship('Borrow', backref='user', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password: str) -> None:
        """
        使用 bcrypt 加密密码并存储
        
        Args:
            password: 明文密码
        """
        password_bytes = password.encode('utf-8')
        # bcrypt 限制密码最大72字节，超出部分截断
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    def check_password(self, password: str) -> bool:
        """
        验证密码是否正确
        
        Args:
            password: 明文密码
            
        Returns:
            密码是否匹配
        """
        password_bytes = password.encode('utf-8')
        # bcrypt 限制密码最大72字节，超出部分截断
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        hash_bytes = self.password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)

    @staticmethod
    def is_valid_bcrypt_hash(hash_string: str) -> bool:
        """
        验证字符串是否为有效的 bcrypt 哈希格式
        
        Args:
            hash_string: 待验证的哈希字符串
            
        Returns:
            是否为有效的 bcrypt 哈希
        """
        if not hash_string or not isinstance(hash_string, str):
            return False
        # bcrypt 哈希以 $2a$, $2b$, 或 $2y$ 开头，长度为60字符
        if len(hash_string) != 60:
            return False
        valid_prefixes = ('$2a$', '$2b$', '$2y$')
        return hash_string.startswith(valid_prefixes)
