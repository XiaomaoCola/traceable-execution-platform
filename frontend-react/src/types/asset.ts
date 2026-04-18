// 资产相关类型，对应后端 schemas/asset.py。
// 资产（Asset）代表一台实体设备，如交换机、路由器，可关联多张工单。

export interface Asset {
  id: number
  name: string
  asset_type: string
  serial_number: string | null
  location: string | null
  description: string | null
  created_by_id: number
  created_at: string
  updated_at: string
}

export interface AssetCreate {
  name: string
  asset_type: string
  serial_number?: string
  location?: string
  description?: string
}
