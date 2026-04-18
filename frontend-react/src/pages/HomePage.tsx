// 系统选择首页，登录后的第一个页面，不带侧边栏。
// 点击工单系统进入 /tickets，点击 AI 助手进入 /ai/fortune。

import { useNavigate } from 'react-router-dom'
import { Card, Typography, Row, Col, Button } from 'antd'
import { FileTextOutlined, RobotOutlined, LogoutOutlined } from '@ant-design/icons'
import { useAuth } from '../context/AuthContext'

const { Title, Text } = Typography

export default function HomePage() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div style={styles.page}>
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
          欢迎回来，{user?.full_name || user?.username}
        </Title>
        <Text type="secondary" style={{ fontSize: 15, display: 'block', marginBottom: 48 }}>
          请选择要进入的系统
        </Text>

        {/* 入口卡片 */}
        <Row gutter={24} justify="center">
          <Col>
            <Card
              hoverable
              style={styles.card}
              onClick={() => navigate('/tickets')}
            >
              <div style={styles.cardIcon}>
                <FileTextOutlined style={{ fontSize: 48, color: '#4f6ef7' }} />
              </div>
              <Title level={4} style={{ margin: '16px 0 8px' }}>工单系统</Title>
              <Text type="secondary">工单管理 · 资产管理 · 执行记录</Text>
            </Card>
          </Col>

          <Col>
            <Card
              hoverable
              style={styles.card}
              onClick={() => navigate('/ai/fortune')}
            >
              <div style={styles.cardIcon}>
                <RobotOutlined style={{ fontSize: 48, color: '#52c41a' }} />
              </div>
              <Title level={4} style={{ margin: '16px 0 8px' }}>AI 助手</Title>
              <Text type="secondary">AI 算命师 · AI 量化先知</Text>
            </Card>
          </Col>
        </Row>
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    minHeight: '100vh',
    background: '#f0f2f5',
    display: 'flex',
    flexDirection: 'column',
  },
  topBar: {
    display: 'flex',
    justifyContent: 'flex-end',
    padding: '16px 24px',
  },
  content: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    paddingBottom: 80,
  },
  card: {
    width: 260,
    textAlign: 'center',
    padding: '32px 24px',
    borderRadius: 12,
    boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
  },
  cardIcon: {
    display: 'flex',
    justifyContent: 'center',
  },
}
