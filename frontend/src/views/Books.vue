<template>
  <div class="books-page">
    <!-- 搜索卡片 -->
    <div class="search-card md-card-outlined">
      <div class="search-header">
        <el-icon class="search-icon"><Search /></el-icon>
        <span class="search-title">搜索图书</span>
      </div>
      <div class="search-fields">
        <el-input 
          v-model="searchForm.title" 
          placeholder="书名" 
          clearable 
          size="large"
          class="search-input"
        />
        <el-input 
          v-model="searchForm.author" 
          placeholder="作者" 
          clearable 
          size="large"
          class="search-input"
        />
        <el-input 
          v-model="searchForm.isbn" 
          placeholder="ISBN" 
          clearable 
          size="large"
          class="search-input"
        />
      </div>
      <div class="search-actions">
        <el-button @click="resetSearch" class="md-outlined-btn">
          重置
        </el-button>
        <el-button type="primary" @click="handleSearch" class="md-filled-btn">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
        <el-button 
          v-if="userStore.isAdmin()" 
          type="primary" 
          @click="showAddDialog"
          class="md-filled-btn add-btn"
        >
          <el-icon><Plus /></el-icon>
          添加图书
        </el-button>
      </div>
    </div>

    <!-- 图书列表 -->
    <div class="books-section">
      <div class="section-header">
        <h2 class="section-title">图书列表</h2>
        <span class="book-count">{{ pagination.total }} 本图书</span>
      </div>

      <div class="books-grid" v-loading="loading">
        <div 
          v-for="book in bookList" 
          :key="book.id" 
          class="book-card md-card-elevated"
        >
          <div class="book-cover">
            <el-icon class="cover-icon"><Document /></el-icon>
          </div>
          <div class="book-info">
            <h3 class="book-title">{{ book.title }}</h3>
            <p class="book-author">{{ book.author }}</p>
            <p class="book-publisher">{{ book.publisher }}</p>
            <div class="book-meta">
              <span class="book-isbn">ISBN: {{ book.isbn }}</span>
              <span class="book-location">{{ book.location }}</span>
            </div>
            <div class="book-stock">
              <div class="stock-bar">
                <div 
                  class="stock-fill" 
                  :style="{ width: (book.available_stock / book.total_stock * 100) + '%' }"
                  :class="{ empty: book.available_stock === 0 }"
                ></div>
              </div>
              <span class="stock-text">
                {{ book.available_stock }} / {{ book.total_stock }} 可借
              </span>
            </div>
          </div>
          <div class="book-actions">
            <template v-if="userStore.isAdmin()">
              <button class="action-btn edit" @click="showEditDialog(book)">
                <el-icon><Edit /></el-icon>
              </button>
              <button class="action-btn delete" @click="handleDelete(book)">
                <el-icon><Delete /></el-icon>
              </button>
            </template>
            <template v-else>
              <el-button 
                type="primary" 
                :disabled="book.available_stock <= 0"
                @click="handleBorrow(book)"
                class="borrow-btn"
              >
                {{ book.available_stock > 0 ? '借阅' : '已借完' }}
              </el-button>
            </template>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="!loading && bookList.length === 0" class="empty-state">
        <el-icon class="empty-icon"><Document /></el-icon>
        <p class="empty-text">暂无图书</p>
      </div>

      <!-- 分页 -->
      <div class="pagination-wrapper" v-if="pagination.total > 0">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.per_page"
          :page-sizes="[12, 24, 48]"
          :total="pagination.total"
          layout="prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑图书' : '添加图书'"
      width="480px"
      class="md-dialog"
    >
      <el-form :model="bookForm" :rules="bookRules" ref="bookFormRef" label-position="top">
        <el-form-item label="ISBN" prop="isbn">
          <el-input v-model="bookForm.isbn" placeholder="请输入ISBN" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="书名" prop="title">
          <el-input v-model="bookForm.title" placeholder="请输入书名" />
        </el-form-item>
        <el-form-item label="作者" prop="author">
          <el-input v-model="bookForm.author" placeholder="请输入作者" />
        </el-form-item>
        <el-form-item label="出版社" prop="publisher">
          <el-input v-model="bookForm.publisher" placeholder="请输入出版社" />
        </el-form-item>
        <el-form-item label="馆藏位置" prop="location">
          <el-input v-model="bookForm.location" placeholder="请输入馆藏位置" />
        </el-form-item>
        <el-form-item label="数量" prop="quantity">
          <el-input-number v-model="bookForm.quantity" :min="1" :max="9999" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
          {{ isEdit ? '保存' : '添加' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import api from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Document, Edit, Delete } from '@element-plus/icons-vue'

const userStore = useUserStore()
const loading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const bookFormRef = ref(null)
const currentBookId = ref(null)

const searchForm = reactive({ title: '', author: '', isbn: '' })
const pagination = reactive({ page: 1, per_page: 12, total: 0 })
const bookList = ref([])
const bookForm = reactive({
  isbn: '', title: '', author: '', publisher: '', location: '', quantity: 1
})

const bookRules = {
  isbn: [{ required: true, message: '请输入ISBN', trigger: 'blur' }],
  title: [{ required: true, message: '请输入书名', trigger: 'blur' }],
  author: [{ required: true, message: '请输入作者', trigger: 'blur' }],
  publisher: [{ required: true, message: '请输入出版社', trigger: 'blur' }],
  location: [{ required: true, message: '请输入馆藏位置', trigger: 'blur' }]
}

const fetchBooks = async () => {
  loading.value = true
  try {
    const params = { page: pagination.page, per_page: pagination.per_page }
    if (searchForm.title) params.title = searchForm.title
    if (searchForm.author) params.author = searchForm.author
    if (searchForm.isbn) params.isbn = searchForm.isbn
    const res = await api.get('/books', { params })
    bookList.value = res.books || res.data || []
    pagination.total = res.total || 0
  } finally {
    loading.value = false
  }
}

const handleSearch = () => { pagination.page = 1; fetchBooks() }
const resetSearch = () => { 
  searchForm.title = ''; searchForm.author = ''; searchForm.isbn = ''
  pagination.page = 1; fetchBooks() 
}
const handleSizeChange = (size) => { pagination.per_page = size; pagination.page = 1; fetchBooks() }
const handlePageChange = (page) => { pagination.page = page; fetchBooks() }

const showAddDialog = () => {
  isEdit.value = false
  currentBookId.value = null
  Object.assign(bookForm, { isbn: '', title: '', author: '', publisher: '', location: '', quantity: 1 })
  dialogVisible.value = true
}

const showEditDialog = (row) => {
  isEdit.value = true
  currentBookId.value = row.id
  Object.assign(bookForm, {
    isbn: row.isbn, title: row.title, author: row.author,
    publisher: row.publisher, location: row.location, quantity: row.total_stock
  })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await bookFormRef.value.validate()
  submitLoading.value = true
  try {
    if (isEdit.value) {
      await api.put(`/books/${currentBookId.value}`, {
        title: bookForm.title, author: bookForm.author,
        publisher: bookForm.publisher, location: bookForm.location, total_stock: bookForm.quantity
      })
      ElMessage.success('更新成功')
    } else {
      await api.post('/books', bookForm)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    fetchBooks()
  } finally {
    submitLoading.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除这本图书吗？', '删除确认', { type: 'warning' })
    await api.delete(`/books/${row.id}`)
    ElMessage.success('删除成功')
    fetchBooks()
  } catch (error) {
    if (error !== 'cancel') console.error('删除失败:', error)
  }
}

const handleBorrow = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要借阅《${row.title}》吗？`, '借阅确认', { type: 'info' })
    await api.post('/borrows', { book_id: row.id })
    ElMessage.success('借阅成功')
    fetchBooks()
  } catch (error) {
    if (error !== 'cancel') console.error('借阅失败:', error)
  }
}

onMounted(() => { fetchBooks() })
</script>

<style scoped>
.books-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 搜索卡片 */
.search-card {
  padding: 24px;
  background: var(--md-surface);
}

.search-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.search-icon {
  font-size: 24px;
  color: var(--md-primary);
}

.search-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--md-on-surface);
}

.search-fields {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.search-input {
  flex: 1;
}

.search-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.md-outlined-btn {
  border-radius: var(--md-shape-full);
  border-color: var(--md-outline);
}

.md-filled-btn {
  border-radius: var(--md-shape-full);
}

.add-btn {
  background: var(--md-tertiary);
}

/* 图书列表 */
.books-section {
  background: var(--md-surface);
  border-radius: var(--md-shape-lg);
  padding: 24px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.section-title {
  font-size: 22px;
  font-weight: 500;
  color: var(--md-on-surface);
  margin: 0;
}

.book-count {
  font-size: 14px;
  color: var(--md-on-surface-variant);
}

/* 图书网格 */
.books-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.book-card {
  padding: 20px;
  display: flex;
  gap: 16px;
  transition: all var(--md-motion-duration-medium) var(--md-motion-easing-standard);
}

.book-card:hover {
  box-shadow: var(--md-elevation-2);
}

.book-cover {
  width: 80px;
  height: 100px;
  background: var(--md-primary-container);
  border-radius: var(--md-shape-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.cover-icon {
  font-size: 32px;
  color: var(--md-on-primary-container);
}

.book-info {
  flex: 1;
  min-width: 0;
}

.book-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--md-on-surface);
  margin: 0 0 4px 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.book-author {
  font-size: 14px;
  color: var(--md-on-surface-variant);
  margin: 0 0 2px 0;
}

.book-publisher {
  font-size: 12px;
  color: var(--md-outline);
  margin: 0 0 8px 0;
}

.book-meta {
  display: flex;
  gap: 12px;
  font-size: 11px;
  color: var(--md-outline);
  margin-bottom: 12px;
}

.book-stock {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stock-bar {
  flex: 1;
  height: 4px;
  background: var(--md-surface-container-highest);
  border-radius: 2px;
  overflow: hidden;
}

.stock-fill {
  height: 100%;
  background: var(--md-primary);
  border-radius: 2px;
  transition: width 0.3s ease;
}

.stock-fill.empty {
  background: var(--md-error);
}

.stock-text {
  font-size: 12px;
  color: var(--md-on-surface-variant);
  white-space: nowrap;
}

.book-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-end;
}

.action-btn {
  width: 40px;
  height: 40px;
  border-radius: var(--md-shape-full);
  border: none;
  background: var(--md-surface-container-highest);
  color: var(--md-on-surface-variant);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--md-motion-duration-short) var(--md-motion-easing-standard);
}

.action-btn:hover {
  background: var(--md-primary-container);
  color: var(--md-on-primary-container);
}

.action-btn.delete:hover {
  background: var(--md-error-container);
  color: var(--md-error);
}

.borrow-btn {
  border-radius: var(--md-shape-full);
  padding: 0 20px;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 64px 24px;
}

.empty-icon {
  font-size: 64px;
  color: var(--md-outline-variant);
  margin-bottom: 16px;
}

.empty-text {
  font-size: 16px;
  color: var(--md-on-surface-variant);
  margin: 0;
}

/* 分页 */
.pagination-wrapper {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

/* 对话框 */
:deep(.el-dialog) {
  border-radius: var(--md-shape-xl);
}

:deep(.el-dialog__header) {
  padding: 24px 24px 16px;
}

:deep(.el-dialog__title) {
  font-size: 24px;
  font-weight: 500;
}

:deep(.el-dialog__body) {
  padding: 0 24px 24px;
}

:deep(.el-dialog__footer) {
  padding: 16px 24px 24px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: var(--md-on-surface-variant);
}
</style>
