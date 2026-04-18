// 路由守卫组件。
// 检查 localStorage 是否有 token，没有则跳转到登录页，
// 对应 Vue Router 里 router.beforeEach 的逻辑。

import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

interface Props {
  children: React.ReactNode
}

export default function ProtectedRoute({ children }: Props) {
  const { isLoggedIn, loading } = useAuth()

  // token 验证期间不渲染任何内容，避免页面闪烁后跳转
  if (loading) return null

  // 未登录则跳到登录页，replace 避免回退时再次触发守卫
  if (!isLoggedIn) return <Navigate to="/login" replace />

  return <>{children}</>
}
