// 资产相关 API：增删改查。
// 对应后端 /api/v1/assets/* 路由。

import { request } from './request'
import type { Asset, AssetCreate } from '../types'

export const assetsApi = {
  list: () => request<Asset[]>('/assets'),

  get: (id: number) => request<Asset>(`/assets/${id}`),

  create: (data: AssetCreate) =>
    request<Asset>('/assets', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (id: number, data: Partial<AssetCreate>) =>
    request<Asset>(`/assets/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
}
