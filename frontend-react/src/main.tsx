// 应用入口，挂载 React 到 #root。
// index.css 包含全局样式，App 包含路由和 AuthProvider。

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
