"""
借阅模块属性测试

Feature: library-management-system
"""
import pytest
from datetime import date, timedelta
from hypothesis import given, strategies as st, settings, assume
from app import create_app, db
from app.models import User, Book, Borrow, BorrowStatus
from config import TestingConfig


# 生成有效的 ISBN-13
def generate_valid_isbn13():
    """生成有效的 ISBN-13 策略"""
    return st.tuples(
        st.sampled_from(['978', '979']),
        st.text(alphabet='0123456789', min_size=9, max_size=9)
    ).map(lambda x: _complete_isbn13(x[0] + x[1]))


def _complete_isbn13(isbn12: str) -> str:
    """计算并添加 ISBN-13 校验位"""
    total = 0
    for i in range(12):
        if i % 2 == 0:
            total += int(isbn12[i])
        else:
            total += int(isbn12[i]) * 3
    check_digit = (10 - (total % 10)) % 10
    return isbn12 + str(check_digit)


# 库存数量策略
stock_strategy = st.integers(min_value=1, max_value=100)

# 借阅次数策略
borrow_count_strategy = st.integers(min_value=1, max_value=50)


class TestStockNonNegativeProperty:
    """
    属性 3: 库存非负约束
    
    **对于任意**借阅操作，图书的可用库存永远不应变为负数。
    
    **验证需求: 5.2**
    """

    @given(
        initial_stock=stock_strategy,
        borrow_attempts=borrow_count_strategy,
        isbn=generate_valid_isbn13()
    )
    @settings(max_examples=100, deadline=None)
    def test_stock_never_negative_after_borrows(self, initial_stock, borrow_attempts, isbn):
        """
        Feature: library-management-system, Property 3: 库存非负约束
        
        对于任意初始库存和借阅次数，可用库存永远不应变为负数
        """
        app = create_app(TestingConfig)
        
        with app.app_context():
            db.create_all()
            
            try:
                # 创建测试用户
                user = User(
                    username=f'testuser_{isbn[:8]}',
                    email=f'test_{isbn[:8]}@example.com',
                    role='reader',
                    is_active=True,
                    password_hash=''
                )
                user.set_password('password123')
                db.session.add(user)
                
                # 创建测试图书
                book = Book(
                    isbn=isbn,
                    title='Test Book',
                    author='Test Author',
                    publisher='Test Publisher',
                    location='A-1',
                    total_stock=initial_stock,
                    available_stock=initial_stock
                )
                db.session.add(book)
                db.session.commit()
                
                # 尝试多次借阅
                successful_borrows = 0
                for i in range(borrow_attempts):
                    # 检查库存
                    if book.available_stock > 0:
                        # 创建借阅记录
                        borrow = Borrow(
                            user_id=user.id,
                            book_id=book.id,
                            borrow_date=date.today(),
                            due_date=Borrow.calculate_due_date(date.today()),
                            status=BorrowStatus.BORROWED.value
                        )
                        book.available_stock -= 1
                        db.session.add(borrow)
                        db.session.commit()
                        successful_borrows += 1
                    
                    # 核心断言：库存永远不应为负数
                    assert book.available_stock >= 0, \
                        f"库存不应为负数，当前值: {book.available_stock}"
                
                # 验证成功借阅次数不超过初始库存
                assert successful_borrows <= initial_stock, \
                    f"成功借阅次数 {successful_borrows} 不应超过初始库存 {initial_stock}"
                
            finally:
                db.session.remove()
                db.drop_all()



