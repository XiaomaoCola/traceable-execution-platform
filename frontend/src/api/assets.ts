import request from "@/utils/request";
import type { Asset } from "@/types/asset";

interface GetAssetsParams {
  page?: number;
  page_size?: number;
  asset_type?: string;
  order_by?: string;       
  order?: "asc" | "desc";
}

interface PaginatedAssets {
  data: Asset[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export const getAssets = (params?: GetAssetsParams) =>
  request.get<PaginatedAssets>("/assets", { params });

export const getAsset = (id: number) =>
  request.get<Asset>(`/assets/${id}`);

export const createAsset = (data: Partial<Asset>) =>
  request.post<Asset>("/assets", data);

export const updateAsset = (id: number, data: Partial<Asset>) =>
  request.patch<Asset>(`/assets/${id}`, data);