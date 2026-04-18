// 运行记录详情页，路由 /runs/:id。
// 展示执行记录的元信息和 stdout/stderr 日志，支持刷新查看最新状态。

import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { runsApi } from '../../api'
import type { RunDetail } from '../../types'

export default function RunDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [run, setRun] = useState<RunDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [refreshing, setRefreshing] = useState(false)

  function loadRun() {
    return runsApi.get(Number(id))
      .then(data => setRun(data))
      .catch(err => setError(err.message))
  }

  useEffect(() => {
    loadRun().finally(() => setLoading(false))
  }, [id])

  async function handleRefresh() {
    setRefreshing(true)
    await loadRun()
    setRefreshing(false)
  }

  function formatDate(iso: string) {
    return new Date(iso).toLocaleString('zh-CN')
  }

  if (loading) return <div className="loading">加载中...</div>
  if (error && !run) return <div className="form-error">{error}</div>
  if (!run) return null

  return (
    <div>
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <h2 className="page-title">运行记录 #{run.id}</h2>
          {/* 类型和状态徽章 */}
          <span className={`badge badge--${run.run_type}`}>
            {run.run_type === 'proof' ? 'Proof' : 'Action'}
          </span>
          <span className={`badge badge--${run.status}`}>
            {run.status}
          </span>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          {/* 对于 running/pending 状态，提供刷新按钮查看最新日志 */}
          {(run.status === 'running' || run.status === 'pending') && (
            <button
              className="btn btn--secondary btn--sm"
              onClick={handleRefresh}
              disabled={refreshing}
            >
              {refreshing ? '刷新中...' : '刷新'}
            </button>
          )}
          <button className="btn btn--secondary" onClick={() => navigate(-1)}>
            返回
          </button>
        </div>
      </div>

      {/* 元信息 */}
      <div className="card">
        <div className="card__header">
          <span className="card__title">基本信息</span>
        </div>
        <div className="card__body">
          <div className="detail-grid">
            <div className="detail-item">
              <span className="detail-label">所属工单</span>
              {/* 点击可跳转到工单详情 */}
              <span
                className="link"
                onClick={() => navigate(`/tickets/${run.ticket_id}`)}
              >
                #{run.ticket_id}
              </span>
            </div>
            <div className="detail-item">
              <span className="detail-label">退出码</span>
              <span>{run.exit_code ?? '—'}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">结果摘要</span>
              <span>{run.result_summary || '—'}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">创建时间</span>
              <span>{formatDate(run.created_at)}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">更新时间</span>
              <span>{formatDate(run.updated_at)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* stdout 日志 */}
      <div className="card">
        <div className="card__header">
          <span className="card__title">标准输出（stdout）</span>
        </div>
        <div className="card__body">
          {run.stdout_log ? (
            <pre style={logStyle}>{run.stdout_log}</pre>
          ) : (
            <div className="empty">暂无输出</div>
          )}
        </div>
      </div>

      {/* stderr 日志，有内容才展示 */}
      {run.stderr_log && (
        <div className="card">
          <div className="card__header">
            <span className="card__title">标准错误（stderr）</span>
          </div>
          <div className="card__body">
            <pre style={{ ...logStyle, borderColor: '#ffcdd2', background: '#fff8f8' }}>
              {run.stderr_log}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}

// 日志区域样式：等宽字体、可滚动、保留空白
const logStyle: React.CSSProperties = {
  fontFamily: 'monospace',
  fontSize: 12,
  lineHeight: 1.6,
  background: '#f8f9fa',
  border: '1px solid #e0e0e0',
  borderRadius: 6,
  padding: 16,
  overflowX: 'auto',
  whiteSpace: 'pre-wrap',
  wordBreak: 'break-all',
  maxHeight: 500,
  overflowY: 'auto',
}
