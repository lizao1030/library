"""
用户模块属性测试

Feature: library-management-system
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from app.models.user import User


# 使用 ASCII 字符策略，避免多字节字符导致的边界问题
password_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P'), min_codepoint=32, max_codepoint=126),
    min_size=4,
    max_size=50
).filter(lambda x: x.strip() and len(x.strip()) >= 4)


class TestPasswordEncryptionProperty:
    """
    属性 2: 密码加密存储
    
    **对于任意**用户注册，存储在数据库中的密码哈希值应为有效的bcrypt格式，
    且原始密码不应出现在数据库中。
    
    **验证需求: 1.4**
    """

    @given(password=password_strategy)
    @settings(max_examples=100, deadline=None)
    def test_password_stored_as_valid_bcrypt_hash(self, password):
        """
        Feature: library-management-system, Property 2: 密码加密存储
        
        对于任意非空密码，设置密码后：
        1. 存储的哈希值应为有效的 bcrypt 格式
        2. 哈希值不等于原始密码（密码被加密）
        3. 使用正确密码验证应返回 True
        """
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash=''
        )
        
        # 设置密码
        user.set_password(password)
        
        # 验证哈希格式为有效的 bcrypt
        assert User.is_valid_bcrypt_hash(user.password_hash), \
            f"密码哈希 '{user.password_hash}' 不是有效的 bcrypt 格式"
        
        # 验证哈希值不等于原始密码（密码被加密存储，而非明文）
        assert user.password_hash != password, \
            "密码哈希不应等于原始密码"
        
        # 验证密码可以正确验证
        assert user.check_password(password), \
            "使用正确密码验证应返回 True"

    @given(password=password_strategy, wrong_password=password_strategy)
    @settings(max_examples=100, deadline=None)
    def test_wrong_password_rejected(self, password, wrong_password):
        """
        Feature: library-management-system, Property 2: 密码加密存储
        
        对于任意两个不同的密码，使用错误密码验证应返回 False
        """
        # 跳过相同密码的情况
        assume(password != wrong_password)
            
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash=''
        )
        
        user.set_password(password)
        
        # 使用错误密码验证应返回 False
        assert not user.check_password(wrong_password), \
            "使用错误密码验证应返回 False"



# 用户名策略
username_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N'), min_codepoint=48, max_codepoint=122),
    min_size=2,
    max_size=20
).filter(lambda x: x.strip() and len(x.strip()) >= 2)


class TestUsernameUniquenessProperty:
    """
    属性 7: 用户名唯一性
    
    **对于任意**两个不同的用户，他们的用户名应不相同。
    
    **验证需求: 1.2**
    """

    @given(
        username=username_strategy,
        email1=st.emails(),
        email2=st.emails()
    )
    @settings(max_examples=100, deadline=None)
    def test_duplicate_username_rejected(self, username, email1, email2):
        """
        Feature: library-management-system, Property 7: 用户名唯一性
        
        对于任意用户名，当第一个用户注册成功后，
        使用相同用户名注册第二个用户应被拒绝
        """
        # 确保两个邮箱不同
        assume(email1 != email2)
        
        from app import create_app, db
        from app.models.user import User
        from config import TestingConfig
        
        app = create_app(TestingConfig)
        
        with app.app_context():
            db.create_all()
            
            try:
                # 创建第一个用户
                user1 = User(
                    username=username,
                    email=email1,
                    role='reader',
                    is_active=True,
                    password_hash=''
                )
                user1.set_password('password123')
                db.session.add(user1)
                db.session.commit()
                
                # 尝试创建具有相同用户名的第二个用户
                user2 = User(
                    username=username,
                    email=email2,
                    role='reader',
                    is_active=True,
                    password_hash=''
                )
                user2.set_password('password456')
                
                # 应该抛出完整性错误
                try:
                    db.session.add(user2)
                    db.session.commit()
                    # 如果没有抛出异常，测试失败
                    assert False, "应该拒绝重复的用户名"
                except Exception:
                    db.session.rollback()
                    # 预期行为：重复用户名被拒绝
                    pass
                
                # 验证数据库中只有一个该用户名的用户
                count = User.query.filter_by(username=username).count()
                assert count == 1, f"数据库中应该只有一个用户名为 '{username}' 的用户，但找到了 {count} 个"
            finally:
                db.session.remove()
                db.drop_all()
