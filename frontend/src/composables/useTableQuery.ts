/**
 * useTableQuery
 *
 * 封装表格通用的分页、排序、防抖逻辑
 * 供 tickets、assets、runs 等列表页复用
 */
import { ref } from "vue"
import { useDebounceFn } from "@vueuse/core"

export function useTableQuery(fetchFn: () => void, defaultOrderBy = "created_at") {
  // 分页状态
  const currentPage = ref(1)
  const pageSize = ref(10)
  const total = ref(0)

  // 排序状态
  const sortBy = ref(defaultOrderBy)
  const sortOrder = ref<"asc" | "desc">("desc")

  // 防抖版本，300ms 内连续触发只执行最后一次
  const debouncedFetch = useDebounceFn(fetchFn, 300)

  // 切换页码时重新拉取数据
  const handlePageChange = (page: number) => {
    currentPage.value = page
    fetchFn()
  }

  // 切换每页条数时，重置到第一页再拉取
  const handleSizeChange = (size: number) => {
    pageSize.value = size
    currentPage.value = 1
    fetchFn()
  }

  // 表格排序变化时重新请求后端
  const handleSortChange = ({ prop, order }: { prop: string; order: string | null }) => {
    sortBy.value = prop || defaultOrderBy
    sortOrder.value = order === "ascending" ? "asc" : "desc"
    currentPage.value = 1
    debouncedFetch()
  }

  return {
    currentPage,
    pageSize,
    total,
    sortBy,
    sortOrder,
    handlePageChange,
    handleSizeChange,
    handleSortChange
  }
}