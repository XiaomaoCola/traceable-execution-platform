// AI 量化先知页，路由 /ai/stock。
// 使用暗色主题 AiChatPage 组件，注入量化先知绿色终端主题。

import AiChatPage from '../../../components/AiChatPage/AiChatPage'
import './AiStockPage.css'

const TOOL_NAMES: Record<string, string> = {
  get_astock_indices: '拉取三大指数行情',
  predict_trend:      '动量模型预测区间',
}

const TOOL_ICONS: Record<string, string> = {
  get_astock_indices: '📡',
  predict_trend:      '🔢',
}

export default function AiStockPage() {
  return (
    <AiChatPage
      themeClass="theme-stock"
      title="📈 AI 量化先知"
      subtitle="实时拉取 A 股三大指数 · 动量模型预测未来 5 日区间"
      placeholder="例：帮我分析今天 A 股大盘走势，预测未来几天的情况"
      endpoint="/api/v1/agent1/stock"
      btnText="分析"
      tipText="⚠️ 以上内容仅供技术演示，不构成任何投资建议"
      toolNames={TOOL_NAMES}
      toolIcons={TOOL_ICONS}
      examplePrompts={[
        '今天大盘行情怎么样？',
        '分析一下沪深300近期走势',
        '现在适合入场吗？',
      ]}
    />
  )
}
