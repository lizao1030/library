"""
前后端集成测试
测试所有 API 接口和数据交互
"""
import pytest
from datetime import date, timedelta
from app.models import User, Book, Borrow, BorrowStatus


def get_auth_headers(token):
    """获取认证头"""
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }


class TestAuthIntegration:
    """认证模块集成测试"""

    def test_full_auth_flow(self, client, db_session):
        """测试完整认证流程：注册 -> 登录"""
        # 1. 注册
        register_resp = client.post('/api/auth/register', json={
            'username': 'integrationuser',
            'password': 'password123',
            'email': 'integration@example.com'
        })
        assert register_resp.status_code == 201
        
        # 2. 登录
        login_resp = client.post('/api/auth/login', json={
            'username': 'integrationuser',
            'password': 'password123'
        })
        assert login_resp.status_code == 200
        data = login_resp.get_json()
        assert 'access_token' in data
        assert data['user']['username'] == 'integrationuser'


class TestBookIntegration:
    """图书模块集成测试"""

    def _create_admin_and_login(self, client, app, db_session):
        """创建管理员并登录"""
        client.post('/api/auth/register', json={
            'username': 'bookadmin',
            'password': 'admin123',
            'email': 'bookadmin@example.com'
        })
        with app.app_context():
            user = User.query.filter_by(username='bookadmin').first()
            user.role = 'admin'
            db_session.commit()
        
        resp = client.post('/api/auth/login', json={
            'username': 'bookadmin',
            'password': 'admin123'
        })
        return resp.get_json()['access_token']

    def test_book_crud_flow(self, client, app, db_session):
        """测试图书CRUD完整流程"""
        token = self._create_admin_and_login(client, app, db_session)
        headers = get_auth_headers(token)
        
        # 1. 添加图书
        add_resp = client.post('/api/books', json={
            'isbn': '9787111111115',
            'title': '测试图书',
            'author': '测试作者',
            'publisher': '测试出版社',
            'location': 'A-1-1',
            'quantity': 5
        }, headers=headers)
        assert add_resp.status_code == 201
        book_id = add_resp.get_json()['book']['id']
        
        # 2. 查询图书列表
        list_resp = client.get('/api/books')
        assert list_resp.status_code == 200
        assert len(list_resp.get_json()['books']) >= 1
        
        # 3. 获取图书详情
        detail_resp = client.get(f'/api/books/{book_id}')
        assert detail_resp.status_code == 200
        assert detail_resp.get_json()['book']['title'] == '测试图书'
        
        # 4. 更新图书
        update_resp = client.put(f'/api/books/{book_id}', json={
            'title': '更新后的图书'
        }, headers=headers)
        assert update_resp.status_code == 200
        
        # 5. 删除图书
        delete_resp = client.delete(f'/api/books/{book_id}', headers=headers)
        assert delete_resp.status_code == 200

    def test_book_search(self, client, app, db_session):
        """测试图书搜索功能"""
        token = self._create_admin_and_login(client, app, db_session)
        headers = get_auth_headers(token)
        
        # 添加测试图书
        client.post('/api/books', json={
            'isbn': '9787111222224',
            'title': 'Python编程',
            'author': '张三',
            'publisher': '人民邮电出版社',
            'location': 'B-1-1',
            'quantity': 3
        }, headers=headers)
        
        # 按书名搜索
        resp = client.get('/api/books?keyword=Python')
        assert resp.status_code == 200
        books = resp.get_json()['books']
        assert any('Python' in b['title'] for b in books)

    def test_duplicate_isbn_updates_stock(self, client, app, db_session):
        """测试重复ISBN更新库存"""
        token = self._create_admin_and_login(client, app, db_session)
        headers = get_auth_headers(token)
        
        # 第一次添加
        client.post('/api/books', json={
            'isbn': '9787111333333',
            'title': '重复测试',
            'author': '作者',
            'publisher': '出版社',
            'location': 'C-1-1',
            'quantity': 2
        }, headers=headers)
        
        # 第二次添加相同ISBN
        resp = client.post('/api/books', json={
            'isbn': '9787111333333',
            'title': '重复测试',
            'author': '作者',
            'publisher': '出版社',
            'location': 'C-1-1',
            'quantity': 3
        }, headers=headers)
        
        assert resp.status_code == 200
        assert resp.get_json()['book']['total_stock'] == 5


