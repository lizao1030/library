<template>
  <div class="login-page">
    <!-- 左侧品牌区域 -->
    <div class="brand-section">
      <div class="brand-content">
        <div class="brand-icon">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M18 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM6 4h5v8l-2.5-1.5L6 12V4z"/>
          </svg>
        </div>
        <h1 class="brand-title">图书馆</h1>
        <p class="brand-subtitle">发现知识，探索世界</p>
      </div>
      <div class="brand-decoration">
        <div class="circle circle-1"></div>
        <div class="circle circle-2"></div>
        <div class="circle circle-3"></div>
      </div>
    </div>

    <!-- 右侧登录区域 -->
    <div class="login-section">
      <div class="login-container">
        <div class="login-header">
          <h2 class="login-title">欢迎回来</h2>
          <p class="login-subtitle">登录您的账户以继续</p>
        </div>

        <el-form :model="form" :rules="rules" ref="formRef" class="login-form">
          <div class="form-field">
            <el-input 
              v-model="form.username" 
              placeholder="用户名"
              size="large"
              class="md-input-field"
            >
              <template #prefix>
                <el-icon class="input-icon"><User /></el-icon>
              </template>
            </el-input>
          </div>

          <div class="form-field">
            <el-input 
              v-model="form.password" 
              type="password" 
              placeholder="密码"
              size="large"
              show-password
              class="md-input-field"
            >
              <template #prefix>
                <el-icon class="input-icon"><Lock /></el-icon>
              </template>
            </el-input>
          </div>

          <el-button 
            type="primary" 
            @click="handleLogin" 
            :loading="loading" 
            class="login-button"
            size="large"
          >
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form>

        <div class="login-footer">
          <span class="footer-text">还没有账户？</span>
          <router-link to="/register" class="register-link">创建账户</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import api from '@/api'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  await formRef.value.validate()
  loading.value = true
  try {
    const res = await api.post('/auth/login', form)
    userStore.setToken(res.access_token)
    userStore.setUserInfo(res.user)
    ElMessage.success('登录成功')
    router.push('/')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  background: var(--md-surface);
}

/* 左侧品牌区域 */
.brand-section {
  flex: 1;
  background: linear-gradient(135deg, var(--md-primary) 0%, #9A82DB 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.brand-content {
  text-align: center;
  color: white;
  z-index: 1;
}

.brand-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 24px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: var(--md-shape-xl);
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-icon svg {
  width: 48px;
  height: 48px;
}

.brand-title {
  font-size: 36px;
  font-weight: 500;
  margin: 0 0 8px 0;
  letter-spacing: -0.5px;
}

.brand-subtitle {
  font-size: 16px;
  opacity: 0.9;
  margin: 0;
}

/* 装饰圆圈 */
.brand-decoration {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
}

.circle-1 {
  width: 300px;
  height: 300px;
  top: -100px;
  right: -100px;
}

.circle-2 {
  width: 200px;
  height: 200px;
  bottom: -50px;
  left: -50px;
}

.circle-3 {
  width: 150px;
  height: 150px;
  top: 50%;
  left: 20%;
}

/* 右侧登录区域 */
.login-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
}

.login-container {
  width: 100%;
  max-width: 400px;
}

.login-header {
  margin-bottom: 40px;
}

.login-title {
  font-size: 28px;
  font-weight: 500;
  color: var(--md-on-surface);
  margin: 0 0 8px 0;
}

.login-subtitle {
  font-size: 14px;
  color: var(--md-on-surface-variant);
  margin: 0;
}

/* 表单 */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-field {
  position: relative;
}

.md-input-field :deep(.el-input__wrapper) {
  height: 56px;
  border-radius: var(--md-shape-xs) var(--md-shape-xs) 0 0;
  background: var(--md-surface-container-highest);
  box-shadow: none;
  border: none;
  border-bottom: 1px solid var(--md-on-surface-variant);
  padding: 0 16px;
  transition: all var(--md-motion-duration-short) var(--md-motion-easing-standard);
}

.md-input-field :deep(.el-input__wrapper:hover) {
  background: var(--md-surface-container-high);
}

.md-input-field :deep(.el-input__wrapper.is-focus) {
  border-bottom: 2px solid var(--md-primary);
  background: var(--md-surface-container-highest);
}

.md-input-field :deep(.el-input__inner) {
  height: 100%;
  font-size: 16px;
}

.input-icon {
  color: var(--md-on-surface-variant);
  font-size: 20px;
}

/* 登录按钮 */
.login-button {
  height: 56px;
  border-radius: var(--md-shape-full);
  font-size: 16px;
  font-weight: 500;
  letter-spacing: 0.1px;
  margin-top: 16px;
  background: var(--md-primary);
  border: none;
  transition: all var(--md-motion-duration-medium) var(--md-motion-easing-emphasized);
}

.login-button:hover {
  box-shadow: var(--md-elevation-2);
  transform: translateY(-1px);
}

/* 底部链接 */
.login-footer {
  margin-top: 32px;
  text-align: center;
}

.footer-text {
  font-size: 14px;
  color: var(--md-on-surface-variant);
}

.register-link {
  font-size: 14px;
  color: var(--md-primary);
  text-decoration: none;
  font-weight: 500;
  margin-left: 4px;
}

.register-link:hover {
  text-decoration: underline;
}

/* 响应式 */
@media (max-width: 900px) {
  .brand-section {
    display: none;
  }
  
  .login-section {
    padding: 24px;
  }
}
</style>
