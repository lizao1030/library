<template>
  <div class="app-layout">
    <!-- Navigation Rail (MD3 侧边导航) -->
    <nav class="nav-rail" :class="{ expanded: isExpanded }">
      <div class="nav-header">
        <button class="menu-button" @click="isExpanded = !isExpanded">
          <el-icon><Menu /></el-icon>
        </button>
        <span v-show="isExpanded" class="nav-title">图书馆</span>
      </div>

      <div class="nav-items">
        <router-link 
          v-for="item in navItems" 
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: $route.path === item.path }"
          v-show="!item.adminOnly || userStore.isAdmin()"
        >
          <div class="nav-icon-wrapper">
            <el-icon class="nav-icon"><component :is="item.icon" /></el-icon>
          </div>
          <span class="nav-label">{{ item.label }}</span>
        </router-link>
      </div>

      <div class="nav-footer">
        <div class="user-section" @click="isExpanded = true">
          <div class="user-avatar">
            {{ userStore.userInfo.username?.charAt(0).toUpperCase() }}
          </div>
          <div v-show="isExpanded" class="user-info">
            <span class="user-name">{{ userStore.userInfo.username }}</span>
            <span class="user-role">{{ userStore.isAdmin() ? '管理员' : '读者' }}</span>
          </div>
        </div>
        <button v-show="isExpanded" class="logout-button" @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
          <span>退出登录</span>
        </button>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="main-content">
      <!-- Top App Bar -->
      <header class="top-bar">
        <h1 class="page-title">{{ pageTitle }}</h1>
      </header>

      <!-- Page Content -->
      <div class="page-content">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { Menu, Document, Reading, DataAnalysis, User, SwitchButton } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const isExpanded = ref(false)

const navItems = [
  { path: '/books', label: '图书', icon: Document },
  { path: '/borrows', label: '借阅', icon: Reading },
  { path: '/statistics', label: '统计', icon: DataAnalysis, adminOnly: true },
  { path: '/users', label: '用户', icon: User, adminOnly: true }
]

const pageTitle = computed(() => {
  const titles = {
    '/books': '图书管理',
    '/borrows': '借阅记录',
    '/statistics': '数据统计',
    '/users': '用户管理'
  }
  return titles[route.path] || '图书馆'
})

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
  background: var(--md-surface);
}

/* Navigation Rail */
.nav-rail {
  width: 80px;
  background: var(--md-surface-container);
  display: flex;
  flex-direction: column;
  padding: 12px;
  transition: width var(--md-motion-duration-medium) var(--md-motion-easing-emphasized);
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: 100;
}

.nav-rail.expanded {
  width: 280px;
}

.nav-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px;
  margin-bottom: 8px;
}

.menu-button {
  width: 48px;
  height: 48px;
  border-radius: var(--md-shape-full);
  background: transparent;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--md-on-surface-variant);
  font-size: 24px;
  transition: background var(--md-motion-duration-short) var(--md-motion-easing-standard);
}

.menu-button:hover {
  background: var(--md-surface-container-highest);
}

.nav-title {
  font-size: 22px;
  font-weight: 500;
  color: var(--md-on-surface);
  white-space: nowrap;
}

/* Nav Items */
.nav-items {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 16px;
  height: 56px;
  border-radius: var(--md-shape-full);
  text-decoration: none;
  color: var(--md-on-surface-variant);
  transition: all var(--md-motion-duration-short) var(--md-motion-easing-standard);
}

.nav-rail:not(.expanded) .nav-item {
  justify-content: center;
  padding: 0;
}

.nav-item:hover {
  background: var(--md-surface-container-highest);
}

.nav-item.active {
  background: var(--md-secondary-container);
  color: var(--md-on-secondary-container);
}

.nav-icon-wrapper {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.nav-icon {
  font-size: 24px;
}

.nav-label {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
}

.nav-rail:not(.expanded) .nav-label {
  display: none;
}

/* Nav Footer */
.nav-footer {
  padding-top: 16px;
  border-top: 1px solid var(--md-outline-variant);
  margin-top: auto;
}

.user-section {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: var(--md-shape-lg);
  cursor: pointer;
  transition: background var(--md-motion-duration-short) var(--md-motion-easing-standard);
}

.user-section:hover {
  background: var(--md-surface-container-highest);
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: var(--md-shape-full);
  background: var(--md-primary);
  color: var(--md-on-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 500;
  flex-shrink: 0;
}

.user-info {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--md-on-surface);
  white-space: nowrap;
}

.user-role {
  font-size: 12px;
  color: var(--md-on-surface-variant);
}

.logout-button {
  width: 100%;
  height: 40px;
  margin-top: 8px;
  border-radius: var(--md-shape-full);
  background: transparent;
  border: 1px solid var(--md-outline);
  color: var(--md-on-surface-variant);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all var(--md-motion-duration-short) var(--md-motion-easing-standard);
}

.logout-button:hover {
  background: var(--md-error-container);
  border-color: var(--md-error);
  color: var(--md-error);
}

/* Main Content */
.main-content {
  flex: 1;
  margin-left: 80px;
  transition: margin-left var(--md-motion-duration-medium) var(--md-motion-easing-emphasized);
  display: flex;
  flex-direction: column;
}

.nav-rail.expanded ~ .main-content {
  margin-left: 280px;
}

/* Top Bar */
.top-bar {
  height: 64px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  background: var(--md-surface);
  position: sticky;
  top: 0;
  z-index: 50;
}

.page-title {
  font-size: 22px;
  font-weight: 500;
  color: var(--md-on-surface);
  margin: 0;
}

/* Page Content */
.page-content {
  flex: 1;
  padding: 24px;
  background: var(--md-surface-container-lowest);
}
</style>
