// 登录页面，使用 Ant Design 组件库重写。
// 支持普通登录和游客一键访问（自动使用预设的 guest 账号登录）。

import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Button, Form, Input, Card, Typography, Divider, Alert } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useAuth } from '../context/AuthContext'

const { Title, Text } = Typography

export default function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()

  const [errorMsg, setErrorMsg] = useState('')
  const [loading, setLoading] = useState(false)
  const [guestLoading, setGuestLoading] = useState(false)

  // 普通登录
  async function handleSubmit(values: { username: string; password: string }) {
    setLoading(true)
    setErrorMsg('')
    try {
      await login(values.username, values.password)
      navigate('/')
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : '登录失败')
    } finally {
      setLoading(false)
    }
  }

  // 游客一键访问：自动用预设 guest 账号登录
  async function handleGuestLogin() {
    setGuestLoading(true)
    setErrorMsg('')
    try {
      await login('guest', 'guest123')
      navigate('/')
    } catch (err: unknown) {
      setErrorMsg('游客登录失败，请联系管理员')
    } finally {
      setGuestLoading(false)
    }
  }

  return (
    <div style={styles.page}>
      <Card style={styles.card} bordered={false}>
        {/* 标题 */}
        <div style={styles.header}>
          <Title level={3} style={{ margin: 0 }}>Traceable Execution Platform</Title>
          <Text type="secondary">请登录以继续</Text>
        </div>

        {/* 错误提示 */}
        {errorMsg && (
          <Alert
            message={errorMsg}
            type="error"
            showIcon
            style={{ marginBottom: 20 }}
          />
        )}

        {/* 登录表单，antd Form 内置校验，不需要手动写 e.preventDefault() */}
        <Form layout="vertical" onFinish={handleSubmit} requiredMark={false}>
          <Form.Item
            name="username"
            label="用户名"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="输入用户名"
              autoComplete="username"
              size="large"
              disabled={loading || guestLoading}
            />
          </Form.Item>

          <Form.Item
            name="password"
            label="密码"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="输入密码"
              autoComplete="current-password"
              size="large"
              disabled={loading || guestLoading}
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 12 }}>
            <Button
              type="primary"
              htmlType="submit"
              size="large"
              block
              loading={loading}
              disabled={guestLoading}
            >
              登录
            </Button>
          </Form.Item>
        </Form>

        {/* 分割线 */}
        <Divider plain style={{ color: '#aaa', fontSize: 12 }}>或</Divider>

        {/* 游客访问按钮 */}
        <Button
          size="large"
          block
          onClick={handleGuestLogin}
          loading={guestLoading}
          disabled={loading}
          style={{ marginBottom: 16 }}
        >
          游客访问
        </Button>

        {/* 注册跳转 */}
        <div style={{ textAlign: 'center' }}>
          <Text type="secondary" style={{ fontSize: 13 }}>
            没有账号？<Link to="/register">去注册</Link>
          </Text>
        </div>
      </Card>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: '#f0f2f5',
  },
  card: {
    width: 400,
    boxShadow: '0 2px 16px rgba(0,0,0,0.08)',
    borderRadius: 8,
    padding: '8px 8px',
  },
  header: {
    textAlign: 'center',
    marginBottom: 28,
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
  },
}
