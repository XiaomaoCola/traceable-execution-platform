// 工单列表页，使用 Ant Design Table 重写。

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Table, Button, Tag, Space, Typography } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { ticketsApi } from '../../api'
import type { Ticket, TicketStatus } from '../../types'

const { Title } = Typography

const STATUS_LABEL: Record<TicketStatus, string> = {
  draft: '草稿', submitted: '待审批', approved: '已审批',
  running: '执行中', done: '已完成', failed: '失败', closed: '已关闭',
}

const STATUS_COLOR: Record<TicketStatus, string> = {
  draft: 'default', submitted: 'blue', approved: 'green',
  running: 'orange', done: 'green', failed: 'red', closed: 'default',
}

export default function TicketsPage() {
  const navigate = useNavigate()
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    ticketsApi.list()
      .then(data => setTickets(data))
      .finally(() => setLoading(false))
  }, [])

  const columns: ColumnsType<Ticket> = [
    { title: 'ID', dataIndex: 'id', width: 80, render: id => `#${id}` },
    { title: '标题', dataIndex: 'title' },
    {
      title: '状态', dataIndex: 'status', width: 100,
      render: (status: TicketStatus) => (
        <Tag color={STATUS_COLOR[status]}>{STATUS_LABEL[status]}</Tag>
      ),
    },
    {
      title: '创建时间', dataIndex: 'created_at', width: 160,
      render: (v: string) => new Date(v).toLocaleDateString('zh-CN'),
    },
    {
      title: '操作', width: 100,
      render: (_, record) => (
        <Button type="link" onClick={() => navigate(`/tickets/${record.id}`)}>
          查看详情
        </Button>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>工单列表</Title>
        <Button type="primary" onClick={() => navigate('/tickets/new')}>+ 创建工单</Button>
      </div>

      <Table
        rowKey="id"
        dataSource={tickets}
        columns={columns}
        loading={loading}
        pagination={{ pageSize: 10 }}
      />
    </div>
  )
}
