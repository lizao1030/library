<template>
  <div class="users-page">
    <!-- 搜索筛选 -->
    <div class="search-bar md-card-outlined">
      <el-input 
        v-model="searchForm.username" 
        placeholder="搜索用户名..." 
        clearable 
        size="large"
        class="search-input"
        @keyup.enter="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <div class="filter-chips">
        <button 
          class="filter-chip"
          :class="{ active: searchForm.role === '' }"
          @click="searchForm.role = ''; handleSearch()"
        >
          全部
        </button>
        <button 
          class="filter-chip"
          :class="{ active: searchForm.role === 'admin' }"
          @click="searchForm.role = 'admin'; handleSearch()"
        >
          <el-icon><UserFilled /></el-icon>
          管理员
        </button>
        <button 
          class="filter-chip"
          :class="{ active: searchForm.role === 'reader' }"
          @click="searchForm.role = 'reader'; handleSearch()"
        >
          <el-icon><User /></el-icon>
          读者
        </button>
      </div>
    </div>

    <!-- 用户列表 -->
    <div class="users-list">
      <div 
        v-for="user in userList" 
        :key="user.id" 
        class="user-card md-card-outlined"
        :class="{ disabled: !user.is_active }"
      >
        <div class="user-avatar" :class="{ admin: user.role === 'admin' }">
          {{ user.username?.charAt(0).toUpperCase() }}
        </div>
        
        <div class="user-info">
          <div class="user-header">
            <h4 class="user-name">{{ user.username }}</h4>
            <el-tag 
              :type="user.role === 'admin' ? 'danger' : ''" 
              size="small"
              class="role-tag"
            >
              {{ user.role === 'admin' ? '管理员' : '读者' }}
            </el-tag>
          </div>
          <p class="user-email">{{ user.email }}</p>
          <p class="user-date">注册于 {{ formatDate(user.created_at) }}</p>
        </div>

        <div class="user-status">
          <el-tag :type="user.is_active ? 'success' : 'info'" class="status-tag">
            {{ user.is_active ? '已启用' : '已禁用' }}
          </el-tag>
        </div>

        <div class="user-actions">
          <button 
            class="action-btn"
            :class="user.is_active ? 'warning' : 'success'"
            @click="toggleUserStatus(user)"
            :disabled="user.id === currentUserId"
          >
            <el-icon v-if="user.is_active"><Lock /></el-icon>
            <el-icon v-else><Unlock /></el-icon>
          </button>
          <button 
            class="action-btn primary"
            @click="showRoleDialog(user)"
            :disabled="user.id === currentUserId"
          >
            <el-icon><Edit /></el-icon>
          </button>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="!loading && userList.length === 0" class="empty-state">
        <el-icon class="empty-icon"><User /></el-icon>
        <p class="empty-text">暂无用户</p>
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

    <!-- 修改角色对话框 -->
    <el-dialog v-model="roleDialogVisible" title="修改角色" width="400px" class="md-dialog">
      <div class="role-dialog-content">
        <div class="dialog-user">
          <div class="dialog-avatar">
            {{ roleForm.username?.charAt(0).toUpperCase() }}
          </div>
          <span class="dialog-username">{{ roleForm.username }}</span>
        </div>
        <div class="role-options">
          <button 
            class="role-option"
            :class="{ active: roleForm.newRole === 'admin' }"
            @click="roleForm.newRole = 'admin'"
          >
            <el-icon><UserFilled /></el-icon>
            <span>管理员</span>
            <p>可以管理图书、用户和查看统计</p>
          </button>
          <button 
            class="role-option"
            :class="{ active: roleForm.newRole === 'reader' }"
            @click="roleForm.newRole = 'reader'"
          >
            <el-icon><User /></el-icon>
            <span>读者</span>
            <p>可以借阅和归还图书</p>
          </button>
        </div>
      </div>
      <template #footer>
        <el-button @click="roleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleRoleChange" :loading="roleLoading">
          确认修改
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useUserStore } from '@/stores/user'
import api from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, User, UserFilled, Lock, Unlock, Edit } from '@element-plus/icons-vue'

const userStore = useUserStore()
const loading = ref(false)
const roleLoading = ref(false)
const roleDialogVisible = ref(false)

const currentUserId = computed(() => userStore.userInfo.id)
const searchForm = reactive({ username: '', role: '' })
const pagination = reactive({ page: 1, per_page: 10, total: 0 })
const userList = ref([])
const roleForm = reactive({ userId: null, username: '', currentRole: '', newRole: '' })

const fetchUsers = async () => {
  loading.value = true
  try {
    const params = { page: pagination.page, per_page: pagination.per_page }
    if (searchForm.username) params.username = searchForm.username
    if (searchForm.role) params.role = searchForm.role
    const res = await api.get('/users', { params })
    userList.value = res.users || res.data || []
    pagination.total = res.total || 0
  } finally {
    loading.value = false
  }
}

