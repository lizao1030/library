<template>
  <div class="statistics-container">
    <!-- 筛选区域 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item label="年份">
          <el-date-picker
            v-model="filterForm.year"
            type="year"
            placeholder="选择年份"
            format="YYYY"
            value-format="YYYY"
            style="width: 120px"
          />
        </el-form-item>
        <el-form-item label="统计周期">
          <el-select v-model="filterForm.period" style="width: 120px">
            <el-option label="按月" value="month" />
            <el-option label="按季度" value="quarter" />
            <el-option label="按年" value="year" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchStatistics">
            <el-icon><Refresh /></el-icon>刷新
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 总体统计卡片 -->
    <el-row :gutter="20" class="stat-cards">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value">{{ totalStats.total_borrows || 0 }}</div>
          <div class="stat-label">年度总借阅</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value">{{ totalStats.total_returns || 0 }}</div>
          <div class="stat-label">年度归还</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card warning">
          <div class="stat-value">{{ totalStats.current_borrowed || 0 }}</div>
          <div class="stat-label">当前借阅中</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card danger">
          <div class="stat-value">{{ totalStats.overdue_rate || 0 }}%</div>
          <div class="stat-label">逾期率</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 借阅趋势图表 -->
    <el-card class="chart-card">
      <template #header>
        <div class="card-header">
          <span>借阅趋势</span>
          <el-button type="primary" size="small" @click="exportBorrowStats">
            <el-icon><Download /></el-icon>导出借阅数据
          </el-button>
        </div>
      </template>
      <div class="chart-container" v-loading="loading">
        <div class="simple-chart">
          <div class="chart-bars">
            <div
              v-for="item in periodStats"
              :key="item.period"
              class="chart-bar-wrapper"
            >
              <div class="chart-bar" :style="{ height: getBarHeight(item.count) + '%' }">
                <span class="bar-value">{{ item.count }}</span>
              </div>
              <span class="bar-label">{{ item.period_name }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <el-row :gutter="20">
      <!-- 图书借阅排行榜 -->
      <el-col :span="12">
        <el-card class="ranking-card">
          <template #header>
            <span>图书借阅排行榜</span>
          </template>
          <el-table :data="bookRanking" v-loading="loading" stripe size="small">
            <el-table-column prop="rank" label="排名" width="60">
              <template #default="{ row }">
                <el-tag :type="getRankType(row.rank)" size="small">{{ row.rank }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="title" label="书名" min-width="150" show-overflow-tooltip />
            <el-table-column prop="author" label="作者" width="100" show-overflow-tooltip />
            <el-table-column prop="borrow_count" label="借阅次数" width="90" />
          </el-table>
        </el-card>
      </el-col>

      <!-- 活跃用户排行榜 -->
      <el-col :span="12">
        <el-card class="ranking-card">
          <template #header>
            <div class="card-header">
              <span>活跃用户排行榜</span>
              <el-button type="primary" size="small" @click="exportUserStats">
                <el-icon><Download /></el-icon>导出用户数据
              </el-button>
            </div>
          </template>
          <el-table :data="userRanking" v-loading="userLoading" stripe size="small">
            <el-table-column prop="rank" label="排名" width="60">
              <template #default="{ row }">
                <el-tag :type="getRankType(row.rank)" size="small">{{ row.rank }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="username" label="用户名" min-width="100" />
            <el-table-column prop="email" label="邮箱" min-width="150" show-overflow-tooltip />
            <el-table-column prop="borrow_count" label="借阅次数" width="90" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 用户统计卡片 -->
    <el-card class="user-stats-card">
      <template #header>
        <span>用户统计</span>
      </template>
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="user-stat-item">
            <div class="user-stat-value">{{ userStats.total_users || 0 }}</div>
            <div class="user-stat-label">总用户数</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="user-stat-item">
            <div class="user-stat-value success">{{ userStats.active_users || 0 }}</div>
            <div class="user-stat-label">活跃用户</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="user-stat-item">
            <div class="user-stat-value warning">{{ userStats.admin_count || 0 }}</div>
            <div class="user-stat-label">管理员</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="user-stat-item">
            <div class="user-stat-value primary">{{ userStats.reader_count || 0 }}</div>
            <div class="user-stat-label">读者</div>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import api from '@/api'
import { ElMessage } from 'element-plus'
import { Refresh, Download } from '@element-plus/icons-vue'

const loading = ref(false)
const userLoading = ref(false)

// 筛选表单
const filterForm = reactive({
  year: new Date().getFullYear().toString(),
  period: 'month'
})

// 统计数据
const totalStats = ref({})
const periodStats = ref([])
const bookRanking = ref([])
const userRanking = ref([])
const userStats = ref({})

// 计算最大借阅量用于图表高度
const maxCount = computed(() => {
  if (periodStats.value.length === 0) return 1
  return Math.max(...periodStats.value.map(item => item.count), 1)
})

// 获取柱状图高度百分比
const getBarHeight = (count) => {
  return Math.max((count / maxCount.value) * 100, 5)
}

// 获取排名标签类型
const getRankType = (rank) => {
  if (rank === 1) return 'danger'
  if (rank === 2) return 'warning'
  if (rank === 3) return 'success'
  return 'info'
}

// 获取借阅统计
const fetchBorrowStatistics = async () => {
  loading.value = true
  try {
    const res = await api.get('/statistics/borrows', {
      params: {
        year: filterForm.year,
        period: filterForm.period,
        limit: 10
      }
    })
    totalStats.value = res.total_stats || {}
    periodStats.value = res.period_stats || []
    bookRanking.value = res.book_ranking || []
  } catch (error) {
    console.error('获取借阅统计失败:', error)
  } finally {
    loading.value = false
  }
}

// 获取用户统计
const fetchUserStatistics = async () => {
  userLoading.value = true
  try {
    const res = await api.get('/statistics/users', {
      params: {
        year: filterForm.year,
        limit: 10
      }
    })
    userRanking.value = res.user_ranking || []
    userStats.value = res.user_stats || {}
  } catch (error) {
    console.error('获取用户统计失败:', error)
  } finally {
    userLoading.value = false
  }
}

// 获取所有统计数据
const fetchStatistics = () => {
  fetchBorrowStatistics()
  fetchUserStatistics()
}

// 导出借阅数据
const exportBorrowStats = async () => {
  try {
    const response = await api.get('/statistics/export/borrows', {
      params: { year: filterForm.year },
      responseType: 'blob'
    })
    downloadFile(response, `borrow_statistics_${filterForm.year}.csv`)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

// 导出用户数据
const exportUserStats = async () => {
  try {
    const response = await api.get('/statistics/export/users', {
      params: { year: filterForm.year },
      responseType: 'blob'
    })
    downloadFile(response, `user_statistics_${filterForm.year}.csv`)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

// 下载文件
const downloadFile = (data, filename) => {
  const blob = new Blob([data], { type: 'text/csv;charset=utf-8' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

onMounted(() => {
  fetchStatistics()
})
</script>

<style scoped>
.statistics-container {
  padding: 20px;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.stat-cards {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  padding: 20px;
}

.stat-card .stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #409EFF;
}

.stat-card.warning .stat-value {
  color: #E6A23C;
}

.stat-card.danger .stat-value {
  color: #F56C6C;
}

.stat-card .stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 10px;
}

.chart-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  height: 300px;
  padding: 20px;
}

.simple-chart {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chart-bars {
  flex: 1;
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  padding-bottom: 30px;
  border-bottom: 1px solid #eee;
}

.chart-bar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  max-width: 60px;
}

.chart-bar {
  width: 40px;
  background: linear-gradient(180deg, #409EFF 0%, #79bbff 100%);
  border-radius: 4px 4px 0 0;
  min-height: 20px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding-top: 5px;
  transition: height 0.3s ease;
}

.bar-value {
  font-size: 12px;
  color: #fff;
  font-weight: bold;
}

.bar-label {
  margin-top: 10px;
  font-size: 12px;
  color: #606266;
  text-align: center;
}

.ranking-card {
  margin-bottom: 20px;
}

.user-stats-card {
  margin-top: 20px;
}

.user-stat-item {
  text-align: center;
  padding: 20px;
}

.user-stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.user-stat-value.success {
  color: #67C23A;
}

.user-stat-value.warning {
  color: #E6A23C;
}

.user-stat-value.primary {
  color: #409EFF;
}

.user-stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 10px;
}
</style>
