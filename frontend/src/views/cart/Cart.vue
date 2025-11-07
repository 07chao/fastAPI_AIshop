<template>
  <div class="max-w-7xl mx-auto">
    <h1 class="text-3xl font-bold mb-8 flex items-center">
      <el-icon :size="32" class="mr-3 text-primary-600"><ShoppingCart /></el-icon>
      购物车
    </h1>

    <!-- Loading -->
    <div v-if="cartStore.loading && cartItems.length === 0" class="flex justify-center py-20">
      <el-icon class="is-loading" :size="50" color="primary">
        <Loading />
      </el-icon>
    </div>

    <!-- Empty Cart -->
    <el-empty 
      v-else-if="!cartStore.loading && cartItems.length === 0" 
      description="购物车空空如也~"
      :image-size="200"
    >
      <el-button type="primary" @click="router.push('/products')" size="large">
        <el-icon class="mr-2"><Box /></el-icon>
        去逛逛
      </el-button>
    </el-empty>

    <!-- Cart Items -->
    <div v-else>
      <div class="grid lg:grid-cols-3 gap-6">
        <!-- Left: Cart Items List -->
        <div class="lg:col-span-2 space-y-4">
          <el-card
            v-for="item in cartItemsWithProducts"
            :key="item.cartItem.id"
            shadow="hover"
            class="cart-item-card"
          >
            <div class="flex gap-4">
              <!-- Product Image -->
              <div 
                class="w-32 h-32 flex-shrink-0 bg-gray-100 rounded-lg overflow-hidden cursor-pointer"
                @click="goToProduct(item.product.id)"
              >
                <el-image
                  :src="item.product.image_url || 'https://via.placeholder.com/200'"
                  fit="cover"
                  class="w-full h-full"
                  lazy
                >
                  <template #error>
                    <div class="flex items-center justify-center h-full bg-gray-100">
                      <el-icon :size="40" class="text-gray-300">
                        <Picture />
                      </el-icon>
                    </div>
                  </template>
                </el-image>
              </div>

              <!-- Product Info -->
              <div class="flex-1 flex flex-col">
                <div class="flex justify-between">
                  <div class="flex-1">
                    <h3 
                      class="text-lg font-semibold text-gray-900 mb-2 cursor-pointer hover:text-primary-600 transition-colors line-clamp-2"
                      @click="goToProduct(item.product.id)"
                    >
                      {{ item.product.name }}
                    </h3>
                    <p class="text-sm text-gray-500 mb-3 line-clamp-2">
                      {{ item.product.description }}
                    </p>
                  </div>
                  <div class="ml-4">
                    <el-button
                      type="danger"
                      text
                      :icon="Delete"
                      @click="handleRemove(item.cartItem.id)"
                      :loading="removingItems.has(item.cartItem.id)"
                    >
                      删除
                    </el-button>
                  </div>
                </div>

                <div class="flex items-center justify-between mt-auto">
                  <!-- Price -->
                  <div class="flex items-baseline">
                    <span class="text-2xl font-bold text-primary-600">
                      ¥{{ item.product.price.toFixed(2) }}
                    </span>
                    <span class="text-sm text-gray-500 ml-2">× {{ item.cartItem.quantity }}</span>
                  </div>

                  <!-- Quantity Controls -->
                  <div class="flex items-center gap-3">
                    <span class="text-sm text-gray-600">数量:</span>
                    <el-input-number
                      :model-value="item.cartItem.quantity"
                      :min="1"
                      :max="item.product.stock"
                      @change="(val) => handleQuantityChange(item.cartItem.id, val)"
                      size="small"
                      :disabled="updatingItems.has(item.cartItem.id)"
                    />
                  </div>
                </div>

                <!-- Stock Warning -->
                <div v-if="item.product.stock < item.cartItem.quantity" class="mt-2">
                  <el-alert
                    type="warning"
                    :closable="false"
                    show-icon
                  >
                    <template #title>
                      <span class="text-sm">库存不足，仅剩 {{ item.product.stock }} 件</span>
                    </template>
                  </el-alert>
                </div>
              </div>
            </div>
          </el-card>

          <!-- Batch Actions -->
          <div class="flex justify-between items-center p-4 bg-white rounded-lg border border-gray-200">
            <div class="flex items-center gap-4">
              <el-checkbox v-model="selectAll" @change="handleSelectAll">
                全选
              </el-checkbox>
              <span class="text-sm text-gray-600">
                已选 <span class="font-semibold text-primary-600">{{ selectedCount }}</span> 件商品
              </span>
            </div>
            <el-button
              type="danger"
              text
              :icon="Delete"
              @click="handleBatchRemove"
              :disabled="selectedCount === 0"
            >
              删除选中
            </el-button>
          </div>
        </div>

        <!-- Right: Order Summary -->
        <div class="lg:col-span-1">
          <el-card shadow="hover" class="sticky top-20">
            <template #header>
              <div class="font-semibold text-lg">订单摘要</div>
            </template>

            <div class="space-y-4">
              <div class="flex justify-between text-sm">
                <span class="text-gray-600">商品件数</span>
                <span class="font-semibold">{{ cartStore.totalItems }} 件</span>
              </div>

              <div class="flex justify-between text-sm">
                <span class="text-gray-600">商品总价</span>
                <span class="font-semibold">¥{{ subtotal.toFixed(2) }}</span>
              </div>

              <div class="flex justify-between text-sm">
                <span class="text-gray-600">运费</span>
                <span class="font-semibold text-green-600">
                  {{ subtotal >= 99 ? '免运费' : '¥10.00' }}
                </span>
              </div>

              <el-divider />

              <div class="flex justify-between items-baseline">
                <span class="text-gray-900 font-semibold">总计</span>
                <div class="text-right">
                  <div class="text-3xl font-bold text-primary-600">
                    ¥{{ total.toFixed(2) }}
                  </div>
                  <div v-if="subtotal < 99" class="text-xs text-gray-500 mt-1">
                    再购 ¥{{ (99 - subtotal).toFixed(2) }} 即可免运费
                  </div>
                </div>
              </div>

              <el-button
                type="primary"
                size="large"
                class="w-full mt-4"
                :disabled="cartItems.length === 0 || hasOutOfStock"
                @click="handleCheckout"
              >
                <el-icon class="mr-2"><CreditCard /></el-icon>
                结算 ({{ selectedCount }})
              </el-button>

              <div v-if="hasOutOfStock" class="text-center">
                <el-text type="warning" size="small">
                  部分商品库存不足，请调整数量
                </el-text>
              </div>

              <!-- Benefits -->
              <div class="mt-6 pt-6 border-t border-gray-200 space-y-3">
                <div class="flex items-start text-sm">
                  <el-icon class="text-green-600 mr-2 mt-0.5"><CircleCheck /></el-icon>
                  <span class="text-gray-600">7天无理由退换</span>
                </div>
                <div class="flex items-start text-sm">
                  <el-icon class="text-blue-600 mr-2 mt-0.5"><Van /></el-icon>
                  <span class="text-gray-600">满99元免运费</span>
                </div>
                <div class="flex items-start text-sm">
                  <el-icon class="text-purple-600 mr-2 mt-0.5"><Service /></el-icon>
                  <span class="text-gray-600">正品保障</span>
                </div>
              </div>
            </div>
          </el-card>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import {
  ShoppingCart,
  Delete,
  Picture,
  Loading,
  Box,
  CreditCard,
  CircleCheck,
  Van,
  Service
} from '@element-plus/icons-vue'
import { useCartStore } from '@/stores/cart'
import { productApi } from '@/api/products'
import type { Product } from '@/types'

