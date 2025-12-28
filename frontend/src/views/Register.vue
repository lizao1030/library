<template>
  <div class="register-page">
    <!-- 左侧品牌区域 -->
    <div class="brand-section">
      <div class="brand-content">
        <div class="brand-icon">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M15 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm-9-2V7H4v3H1v2h3v3h2v-3h3v-2H6zm9 4c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
          </svg>
        </div>
        <h1 class="brand-title">加入我们</h1>
        <p class="brand-subtitle">开启您的阅读之旅</p>
      </div>
      <div class="brand-decoration">
        <div class="circle circle-1"></div>
        <div class="circle circle-2"></div>
        <div class="circle circle-3"></div>
      </div>
    </div>

    <!-- 右侧注册区域 -->
    <div class="register-section">
      <div class="register-container">
        <div class="register-header">
          <h2 class="register-title">创建账户</h2>
          <p class="register-subtitle">填写以下信息完成注册</p>
        </div>

        <el-form :model="form" :rules="rules" ref="formRef" class="register-form">
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
              v-model="form.email" 
              placeholder="邮箱"
              size="large"
              class="md-input-field"
            >
              <template #prefix>
                <el-icon class="input-icon"><Message /></el-icon>
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

          <div class="form-field">
            <el-input 
              v-model="form.confirmPassword" 
              type="password" 
              placeholder="确认密码"
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
            @click="handleRegister" 
            :loading="loading" 
            class="register-button"
            size="large"
          >
            {{ loading ? '注册中...' : '创建账户' }}
          </el-button>
        </el-form>

        <div class="register-footer">
          <span class="footer-text">已有账户？</span>
          <router-link to="/login" class="login-link">立即登录</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'
import { ElMessage } from 'element-plus'
import { User, Lock, Message } from '@element-plus/icons-vue'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度为3-50个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const handleRegister = async () => {
  await formRef.value.validate()
  loading.value = true
  try {
    await api.post('/auth/register', {
      username: form.username,
      email: form.email,
      password: form.password
    })
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  background: var(--md-surface);
}

.brand-section {
  flex: 1;
  background: linear-gradient(135deg, var(--md-tertiary) 0%, #B8879A 100%);
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
}

.brand-subtitle {
  font-size: 16px;
  opacity: 0.9;
  margin: 0;
}

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

.circle-1 { width: 300px; height: 300px; top: -100px; left: -100px; }
.circle-2 { width: 200px; height: 200px; bottom: -50px; right: -50px; }
.circle-3 { width: 150px; height: 150px; bottom: 30%; right: 20%; }

.register-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
}

.register-container {
  width: 100%;
  max-width: 400px;
}

.register-header {
  margin-bottom: 32px;
}

.register-title {
  font-size: 28px;
  font-weight: 500;
  color: var(--md-on-surface);
  margin: 0 0 8px 0;
}

.register-subtitle {
  font-size: 14px;
  color: var(--md-on-surface-variant);
  margin: 0;
}

.register-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
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
}

.md-input-field :deep(.el-input__wrapper:hover) {
  background: var(--md-surface-container-high);
}

.md-input-field :deep(.el-input__wrapper.is-focus) {
  border-bottom: 2px solid var(--md-primary);
}

.md-input-field :deep(.el-input__inner) {
  height: 100%;
  font-size: 16px;
}

.input-icon {
  color: var(--md-on-surface-variant);
  font-size: 20px;
}

.register-button {
  height: 56px;
  border-radius: var(--md-shape-full);
  font-size: 16px;
  font-weight: 500;
  margin-top: 8px;
  background: var(--md-primary);
  border: none;
}

.register-button:hover {
  box-shadow: var(--md-elevation-2);
}

.register-footer {
  margin-top: 32px;
  text-align: center;
}

.footer-text {
  font-size: 14px;
  color: var(--md-on-surface-variant);
}

.login-link {
  font-size: 14px;
  color: var(--md-primary);
  text-decoration: none;
  font-weight: 500;
  margin-left: 4px;
}

.login-link:hover {
  text-decoration: underline;
}

@media (max-width: 900px) {
  .brand-section { display: none; }
  .register-section { padding: 24px; }
}
</style>
