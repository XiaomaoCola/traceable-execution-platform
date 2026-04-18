// 应用路由总装。
// 首页（/）独立全屏显示，不带侧边栏。
// 进入工单系统或 AI 系统后才显示对应的侧边栏布局。

import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom'

import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'

import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import HomePage from './pages/HomePage'

import TicketsPage from './pages/tickets/TicketsPage'
import TicketDetailPage from './pages/tickets/TicketDetailPage'
import AssetsPage from './pages/assets/AssetsPage'
import AssetDetailPage from './pages/assets/AssetDetailPage'
import RunsPage from './pages/runs/RunsPage'
import RunDetailPage from './pages/runs/RunDetailPage'

import AiFortunePage from './pages/ai/AiFortunePage'
import AiStockPage from './pages/ai/AiStockPage'
import AiTicketPage from './pages/ai/AiTicketPage'

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
      { path: '/ai/fortune', element: <AiFortunePage /> },
      { path: '/ai/stock', element: <AiStockPage /> },
      { path: '/ai', element: <Navigate to="/ai/fortune" replace /> },
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
