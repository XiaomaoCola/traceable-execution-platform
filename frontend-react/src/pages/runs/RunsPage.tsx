// 运行记录列表页。
// 展示当前用户所有的执行记录，可点击查看详细日志。

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Table, Button, Tag, Typography } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { runsApi } from '../../api'
import type { Run, RunType, RunStatus } from '../../types/run'

const { Title } = Typography

const RUN_TYPE_LABEL: Record<RunType, string> = {
  proof: 'Proof',
  action: 'Action',
}

const RUN_TYPE_COLOR: Record<RunType, string> = {
  proof: 'blue',
  action: 'orange',
}

const STATUS_LABEL: Record<RunStatus, string> = {
  pending: '等待中',
  running: '执行中',
  done: '已完成',
  failed: '失败',
}

const STATUS_COLOR: Record<RunStatus, string> = {
  pending: 'default',
  running: 'orange',
  done: 'green',
  failed: 'red',
}

export default function RunsPage() {
  const navigate = useNavigate()
  const [runs, setRuns] = useState<Run[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // 不传 ticketId，拉取当前用户全部 run
    runsApi.list()
      .then(data => setRuns(data))
      .finally(() => setLoading(false))
  }, [])

  const columns: ColumnsType<Run> = [
    { title: 'ID', dataIndex: 'id', width: 80, render: id => `#${id}` },
    {
      title: '工单', dataIndex: 'ticket_id', width: 100,
      render: (id: number) => (
        <Button type="link" style={{ padding: 0 }} onClick={() => navigate(`/tickets/${id}`)}>
          #{id}
        </Button>
      ),
    },
    {
      title: '类型', dataIndex: 'run_type', width: 100,
      render: (type: RunType) => (
        <Tag color={RUN_TYPE_COLOR[type]}>{RUN_TYPE_LABEL[type]}</Tag>
      ),
    },
    {
      title: '状态', dataIndex: 'status', width: 100,
      render: (status: RunStatus) => (
        <Tag color={STATUS_COLOR[status]}>{STATUS_LABEL[status]}</Tag>
      ),
    },
    {
      title: '创建时间', dataIndex: 'created_at', width: 160,
      render: (v: string) => new Date(v).toLocaleString('zh-CN'),
    },
    {
      title: '操作', width: 100,
      render: (_, record) => (
        <Button type="link" onClick={() => navigate(`/runs/${record.id}`)}>
          查看日志
        </Button>
      ),
    },
  ]

  return (
    <div>
      <Title level={4} style={{ marginBottom: 16 }}>运行记录</Title>

      <Table
        rowKey="id"
        dataSource={runs}
        columns={columns}
        loading={loading}
        pagination={{ pageSize: 10 }}
      />
    </div>
  )
}