const router = useRouter()
const cartStore = useCartStore()

// State
const products = ref<Map<number, Product>>(new Map())
const updatingItems = ref<Set<number>>(new Set())
const removingItems = ref<Set<number>>(new Set())
const selectedItems = ref<Set<number>>(new Set())
const selectAll = ref(false)

// Computed
const cartItems = computed(() => cartStore.cartItems)

const cartItemsWithProducts = computed(() => {
  return cartItems.value
    .map(cartItem => {
      const product = products.value.get(cartItem.product_id)
      if (!product) return null
      return { cartItem, product }
    })
    .filter(item => item !== null) as Array<{ cartItem: any, product: Product }>
})

const selectedCount = computed(() => selectedItems.value.size)

const subtotal = computed(() => {
  return cartItemsWithProducts.value.reduce((sum, item) => {
    if (selectedItems.value.has(item.cartItem.id)) {
      return sum + (item.product.price * item.cartItem.quantity)
    }
    return sum
  }, 0)
})

const shippingFee = computed(() => {
  return subtotal.value >= 99 ? 0 : 10
})

const total = computed(() => {
  return subtotal.value + shippingFee.value
})

const hasOutOfStock = computed(() => {
  return cartItemsWithProducts.value.some(
    item => item.product.stock < item.cartItem.quantity
  )
})

