// 系统选择首页，登录后的第一个页面，不带侧边栏。
// 鼠标悬停卡片触发翻转，正面显示图标，背面显示功能介绍，点击进入对应系统。

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Typography, Button } from 'antd'
import { FileTextOutlined, RobotOutlined, LogoutOutlined } from '@ant-design/icons'
import { useAuth } from '../../context/AuthContext'
import './HomePage.css'

const { Title, Text } = Typography

export default function HomePage() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [flipped, setFlipped] = useState<string | null>(null)

  function handleLogout() {
    logout()
    navigate('/login')
  }

  function handleCardClick(key: string, path: string) {
    const isTouch = window.matchMedia('(hover: none)').matches
    if (!isTouch) {
      navigate(path)
      return
    }
    if (flipped === key) {
      navigate(path)
    } else {
      setFlipped(key)
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.bg} />
      {/* 右上角退出按钮 */}
      <div style={styles.topBar}>
        <Button
          icon={<LogoutOutlined />}
          onClick={handleLogout}
          type="text"
          style={{ color: '#888' }}
        >
          退出登录
        </Button>
      </div>

      <div style={styles.content}>
        {/* 欢迎语 */}
        <Title level={2} style={{ marginBottom: 8 }}>
          欢迎回来，{user?.username}
        </Title>
        <Text type="secondary" style={{ fontSize: 15, display: 'block', marginBottom: 48 }}>
          请选择要进入的系统
        </Text>

        {/* 翻转卡片入口 */}
        <div className="home-card-row">
          {/* 工单系统 */}
          <div className={`flip-card${flipped === 'tickets' ? ' flipped' : ''}`} onClick={() => handleCardClick('tickets', '/tickets')}>
            <div className="flip-card-inner">
              <div className="flip-card-front ticket">
                <FileTextOutlined style={{ fontSize: 100 }} />
                <p className="flip-card-title">工单系统</p>
              </div>
              <div className="flip-card-back ticket">
                <p className="flip-card-title">工单系统</p>
                <p className="flip-card-desc">
                  工单管理<br />
                  资产管理<br />
                  AI工单助手
                </p>
                <p className="flip-card-hint">点击进入 →</p>
              </div>
            </div>
          </div>

          {/* AI 助手 */}
          <div className={`flip-card${flipped === 'ai' ? ' flipped' : ''}`} onClick={() => handleCardClick('ai', '/ai')}>
            <div className="flip-card-inner">
              <div className="flip-card-front ai">
                <RobotOutlined style={{ fontSize: 100 }} />
                <p className="flip-card-title">AI 智能体</p>
              </div>
              <div className="flip-card-back ai">
                <p className="flip-card-title">AI 智能体</p>
                <p className="flip-card-desc">
                  AI 算命师<br />
                  AI 量化先知<br />
                  AI 客服机器人
                </p>
                <p className="flip-card-hint">点击进入 →</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    position: 'relative',
    overflow: 'hidden',
  },
  bg: {
    position: 'fixed',
    inset: 0,
    backgroundImage: 'url(/backend1.png)',
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    filter: 'blur(8px)',
    transform: 'scale(1.08)',
    zIndex: 0,
  },
  topBar: {
    display: 'flex',
    justifyContent: 'flex-end',
    padding: '16px 24px',
    position: 'relative',
    zIndex: 1,
  },
  content: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    paddingBottom: 80,
    position: 'relative',
    zIndex: 1,
  },
}
