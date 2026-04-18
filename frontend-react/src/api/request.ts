// 底层 fetch 封装，所有 API 模块都基于这个函数。
// 统一处理：token 注入、Content-Type 设置、错误解析。

const BASE_URL = '/api/v1'

export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('access_token')

  // 文件上传时 body 是 FormData，不能手动设置 Content-Type，
  // 否则浏览器无法自动生成正确的 multipart boundary
  const isFormData = options.body instanceof FormData

  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(!isFormData ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  })

  if (!response.ok) {
    // 后端错误统一放在 detail 字段（FastAPI 默认格式）
    const error = await response.json().catch(() => ({ detail: '请求失败' }))
    throw new Error(error.detail || '请求失败')
  }

  return response.json()
}

export { BASE_URL }
