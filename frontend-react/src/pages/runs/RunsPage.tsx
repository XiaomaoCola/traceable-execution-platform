// 运行记录列表页。
// 展示当前用户所有的执行记录，可点击查看详细日志。

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { runsApi } from '../../api'
import type { Run } from '../../types'

export default function RunsPage() {
  const navigate = useNavigate()
  const [runs, setRuns] = useState<Run[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    // 不传 ticketId，拉取当前用户全部 run
    runsApi.list()
      .then(data => setRuns(data))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  function formatDate(iso: string) {
    return new Date(iso).toLocaleString('zh-CN')
  }

  return (
    <div>
      <div className="page-header">
        <h2 className="page-title">运行记录</h2>
      </div>

      <div className="card">
        {loading && <div className="loading">加载中...</div>}
        {error && <div className="card__body form-error">{error}</div>}

        {!loading && !error && (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>工单</th>
                  <th>类型</th>
                  <th>状态</th>
                  <th>创建时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {runs.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="empty">暂无运行记录</td>
                  </tr>
                ) : (
                  runs.map(run => (
                    <tr key={run.id}>
                      <td>#{run.id}</td>
                      <td>
                        {/* 点击工单 ID 可跳转到对应工单详情 */}
                        <span
                          className="link"
                          onClick={() => navigate(`/tickets/${run.ticket_id}`)}
                        >
                          #{run.ticket_id}
                        </span>
                      </td>
                      <td>
                        <span className={`badge badge--${run.run_type}`}>
                          {run.run_type === 'proof' ? 'Proof' : 'Action'}
                        </span>
                      </td>
                      <td>
                        <span className={`badge badge--${run.status}`}>
                          {run.status}
                        </span>
                      </td>
                      <td>{formatDate(run.created_at)}</td>
                      <td>
                        <span
                          className="link"
                          onClick={() => navigate(`/runs/${run.id}`)}
                        >
                          查看日志
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