class TestBorrowIntegration:
    """借阅模块集成测试"""

    def _setup_test_data(self, client, app, db_session):
        """设置测试数据"""
        # 创建管理员
        client.post('/api/auth/register', json={
            'username': 'borrowadmin',
            'password': 'admin123',
            'email': 'borrowadmin@example.com'
        })
        with app.app_context():
            admin = User.query.filter_by(username='borrowadmin').first()
            admin.role = 'admin'
            db_session.commit()
        
        admin_resp = client.post('/api/auth/login', json={
            'username': 'borrowadmin',
            'password': 'admin123'
        })
        admin_token = admin_resp.get_json()['access_token']
        
        # 创建读者
        client.post('/api/auth/register', json={
            'username': 'borrowreader',
            'password': 'reader123',
            'email': 'borrowreader@example.com'
        })
        reader_resp = client.post('/api/auth/login', json={
            'username': 'borrowreader',
            'password': 'reader123'
        })
        reader_token = reader_resp.get_json()['access_token']
        
        # 添加图书
        book_resp = client.post('/api/books', json={
            'isbn': '9787111444442',
            'title': '借阅测试图书',
            'author': '借阅作者',
            'publisher': '借阅出版社',
            'location': 'D-1-1',
            'quantity': 2
        }, headers=get_auth_headers(admin_token))
        book_id = book_resp.get_json()['book']['id']
        
        return admin_token, reader_token, book_id

    def test_borrow_return_flow(self, client, app, db_session):
        """测试借阅归还完整流程"""
        admin_token, reader_token, book_id = self._setup_test_data(client, app, db_session)
        reader_headers = get_auth_headers(reader_token)
        
        # 1. 借书
        borrow_resp = client.post('/api/borrows', json={
            'book_id': book_id
        }, headers=reader_headers)
        assert borrow_resp.status_code == 201
        borrow_id = borrow_resp.get_json()['borrow']['id']
        
        # 验证库存减少
        book_resp = client.get(f'/api/books/{book_id}')
        assert book_resp.get_json()['book']['available_stock'] == 1
        
        # 2. 查询借阅记录
        list_resp = client.get('/api/borrows', headers=reader_headers)
        assert list_resp.status_code == 200
        assert len(list_resp.get_json()['borrows']) >= 1
        
        # 3. 还书
        return_resp = client.put(f'/api/borrows/{borrow_id}/return', 
            headers=reader_headers)
        assert return_resp.status_code == 200
        
        # 验证库存恢复
        book_resp = client.get(f'/api/books/{book_id}')
        assert book_resp.get_json()['book']['available_stock'] == 2

    def test_out_of_stock_borrow(self, client, app, db_session):
        """测试库存不足时借阅"""
        admin_token, reader_token, book_id = self._setup_test_data(client, app, db_session)
        reader_headers = get_auth_headers(reader_token)
        
        # 借完所有库存
        for _ in range(2):
            client.post('/api/borrows', json={'book_id': book_id}, 
                headers=reader_headers)
        
        # 再次借阅应失败
        resp = client.post('/api/borrows', json={'book_id': book_id}, 
            headers=reader_headers)
        assert resp.status_code == 409
        assert resp.get_json()['error']['code'] == 'OUT_OF_STOCK'


