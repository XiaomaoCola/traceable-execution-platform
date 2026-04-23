// AI 智能体选择页，路由 /ai。
// 3 张卡片横排，鼠标悬停有 3D 倾斜效果，点击进入对应 Agent 页面。

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, Typography } from 'antd'
import { LogoutOutlined } from '@ant-design/icons'
import { useAuth } from '../../../context/AuthContext'
import './AiHomePage.css'

const { Title } = Typography

interface AgentCard {
  title: string
  desc: string[]
  icon: string
  gradient: string
  path: string
}

const agents: AgentCard[] = [
  {
    title: 'AI 算命师',
    desc: ['生辰八字推算', '今日运势分析', '财运事业占卜'],
    icon: '🔮',
    gradient: 'linear-gradient(43deg, rgb(120, 40, 200) 0%, rgb(200, 80, 192) 46%, rgb(255, 180, 60) 100%)',
    path: '/ai/fortune',
  },
  {
    title: 'AI 量化先知',
    desc: ['A 股实时行情', '短期走势分析', '操作建议参考'],
    icon: '📈',
    gradient: 'linear-gradient(43deg, rgb(20, 100, 60) 0%, rgb(50, 180, 100) 46%, rgb(180, 240, 100) 100%)',
    path: '/ai/stock',
  },
  {
    title: 'AI 客服机器人',
    desc: ['长期对话记忆', '跨会话上下文', '智能问题解答'],
    icon: '🤖',
    gradient: 'linear-gradient(43deg, rgb(65, 88, 208) 0%, rgb(100, 160, 240) 46%, rgb(180, 220, 255) 100%)',
    path: '/ai/customer-service',
  },
]

const TRACKERS = Array.from({ length: 25 }, (_, i) => i + 1)

export default function AiHomePage() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [active, setActive] = useState<number | null>(null)

  function handleLogout() {
    logout()
    navigate('/login')
  }

  function handleCardClick(i: number, path: string) {
    const isTouch = window.matchMedia('(hover: none)').matches
    if (!isTouch) {
      navigate(path)
      return
    }
    if (active === i) {
      navigate(path)
    } else {
      setActive(i)
    }
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

      {/* 卡片横排 */}
      <div className="ai-cards-row">
        {agents.map((agent, i) => (
          <div
            key={i}
            className={`ai-card-container noselect${active === i ? ' active' : ''}`}
            onClick={() => handleCardClick(i, agent.path)}
          >
            <div className="canvas">
              {TRACKERS.map(n => (
                <div key={n} className={`tracker tr-${n}`} />
              ))}
              <div className="uiverse-card" style={{ background: agent.gradient }}>
                <span className="card-icon-center">{agent.icon}</span>
                <p className="card-title">{agent.title}</p>
                <p className="card-desc-hover">
                  {agent.desc.map((line, i) => (
                    <span key={i} style={{ display: 'block' }}>{line}</span>
                  ))}
                </p>
                <p className="uiverse-prompt">点击进入 →</p>
              </div>
            </div>
          </div>
        ))}

        {/* 更多智能体占位 */}
        <div className="more-card noselect">
          <span className="more-card-icon">✦</span>
          <span className="more-card-text">更多智能体</span>
          <span className="more-card-text" style={{ fontSize: 11, letterSpacing: 0.5 }}>敬请期待…</span>
        </div>
      </div>
    </div>
  )
}
