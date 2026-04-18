// AI 量化先知页，路由 /ai/stock。
// 调用 agent1 接口，能获取 A 股三大指数实时行情并给出短期走势分析。

import AiChatPage from '../../components/AiChatPage'

export default function AiStockPage() {
  return (
    <AiChatPage
      title="AI 量化先知"
      subtitle="基于 A 股实时行情，AI 给出短期走势分析与操作建议"
      placeholder="例如：现在大盘怎么样？沪深300近期走势如何？"
      endpoint="/api/v1/agent1/stock"
      examplePrompts={[
        '今天大盘行情怎么样？',
        '分析一下沪深300近期走势',
        '现在适合入场吗？',
      ]}
    />
  )
}