const handleSearch = () => { pagination.page = 1; fetchUsers() }
const handlePageChange = (page) => { pagination.page = page; fetchUsers() }

const toggleUserStatus = async (row) => {
  const action = row.is_active ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(`确定要${action}用户 "${row.username}" 吗？`, '确认操作', { type: 'warning' })
    await api.put(`/users/${row.id}`, { is_active: !row.is_active })
    ElMessage.success(`${action}成功`)
    fetchUsers()
  } catch (error) {
    if (error !== 'cancel') console.error('操作失败:', error)
  }
}

const showRoleDialog = (row) => {
  roleForm.userId = row.id
  roleForm.username = row.username
  roleForm.currentRole = row.role
  roleForm.newRole = row.role
  roleDialogVisible.value = true
}

const handleRoleChange = async () => {
  if (roleForm.newRole === roleForm.currentRole) {
    ElMessage.warning('角色未改变')
    return
  }
  roleLoading.value = true
  try {
    await api.put(`/users/${roleForm.userId}`, { role: roleForm.newRole })
    ElMessage.success('角色修改成功')
    roleDialogVisible.value = false
    fetchUsers()
  } finally {
    roleLoading.value = false
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

onMounted(() => { fetchUsers() })
</script>

<style scoped>
.users-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 搜索栏 */
.search-bar {
  padding: 20px 24px;
  display: flex;
  align-items: center;
  gap: 24px;
  background: var(--md-surface);
}

.search-input {
  width: 300px;
}

.filter-chips {
  display: flex;
  gap: 8px;
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

/* 用户列表 */
.users-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.user-card {
  padding: 20px 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  background: var(--md-surface);
  transition: all var(--md-motion-duration-short) var(--md-motion-easing-standard);
}

.user-card:hover {
  background: var(--md-surface-container-low);
}

.user-card.disabled {
  opacity: 0.6;
}

.user-avatar {
  width: 48px;
  height: 48px;
  border-radius: var(--md-shape-full);
  background: var(--md-primary);
  color: var(--md-on-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 500;
  flex-shrink: 0;
}

.user-avatar.admin {
  background: var(--md-tertiary);
  color: var(--md-on-tertiary);
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.user-name {
  font-size: 16px;
  font-weight: 500;
  color: var(--md-on-surface);
  margin: 0;
}

.role-tag {
  border-radius: var(--md-shape-sm);
}

.user-email {
  font-size: 14px;
  color: var(--md-on-surface-variant);
  margin: 0 0 2px 0;
}

.user-date {
  font-size: 12px;
  color: var(--md-outline);
  margin: 0;
}

.user-status {
  flex-shrink: 0;
}

.status-tag {
  border-radius: var(--md-shape-sm);
}

.user-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
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
  font-size: 18px;
  transition: all var(--md-motion-duration-short) var(--md-motion-easing-standard);
}

.action-btn:hover {
  background: var(--md-primary-container);
  color: var(--md-on-primary-container);
}

.action-btn.warning:hover {
  background: var(--md-warning-container);
  color: var(--md-warning);
}

.action-btn.success:hover {
  background: var(--md-success-container);
  color: var(--md-success);
}

.action-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
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
}

/* 对话框 */
.role-dialog-content {
  padding: 8px 0;
}

.dialog-user {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.dialog-avatar {
  width: 48px;
  height: 48px;
  border-radius: var(--md-shape-full);
  background: var(--md-primary);
  color: var(--md-on-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 500;
}

.dialog-username {
  font-size: 18px;
  font-weight: 500;
  color: var(--md-on-surface);
}

.role-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.role-option {
  padding: 16px;
  border-radius: var(--md-shape-md);
  border: 1px solid var(--md-outline-variant);
  background: var(--md-surface);
  cursor: pointer;
  text-align: left;
  transition: all var(--md-motion-duration-short) var(--md-motion-easing-standard);
}

.role-option:hover {
  background: var(--md-surface-container-low);
}

.role-option.active {
  border-color: var(--md-primary);
  background: var(--md-primary-container);
}

.role-option .el-icon {
  font-size: 24px;
  color: var(--md-primary);
  margin-bottom: 8px;
}

.role-option span {
  display: block;
  font-size: 16px;
  font-weight: 500;
  color: var(--md-on-surface);
  margin-bottom: 4px;
}

.role-option p {
  font-size: 13px;
  color: var(--md-on-surface-variant);
  margin: 0;
}

:deep(.el-dialog) {
  border-radius: var(--md-shape-xl);
}

:deep(.el-dialog__header) {
  padding: 24px 24px 16px;
}

:deep(.el-dialog__body) {
  padding: 0 24px;
}

:deep(.el-dialog__footer) {
  padding: 16px 24px 24px;
}
</style>