class TestBorrowDueDateProperty:
    """
    属性 5: 借阅期限设置
    
    **对于任意**新创建的借阅记录，应还日期应等于借阅日期加30天。
    
    **验证需求: 5.4, 5.5**
    """

    @given(
        days_offset=st.integers(min_value=-365, max_value=365),
        isbn=generate_valid_isbn13()
    )
    @settings(max_examples=100, deadline=None)
    def test_due_date_equals_borrow_date_plus_30_days(self, days_offset, isbn):
        """
        Feature: library-management-system, Property 5: 借阅期限设置
        
        对于任意借阅日期，应还日期应等于借阅日期加30天
        """
        app = create_app(TestingConfig)
        
        with app.app_context():
            db.create_all()
            
            try:
                # 创建测试用户
                user = User(
                    username=f'testuser_{isbn[:8]}',
                    email=f'test_{isbn[:8]}@example.com',
                    role='reader',
                    is_active=True,
                    password_hash=''
                )
                user.set_password('password123')
                db.session.add(user)
                
                # 创建测试图书
                book = Book(
                    isbn=isbn,
                    title='Test Book',
                    author='Test Author',
                    publisher='Test Publisher',
                    location='A-1',
                    total_stock=10,
                    available_stock=10
                )
                db.session.add(book)
                db.session.commit()
                
                # 使用不同的借阅日期
                borrow_date = date.today() + timedelta(days=days_offset)
                expected_due_date = borrow_date + timedelta(days=30)
                
                # 创建借阅记录
                borrow = Borrow(
                    user_id=user.id,
                    book_id=book.id,
                    borrow_date=borrow_date,
                    due_date=Borrow.calculate_due_date(borrow_date),
                    status=BorrowStatus.BORROWED.value
                )
                db.session.add(borrow)
                db.session.commit()
                
                # 核心断言：应还日期等于借阅日期加30天
                assert borrow.due_date == expected_due_date, \
                    f"应还日期 {borrow.due_date} 应等于借阅日期 {borrow_date} 加30天 ({expected_due_date})"
                
                # 验证借阅记录中记录了借阅日期和预计归还日期
                assert borrow.borrow_date == borrow_date, \
                    f"借阅日期应被正确记录"
                assert borrow.due_date is not None, \
                    f"应还日期不应为空"
                
            finally:
                db.session.remove()
                db.drop_all()

    @given(isbn=generate_valid_isbn13())
    @settings(max_examples=100, deadline=None)
    def test_calculate_due_date_function(self, isbn):
        """
        Feature: library-management-system, Property 5: 借阅期限设置
        
        验证 calculate_due_date 函数的正确性
        """
        # 测试默认30天
        borrow_date = date.today()
        due_date = Borrow.calculate_due_date(borrow_date)
        expected = borrow_date + timedelta(days=30)
        
        assert due_date == expected, \
            f"calculate_due_date 应返回借阅日期加30天"
        
        # 测试自定义天数
        custom_days = 14
        due_date_custom = Borrow.calculate_due_date(borrow_date, custom_days)
        expected_custom = borrow_date + timedelta(days=custom_days)
        
        assert due_date_custom == expected_custom, \
            f"calculate_due_date 应支持自定义借阅天数"



