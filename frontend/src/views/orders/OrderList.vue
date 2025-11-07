<template>
  <div class="max-w-7xl mx-auto">
    <h1 class="text-3xl font-bold mb-8 flex items-center">
      <el-icon :size="32" class="mr-3 text-primary-600"><List /></el-icon>
      我的订单
    </h1>

    <!-- Status Tabs -->
    <el-card shadow="never" class="mb-6">
      <el-radio-group v-model="currentStatus" @change="fetchOrders" class="status-tabs">
        <el-radio-button label="all">
          <el-icon class="mr-2"><Tickets /></el-icon>
          全部订单
        </el-radio-button>
        <el-radio-button label="pending">
          <el-icon class="mr-2"><Clock /></el-icon>
          待支付
        </el-radio-button>
        <el-radio-button label="paid">
          <el-icon class="mr-2"><Check /></el-icon>
          已支付
        </el-radio-button>
        <el-radio-button label="shipped">
          <el-icon class="mr-2"><Van /></el-icon>
          已发货
        </el-radio-button>
        <el-radio-button label="canceled">
          <el-icon class="mr-2"><Close /></el-icon>
          已取消
        </el-radio-button>
      </el-radio-group>
    </el-card>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-20">
      <el-icon class="is-loading" :size="50" color="primary">
        <Loading />
      </el-icon>
    </div>

    <!-- Empty State -->
    <el-empty
      v-else-if="!loading && orders.length === 0"
      description="暂无订单"
      :image-size="200"
    >
      <el-button type="primary" @click="router.push('/products')">
        <el-icon class="mr-2"><Box /></el-icon>
        去购物
      </el-button>
    </el-empty>

    <!-- Orders List -->
    <div v-else class="space-y-4">
      <el-card
        v-for="order in orders"
        :key="order.id"
        shadow="hover"
        class="order-card"
      >
        <!-- Order Header -->
        <template #header>
          <div class="flex justify-between items-center">
            <div class="flex items-center gap-6">
              <div>
                <span class="text-sm text-gray-500">订单号: </span>
                <span class="text-sm font-mono font-semibold">{{ formatOrderId(order.id) }}</span>
              </div>
              <div>
                <span class="text-sm text-gray-500">下单时间: </span>
                <span class="text-sm">{{ formatDate(order.created_at) }}</span>
              </div>
            </div>
            <div>
              <el-tag :type="getStatusType(order.order_status)" size="large">
                {{ getStatusLabel(order.order_status) }}
              </el-tag>
            </div>
          </div>
        </template>

        <!-- Order Body -->
        <div>
          <!-- Order Items Placeholder -->
          <div class="mb-4 p-4 bg-gray-50 rounded-lg">
            <div class="text-sm text-gray-600 mb-2">订单商品</div>
            <div class="text-xs text-gray-500">
              <el-icon class="mr-1"><InfoFilled /></el-icon>
              订单详情功能开发中，暂不显示具体商品列表
            </div>
          </div>

          <!-- Order Summary -->
          <div class="flex justify-between items-center pt-4 border-t border-gray-200">
            <div class="flex items-center gap-4 text-sm text-gray-600">
              <el-icon :size="18"><Money /></el-icon>
              <span>订单总额</span>
            </div>
            <div class="text-right">
              <div class="text-2xl font-bold text-primary-600">
                ¥{{ order.total_amount.toFixed(2) }}
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex justify-end gap-3 mt-4 pt-4 border-t border-gray-200">
            <el-button @click="viewOrderDetail(order.id)" :icon="View">
              查看详情
            </el-button>
            <el-button
              v-if="order.order_status === 'pending'"
              type="primary"
              :icon="CreditCard"
              @click="handlePay(order.id)"
            >
              去支付
            </el-button>
            <el-button
              v-if="order.order_status === 'pending'"
              type="danger"
              text
              :icon="Close"
              @click="handleCancel(order.id)"
              :loading="cancelingOrders.has(order.id)"
            >
              取消订单
            </el-button>
            <el-button
              v-if="order.order_status === 'shipped'"
              type="success"
              :icon="Check"
              @click="handleConfirmReceipt(order.id)"
            >
              确认收货
            </el-button>
            <el-button
              v-if="['paid', 'shipped'].includes(order.order_status)"
              :icon="ChatDotRound"
              @click="handleContact(order.id)"
            >
              联系客服
            </el-button>
          </div>
        </div>
      </el-card>

      <!-- Pagination -->
      <div v-if="total > pageSize" class="flex justify-center mt-8">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 30, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  List,
  Loading,
  Box,
  Tickets,
  Clock,
  Check,
  Van,
  Close,
  View,
  CreditCard,
  ChatDotRound,
  InfoFilled,
  Money
} from '@element-plus/icons-vue'
import { orderApi } from '@/api/orders'
import type { Order, OrderStatus } from '@/types'

