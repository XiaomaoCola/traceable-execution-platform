// 注册页面。
// 对应 Vue 版本的 RegisterView.vue，注册成功后自动登录并跳转首页。

import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function RegisterPage() {
  const navigate = useNavigate()
  const { register } = useAuth()

  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [fullName, setFullName] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [errorMsg, setErrorMsg] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()

    if (!username || !email || !password) {
      setErrorMsg('请填写用户名、邮箱和密码')
      return
    }

    if (password !== confirmPassword) {
      setErrorMsg('两次输入的密码不一致')
      return
    }

    setLoading(true)
    setErrorMsg('')

    try {
      // register 内部会自动调用 login，注册完直接登录
      await register(username, email, password, fullName || undefined)
      navigate('/')
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : '注册失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1 className="auth-title">Traceable Execution Platform</h1>
        <p className="auth-subtitle">创建账号以开始使用</p>

        <form onSubmit={handleSubmit} className="form">
          <div className="form-field">
            <label htmlFor="username">
              用户名 <span className="required">*</span>
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="输入用户名"
              autoComplete="username"
              disabled={loading}
            />
          </div>

          <div className="form-field">
            <label htmlFor="email">
              邮箱 <span className="required">*</span>
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="输入邮箱地址"
              autoComplete="email"
              disabled={loading}
            />
          </div>

          <div className="form-field">
            <label htmlFor="fullName">姓名（可选）</label>
            <input
              id="fullName"
              type="text"
              value={fullName}
              onChange={e => setFullName(e.target.value)}
              placeholder="输入真实姓名"
              autoComplete="name"
              disabled={loading}
            />
          </div>

          <div className="form-field">
            <label htmlFor="password">
              密码 <span className="required">*</span>
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="输入密码"
              autoComplete="new-password"
              disabled={loading}
            />
          </div>

          <div className="form-field">
            <label htmlFor="confirmPassword">
              确认密码 <span className="required">*</span>
            </label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={e => setConfirmPassword(e.target.value)}
              placeholder="再次输入密码"
              autoComplete="new-password"
              disabled={loading}
            />
          </div>

          {errorMsg && <p className="form-error">{errorMsg}</p>}

          <button type="submit" className="btn btn--primary btn--full" disabled={loading}>
            {loading ? '注册中...' : '注册'}
          </button>
        </form>

        <p className="auth-switch">
          已有账号？<Link to="/login">去登录</Link>
        </p>
      </div>
    </div>
  )
}