class TestOverdueUserBorrowRestrictionProperty:
    """
    属性 8: 逾期用户借阅限制
    
    **对于任意**有逾期未还图书的读者，系统应拒绝其新的借阅请求。
    
    **验证需求: 5.3**
    """

    @given(
        overdue_days=st.integers(min_value=1, max_value=365),
        isbn1=generate_valid_isbn13(),
        isbn2=generate_valid_isbn13()
    )
    @settings(max_examples=100, deadline=None)
    def test_user_with_overdue_cannot_borrow(self, overdue_days, isbn1, isbn2):
        """
        Feature: library-management-system, Property 8: 逾期用户借阅限制
        
        对于任意有逾期未还图书的用户，新的借阅请求应被拒绝
        """
        # 确保两个 ISBN 不同
        assume(isbn1 != isbn2)
        
        app = create_app(TestingConfig)
        
        with app.app_context():
            db.create_all()
            
            try:
                # 创建测试用户
                user = User(
                    username=f'testuser_{isbn1[:8]}',
                    email=f'test_{isbn1[:8]}@example.com',
                    role='reader',
                    is_active=True,
                    password_hash=''
                )
                user.set_password('password123')
                db.session.add(user)
                
                # 创建两本测试图书
                book1 = Book(
                    isbn=isbn1,
                    title='Test Book 1',
                    author='Test Author',
                    publisher='Test Publisher',
                    location='A-1',
                    total_stock=10,
                    available_stock=10
                )
                book2 = Book(
                    isbn=isbn2,
                    title='Test Book 2',
                    author='Test Author',
                    publisher='Test Publisher',
                    location='A-2',
                    total_stock=10,
                    available_stock=10
                )
                db.session.add(book1)
                db.session.add(book2)
                db.session.commit()
                
                # 创建一个逾期的借阅记录
                past_borrow_date = date.today() - timedelta(days=30 + overdue_days)
                past_due_date = past_borrow_date + timedelta(days=30)
                
                overdue_borrow = Borrow(
                    user_id=user.id,
                    book_id=book1.id,
                    borrow_date=past_borrow_date,
                    due_date=past_due_date,
                    status=BorrowStatus.BORROWED.value  # 未归还
                )
                book1.available_stock -= 1
                db.session.add(overdue_borrow)
                db.session.commit()
                
                # 导入检查函数
                from app.routes.borrows import check_user_has_overdue
                
                # 核心断言：用户应被标记为有逾期
                has_overdue = check_user_has_overdue(user.id)
                assert has_overdue, \
                    f"用户有逾期 {overdue_days} 天的图书，应被检测到"
                
                # 验证逾期记录确实是逾期的
                assert overdue_borrow.is_overdue(), \
                    f"借阅记录应被标记为逾期"
                
            finally:
                db.session.remove()
                db.drop_all()

    @given(isbn=generate_valid_isbn13())
    @settings(max_examples=100, deadline=None)
    def test_user_without_overdue_can_borrow(self, isbn):
        """
        Feature: library-management-system, Property 8: 逾期用户借阅限制
        
        对于没有逾期图书的用户，应允许借阅
        """
        app = create_app(TestingConfig)
        
        with app.app_context():
            db.create_all()
            
            try:
                # 创建测试用户
                user = User(
                    username=f'testuser_{isbn[:8]}',
                    email=f'test_{isbn[:8]}@example.com',
                    role='reader',
                    is_active=True,
                    password_hash=''
                )
                user.set_password('password123')
                db.session.add(user)
                
                # 创建测试图书
                book = Book(
                    isbn=isbn,
                    title='Test Book',
                    author='Test Author',
                    publisher='Test Publisher',
                    location='A-1',
                    total_stock=10,
                    available_stock=10
                )
                db.session.add(book)
                db.session.commit()
                
                # 导入检查函数
                from app.routes.borrows import check_user_has_overdue
                
                # 核心断言：没有借阅记录的用户不应有逾期
                has_overdue = check_user_has_overdue(user.id)
                assert not has_overdue, \
                    f"没有借阅记录的用户不应被标记为有逾期"
                
            finally:
                db.session.remove()
                db.drop_all()



