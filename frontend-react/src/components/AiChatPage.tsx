// 通用 AI 对话页组件，三个 Agent 共用这一套 UI。
// 新增：停止按钮（AbortController 中断请求，保留已输出内容）
//      对话持久化（localStorage 按 endpoint 存储，换页面再回来内容还在）

import { useState, useRef, useEffect } from 'react'
import { Button, Input, Typography, Tag } from 'antd'
import { SendOutlined, StopOutlined, DeleteOutlined } from '@ant-design/icons'
import type { SseEvent } from '../types'

const { Text } = Typography

interface AiChatPageProps {
  title: string
  subtitle: string
  placeholder: string
  endpoint: string
  examplePrompts?: string[]
}

interface Message {
  role: 'user' | 'assistant'
  blocks: Block[]
}

type Block =
  | { kind: 'text'; content: string }
  | { kind: 'tool'; tool: string; status: 'running' | 'done'; result?: string }

// localStorage key 根据 endpoint 生成，每个 Agent 独立存储
function storageKey(endpoint: string) {
  return `chat_history_${endpoint.replace(/\//g, '_')}`
}

function loadMessages(endpoint: string): Message[] {
  try {
    const raw = localStorage.getItem(storageKey(endpoint))
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function saveMessages(endpoint: string, messages: Message[]) {
  localStorage.setItem(storageKey(endpoint), JSON.stringify(messages))
}

export default function AiChatPage({
  title,
  subtitle,
  placeholder,
  endpoint,
  examplePrompts = [],
}: AiChatPageProps) {
  // 初始化时从 localStorage 恢复对话历史
  const [messages, setMessages] = useState<Message[]>(() => loadMessages(endpoint))
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  // AbortController 用于中断正在进行的请求
  const abortRef = useRef<AbortController | null>(null)

  // 消息变化时同步到 localStorage
  useEffect(() => {
    saveMessages(endpoint, messages)
  }, [messages, endpoint])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // 组件卸载时取消正在进行的请求，避免内存泄漏
  useEffect(() => {
    return () => { abortRef.current?.abort() }
  }, [])

  async function handleSend() {
    const text = input.trim()
    if (!text || loading) return

    setInput('')
    setLoading(true)

    // 创建新的 AbortController，保存引用供停止按钮使用
    const controller = new AbortController()
    abortRef.current = controller

    setMessages(prev => [
      ...prev,
      { role: 'user', blocks: [{ kind: 'text', content: text }] },
      { role: 'assistant', blocks: [] },
    ])

    try {
      const token = localStorage.getItem('access_token')
      const resp = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ message: text }),
        signal: controller.signal, // 绑定 abort 信号
      })

      if (!resp.ok) throw new Error(`请求失败：${resp.status}`)

      const reader = resp.body!.getReader()
      const decoder = new TextDecoder()
      let buf = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buf += decoder.decode(value, { stream: true })
        const parts = buf.split('\n\n')
        buf = parts.pop() ?? ''

        for (const part of parts) {
          if (!part.startsWith('data:')) continue
          try {
            const event: SseEvent = JSON.parse(part.slice('data:'.length).trim())
            handleSseEvent(event)
          } catch { continue }
        }
      }
    } catch (err: unknown) {
      // AbortError 是用户主动停止，不显示错误
      if (err instanceof Error && err.name === 'AbortError') return
      const msg = err instanceof Error ? err.message : '请求失败'
      setMessages(prev => {
        const copy = [...prev]
        const last = { ...copy[copy.length - 1] }
        last.blocks = [...last.blocks, { kind: 'text', content: `❌ ${msg}` }]
        copy[copy.length - 1] = last
        return copy
      })
    } finally {
      setLoading(false)
      abortRef.current = null
    }
  }

  // 停止按钮：中断请求，已输出的内容保留
  function handleStop() {
    abortRef.current?.abort()
  }

  // 清空对话
  function handleClear() {
    setMessages([])
    localStorage.removeItem(storageKey(endpoint))
  }

  function handleSseEvent(event: SseEvent) {
    setMessages(prev => {
      const copy = [...prev]
      const last = { ...copy[copy.length - 1] }
      const blocks = [...last.blocks]

      if (event.type === 'tool_start') {
        blocks.push({ kind: 'tool', tool: event.tool ?? '工具', status: 'running' })
      } else if (event.type === 'tool_result') {
        const idx = blocks.findLastIndex(
          b => b.kind === 'tool' && b.tool === event.tool && b.status === 'running'
        )
        if (idx !== -1) {
          blocks[idx] = { kind: 'tool', tool: event.tool ?? '工具', status: 'done', result: event.result }
        }
      } else if (event.type === 'text_chunk') {
        const lastBlock = blocks[blocks.length - 1]
        if (lastBlock?.kind === 'text') {
          blocks[blocks.length - 1] = { kind: 'text', content: lastBlock.content + (event.content ?? '') }
        } else {
          blocks.push({ kind: 'text', content: event.content ?? '' })
        }
      } else if (event.type === 'error') {
        blocks.push({ kind: 'text', content: `❌ ${event.content ?? '未知错误'}` })
      }

      last.blocks = blocks
      copy[copy.length - 1] = last
      return copy
    })
  }

  return (
    <div style={styles.page}>
      {/* 页面标题 + 清空按钮 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
        <div>
          <Text strong style={{ fontSize: 18 }}>{title}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: 13 }}>{subtitle}</Text>
        </div>
        {messages.length > 0 && (
          <Button icon={<DeleteOutlined />} size="small" onClick={handleClear} disabled={loading}>
            清空对话
          </Button>
        )}
      </div>

      {/* 消息区 */}
      <div style={styles.messageArea}>
        {messages.length === 0 && (
          <div style={styles.emptyTip}>
            <div style={{ fontSize: 40, marginBottom: 12 }}>✨</div>
            <Text type="secondary">发送消息开始对话</Text>
            {examplePrompts.length > 0 && (
              <div style={styles.examples}>
                {examplePrompts.map(p => (
                  <Button key={p} size="small" shape="round" onClick={() => setInput(p)}>
                    {p}
                  </Button>
                ))}
              </div>
            )}
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} style={msg.role === 'user' ? styles.userRow : styles.assistantRow}>
            <div style={msg.role === 'user' ? styles.userBubble : styles.assistantBubble}>
              {msg.blocks.map((block, j) => {
                if (block.kind === 'text') {
                  return <span key={j} style={{ whiteSpace: 'pre-wrap' }}>{block.content}</span>
                }
                return (
                  <div key={j} style={styles.toolBlock}>
                    <Tag color={block.status === 'running' ? 'processing' : 'success'}>
                      {block.status === 'running' ? '⚙️ 执行中' : '✅ 完成'}
                    </Tag>
                    <Text style={{ fontSize: 12, color: '#4f6ef7' }}>{block.tool}</Text>
                  </div>
                )
              })}
              {/* 流式输出时的光标 */}
              {loading && msg.role === 'assistant' && i === messages.length - 1 && (
                <span style={styles.cursor}>▍</span>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* 输入区 */}
      <div style={styles.inputArea}>
        <Input.TextArea
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
          }}
          placeholder={placeholder}
          autoSize={{ minRows: 2, maxRows: 5 }}
          disabled={loading}
          style={{ flex: 1 }}
        />
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {loading ? (
            // 生成中显示停止按钮
            <Button
              danger
              icon={<StopOutlined />}
              onClick={handleStop}
              style={{ minWidth: 80 }}
            >
              停止
            </Button>
          ) : (
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSend}
              disabled={!input.trim()}
              style={{ minWidth: 80 }}
            >
              发送
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  page: { display: 'flex', flexDirection: 'column', height: '100%' },
  messageArea: {
    flex: 1, overflowY: 'auto', padding: '8px 0',
    display: 'flex', flexDirection: 'column', gap: 16,
  },
  emptyTip: {
    flex: 1, display: 'flex', flexDirection: 'column',
    alignItems: 'center', justifyContent: 'center', paddingTop: 60,
  },
  examples: {
    display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 16, justifyContent: 'center',
  },
  userRow: { display: 'flex', justifyContent: 'flex-end' },
  assistantRow: { display: 'flex', justifyContent: 'flex-start' },
  userBubble: {
    maxWidth: '72%', background: '#4f6ef7', color: '#fff',
    borderRadius: '12px 12px 2px 12px', padding: '10px 14px',
    fontSize: 14, lineHeight: 1.6,
  },
  assistantBubble: {
    maxWidth: '80%', background: '#fff', border: '1px solid #e8e8e8',
    borderRadius: '12px 12px 12px 2px', padding: '10px 14px',
    fontSize: 14, lineHeight: 1.8, boxShadow: '0 1px 4px rgba(0,0,0,0.05)',
  },
  toolBlock: {
    display: 'flex', alignItems: 'center', gap: 6,
    padding: '4px 8px', background: '#f5f7ff',
    border: '1px solid #e0e7ff', borderRadius: 6, marginBottom: 6,
  },
  cursor: { display: 'inline-block', color: '#4f6ef7' },
  inputArea: {
    display: 'flex', gap: 12, alignItems: 'flex-end',
    padding: '12px 0 0', borderTop: '1px solid #f0f0f0',
  },
}
