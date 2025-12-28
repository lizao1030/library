<template>
  <div class="borrows-page">
    <!-- 快速借阅 (非管理员) -->
    <div v-if="!userStore.isAdmin()" class="quick-borrow md-card-filled">
      <div class="borrow-header">
        <el-icon class="borrow-icon"><Reading /></el-icon>
        <div class="borrow-text">
          <h3>快速借阅</h3>
          <p>搜索并借阅您想要的图书</p>
        </div>
      </div>
      <div class="borrow-form">
        <el-select
          v-model="borrowForm.book_id"
          filterable
          remote
          reserve-keyword
          placeholder="搜索图书..."
          :remote-method="searchBooks"
          :loading="searchLoading"
          size="large"
          class="book-select"
        >
          <el-option
            v-for="book in availableBooks"
            :key="book.id"
            :label="book.title"
            :value="book.id"
            :disabled="book.available_stock <= 0"
          >
            <div class="book-option">
              <span class="option-title">{{ book.title }}</span>
              <span class="option-author">{{ book.author }}</span>
              <el-tag size="small" :type="book.available_stock > 0 ? 'success' : 'info'">
                {{ book.available_stock }} 可借
              </el-tag>
            </div>
          </el-option>
        </el-select>
        <el-button 
          type="primary" 
          @click="handleBorrow" 
          :loading="borrowLoading"
          size="large"
          class="borrow-btn"
        >
          借阅
        </el-button>
      </div>
    </div>

    <!-- 筛选器 -->
    <div class="filter-chips">
      <button 
        v-for="filter in statusFilters" 
        :key="filter.value"
        class="filter-chip"
        :class="{ active: filterForm.status === filter.value }"
        @click="setStatusFilter(filter.value)"
      >
        <el-icon v-if="filter.icon"><component :is="filter.icon" /></el-icon>
        {{ filter.label }}
      </button>
    </div>

    <!-- 借阅列表 -->
    <div class="borrows-list">
      <div 
        v-for="borrow in borrowList" 
        :key="borrow.id" 
        class="borrow-item md-card-outlined"
        :class="{ overdue: borrow.status === 'borrowed' && getDaysRemaining(borrow) < 0 }"
      >
        <div class="item-icon" :class="getStatusClass(borrow)">
          <el-icon v-if="borrow.status === 'returned'"><CircleCheck /></el-icon>
          <el-icon v-else-if="getDaysRemaining(borrow) < 0"><Warning /></el-icon>
          <el-icon v-else><Clock /></el-icon>
        </div>
        
        <div class="item-content">
          <h4 class="item-title">{{ borrow.book?.title || borrow.book_title }}</h4>
          <p class="item-meta">
            ISBN: {{ borrow.book?.isbn || borrow.book_isbn }}
            <span v-if="userStore.isAdmin()"> · {{ borrow.user?.username || borrow.username }}</span>
          </p>
          <div class="item-dates">
            <span>借阅: {{ borrow.borrow_date }}</span>
            <span>应还: {{ borrow.due_date }}</span>
            <span v-if="borrow.return_date">归还: {{ borrow.return_date }}</span>
          </div>
        </div>

        <div class="item-status">
          <el-tag :type="getStatusType(borrow)" class="status-tag">
            {{ getStatusText(borrow) }}
          </el-tag>
          <span v-if="borrow.status === 'borrowed'" class="days-text" :class="{ overdue: getDaysRemaining(borrow) < 0 }">
            {{ getDaysRemaining(borrow) >= 0 ? `${getDaysRemaining(borrow)} 天后到期` : `逾期 ${Math.abs(getDaysRemaining(borrow))} 天` }}
          </span>
        </div>

        <div class="item-action">
          <el-button
            v-if="borrow.status === 'borrowed'"
            type="primary"
            @click="handleReturn(borrow)"
            class="return-btn"
          >
            归还
          </el-button>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="!loading && borrowList.length === 0" class="empty-state">
        <el-icon class="empty-icon"><Reading /></el-icon>
        <p class="empty-text">暂无借阅记录</p>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination-wrapper" v-if="pagination.total > 0">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.per_page"
        :total="pagination.total"
        layout="prev, pager, next"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import api from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Reading, Clock, CircleCheck, Warning } from '@element-plus/icons-vue'

const userStore = useUserStore()
const loading = ref(false)
const borrowLoading = ref(false)
const searchLoading = ref(false)

const borrowForm = reactive({ book_id: null })
const availableBooks = ref([])
const filterForm = reactive({ status: '' })
const pagination = reactive({ page: 1, per_page: 10, total: 0 })
const borrowList = ref([])

const statusFilters = [
  { label: '全部', value: '', icon: null },
  { label: '借阅中', value: 'borrowed', icon: Clock },
  { label: '已归还', value: 'returned', icon: CircleCheck },
  { label: '逾期', value: 'overdue', icon: Warning }
]

const searchBooks = async (query) => {
  if (query.length < 1) { availableBooks.value = []; return }
  searchLoading.value = true
  try {
    const res = await api.get('/books', { params: { title: query, per_page: 20 } })
    availableBooks.value = (res.books || res.data || []).filter(book => book.available_stock > 0)
  } finally {
    searchLoading.value = false
  }
}

