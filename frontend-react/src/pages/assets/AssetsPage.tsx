// 资产列表页。
// 展示所有资产（设备），支持跳转到详情页和创建新资产。

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { assetsApi } from '../../api'
import type { Asset } from '../../types'

export default function AssetsPage() {
  const navigate = useNavigate()
  const [assets, setAssets] = useState<Asset[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    assetsApi.list()
      .then(data => setAssets(data))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <div className="page-header">
        <h2 className="page-title">资产列表</h2>
        <button
          className="btn btn--primary"
          onClick={() => navigate('/assets/new')}
        >
          + 新建资产
        </button>
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
                  <th>名称</th>
                  <th>类型</th>
                  <th>序列号</th>
                  <th>位置</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {assets.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="empty">暂无资产</td>
                  </tr>
                ) : (
                  assets.map(asset => (
                    <tr key={asset.id}>
                      <td>#{asset.id}</td>
                      <td>{asset.name}</td>
                      <td>{asset.asset_type}</td>
                      <td>{asset.serial_number || '—'}</td>
                      <td>{asset.location || '—'}</td>
                      <td>
                        <span
                          className="link"
                          onClick={() => navigate(`/assets/${asset.id}`)}
                        >
                          查看详情
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
