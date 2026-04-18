// 用户相关类型，对应后端 schemas/user.py。

export interface User {
  id: number
  username: string
  email: string
  full_name: string | null
  is_active: boolean
  is_admin: boolean
  created_at: string
}