class TestBorrowReturnRoundTripProperty:
    """
    属性 1: 借阅归还往返一致性
    
    **对于任意**图书和读者，借阅一本图书然后归还，图书的可用库存应恢复到借阅前的值。
    
    **验证需求: 5.1, 6.1**
    """

    @given(
        initial_stock=st.integers(min_value=1, max_value=100),
        isbn=generate_valid_isbn13()
    )
    @settings(max_examples=100, deadline=None)
    def test_stock_restored_after_borrow_and_return(self, initial_stock, isbn):
        """
        Feature: library-management-system, Property 1: 借阅归还往返一致性
        
        对于任意图书，借阅后归还，库存应恢复到借阅前的值
        """
        app = create_app(TestingConfig)
        
        with app.app_context():
            db.create_all()
            
            try:
                # 创建测试用户
                user = User(
                    username=f'testuser_{isbn[:8]}',
                    email=f'test_{isbn[:8]}@example.com',
                    role='reader',
                    is_active=True,
                    password_hash=''
                )
                user.set_password('password123')
                db.session.add(user)
                
                # 创建测试图书
                book = Book(
                    isbn=isbn,
                    title='Test Book',
                    author='Test Author',
                    publisher='Test Publisher',
                    location='A-1',
                    total_stock=initial_stock,
                    available_stock=initial_stock
                )
                db.session.add(book)
                db.session.commit()
                
                # 记录借阅前的库存
                stock_before_borrow = book.available_stock
                
                # 借阅图书
                borrow = Borrow(
                    user_id=user.id,
                    book_id=book.id,
                    borrow_date=date.today(),
                    due_date=Borrow.calculate_due_date(date.today()),
                    status=BorrowStatus.BORROWED.value
                )
                book.available_stock -= 1
                db.session.add(borrow)
                db.session.commit()
                
                # 验证借阅后库存减少
                assert book.available_stock == stock_before_borrow - 1, \
                    f"借阅后库存应减少1"
                
                # 归还图书
                borrow.return_date = date.today()
                borrow.status = BorrowStatus.RETURNED.value
                book.available_stock += 1
                db.session.commit()
                
                # 核心断言：归还后库存应恢复
                assert book.available_stock == stock_before_borrow, \
                    f"归还后库存 {book.available_stock} 应等于借阅前库存 {stock_before_borrow}"
                
            finally:
                db.session.remove()
                db.drop_all()

    @given(
        borrow_count=st.integers(min_value=1, max_value=10),
        initial_stock=st.integers(min_value=10, max_value=50),
        isbn=generate_valid_isbn13()
    )
    @settings(max_examples=100, deadline=None)
    def test_multiple_borrows_and_returns_restore_stock(self, borrow_count, initial_stock, isbn):
        """
        Feature: library-management-system, Property 1: 借阅归还往返一致性
        
        对于任意多次借阅和归还，最终库存应恢复到初始值
        """
        app = create_app(TestingConfig)
        
        with app.app_context():
            db.create_all()
            
            try:
                # 创建测试图书
                book = Book(
                    isbn=isbn,
                    title='Test Book',
                    author='Test Author',
                    publisher='Test Publisher',
                    location='A-1',
                    total_stock=initial_stock,
                    available_stock=initial_stock
                )
                db.session.add(book)
                db.session.commit()
                
                borrows = []
                
                # 创建多个用户并借阅
                for i in range(borrow_count):
                    user = User(
                        username=f'testuser_{isbn[:6]}_{i}',
                        email=f'test_{isbn[:6]}_{i}@example.com',
                        role='reader',
                        is_active=True,
                        password_hash=''
                    )
                    user.set_password('password123')
                    db.session.add(user)
                    db.session.commit()
                    
                    # 借阅
                    borrow = Borrow(
                        user_id=user.id,
                        book_id=book.id,
                        borrow_date=date.today(),
                        due_date=Borrow.calculate_due_date(date.today()),
                        status=BorrowStatus.BORROWED.value
                    )
                    book.available_stock -= 1
                    db.session.add(borrow)
                    borrows.append(borrow)
                
                db.session.commit()
                
                # 验证借阅后库存
                assert book.available_stock == initial_stock - borrow_count, \
                    f"借阅 {borrow_count} 本后库存应为 {initial_stock - borrow_count}"
                
                # 全部归还
                for borrow in borrows:
                    borrow.return_date = date.today()
                    borrow.status = BorrowStatus.RETURNED.value
                    book.available_stock += 1
                
                db.session.commit()
                
                # 核心断言：全部归还后库存应恢复到初始值
                assert book.available_stock == initial_stock, \
                    f"全部归还后库存 {book.available_stock} 应等于初始库存 {initial_stock}"
                
            finally:
                db.session.remove()
                db.drop_all()



