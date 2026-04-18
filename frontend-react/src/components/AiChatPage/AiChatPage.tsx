// 暗色主题 AI 对话页共享组件。
// 供 AiFortunePage 和 AiStockPage 使用，各自通过 CSS 变量注入主题色。
// SSE 事件：tool_start / tool_result / text_chunk / error / done

import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import './AiChatPage.css'

export interface AiChatPageProps {
  title: string
  subtitle: string
  placeholder: string
  endpoint: string
  tipText?: string
  btnText?: string
  toolNames?: Record<string, string>
  toolIcons?: Record<string, string>
  examplePrompts?: string[]
  /** 页面根元素额外 className，用于注入主题 CSS 变量 */
  themeClass: string
}

interface ToolStep {
  tool: string
  status: 'calling' | 'done'
  result?: string
}

interface Turn {
  userText: string
  steps: ToolStep[]
  answer: string
  error?: string
}

export default function AiChatPage({
  title,
  subtitle,
  placeholder,
  endpoint,
  tipText,
  btnText = '发送',
  toolNames = {},
  toolIcons = {},
  examplePrompts = [],
  themeClass,
}: AiChatPageProps) {
  const navigate = useNavigate()
  const [turns, setTurns] = useState<Turn[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const abortRef = useRef<AbortController | null>(null)
  const chatBoxRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    chatBoxRef.current?.scrollTo({ top: chatBoxRef.current.scrollHeight, behavior: 'smooth' })
  }, [turns])

  useEffect(() => {
    return () => { abortRef.current?.abort() }
  }, [])

  async function handleSend() {
    const text = input.trim()
    if (!text || loading) return

    setInput('')
    setLoading(true)

    const controller = new AbortController()
    abortRef.current = controller

    const newTurn: Turn = { userText: text, steps: [], answer: '' }
    setTurns(prev => [...prev, newTurn])
    const turnIdx = turns.length

    try {
      const token = localStorage.getItem('access_token')
      const resp = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ message: text }),
        signal: controller.signal,
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
            const event = JSON.parse(part.slice(5).trim())
            setTurns(prev => {
              const copy = [...prev]
              const turn = { ...copy[turnIdx] }

              if (event.type === 'tool_start') {
                turn.steps = [...turn.steps, { tool: event.tool ?? '', status: 'calling' }]
              } else if (event.type === 'tool_result') {
                turn.steps = turn.steps.map(s =>
                  s.tool === event.tool && s.status === 'calling'
                    ? { ...s, status: 'done', result: event.result }
                    : s
                )
              } else if (event.type === 'text_chunk') {
                turn.answer = turn.answer + (event.content ?? '')
              } else if (event.type === 'error') {
                turn.error = event.content ?? '未知错误'
              }

              copy[turnIdx] = turn
              return copy
            })
          } catch { continue }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') return
      const msg = err instanceof Error ? err.message : '请求失败'
      setTurns(prev => {
        const copy = [...prev]
        copy[turnIdx] = { ...copy[turnIdx], error: msg }
        return copy
      })
    } finally {
      setLoading(false)
      abortRef.current = null
    }
  }

  function escapeHtml(s: string) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  }

  return (
    <div className={`ai-page ${themeClass}`}>
      <div className="ai-container">
        {/* 返回按钮 */}
        <div className="ai-topbar">
          <button className="ai-back-btn" onClick={() => navigate('/ai')}>← 返回</button>
        </div>

        {/* 标题 */}
        <h1 className="ai-title">{title}</h1>
        <p className="ai-subtitle">{subtitle}</p>

        {/* 输入区 */}
        <div className="ai-input-area">
          <textarea
            className="ai-textarea"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
            }}
            placeholder={placeholder}
            disabled={loading}
          />
          <button className="ai-send-btn" onClick={handleSend} disabled={loading || !input.trim()}>
            {loading ? '生成中…' : btnText}
          </button>
        </div>

        {/* 对话框 */}
        <div className="ai-chat-box" ref={chatBoxRef}>
          {turns.length === 0 && (
            <div className="ai-placeholder">
              {examplePrompts.length > 0
                ? examplePrompts.map(p => <div key={p}>💬 {p}</div>)
                : '发送消息开始对话'}
            </div>
          )}

          {turns.map((turn, i) => (
            <div key={i}>
              {/* 用户消息 */}
              <div className="ai-user-bubble">你：{turn.userText}</div>

              {/* 工具调用步骤 */}
              {turn.steps.map((step, j) => (
                <div key={j} className={`ai-step ${step.status === 'calling' ? 'calling' : 'done'}`}>
                  <div className="ai-step-icon">
                    {toolIcons[step.tool] ?? '⚙️'}
                  </div>
                  <div className="ai-step-body">
                    <div className="ai-step-label">
                      {step.status === 'done' ? '✓ ' : ''}{toolNames[step.tool] ?? step.tool}
                    </div>
                    <div className="ai-step-detail">
                      {step.status === 'calling'
                        ? <><div className="ai-spinner" />请求中…</>
                        : <span dangerouslySetInnerHTML={{ __html: escapeHtml(step.result ?? '') }} />
                      }
                    </div>
                  </div>
                </div>
              ))}

              {/* 最终回答 */}
              {turn.answer && (
                <div className="ai-answer">{turn.answer}</div>
              )}

              {/* 错误 */}
              {turn.error && (
                <div className="ai-error">出错了：{turn.error}</div>
              )}

              {/* 生成中光标 */}
              {loading && i === turns.length - 1 && !turn.answer && !turn.error && (
                <div className="ai-step calling">
                  <div className="ai-step-icon">🤔</div>
                  <div className="ai-step-body">
                    <div className="ai-step-detail"><div className="ai-spinner" />思考中…</div>
                  </div>
                </div>
              )}
            </div>
          ))}
          <div ref={bottomRef} />
        </div>

        {tipText && <p className="ai-tip">{tipText}</p>}
      </div>
    </div>
  )
}