class TestUserManagementIntegration:
    """用户管理集成测试"""

    def _create_admin(self, client, app, db_session):
        """创建管理员"""
        client.post('/api/auth/register', json={
            'username': 'useradmin',
            'password': 'admin123',
            'email': 'useradmin@example.com'
        })
        with app.app_context():
            admin = User.query.filter_by(username='useradmin').first()
            admin.role = 'admin'
            db_session.commit()
        
        resp = client.post('/api/auth/login', json={
            'username': 'useradmin',
            'password': 'admin123'
        })
        return resp.get_json()['access_token']

    def test_user_list_and_update(self, client, app, db_session):
        """测试用户列表和更新"""
        admin_token = self._create_admin(client, app, db_session)
        headers = get_auth_headers(admin_token)
        
        # 创建测试用户
        client.post('/api/auth/register', json={
            'username': 'testuser1',
            'password': 'test123',
            'email': 'testuser1@example.com'
        })
        
        # 获取用户列表
        list_resp = client.get('/api/users', headers=headers)
        assert list_resp.status_code == 200
        users = list_resp.get_json()['users']
        assert len(users) >= 2
        
        # 找到测试用户
        test_user = next((u for u in users if u['username'] == 'testuser1'), None)
        assert test_user is not None
        
        # 禁用用户
        update_resp = client.put(f'/api/users/{test_user["id"]}', json={
            'is_active': False
        }, headers=headers)
        assert update_resp.status_code == 200
        
        # 验证禁用用户无法登录
        login_resp = client.post('/api/auth/login', json={
            'username': 'testuser1',
            'password': 'test123'
        })
        assert login_resp.status_code == 403

    def test_role_change(self, client, app, db_session):
        """测试角色更改"""
        admin_token = self._create_admin(client, app, db_session)
        headers = get_auth_headers(admin_token)
        
        # 创建读者
        client.post('/api/auth/register', json={
            'username': 'roletest',
            'password': 'test123',
            'email': 'roletest@example.com'
        })
        
        with app.app_context():
            user = User.query.filter_by(username='roletest').first()
            user_id = user.id
        
        # 更改为管理员
        resp = client.put(f'/api/users/{user_id}', json={
            'role': 'admin'
        }, headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()['user']['role'] == 'admin'


class TestStatisticsIntegration:
    """统计模块集成测试"""

    def _setup_statistics_data(self, client, app, db_session):
        """设置统计测试数据"""
        # 创建管理员
        client.post('/api/auth/register', json={
            'username': 'statsadmin',
            'password': 'admin123',
            'email': 'statsadmin@example.com'
        })
        with app.app_context():
            admin = User.query.filter_by(username='statsadmin').first()
            admin.role = 'admin'
            db_session.commit()
        
        resp = client.post('/api/auth/login', json={
            'username': 'statsadmin',
            'password': 'admin123'
        })
        return resp.get_json()['access_token']

    def test_borrow_statistics(self, client, app, db_session):
        """测试借阅统计"""
        token = self._setup_statistics_data(client, app, db_session)
        headers = get_auth_headers(token)
        
        # 获取借阅统计
        resp = client.get('/api/statistics/borrows', headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'period_stats' in data
        assert 'book_ranking' in data
        assert 'total_stats' in data

    def test_user_statistics(self, client, app, db_session):
        """测试用户统计"""
        token = self._setup_statistics_data(client, app, db_session)
        headers = get_auth_headers(token)
        
        # 获取用户统计
        resp = client.get('/api/statistics/users', headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'user_ranking' in data
        assert 'user_stats' in data

    def test_export_borrows(self, client, app, db_session):
        """测试导出借阅数据"""
        token = self._setup_statistics_data(client, app, db_session)
        headers = get_auth_headers(token)
        
        # 导出借阅统计
        resp = client.get('/api/statistics/export/borrows', headers=headers)
        assert resp.status_code == 200
        assert resp.content_type == 'text/csv; charset=utf-8'

    def test_export_users(self, client, app, db_session):
        """测试导出用户数据"""
        token = self._setup_statistics_data(client, app, db_session)
        headers = get_auth_headers(token)
        
        # 导出用户统计
        resp = client.get('/api/statistics/export/users', headers=headers)
        assert resp.status_code == 200
        assert resp.content_type == 'text/csv; charset=utf-8'


class TestPermissionIntegration:
    """权限控制集成测试"""

    def test_reader_cannot_add_book(self, client, db_session):
        """测试读者无法添加图书"""
        # 创建读者
        client.post('/api/auth/register', json={
            'username': 'permreader',
            'password': 'reader123',
            'email': 'permreader@example.com'
        })
        resp = client.post('/api/auth/login', json={
            'username': 'permreader',
            'password': 'reader123'
        })
        token = resp.get_json()['access_token']
        
        # 尝试添加图书
        add_resp = client.post('/api/books', json={
            'isbn': '9787111555551',
            'title': '权限测试',
            'author': '作者',
            'publisher': '出版社',
            'location': 'E-1-1',
            'quantity': 1
        }, headers=get_auth_headers(token))
        
        assert add_resp.status_code == 403

    def test_reader_cannot_view_statistics(self, client, db_session):
        """测试读者无法查看统计"""
        # 创建读者
        client.post('/api/auth/register', json={
            'username': 'statsreader',
            'password': 'reader123',
            'email': 'statsreader@example.com'
        })
        resp = client.post('/api/auth/login', json={
            'username': 'statsreader',
            'password': 'reader123'
        })
        token = resp.get_json()['access_token']
        
        # 尝试查看统计
        stats_resp = client.get('/api/statistics/borrows', 
            headers=get_auth_headers(token))
        assert stats_resp.status_code == 403

    def test_unauthenticated_cannot_borrow(self, client, app, db_session):
        """测试未认证用户无法借书"""
        # 创建管理员添加图书
        client.post('/api/auth/register', json={
            'username': 'authadmin',
            'password': 'admin123',
            'email': 'authadmin@example.com'
        })
        with app.app_context():
            admin = User.query.filter_by(username='authadmin').first()
            admin.role = 'admin'
            db_session.commit()
        
        resp = client.post('/api/auth/login', json={
            'username': 'authadmin',
            'password': 'admin123'
        })
        token = resp.get_json()['access_token']
        
        # 添加图书
        book_resp = client.post('/api/books', json={
            'isbn': '9787111666660',
            'title': '认证测试',
            'author': '作者',
            'publisher': '出版社',
            'location': 'F-1-1',
            'quantity': 1
        }, headers=get_auth_headers(token))
        book_id = book_resp.get_json()['book']['id']
        
        # 未认证借书
        borrow_resp = client.post('/api/borrows', json={'book_id': book_id})
        assert borrow_resp.status_code == 401
