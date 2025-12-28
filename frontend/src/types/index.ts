// User Types
export enum UserRole {
  ADMIN = 'admin',
  VENDOR = 'vendor',
  CUSTOMER = 'customer'
}

export interface SensitiveInfo {
  country?: string
  city?: string
  state?: string
  street?: string
  zip_code?: string
}

export interface User {
  id: number
  username: string
  name: string
  surname: string
  email: string
  phone_number: string
  image_url?: string
  sensitive_info?: SensitiveInfo
  role: UserRole
}

export interface UserRegister {
  username: string
  name: string
  surname: string
  email: string
  password: string
  phone_number: string
  role?: UserRole
  sensitive_info?: SensitiveInfo
}

export interface UserLogin {
  email: string
  password: string
}

export interface ChangePassword {
  password: string
  new_password: string
}

export interface AuthResponse {
  accessToken: string
  refreshToken: string
}

// Product Types
export enum CategoryEnum {
  ELECTRONICS = 'electronics',
  FASHION = 'fashion',
  HOME = 'home',
  BOOKS = 'books'
}

export interface Product {
  id: number
  name: string
  description: string
  price: number
  stock: number
  category: CategoryEnum
  image_url?: string
  vendor_id: number
  is_active: boolean
  view_count: number
  created_at: string
  updated_at: string
  average_rating: number // 新增：商品平均评分
  review_count: number // 新增：商品评价总数
}

export interface ProductCreate {
  name: string
  description: string
  price: number
  stock: number
  category: CategoryEnum
  image_url?: string
}

export interface ProductFilter {
  page?: number
  size?: number
  category?: string
  min_price?: number
  max_price?: number
  availability?: boolean
}

// Review Types
export interface Review {
  id: number
  product_id: number
  parent_review_id?: number
  content: string
  rating: number
  created_at: string
  follow_up_reviews?: Review[]
}

export interface ReviewCreate {
  product_id: number
  content: string
  rating: number
}


// Cart Types
export interface CartItem {
  id: number
  product_id: number
  quantity: number
  price: number
  user_id: number
}

export interface CartItemCreate {
  product_id: number
  quantity: number
}

// Order Types
export enum OrderStatus {
  PENDING = 'pending',
  PAID = 'paid',
  SHIPPED = 'shipped',
  CANCELED = 'canceled'
}

export interface Order {
  id: number
  user_id: number
  total_amount: number
  order_status: OrderStatus
  created_at: string
  updated_at: string
}

// Payment Types
export enum PaymentStatus {
  PENDING = 'Pending',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

export interface Payment {
  id: number
  user_id: number
  order_id: number
  amount: number
  status: PaymentStatus
  currency: string
  stripe_session_id: string
  created_at: string
}

// API Response Types
export interface ApiResponse<T> {
  data?: T
  message?: string
  error?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

