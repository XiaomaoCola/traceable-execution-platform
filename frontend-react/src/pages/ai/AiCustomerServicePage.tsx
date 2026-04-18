// AI 客服机器人页，路由 /ai/customer-service。
// 直接复用 AiChatPage，传入客服专属配置项。
//
// 功能介绍：
//   · 基于用户身份的长期对话记忆：每次登录后继续上次对话，无需重新说明背景
//   · 登录态自动关联：后端按当前登录用户 ID 维护独立的对话历史，无需手动选择会话
//   · 流式输出：回答逐字实时显示，无需等待完整响应
//   · 上下文感知：可记住你的姓名、问题背景、之前的处理进展，跨会话连贯对话
//   · 智能问答：支持咨询产品使用、反馈问题、查询订单状态等常见客服场景

import AiChatPage from '../../components/AiChatPage'

export default function AiCustomerServicePage() {
  return (
    <AiChatPage
      title="AI 客服机器人"
      subtitle="登录后自动关联你的对话历史，上次聊到哪里这次继续"
      placeholder="请描述你遇到的问题，或直接提问"
      endpoint="/api/v1/agent/customer-service/chat"
      examplePrompts={[
        '我上次提交的工单处理到哪一步了？',
        '系统登录一直报错，该怎么解决？',
        '我想了解一下平台的资产管理功能怎么用',
      ]}
    />
  )
}
