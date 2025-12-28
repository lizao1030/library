"""
图书模块属性测试

Feature: library-management-system
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from app.models.book import Book


# ISBN-13 策略：生成有效的 ISBN-13
def generate_valid_isbn13():
    """生成有效的 ISBN-13 策略"""
    return st.tuples(
        st.sampled_from(['978', '979']),  # 前缀
        st.text(alphabet='0123456789', min_size=9, max_size=9)  # 9位数字
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


# 图书标题策略
title_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'), min_codepoint=32, max_codepoint=126),
    min_size=1,
    max_size=50
).filter(lambda x: x.strip())


# 作者名策略
author_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'Z'), min_codepoint=32, max_codepoint=126),
    min_size=1,
    max_size=30
).filter(lambda x: x.strip())


class TestSearchRelevanceProperty:
    """
    属性 6: 搜索结果相关性
    
    **对于任意**图书搜索，返回的所有图书都应包含搜索关键词（在书名、作者或ISBN中）。
    
    **验证需求: 4.1, 4.2**
    """

    @given(
        title=title_strategy,
        author=author_strategy,
        isbn=generate_valid_isbn13()
    )
    @settings(max_examples=100, deadline=None)
    def test_search_by_title_returns_relevant_books(self, title, author, isbn):
        """
        Feature: library-management-system, Property 6: 搜索结果相关性
        
        对于任意图书，使用书名搜索时，返回的结果应包含该书名
        """
        from app import create_app, db
        from config import TestingConfig
        
        app = create_app(TestingConfig)
        
        with app.app_context():
            db.create_all()
            
            try:
                # 创建测试图书
                book = Book(
                    isbn=isbn,
                    title=title,
                    author=author,
                    publisher='Test Publisher',
                    location='A-1',
                    total_stock=5,
                    available_stock=5
                )
                db.session.add(book)
                db.session.commit()
                
                # 使用书名的一部分进行搜索
                search_term = title[:len(title)//2 + 1] if len(title) > 1 else title
                
                # 执行搜索
                results = Book.query.filter(
                    Book.title.ilike(f'%{search_term}%')
                ).all()
                
                # 验证搜索结果
                assert len(results) >= 1, f"搜索 '{search_term}' 应返回至少一个结果"
                
                # 验证所有结果都包含搜索词
                for result in results:
                    assert search_term.lower() in result.title.lower(), \
                        f"搜索结果 '{result.title}' 应包含搜索词 '{search_term}'"
            finally:
                db.session.remove()
                db.drop_all()

    @given(
        title=title_strategy,
        author=author_strategy,
        isbn=generate_valid_isbn13()
    )
    @settings(max_examples=100, deadline=None)
    def test_search_by_author_returns_relevant_books(self, title, author, isbn):
        """
        Feature: library-management-system, Property 6: 搜索结果相关性
        
        对于任意图书，使用作者名搜索时，返回的结果应包含该作者
        """
        from app import create_app, db
        from config import TestingConfig
        
        app = create_app(TestingConfig)
        
        with app.app_context():
            db.create_all()
            
            try:
                # 创建测试图书
                book = Book(
                    isbn=isbn,
                    title=title,
                    author=author,
                    publisher='Test Publisher',
                    location='A-1',
                    total_stock=5,
                    available_stock=5
                )
                db.session.add(book)
                db.session.commit()
                
                # 使用作者名的一部分进行搜索
                search_term = author[:len(author)//2 + 1] if len(author) > 1 else author
                
                # 执行搜索
                results = Book.query.filter(
                    Book.author.ilike(f'%{search_term}%')
                ).all()
                
                # 验证搜索结果
                assert len(results) >= 1, f"搜索作者 '{search_term}' 应返回至少一个结果"
                
                # 验证所有结果都包含搜索词
                for result in results:
                    assert search_term.lower() in result.author.lower(), \
                        f"搜索结果作者 '{result.author}' 应包含搜索词 '{search_term}'"
            finally:
                db.session.remove()
                db.drop_all()

    @given(
        title=title_strategy,
        author=author_strategy,
        isbn=generate_valid_isbn13()
    )
    @settings(max_examples=100, deadline=None)
    def test_search_by_isbn_returns_relevant_books(self, title, author, isbn):
        """
        Feature: library-management-system, Property 6: 搜索结果相关性
        
        对于任意图书，使用ISBN搜索时，返回的结果应包含该ISBN
        """
        from app import create_app, db
        from config import TestingConfig
        
        app = create_app(TestingConfig)
        
        with app.app_context():
            db.create_all()
            
            try:
                # 创建测试图书
                book = Book(
                    isbn=isbn,
                    title=title,
                    author=author,
                    publisher='Test Publisher',
                    location='A-1',
                    total_stock=5,
                    available_stock=5
                )
                db.session.add(book)
                db.session.commit()
                
                # 使用 ISBN 的一部分进行搜索
                search_term = isbn[:6]
                
                # 执行搜索
                results = Book.query.filter(
                    Book.isbn.ilike(f'%{search_term}%')
                ).all()
                
                # 验证搜索结果
                assert len(results) >= 1, f"搜索 ISBN '{search_term}' 应返回至少一个结果"
                
                # 验证所有结果都包含搜索词
                for result in results:
                    assert search_term in result.isbn, \
                        f"搜索结果 ISBN '{result.isbn}' 应包含搜索词 '{search_term}'"
            finally:
                db.session.remove()
                db.drop_all()

    @given(
        title=title_strategy,
        author=author_strategy,
        isbn=generate_valid_isbn13()
    )
    @settings(max_examples=100, deadline=None)
    def test_keyword_search_returns_relevant_books(self, title, author, isbn):
        """
        Feature: library-management-system, Property 6: 搜索结果相关性
        
        对于任意图书，使用通用关键词搜索时，返回的结果应在书名、作者或ISBN中包含该关键词
        """
        from app import create_app, db
        from config import TestingConfig
        
        app = create_app(TestingConfig)
        
        with app.app_context():
            db.create_all()
            
            try:
                # 创建测试图书
                book = Book(
                    isbn=isbn,
                    title=title,
                    author=author,
                    publisher='Test Publisher',
                    location='A-1',
                    total_stock=5,
                    available_stock=5
                )
                db.session.add(book)
                db.session.commit()
                
                # 使用书名的一部分作为关键词
                keyword = title[:len(title)//2 + 1] if len(title) > 1 else title
                keyword_filter = f'%{keyword}%'
                
                # 执行通用关键词搜索
                results = Book.query.filter(
                    db.or_(
                        Book.title.ilike(keyword_filter),
                        Book.author.ilike(keyword_filter),
                        Book.isbn.ilike(keyword_filter)
                    )
                ).all()
                
                # 验证搜索结果
                assert len(results) >= 1, f"关键词搜索 '{keyword}' 应返回至少一个结果"
                
                # 验证所有结果都在某个字段中包含关键词
                for result in results:
                    keyword_lower = keyword.lower()
                    contains_keyword = (
                        keyword_lower in result.title.lower() or
                        keyword_lower in result.author.lower() or
                        keyword_lower in result.isbn.lower()
                    )
                    assert contains_keyword, \
                        f"搜索结果应在书名、作者或ISBN中包含关键词 '{keyword}'"
            finally:
                db.session.remove()
                db.drop_all()


class TestISBNValidationProperty:
    """
    ISBN 验证属性测试
    
    验证 ISBN 格式验证功能的正确性
    """

    @given(isbn=generate_valid_isbn13())
    @settings(max_examples=100, deadline=None)
    def test_valid_isbn13_accepted(self, isbn):
        """
        对于任意有效的 ISBN-13，验证应返回 True
        """
        assert Book.validate_isbn(isbn), f"有效的 ISBN-13 '{isbn}' 应被接受"

    @given(
        invalid_isbn=st.text(
            alphabet='0123456789',
            min_size=1,
            max_size=8
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_invalid_length_isbn_rejected(self, invalid_isbn):
        """
        对于任意长度不正确的字符串，ISBN 验证应返回 False
        """
        # 跳过长度为 10 或 13 的情况
        assume(len(invalid_isbn) not in [10, 13])
        assert not Book.validate_isbn(invalid_isbn), \
            f"长度为 {len(invalid_isbn)} 的字符串 '{invalid_isbn}' 不应被接受为有效 ISBN"
