// 工单详情/创建页，使用 Ant Design 重写。
// id === 'new' 时为创建模式，否则为详情模式。

import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Button, Form, Input, Card, Table, Tag, Typography,
  Space, Upload, Spin, Alert, Descriptions, Divider,
} from 'antd'
import { UploadOutlined, RobotOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { ticketsApi, artifactsApi, runsApi, workflowsApi } from '../../api'
import { useAuth } from '../../context/AuthContext'
import type { Ticket, Artifact, Run, TicketStatus, TicketCreate } from '../../types'

const { Title, Text } = Typography

const STATUS_LABEL: Record<TicketStatus, string> = {
  draft: '草稿', submitted: '待审批', approved: '已审批',
  running: '执行中', done: '已完成', failed: '失败', closed: '已关闭',
}

const STATUS_COLOR: Record<TicketStatus, string> = {
  draft: 'default', submitted: 'blue', approved: 'green',
  running: 'orange', done: 'green', failed: 'red', closed: 'default',
}

export default function TicketDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [form] = Form.useForm<TicketCreate>()

  const isNew = id === 'new'

  const [ticket, setTicket] = useState<Ticket | null>(null)
  const [artifacts, setArtifacts] = useState<Artifact[]>([])
  const [runs, setRuns] = useState<Run[]>([])
  const [loading, setLoading] = useState(!isNew)
  const [submitting, setSubmitting] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<string | null>(null)
  const [error, setError] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (isNew) return
    const ticketId = Number(id)
    // 先加载工单主体，再并行加载附件和运行记录
    // 附件/运行记录失败不影响工单基本信息展示
    ticketsApi.get(ticketId)
      .then(t => {
        setTicket(t)
        // 附件和运行记录单独请求，失败只记录错误不影响主体
        artifactsApi.listByTicket(ticketId)
          .then(a => setArtifacts(a))
          .catch(() => {})
        runsApi.list(ticketId)
          .then(r => setRuns(r))
          .catch(() => {})
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [id, isNew])

  async function handleCreate(values: TicketCreate) {
    setSubmitting(true)
    try {
      const created = await ticketsApi.create(values)
      navigate(`/tickets/${created.id}`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '创建失败')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file || !ticket) return
    setUploading(true)
    try {
      const res = await artifactsApi.upload(ticket.id, file)
      setArtifacts(prev => [...prev, res.artifact])
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '上传失败')
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  async function handleAnalyze() {
    if (!ticket || artifacts.length === 0) return
    setAnalyzing(true)
    setAnalysisResult(null)
    try {
      const res = await workflowsApi.analyzeRouterConfig(ticket.id, artifacts[0].id)
      setAnalysisResult(res.analysis || res.error || '分析完成')
    } catch (err: unknown) {
      setAnalysisResult(err instanceof Error ? err.message : '分析失败')
    } finally {
      setAnalyzing(false)
    }
  }

  async function handleApprove() {
    if (!ticket) return
    try {
      const updated = await ticketsApi.approve(ticket.id)
      setTicket(updated)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '审批失败')
    }
  }

  async function handleCreateRun(runType: 'proof' | 'action') {
    if (!ticket) return
    try {
      const run = await runsApi.create(ticket.id, runType)
      setRuns(prev => [run, ...prev])
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '创建失败')
    }
  }

  // ── 创建模式 ──────────────────────────────────────────────────────────────

  if (isNew) {
    return (
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <Title level={4} style={{ margin: 0 }}>创建工单</Title>
          <Button onClick={() => navigate('/tickets')}>返回列表</Button>
        </div>

        <Card>
          {error && <Alert message={error} type="error" showIcon style={{ marginBottom: 16 }} />}
          <Form form={form} layout="vertical" onFinish={handleCreate} style={{ maxWidth: 600 }}>
            <Form.Item name="title" label="标题" rules={[{ required: true, message: '请输入标题' }]}>
              <Input placeholder="输入工单标题" />
            </Form.Item>
            <Form.Item name="description" label="描述">
              <Input.TextArea rows={4} placeholder="输入工单描述（可选）" />
            </Form.Item>
            <Form.Item>
              <Space>
                <Button type="primary" htmlType="submit" loading={submitting}>创建工单</Button>
                <Button onClick={() => navigate('/tickets')}>取消</Button>
              </Space>
            </Form.Item>
          </Form>
        </Card>
      </div>
    )
  }

  // ── 详情模式 ──────────────────────────────────────────────────────────────

  if (loading) return <Spin size="large" style={{ display: 'block', marginTop: 80, textAlign: 'center' }} />
  if (error && !ticket) return <Alert message="加载失败" description={error} type="error" showIcon style={{ margin: 24 }} />
  if (!ticket) return null

  const artifactColumns: ColumnsType<Artifact> = [
    { title: '文件名', dataIndex: 'filename' },
    { title: '类型', dataIndex: 'artifact_type', render: v => v || '—' },
    { title: '大小', dataIndex: 'size_bytes', render: (v: number) => `${(v / 1024).toFixed(1)} KB` },
    { title: '上传时间', dataIndex: 'created_at', render: (v: string) => new Date(v).toLocaleString('zh-CN') },
    {
      title: '操作',
      render: (_, a) => (
        <Button type="link" href={artifactsApi.downloadUrl(a.id)} target="_blank">下载</Button>
      ),
    },
  ]

  const runColumns: ColumnsType<Run> = [
    { title: 'ID', dataIndex: 'id', width: 80, render: v => `#${v}` },
    {
      title: '类型', dataIndex: 'run_type', width: 100,
      render: (v: string) => <Tag color={v === 'proof' ? 'purple' : 'volcano'}>{v === 'proof' ? 'Proof' : 'Action'}</Tag>,
    },
    {
      title: '状态', dataIndex: 'status', width: 100,
      render: (v: string) => <Tag color={v === 'done' ? 'green' : v === 'failed' ? 'red' : 'orange'}>{v}</Tag>,
    },
    { title: '创建时间', dataIndex: 'created_at', render: (v: string) => new Date(v).toLocaleString('zh-CN') },
    {
      title: '操作',
      render: (_, run) => (
        <Button type="link" onClick={() => navigate(`/runs/${run.id}`)}>查看日志</Button>
      ),
    },
  ]

  return (
    <div>
      {/* 页头 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Space>
          <Title level={4} style={{ margin: 0 }}>工单 #{ticket.id}</Title>
          <Tag color={STATUS_COLOR[ticket.status]}>{STATUS_LABEL[ticket.status]}</Tag>
        </Space>
        <Button onClick={() => navigate('/tickets')}>返回列表</Button>
      </div>

      {error && <Alert message={error} type="error" showIcon style={{ marginBottom: 16 }} />}

      {/* 基本信息 */}
      <Card
        title="基本信息"
        style={{ marginBottom: 16 }}
        extra={
          user?.is_admin && ticket.status === 'submitted' && (
            <Button type="primary" size="small" onClick={handleApprove}>审批通过</Button>
          )
        }
      >
        <Descriptions column={2}>
          <Descriptions.Item label="标题">{ticket.title}</Descriptions.Item>
          <Descriptions.Item label="描述">{ticket.description || '—'}</Descriptions.Item>
          <Descriptions.Item label="创建时间">{new Date(ticket.created_at).toLocaleString('zh-CN')}</Descriptions.Item>
          <Descriptions.Item label="更新时间">{new Date(ticket.updated_at).toLocaleString('zh-CN')}</Descriptions.Item>
        </Descriptions>
      </Card>

      {/* 附件 */}
      <Card
        title="附件"
        style={{ marginBottom: 16 }}
        extra={
          <Space>
            {artifacts.length > 0 && (
              <Button
                icon={<RobotOutlined />}
                size="small"
                onClick={handleAnalyze}
                loading={analyzing}
              >
                LLM 分析
              </Button>
            )}
            <Button
              icon={<UploadOutlined />}
              size="small"
              loading={uploading}
              onClick={() => fileInputRef.current?.click()}
            >
              上传附件
            </Button>
            <input ref={fileInputRef} type="file" style={{ display: 'none' }} onChange={handleUpload} />
          </Space>
        }
      >
        {analysisResult && (
          <Alert
            message="LLM 分析结果"
            description={<pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{analysisResult}</pre>}
            type="info"
            style={{ marginBottom: 16 }}
          />
        )}
        <Table rowKey="id" dataSource={artifacts} columns={artifactColumns} pagination={false} size="small" />
      </Card>

      {/* 执行记录 */}
      <Card
        title="执行记录"
        extra={
          <Space>
            <Button size="small" onClick={() => handleCreateRun('proof')}>+ Proof Run</Button>
            {ticket.status === 'approved' && (
              <Button type="primary" size="small" onClick={() => handleCreateRun('action')}>+ Action Run</Button>
            )}
          </Space>
        }
      >
        <Table rowKey="id" dataSource={runs} columns={runColumns} pagination={false} size="small" />
      </Card>
    </div>
  )
}
