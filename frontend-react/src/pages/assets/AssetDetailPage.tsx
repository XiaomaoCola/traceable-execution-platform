// 资产详情/创建页，路由 /assets/new（创建）或 /assets/:id（详情/编辑）。
// 支持查看基本信息、在线编辑字段（PATCH）、以及新建资产（POST）。

import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Button, Form, Input, Card, Typography,
  Space, Spin, Alert, Descriptions,
} from 'antd'
import { assetsApi } from '../../api'
import type { Asset, AssetCreate } from '../../types'

const { Title } = Typography

export default function AssetDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [form] = Form.useForm<AssetCreate>()

  const isNew = id === 'new'

  const [asset, setAsset] = useState<Asset | null>(null)
  const [loading, setLoading] = useState(!isNew)
  const [editing, setEditing] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (isNew) return
    assetsApi.get(Number(id))
      .then(data => {
        setAsset(data)
        form.setFieldsValue({
          name: data.name,
          asset_type: data.asset_type,
          serial_number: data.serial_number ?? '',
          location: data.location ?? '',
          description: data.description ?? '',
        })
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [id, isNew, form])

  // 创建新资产
  async function handleCreate(values: AssetCreate) {
    setSubmitting(true)
    try {
      const created = await assetsApi.create(values)
      navigate(`/assets/${created.id}`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '创建失败')
    } finally {
      setSubmitting(false)
    }
  }

  // 保存编辑（PATCH）
  async function handleSave(values: AssetCreate) {
    if (!asset) return
    setSubmitting(true)
    try {
      const updated = await assetsApi.update(asset.id, values)
      setAsset(updated)
      setEditing(false)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '保存失败')
    } finally {
      setSubmitting(false)
    }
  }

  function handleCancelEdit() {
    if (!asset) return
    form.setFieldsValue({
      name: asset.name,
      asset_type: asset.asset_type,
      serial_number: asset.serial_number ?? '',
      location: asset.location ?? '',
      description: asset.description ?? '',
    })
    setEditing(false)
  }

  // ── 创建模式 ────────────────────────────────────────────────────────────

  if (isNew) {
    return (
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <Title level={4} style={{ margin: 0 }}>新建资产</Title>
          <Button onClick={() => navigate('/assets')}>返回列表</Button>
        </div>

        <Card>
          {error && <Alert message={error} type="error" showIcon style={{ marginBottom: 16 }} />}
          <Form form={form} layout="vertical" onFinish={handleCreate} style={{ maxWidth: 600 }}>
            <Form.Item name="name" label="名称" rules={[{ required: true, message: '请输入资产名称' }]}>
              <Input placeholder="例如：核心交换机-01" />
            </Form.Item>
            <Form.Item name="asset_type" label="类型" rules={[{ required: true, message: '请输入资产类型' }]}>
              <Input placeholder="例如：switch / router" />
            </Form.Item>
            <Form.Item name="serial_number" label="序列号">
              <Input placeholder="设备序列号（可选）" />
            </Form.Item>
            <Form.Item name="location" label="位置">
              <Input placeholder="机房位置（可选）" />
            </Form.Item>
            <Form.Item name="description" label="描述">
              <Input.TextArea rows={4} placeholder="资产描述（可选）" />
            </Form.Item>
            <Form.Item>
              <Space>
                <Button type="primary" htmlType="submit" loading={submitting}>创建资产</Button>
                <Button onClick={() => navigate('/assets')}>取消</Button>
              </Space>
            </Form.Item>
          </Form>
        </Card>
      </div>
    )
  }

  // ── 详情模式 ────────────────────────────────────────────────────────────

  if (loading) return <Spin size="large" style={{ display: 'block', marginTop: 80, textAlign: 'center' }} />
  if (error && !asset) return <Alert message="加载失败" description={error} type="error" showIcon style={{ margin: 24 }} />
  if (!asset) return null

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>资产 #{asset.id}</Title>
        <Button onClick={() => navigate('/assets')}>返回列表</Button>
      </div>

      {error && <Alert message={error} type="error" showIcon style={{ marginBottom: 16 }} />}

      <Card
        title="基本信息"
        extra={
          !editing ? (
            <Button size="small" onClick={() => setEditing(true)}>编辑</Button>
          ) : (
            <Space>
              <Button type="primary" size="small" loading={submitting} onClick={() => form.submit()}>保存</Button>
              <Button size="small" onClick={handleCancelEdit}>取消</Button>
            </Space>
          )
        }
      >
        {editing ? (
          <Form form={form} layout="vertical" onFinish={handleSave} style={{ maxWidth: 600 }}>
            <Form.Item name="name" label="名称" rules={[{ required: true, message: '请输入资产名称' }]}>
              <Input />
            </Form.Item>
            <Form.Item name="asset_type" label="类型" rules={[{ required: true, message: '请输入资产类型' }]}>
              <Input />
            </Form.Item>
            <Form.Item name="serial_number" label="序列号">
              <Input />
            </Form.Item>
            <Form.Item name="location" label="位置">
              <Input />
            </Form.Item>
            <Form.Item name="description" label="描述">
              <Input.TextArea rows={4} />
            </Form.Item>
          </Form>
        ) : (
          <Descriptions column={2}>
            <Descriptions.Item label="名称">{asset.name}</Descriptions.Item>
            <Descriptions.Item label="类型">{asset.asset_type}</Descriptions.Item>
            <Descriptions.Item label="序列号">{asset.serial_number || '—'}</Descriptions.Item>
            <Descriptions.Item label="位置">{asset.location || '—'}</Descriptions.Item>
            <Descriptions.Item label="描述">{asset.description || '—'}</Descriptions.Item>
            <Descriptions.Item label="创建时间">{new Date(asset.created_at).toLocaleString('zh-CN')}</Descriptions.Item>
            <Descriptions.Item label="更新时间">{new Date(asset.updated_at).toLocaleString('zh-CN')}</Descriptions.Item>
          </Descriptions>
        )}
      </Card>
    </div>
  )
}
