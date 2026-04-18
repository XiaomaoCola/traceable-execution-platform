// 资产详情/创建页，路由 /assets/new（创建）或 /assets/:id（详情/编辑）。
// 支持查看基本信息、在线编辑字段（PATCH）、以及新建资产（POST）。

import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { assetsApi } from '../../api'
import type { Asset, AssetCreate } from '../../types'

export default function AssetDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const isNew = id === 'new'

  const [asset, setAsset] = useState<Asset | null>(null)
  const [loading, setLoading] = useState(!isNew)
  const [error, setError] = useState('')

  // editing 控制是否进入编辑模式（只在详情页显示编辑按钮）
  const [editing, setEditing] = useState(false)

  // 表单字段，创建时初始为空，编辑时从 asset 填充
  const [form, setForm] = useState<AssetCreate>({
    name: '',
    asset_type: '',
    serial_number: '',
    location: '',
    description: '',
  })
  const [submitting, setSubmitting] = useState(false)

  // 加载资产详情（仅详情模式）
  useEffect(() => {
    if (isNew) return
    assetsApi.get(Number(id))
      .then(data => {
        setAsset(data)
        // 把已有数据填入表单，便于编辑时使用
        setForm({
          name: data.name,
          asset_type: data.asset_type,
          serial_number: data.serial_number ?? '',
          location: data.location ?? '',
          description: data.description ?? '',
        })
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [id, isNew])

  // 创建新资产
  async function handleCreate() {
    if (!form.name.trim() || !form.asset_type.trim()) return
    setSubmitting(true)
    try {
      const created = await assetsApi.create(form)
      navigate(`/assets/${created.id}`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '创建失败')
    } finally {
      setSubmitting(false)
    }
  }

  // 保存编辑（PATCH）
  async function handleSave() {
    if (!asset) return
    setSubmitting(true)
    try {
      const updated = await assetsApi.update(asset.id, form)
      setAsset(updated)
      setEditing(false)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '保存失败')
    } finally {
      setSubmitting(false)
    }
  }

  function formatDate(iso: string) {
    return new Date(iso).toLocaleString('zh-CN')
  }

  // ── 创建模式 ────────────────────────────────────────────────────────────

  if (isNew) {
    return (
      <div>
        <div className="page-header">
          <h2 className="page-title">新建资产</h2>
        </div>

        <div className="card">
          <div className="card__body">
            <div className="form">
              <div className="form-field">
                <label>名称 <span className="required">*</span></label>
                <input
                  type="text"
                  value={form.name}
                  onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                  placeholder="例如：核心交换机-01"
                />
              </div>

              <div className="form-field">
                <label>类型 <span className="required">*</span></label>
                <input
                  type="text"
                  value={form.asset_type}
                  onChange={e => setForm(f => ({ ...f, asset_type: e.target.value }))}
                  placeholder="例如：switch / router"
                />
              </div>

              <div className="form-field">
                <label>序列号</label>
                <input
                  type="text"
                  value={form.serial_number}
                  onChange={e => setForm(f => ({ ...f, serial_number: e.target.value }))}
                  placeholder="设备序列号（可选）"
                />
              </div>

              <div className="form-field">
                <label>位置</label>
                <input
                  type="text"
                  value={form.location}
                  onChange={e => setForm(f => ({ ...f, location: e.target.value }))}
                  placeholder="机房位置（可选）"
                />
              </div>

              <div className="form-field">
                <label>描述</label>
                <textarea
                  value={form.description}
                  onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                  placeholder="资产描述（可选）"
                />
              </div>

              {error && <p className="form-error">{error}</p>}

              <div style={{ display: 'flex', gap: '12px' }}>
                <button
                  className="btn btn--primary"
                  onClick={handleCreate}
                  disabled={submitting || !form.name.trim() || !form.asset_type.trim()}
                >
                  {submitting ? '提交中...' : '创建资产'}
                </button>
                <button
                  className="btn btn--secondary"
                  onClick={() => navigate('/assets')}
                >
                  取消
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // ── 详情模式 ────────────────────────────────────────────────────────────

  if (loading) return <div className="loading">加载中...</div>
  if (error && !asset) return <div className="form-error">{error}</div>
  if (!asset) return null

  return (
    <div>
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <h2 className="page-title">资产 #{asset.id}</h2>
        </div>
        <button className="btn btn--secondary" onClick={() => navigate('/assets')}>
          返回列表
        </button>
      </div>

      {error && <p className="form-error" style={{ marginBottom: 12 }}>{error}</p>}

      <div className="card">
        <div className="card__header">
          <span className="card__title">基本信息</span>
          {/* 切换编辑模式 */}
          {!editing ? (
            <button className="btn btn--secondary btn--sm" onClick={() => setEditing(true)}>
              编辑
            </button>
          ) : (
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                className="btn btn--primary btn--sm"
                onClick={handleSave}
                disabled={submitting}
              >
                {submitting ? '保存中...' : '保存'}
              </button>
              <button
                className="btn btn--secondary btn--sm"
                onClick={() => {
                  setEditing(false)
                  // 取消时把表单重置回原始值
                  setForm({
                    name: asset.name,
                    asset_type: asset.asset_type,
                    serial_number: asset.serial_number ?? '',
                    location: asset.location ?? '',
                    description: asset.description ?? '',
                  })
                }}
              >
                取消
              </button>
            </div>
          )}
        </div>

        <div className="card__body">
          {editing ? (
            // 编辑态：内联表单
            <div className="form">
              <div className="form-field">
                <label>名称 <span className="required">*</span></label>
                <input
                  type="text"
                  value={form.name}
                  onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                />
              </div>
              <div className="form-field">
                <label>类型 <span className="required">*</span></label>
                <input
                  type="text"
                  value={form.asset_type}
                  onChange={e => setForm(f => ({ ...f, asset_type: e.target.value }))}
                />
              </div>
              <div className="form-field">
                <label>序列号</label>
                <input
                  type="text"
                  value={form.serial_number}
                  onChange={e => setForm(f => ({ ...f, serial_number: e.target.value }))}
                />
              </div>
              <div className="form-field">
                <label>位置</label>
                <input
                  type="text"
                  value={form.location}
                  onChange={e => setForm(f => ({ ...f, location: e.target.value }))}
                />
              </div>
              <div className="form-field">
                <label>描述</label>
                <textarea
                  value={form.description}
                  onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                />
              </div>
            </div>
          ) : (
            // 只读态：detail-grid 展示
            <div className="detail-grid">
              <div className="detail-item">
                <span className="detail-label">名称</span>
                <span>{asset.name}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">类型</span>
                <span>{asset.asset_type}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">序列号</span>
                <span>{asset.serial_number || '—'}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">位置</span>
                <span>{asset.location || '—'}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">描述</span>
                <span>{asset.description || '—'}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">创建时间</span>
                <span>{formatDate(asset.created_at)}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
