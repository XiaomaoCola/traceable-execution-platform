// AI 智能体选择页，路由 /ai。
// 4 张卡片组成 3D 旋转转盘，鼠标悬停暂停，点击进入对应 Agent 页面。

import { useNavigate } from 'react-router-dom'
import { Button, Typography } from 'antd'
import { LogoutOutlined } from '@ant-design/icons'
import { useAuth } from '../../../context/AuthContext'
import './AiHomePage.css'

const { Title } = Typography

interface AgentCard {
  index: number
  title: string
  desc: string[]
  icon: string
  color: string   // RGB 值，供 CSS var(--color-card) 使用
  path: string
}

const agents: AgentCard[] = [
  {
    index: 0,
    title: 'AI 算命师',
    desc: ['生辰八字推算', '今日运势分析', '财运事业占卜'],
    icon: '🔮',
    color: '255, 180, 50',
    path: '/ai/fortune',
  },
  {
    index: 1,
    title: 'AI 量化先知',
    desc: ['A 股实时行情', '短期走势分析', '操作建议参考'],
    icon: '📈',
    color: '50, 200, 120',
    path: '/ai/stock',
  },
  {
    index: 2,
    title: 'AI 客服机器人',
    desc: ['长期对话记忆', '跨会话上下文', '智能问题解答'],
    icon: '🤖',
    color: '220, 80, 220',
    path: '/ai/customer-service',
  },
]

export default function AiHomePage() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="ai-home-page">
      {/* 顶栏 */}
      <div className="ai-home-topbar">
        <Button
          onClick={() => navigate('/')}
          type="text"
          style={{ color: 'rgba(255,255,255,0.6)' }}
        >
          ← 返回首页
        </Button>
        <Button
          icon={<LogoutOutlined />}
          onClick={handleLogout}
          type="text"
          style={{ color: 'rgba(255,255,255,0.6)' }}
        >
          退出登录
        </Button>
      </div>

      {/* 标题 */}
      <div className="ai-home-title">
        <Title level={2}>欢迎，{user?.username}</Title>
        <p>选择一个 AI 智能体开始对话</p>
      </div>

      {/* 3D 转盘 */}
      <div className="wrapper">
        <div className="inner" style={{ '--quantity': agents.length } as React.CSSProperties}>
          {agents.map((agent) => (
            <div
              key={agent.index}
              className="card"
              style={{
                '--index': agent.index,
                '--color-card': agent.color,
              } as React.CSSProperties}
              onClick={() => navigate(agent.path)}
            >
              <div className="card-content">
                <span className="card-icon">{agent.icon}</span>
                <p className="card-title">{agent.title}</p>
                <p className="card-desc">{agent.desc.join('\n').split('\n').map((line, i) => (
                  <span key={i}>{line}<br /></span>
                ))}</p>
                <p className="card-hint">点击进入 →</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <p className="ai-home-hint">悬停暂停 · 点击进入</p>
    </div>
  )
}
