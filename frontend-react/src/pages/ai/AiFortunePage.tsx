// AI 算命师页，路由 /ai/fortune。
// 直接复用 AiChatPage，传入算命师专属的配置项。

import AiChatPage from '../../components/AiChatPage'

export default function AiFortunePage() {
  return (
    <AiChatPage
      title="AI 算命师"
      subtitle="输入你的出生年月日，AI 帮你推算今日运势"
      placeholder="例如：我1990年5月15日出生，帮我算一下今日运势"
      endpoint="/api/v1/agent/fortune"
      examplePrompts={[
        '我1990年5月15日出生，今日运势如何？',
        '我是1985年8月8日生的，帮我看看近期财运',
        '属龙的今年运势怎么样？',
      ]}
    />
  )
}