const router = useRouter()

// State
const orders = ref<Order[]>([])
const loading = ref(false)
const currentStatus = ref('all')
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const cancelingOrders = ref<Set<number>>(new Set())

// Methods
const fetchOrders = async () => {
  loading.value = true
  try {
    let response
    if (currentStatus.value === 'all') {
      response = await orderApi.getOrders()
    } else {
      response = await orderApi.getOrdersByStatus(currentStatus.value)
    }
    
    orders.value = Array.isArray(response.data) ? response.data : []
    total.value = orders.value.length
    
    // Apply pagination (client-side for now)
    const start = (currentPage.value - 1) * pageSize.value
    const end = start + pageSize.value
    orders.value = orders.value.slice(start, end)
  } catch (error: any) {
    console.error('Failed to fetch orders:', error)
    ElMessage.error('获取订单列表失败')
    orders.value = []
  } finally {
    loading.value = false
  }
}

const formatOrderId = (id: number) => {
  return `ORD${String(id).padStart(8, '0')}`
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getStatusType = (status: string) => {
  const types: Record<string, any> = {
    'pending': 'warning',
    'paid': 'primary',
    'shipped': 'success',
    'canceled': 'info'
  }
  return types[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    'pending': '待支付',
    'paid': '已支付',
    'shipped': '已发货',
    'canceled': '已取消'
  }
  return labels[status] || status
}

const viewOrderDetail = (orderId: number) => {
  ElMessage.info('订单详情页面开发中...')
  // router.push(`/orders/${orderId}`)
}

const handlePay = (orderId: number) => {
  ElMessage.info('支付功能开发中...')
  // TOD: Implement payment
}

const handleCancel = async (orderId: number) => {
  try {
    await ElMessageBox.confirm('确定要取消此订单吗？', '取消订单', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    cancelingOrders.value.add(orderId)
    try {
      await orderApi.cancelOrder(orderId)
      ElMessage.success('订单已取消')
      await fetchOrders()
    } finally {
      cancelingOrders.value.delete(orderId)
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      const message = error.response?.data?.detail || '取消订单失败'
      ElMessage.error(message)
    }
  }
}

const handleConfirmReceipt = (orderId: number) => {
  ElMessage.info('确认收货功能开发中...')
  // TOD: Implement confirm receipt
}

const handleContact = (orderId: number) => {
  ElMessage.info('客服功能开发中...')
  // TOD: Implement contact customer service
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchOrders()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  fetchOrders()
}

// Initialize
onMounted(() => {
  fetchOrders()
})
</script>

<style scoped>
.order-card {
  transition: all 0.3s ease;
}

.order-card:hover {
  border-color: #0ea5e9;
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.15) !important;
}

:deep(.el-card) {
  border-radius: 12px !important;
  border: 1px solid #e5e7eb !important;
}

:deep(.el-card__header) {
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  padding: 16px 24px !important;
}

:deep(.el-card__body) {
  padding: 24px !important;
}

:deep(.status-tabs) {
  width: 100%;
  display: flex;
  justify-content: space-around;
}

:deep(.status-tabs .el-radio-button__inner) {
  border-radius: 8px !important;
  padding: 12px 24px !important;
  font-weight: 500;
  border: 1.5px solid #e5e7eb !important;
  transition: all 0.2s ease;
}

:deep(.status-tabs .el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background-color: #0ea5e9 !important;
  border-color: #0ea5e9 !important;
  color: white !important;
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.3) !important;
}

:deep(.el-button) {
  border-radius: 8px;
  transition: all 0.2s ease;
}

:deep(.el-button:hover) {
  transform: translateY(-1px);
}

:deep(.el-tag--large) {
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  border-radius: 8px;
}
</style>
