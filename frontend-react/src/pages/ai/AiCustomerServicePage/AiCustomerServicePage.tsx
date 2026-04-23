// AI 客服机器人页，路由 /ai/customer-service。
// 使用暗色主题 AiChatPage 组件，注入客服蓝色主题。

import AiChatPage from '../../../components/AiChatPage/AiChatPage'
import './AiCustomerServicePage.css'

export default function AiCustomerServicePage() {
  return (
    <AiChatPage
      themeClass="theme-customer"
      title="🤖 AI 客服机器人"
      subtitle="登录后自动关联你的对话历史，上次聊到哪里这次继续"
      placeholder="请描述你遇到的问题，或直接提问"
      endpoint="/api/v1/agent/customer-service/chat"
      btnText="发送"
      tipText="支持长期对话记忆 · 跨会话上下文 · 智能问题解答"
      examplePrompts={[
        '我上次提交的工单处理到哪一步了？',
        '系统登录一直报错，该怎么解决？',
        '我想了解一下平台的资产管理功能怎么用',
      ]}
    />
  )
}