class TestOverdueDaysCalculationProperty:
    """
    属性 4: 逾期天数计算正确性
    
    **对于任意**逾期归还的借阅记录，逾期天数应等于实际归还日期减去应还日期的天数差。
    
    **验证需求: 6.3**
    """

    @given(
        overdue_days=st.integers(min_value=1, max_value=365),
        borrow_days_ago=st.integers(min_value=31, max_value=400),
        isbn=generate_valid_isbn13()
    )
    @settings(max_examples=100, deadline=None)
    def test_overdue_days_equals_return_date_minus_due_date(self, overdue_days, borrow_days_ago, isbn):
        """
        Feature: library-management-system, Property 4: 逾期天数计算正确性
        
        对于任意逾期归还，逾期天数应等于归还日期减去应还日期
        """
        app = create_app(TestingConfig)
        
        with app.app_context():
            db.create_all()
            
            try:
                # 创建测试用户
                user = User(
                    username=f'testuser_{isbn[:8]}',
                    email=f'test_{isbn[:8]}@example.com',
                    role='reader',
                    is_active=True,
                    password_hash=''
                )
                user.set_password('password123')
                db.session.add(user)
                
                # 创建测试图书
                book = Book(
                    isbn=isbn,
                    title='Test Book',
                    author='Test Author',
                    publisher='Test Publisher',
                    location='A-1',
                    total_stock=10,
                    available_stock=10
                )
                db.session.add(book)
                db.session.commit()
                
                # 计算日期
                borrow_date = date.today() - timedelta(days=borrow_days_ago)
                due_date = borrow_date + timedelta(days=30)
                return_date = due_date + timedelta(days=overdue_days)
                
                # 创建逾期借阅记录
                borrow = Borrow(
                    user_id=user.id,
                    book_id=book.id,
                    borrow_date=borrow_date,
                    due_date=due_date,
                    return_date=return_date,
                    status=BorrowStatus.OVERDUE.value
                )
                db.session.add(borrow)
                db.session.commit()
                
                # 核心断言：逾期天数等于归还日期减去应还日期
                calculated_overdue = borrow.calculate_overdue_days()
                expected_overdue = (return_date - due_date).days
                
                assert calculated_overdue == expected_overdue, \
                    f"计算的逾期天数 {calculated_overdue} 应等于预期值 {expected_overdue}"
                
                assert calculated_overdue == overdue_days, \
                    f"逾期天数 {calculated_overdue} 应等于 {overdue_days}"
                
            finally:
                db.session.remove()
                db.drop_all()

    @given(
        early_days=st.integers(min_value=1, max_value=29),
        isbn=generate_valid_isbn13()
    )
    @settings(max_examples=100, deadline=None)
    def test_no_overdue_when_returned_before_due_date(self, early_days, isbn):
        """
        Feature: library-management-system, Property 4: 逾期天数计算正确性
        
        对于任意在应还日期前归还的记录，逾期天数应为0
        """
        app = create_app(TestingConfig)
        
        with app.app_context():
            db.create_all()
            
            try:
                # 创建测试用户
                user = User(
                    username=f'testuser_{isbn[:8]}',
                    email=f'test_{isbn[:8]}@example.com',
                    role='reader',
                    is_active=True,
                    password_hash=''
                )
                user.set_password('password123')
                db.session.add(user)
                
                # 创建测试图书
                book = Book(
                    isbn=isbn,
                    title='Test Book',
                    author='Test Author',
                    publisher='Test Publisher',
                    location='A-1',
                    total_stock=10,
                    available_stock=10
                )
                db.session.add(book)
                db.session.commit()
                
                # 计算日期（提前归还）
                borrow_date = date.today() - timedelta(days=30)
                due_date = borrow_date + timedelta(days=30)
                return_date = due_date - timedelta(days=early_days)
                
                # 创建借阅记录
                borrow = Borrow(
                    user_id=user.id,
                    book_id=book.id,
                    borrow_date=borrow_date,
                    due_date=due_date,
                    return_date=return_date,
                    status=BorrowStatus.RETURNED.value
                )
                db.session.add(borrow)
                db.session.commit()
                
                # 核心断言：提前归还时逾期天数应为0
                calculated_overdue = borrow.calculate_overdue_days()
                
                assert calculated_overdue == 0, \
                    f"提前 {early_days} 天归还时，逾期天数应为0，实际为 {calculated_overdue}"
                
            finally:
                db.session.remove()
                db.drop_all()

    @given(isbn=generate_valid_isbn13())
    @settings(max_examples=100, deadline=None)
    def test_overdue_days_zero_when_returned_on_due_date(self, isbn):
        """
        Feature: library-management-system, Property 4: 逾期天数计算正确性
        
        在应还日期当天归还时，逾期天数应为0
        """
        app = create_app(TestingConfig)
        
        with app.app_context():
            db.create_all()
            
            try:
                # 创建测试用户
                user = User(
                    username=f'testuser_{isbn[:8]}',
                    email=f'test_{isbn[:8]}@example.com',
                    role='reader',
                    is_active=True,
                    password_hash=''
                )
                user.set_password('password123')
                db.session.add(user)
                
                # 创建测试图书
                book = Book(
                    isbn=isbn,
                    title='Test Book',
                    author='Test Author',
                    publisher='Test Publisher',
                    location='A-1',
                    total_stock=10,
                    available_stock=10
                )
                db.session.add(book)
                db.session.commit()
                
                # 在应还日期当天归还
                borrow_date = date.today() - timedelta(days=30)
                due_date = borrow_date + timedelta(days=30)
                return_date = due_date  # 当天归还
                
                # 创建借阅记录
                borrow = Borrow(
                    user_id=user.id,
                    book_id=book.id,
                    borrow_date=borrow_date,
                    due_date=due_date,
                    return_date=return_date,
                    status=BorrowStatus.RETURNED.value
                )
                db.session.add(borrow)
                db.session.commit()
                
                # 核心断言：当天归还时逾期天数应为0
                calculated_overdue = borrow.calculate_overdue_days()
                
                assert calculated_overdue == 0, \
                    f"在应还日期当天归还时，逾期天数应为0，实际为 {calculated_overdue}"
                
            finally:
                db.session.remove()
                db.drop_all()