// Methods
const fetchProducts = async () => {
  const productIds = [...new Set(cartItems.value.map(item => item.product_id))]
  
  try {
    const fetchPromises = productIds.map(id => productApi.getProduct(id))
    const responses = await Promise.all(fetchPromises)
    
    responses.forEach(response => {
      if (response.data) {
        products.value.set(response.data.id, response.data)
      }
    })
  } catch (error) {
    console.error('Failed to fetch products:', error)
    ElMessage.error('加载商品信息失败')
  }
}

const handleQuantityChange = async (cartItemId: number, quantity: number | null) => {
  if (quantity === null || quantity < 1) return
  
  updatingItems.value.add(cartItemId)
  try {
    await cartStore.updateCartItem(cartItemId, quantity)
  } finally {
    updatingItems.value.delete(cartItemId)
  }
}

const handleRemove = async (cartItemId: number) => {
  try {
    await ElMessageBox.confirm('确定要移除该商品吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    removingItems.value.add(cartItemId)
    try {
      await cartStore.removeFromCart(cartItemId)
      selectedItems.value.delete(cartItemId)
    } finally {
      removingItems.value.delete(cartItemId)
    }
  } catch (error) {
    // User cancelled
  }
}

const handleSelectAll = (value: boolean) => {
  if (value) {
    cartItems.value.forEach(item => {
      selectedItems.value.add(item.id)
    })
  } else {
    selectedItems.value.clear()
  }
}

const handleBatchRemove = async () => {
  if (selectedCount.value === 0) return
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedCount.value} 件商品吗？`,
      '批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const promises = Array.from(selectedItems.value).map(id => 
      cartStore.removeFromCart(id)
    )
    
    await Promise.all(promises)
    selectedItems.value.clear()
    selectAll.value = false
  } catch (error) {
    // User cancelled
  }
}

const handleCheckout = () => {
  if (selectedCount.value === 0) {
    ElMessage.warning('请先选择要结算的商品')
    return
  }
  
  if (hasOutOfStock.value) {
    ElMessage.warning('部分商品库存不足，请调整数量')
    return
  }
  
  ElMessage.info('结算功能开发中...')
  // TOD: Implement checkout
  // router.push('/checkout')
}

const goToProduct = (productId: number) => {
  router.push(`/products/${productId}`)
}

// Initialize
onMounted(async () => {
  await cartStore.fetchCartItems()
  await fetchProducts()
  
  // Select all items by default
  cartItems.value.forEach(item => {
    selectedItems.value.add(item.id)
  })
  selectAll.value = true
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.cart-item-card {
  transition: all 0.3s ease;
}

.cart-item-card:hover {
  border-color: #0ea5e9;
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.15);
}

:deep(.el-card) {
  border-radius: 12px !important;
  border: 1px solid #e5e7eb !important;
}

:deep(.el-card__header) {
  border-bottom: 1px solid #e5e7eb;
  padding: 20px 24px !important;
}

:deep(.el-card__body) {
  padding: 24px !important;
}

:deep(.el-button) {
  border-radius: 8px;
  transition: all 0.2s ease;
}

:deep(.el-button:hover) {
  transform: translateY(-1px);
}

:deep(.el-input-number) {
  width: 120px;
}

:deep(.el-input-number .el-input__wrapper) {
  border-radius: 8px !important;
  border: 1.5px solid #e5e7eb !important;
  box-shadow: none !important;
}

:deep(.el-checkbox__label) {
  font-weight: 500;
  color: #374151;
}

:deep(.el-divider) {
  margin: 16px 0 !important;
}
</style>
