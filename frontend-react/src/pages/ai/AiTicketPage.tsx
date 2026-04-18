// AI 工单助手页，路由 /ai/ticket，归属工单系统侧边栏。
// 调用 agent2 接口，可以辅助分析工单、设备配置等问题。

import AiChatPage from '../../components/AiChatPage'

export default function AiTicketPage() {
  return (
    <AiChatPage
      title="AI 工单助手"
      subtitle="输入问题，AI 帮你分析工单内容、设备配置或操作建议"
      placeholder="例如：帮我分析这台交换机的配置变更风险"
      endpoint="/api/v1/agent2/ticket"
      examplePrompts={[
        '帮我分析一下路由器配置变更的风险',
        '如何排查 OSPF 邻居断开的问题？',
        '这条 ACL 规则有没有安全隐患？',
      ]}
    />
  )
}
