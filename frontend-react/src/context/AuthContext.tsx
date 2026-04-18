// 全局认证状态管理。
// 用 React Context 在整个应用共享登录状态（user、token），
// 对应 Vue 版本的 composables/useAuth.js，但改用 Context + Provider 模式。

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  type ReactNode,
} from 'react'
import type { User } from '../types'
import { authApi } from '../api'

// ── Context 的数据结构 ────────────────────────────────────────────────────

interface AuthContextValue {
  user: User | null
  isLoggedIn: boolean
  // 初始化时从后端拉取用户信息，loading 期间避免渲染需要登录的页面
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  register: (username: string, email: string, password: string, fullName?: string) => Promise<void>
  logout: () => void
}

// createContext 需要一个默认值，这里传 null，
// 在 useAuth() 里做非空校验，防止在 Provider 外部使用
const AuthContext = createContext<AuthContextValue | null>(null)

// ── Provider 组件 ─────────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  // loading = true 表示正在从后端验证 token，此时不应跳转到登录页
  const [loading, setLoading] = useState(true)

  // 应用启动时，如果 localStorage 里有 token，就去后端验证并拉取用户信息。
  // 这样刷新页面后不会丢失登录状态。
  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      setLoading(false)
      return
    }

    authApi.me()
      .then(me => setUser(me))
      .catch(() => {
        // token 过期或无效，清掉本地缓存，下次访问会跳到登录页
        localStorage.removeItem('access_token')
      })
      .finally(() => setLoading(false))
  }, []) // 空依赖数组 = 只在组件挂载时执行一次，对应 Vue 的 onMounted

  // isLoggedIn 直接读 localStorage，不依赖 user 状态，
  // 避免刷新后 user 还没加载完就被判定为未登录
  const isLoggedIn = !!localStorage.getItem('access_token')

  // useCallback 缓存函数引用，避免每次渲染都创建新函数。
  // 对应 Vue 中 methods 里的方法（Vue methods 天然不会每次渲染重建）。
  const login = useCallback(async (username: string, password: string) => {
    const data = await authApi.login(username, password)
    localStorage.setItem('access_token', data.access_token)
    // 登录成功后立即拉取用户信息，填充 user 状态
    const me = await authApi.me()
    setUser(me)
  }, [])

  const register = useCallback(async (
    username: string,
    email: string,
    password: string,
    fullName?: string,
  ) => {
    await authApi.register(username, email, password, fullName)
    // 注册成功后自动登录，复用 login 逻辑
    await login(username, password)
  }, [login])

  const logout = useCallback(() => {
    localStorage.removeItem('access_token')
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, isLoggedIn, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

// ── useAuth hook ──────────────────────────────────────────────────────────

// 所有需要访问登录状态的组件都通过这个 hook 获取，
// 不需要手动传 props，对应 Vue 里 const { user } = useAuth()
export function useAuth() {
  const ctx = useContext(AuthContext)
  // 如果在 AuthProvider 外部调用，ctx 为 null，直接报错提示开发者
  if (!ctx) throw new Error('useAuth 必须在 AuthProvider 内部使用')
  return ctx
}