const fetchBorrows = async () => {
  loading.value = true
  try {
    const params = { page: pagination.page, per_page: pagination.per_page }
    if (filterForm.status) params.status = filterForm.status
    const res = await api.get('/borrows', { params })
    borrowList.value = res.borrows || res.data || []
    pagination.total = res.pagination?.total || res.total || 0
  } finally {
    loading.value = false
  }
}

const handleBorrow = async () => {
  if (!borrowForm.book_id) { ElMessage.warning('请选择图书'); return }
  borrowLoading.value = true
  try {
    await api.post('/borrows', { book_id: borrowForm.book_id })
    ElMessage.success('借阅成功')
    borrowForm.book_id = null
    availableBooks.value = []
    fetchBorrows()
  } finally {
    borrowLoading.value = false
  }
}

const handleReturn = async (row) => {
  try {
    await ElMessageBox.confirm('确定要归还这本图书吗？', '归还确认', { type: 'info' })
    await api.put(`/borrows/${row.id}/return`)
    ElMessage.success('归还成功')
    fetchBorrows()
  } catch (error) {
    if (error !== 'cancel') console.error('归还失败:', error)
  }
}

const setStatusFilter = (status) => {
  filterForm.status = status
  pagination.page = 1
  fetchBorrows()
}

const handlePageChange = (page) => { pagination.page = page; fetchBorrows() }

const getDaysRemaining = (row) => {
  if (row.status !== 'borrowed') return 0
  return Math.ceil((new Date(row.due_date) - new Date()) / (1000 * 60 * 60 * 24))
}

const getStatusType = (row) => {
  if (row.status === 'returned') return 'success'
  if (row.status === 'overdue' || getDaysRemaining(row) < 0) return 'danger'
  return 'warning'
}

const getStatusText = (row) => {
  if (row.status === 'returned') return '已归还'
  if (row.status === 'overdue') return '逾期归还'
  if (getDaysRemaining(row) < 0) return '逾期中'
  return '借阅中'
}

const getStatusClass = (row) => {
  if (row.status === 'returned') return 'success'
  if (getDaysRemaining(row) < 0) return 'error'
  return 'warning'
}

onMounted(() => { fetchBorrows() })
</script>

<style scoped>
.borrows-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 快速借阅 */
.quick-borrow {
  padding: 24px;
  background: var(--md-primary-container);
  border-radius: var(--md-shape-lg);
}

.borrow-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.borrow-icon {
  font-size: 32px;
  color: var(--md-on-primary-container);
}

.borrow-text h3 {
  font-size: 18px;
  font-weight: 500;
  color: var(--md-on-primary-container);
  margin: 0 0 4px 0;
}

.borrow-text p {
  font-size: 14px;
  color: var(--md-on-primary-container);
  opacity: 0.8;
  margin: 0;
}

.borrow-form {
  display: flex;
  gap: 12px;
}

.book-select {
  flex: 1;
}

.book-option {
  display: flex;
  align-items: center;
  gap: 12px;
}

.option-title {
  font-weight: 500;
}

.option-author {
  color: var(--md-on-surface-variant);
  font-size: 13px;
}

.borrow-btn {
  border-radius: var(--md-shape-full);
  padding: 0 32px;
}

/* 筛选器 */
.filter-chips {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.filter-chip {
  height: 32px;
  padding: 0 16px;
  border-radius: var(--md-shape-sm);
  background: var(--md-surface-container-low);
  border: 1px solid var(--md-outline-variant);
  color: var(--md-on-surface-variant);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all var(--md-motion-duration-short) var(--md-motion-easing-standard);
}

.filter-chip:hover {
  background: var(--md-surface-container-highest);
}

.filter-chip.active {
  background: var(--md-secondary-container);
  border-color: transparent;
  color: var(--md-on-secondary-container);
}

/* 借阅列表 */
.borrows-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.borrow-item {
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all var(--md-motion-duration-short) var(--md-motion-easing-standard);
}

.borrow-item:hover {
  background: var(--md-surface-container-low);
}

.borrow-item.overdue {
  border-color: var(--md-error);
  background: var(--md-error-container);
}

.item-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--md-shape-full);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
}

.item-icon.success {
  background: var(--md-success-container);
  color: var(--md-success);
}

.item-icon.warning {
  background: var(--md-warning-container);
  color: var(--md-warning);
}

.item-icon.error {
  background: var(--md-error-container);
  color: var(--md-error);
}

.item-content {
  flex: 1;
  min-width: 0;
}

.item-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--md-on-surface);
  margin: 0 0 4px 0;
}

.item-meta {
  font-size: 13px;
  color: var(--md-on-surface-variant);
  margin: 0 0 8px 0;
}

.item-dates {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--md-outline);
}

.item-status {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.status-tag {
  border-radius: var(--md-shape-sm);
}

.days-text {
  font-size: 12px;
  color: var(--md-on-surface-variant);
}

.days-text.overdue {
  color: var(--md-error);
  font-weight: 500;
}

.item-action {
  flex-shrink: 0;
}

.return-btn {
  border-radius: var(--md-shape-full);
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
  display: flex;
  justify-content: center;
  margin-top: 16px;
}
</style>
