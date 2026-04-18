// 全局布局组件，使用 Ant Design 的 Layout + Menu 重写。
// 侧边栏根据当前路径自动切换工单系统 / AI 系统导航，支持折叠。

import { useState } from 'react'
import { useLocation, useNavigate, Outlet } from 'react-router-dom'
import {
  Layout as AntLayout, Menu, Button, Avatar, Dropdown, Tag, theme,
} from 'antd'
import {
  HomeOutlined, FileTextOutlined, DesktopOutlined, PlayCircleOutlined,
  RobotOutlined, StarOutlined, StockOutlined, MenuFoldOutlined,
  MenuUnfoldOutlined, UserOutlined, LogoutOutlined,
} from '@ant-design/icons'
import { useAuth } from '../context/AuthContext'

const { Sider, Header, Content } = AntLayout

// ── 工单系统菜单 ───────────────────────────────────────────────────────────

const ticketMenuItems = [
  { key: '/', icon: <HomeOutlined />, label: '首页' },
  {
    key: 'tickets-group',
    icon: <FileTextOutlined />,
    label: '工单管理',
    children: [
      { key: '/tickets', label: '工单列表' },
      { key: '/tickets/new', label: '创建工单' },
    ],
  },
  {
    key: 'assets-group',
    icon: <DesktopOutlined />,
    label: '资产管理',
    children: [
      { key: '/assets', label: '资产列表' },
      { key: '/assets/new', label: '创建资产' },
    ],
  },
  {
    key: 'runs-group',
    icon: <PlayCircleOutlined />,
    label: '运行记录',
    children: [
      { key: '/runs', label: '运行列表' },
    ],
  },
  { key: '/ai/ticket', icon: <RobotOutlined />, label: 'AI 工单助手' },
]

// ── AI 系统菜单 ────────────────────────────────────────────────────────────

const aiMenuItems = [
  { key: '/', icon: <HomeOutlined />, label: '首页' },
  { key: '/ai/fortune', icon: <StarOutlined />, label: 'AI 算命师' },
  { key: '/ai/stock', icon: <StockOutlined />, label: 'AI 量化先知' },
]

// /ai/fortune 和 /ai/stock 显示 AI 导航，其余显示工单系统导航
function getMenuItems(pathname: string) {
  if (pathname.startsWith('/ai/fortune') || pathname.startsWith('/ai/stock')) {
    return aiMenuItems
  }
  return ticketMenuItems
}

// 根据当前路径找到应该展开的父菜单 key
function getOpenKeys(pathname: string): string[] {
  if (pathname.startsWith('/tickets')) return ['tickets-group']
  if (pathname.startsWith('/assets')) return ['assets-group']
  if (pathname.startsWith('/runs')) return ['runs-group']
  return []
}

// ── Layout 组件 ────────────────────────────────────────────────────────────

export default function Layout() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [collapsed, setCollapsed] = useState(false)
  const { token } = theme.useToken()

  const menuItems = getMenuItems(location.pathname)
  // 当前激活的菜单项 key = 当前路径
  const selectedKey = location.pathname

  function handleLogout() {
    logout()
    navigate('/login')
  }

  // 右上角用户下拉菜单
  const userMenuItems = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ]

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      {/* 侧边栏 */}
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        trigger={null}
        style={{ background: token.colorBgContainer }}
        theme="light"
        width={220}
      >
        {/* Logo */}
        <div style={{
          height: 52,
          display: 'flex',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'flex-start',
          padding: collapsed ? 0 : '0 20px',
          fontWeight: 700,
          fontSize: 16,
          color: token.colorPrimary,
          borderBottom: `1px solid ${token.colorBorderSecondary}`,
          gap: 8,
        }}>
          ⚡ {!collapsed && 'Traceable'}
        </div>

        {/* 导航菜单，点击菜单项时跳转对应路由 */}
        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          defaultOpenKeys={getOpenKeys(location.pathname)}
          items={menuItems}
          style={{ borderRight: 0, marginTop: 4 }}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>

      <AntLayout>
        {/* 顶栏 */}
        <Header style={{
          padding: '0 16px 0 0',
          background: token.colorBgContainer,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: `1px solid ${token.colorBorderSecondary}`,
          height: 52,
        }}>
          {/* 折叠/展开按钮 */}
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(c => !c)}
            style={{ fontSize: 16, width: 52, height: 52 }}
          />

          {/* 右侧用户信息 */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {user?.is_admin && <Tag color="gold">管理员</Tag>}
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                <Avatar size="small" icon={<UserOutlined />} style={{ background: token.colorPrimary }} />
                <span style={{ fontSize: 13 }}>{user?.full_name || user?.username}</span>
              </div>
            </Dropdown>
          </div>
        </Header>

        {/* 页面内容区 */}
        <Content style={{ padding: 24, overflow: 'auto' }}>
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  )
}
