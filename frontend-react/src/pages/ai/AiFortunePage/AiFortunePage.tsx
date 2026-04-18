// AI 算命师页，路由 /ai/fortune。
// 使用暗色主题 AiChatPage 组件，注入算命师紫色主题。

import AiChatPage from '../../../components/AiChatPage/AiChatPage'
import './AiFortunePage.css'

const TOOL_NAMES: Record<string, string> = {
  get_current_date: '查询今日日期',
  get_weather:      '查询实时天气',
  get_zodiac:       '推算星座命盘',
}

const TOOL_ICONS: Record<string, string> = {
  get_current_date: '📅',
  get_weather:      '🌤️',
  get_zodiac:       '⭐',
}

export default function AiFortunePage() {
  return (
    <AiChatPage
      themeClass="theme-fortune"
      title="🔮 AI 算命师"
      subtitle="告诉我你的生日和所在城市，我来算今日运势"
      placeholder="例：我1990年5月15日出生，现在在上海，帮我算算今日运势"
      endpoint="/api/v1/agent/fortune"
      btnText="占卜"
      tipText="Agent 会自动调用工具：查今日日期 · 查实时天气 · 推算星座生肖"
      toolNames={TOOL_NAMES}
      toolIcons={TOOL_ICONS}
      examplePrompts={[
        '我1990年5月15日出生，今日运势如何？',
        '我是1985年8月8日生的，帮我看看近期财运',
        '属龙的今年运势怎么样？',
      ]}
    />
  )
}
