// AI Agent SSE 事件类型。
// 三个 agent（算命师、量化先知、工单助手）共用同一套事件格式，
// 前端用这些类型来解析流式响应。

export type SseEventType = 'tool_start' | 'tool_result' | 'text_chunk' | 'error' | 'done'

export interface SseEvent {
  type: SseEventType
  tool?: string                     // tool_start / tool_result 时有值
  args?: Record<string, unknown>    // tool_start 时的工具入参
  result?: string                   // tool_result 时的工具返回内容
  content?: string                  // text_chunk / error 时的文本
}
