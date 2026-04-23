// 应用路由总装。
// 首页（/）独立全屏显示，不带侧边栏。
// 进入工单系统或 AI 系统后才显示对应的侧边栏布局。

import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom'

import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'

import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import HomePage from './pages/home/HomePage'

import TicketsPage from './pages/tickets/TicketsPage'
import TicketDetailPage from './pages/tickets/TicketDetailPage'
import AssetsPage from './pages/assets/AssetsPage'
import AssetDetailPage from './pages/assets/AssetDetailPage'
import RunsPage from './pages/runs/RunsPage'
import RunDetailPage from './pages/runs/RunDetailPage'

import AiHomePage from './pages/ai/AiHomePage/AiHomePage'
import AiFortunePage from './pages/ai/AiFortunePage/AiFortunePage'
import AiStockPage from './pages/ai/AiStockPage/AiStockPage'
import AiTicketPage from './pages/ai/AiTicketPage'
// 客服机器人：需要登录，后端按用户 ID 维护长期对话记忆
import AiCustomerServicePage from './pages/ai/AiCustomerServicePage/AiCustomerServicePage'

const router = createBrowserRouter([
  // ── 公开页面 ────────────────────────────────────────────────────────────
  { path: '/login', element: <LoginPage /> },
  { path: '/register', element: <RegisterPage /> },

  // ── 首页：登录后全屏显示，不带侧边栏 ────────────────────────────────────
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <HomePage />
      </ProtectedRoute>
    ),
  },

  // ── AI 系统：全屏无侧边栏（fortune / stock / customer-service）─────────
  {
    path: '/ai',
    element: <ProtectedRoute><AiHomePage /></ProtectedRoute>,
  },
  {
    path: '/ai/fortune',
    element: <ProtectedRoute><AiFortunePage /></ProtectedRoute>,
  },
  {
    path: '/ai/stock',
    element: <ProtectedRoute><AiStockPage /></ProtectedRoute>,
  },
  // 客服机器人：后端按用户身份维护长期记忆，需要登录态（已由外层 ProtectedRoute 保证）
  {
    path: '/ai/customer-service',
    element: <ProtectedRoute><AiCustomerServicePage /></ProtectedRoute>,
  },

  // ── 工单系统：带侧边栏布局 ───────────────────────────────────────────────
  {
    element: (
      <ProtectedRoute>
        <Layout />
      </ProtectedRoute>
    ),
    children: [
      { path: '/tickets', element: <TicketsPage /> },
      { path: '/tickets/:id', element: <TicketDetailPage /> },
      { path: '/assets', element: <AssetsPage /> },
      { path: '/assets/:id', element: <AssetDetailPage /> },
      { path: '/runs', element: <RunsPage /> },
      { path: '/runs/:id', element: <RunDetailPage /> },
      { path: '/ai/ticket', element: <AiTicketPage /> },
      { path: '*', element: <Navigate to="/" replace /> },
    ],
  },
])

export default function App() {
  return (
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  )
}
