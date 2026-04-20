// 资产列表页。
// 展示所有资产（设备），支持跳转到详情页和创建新资产。

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Table, Button, Typography } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { assetsApi } from '../../api'
import type { Asset } from '../../types/asset'

const { Title } = Typography

export default function AssetsPage() {
  const navigate = useNavigate()
  const [assets, setAssets] = useState<Asset[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    assetsApi.list()
      .then(data => setAssets(data))
      .finally(() => setLoading(false))
  }, [])

  const columns: ColumnsType<Asset> = [
    { title: 'ID', dataIndex: 'id', width: 80, render: id => `#${id}` },
    { title: '名称', dataIndex: 'name' },
    { title: '类型', dataIndex: 'asset_type', width: 120 },
    { title: '序列号', dataIndex: 'serial_number', width: 160, render: v => v || '—' },
    { title: '位置', dataIndex: 'location', width: 160, render: v => v || '—' },
    {
      title: '操作', width: 100,
      render: (_, record) => (
        <Button type="link" onClick={() => navigate(`/assets/${record.id}`)}>
          查看详情
        </Button>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>资产列表</Title>
        <Button type="primary" onClick={() => navigate('/assets/new')}>+ 新建资产</Button>
      </div>

      <Table
        rowKey="id"
        dataSource={assets}
        columns={columns}
        loading={loading}
        pagination={{ pageSize: 10 }}
      />
    </div>
  )
}
