export interface User {
  id: string;
  email: string;
  full_name?: string | null;
  role_id: number; // 1: Admin, 2: User
  avatar_url?: string | null;
  is_active?: boolean;
  created_at?: string;
}

export interface Role {
  id: number;
  name: string;
  description?: string | null;
}

export interface BoundingBox {
  xmin: number;
  ymin: number;
  xmax: number;
  ymax: number;
}

export interface DetectionObject {
  name: string;
  label_vi: string;
  confidence: number;
  box: BoundingBox;
}

export interface DetectionResult {
  id: string;
  user_id?: string;
  summary: string;
  raw_detected_text?: string;
  objects: DetectionObject[];
  json_data?: DetectionObject[];
  ocr_json_data?: DetectionObject[];
  image_url: string;
  annotated_image_url?: string;
  audio_url: string;
  status: string;
  created_at: string;
}

export type DetectionRecord = DetectionResult;

export interface Category {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  product_count?: number;
}

export interface Product {
  id: string;
  category_id?: string | null;
  name: string;
  class_name?: string | null;
  sku?: string | null;
  price: number;
  stock_quantity: number;
  image_url?: string | null;
  description?: string | null;
  is_available: boolean;
  created_at?: string;
}

export interface CartItem {
  id: string;
  product_id: string;
  product_name: string;
  product_price: number;
  product_image?: string;
  class_name?: string;
  record_id?: string | null;
  quantity: number;
  item_total: number;
}

export interface CartResponse {
  items: CartItem[];
  total_items: number;
  total_amount: number;
}

export interface OrderItem {
  id: string;
  order_id: string;
  product_id: string;
  product_name: string;
  quantity: number;
  unit_price: number;
}

export interface Order {
  id: string;
  user_id: string;
  total_amount: number;
  shipping_address: string;
  phone_number: string;
  status: "pending" | "paid" | "shipped" | "cancelled" | string;
  audio_confirmation_url?: string | null;
  created_at: string;
  items: OrderItem[];
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface CheckoutRequest {
  shipping_address: string;
  phone_number: string;
}

export interface ProductStats {
  total_products: number;
  available_products: number;
  out_of_stock_products: number;
  total_stock_units: number;
  total_inventory_value: number;
}

export interface OrderStats {
  total_orders: number;
  total_revenue: number;
  pending_orders: number;
  paid_orders: number;
  shipped_orders: number;
  cancelled_orders: number;
}

