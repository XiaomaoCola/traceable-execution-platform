<script setup lang="ts">
/**
 * 工单列表页
 *
 * 数据流：
 *   页面加载
 *     └─ onMounted → fetchTickets() → 拉取第一页数据 → 渲染表格
 *
 *   用户翻页 / 改每页条数
 *     └─ handlePageChange / handleSizeChange → fetchTickets() → 刷新表格
 *
 *   管理员点击审批
 *     └─ handleApprove() → 确认弹窗 → 乐观更新状态 → approveTicket()
 *                       → 失败时回滚状态
 */
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";       // 消息提示 & 确认弹窗
import { getTickets, approveTicket } from "@/api/tickets";
import type { Ticket } from "@/types/ticket";
import { TICKET_STATUS_MAP } from "@/types/ticket";           // 状态码 → 中文的映射表
import { useUserStore } from "@/stores/user";
import { formatTime } from "@/utils/format";                  // 时间格式化工具
import StatusTag from "@/components/StatusTag.vue";           // 状态标签组件
import { useTableQuery } from "@/composables/useTableQuery";  // 【新增】

const router = useRouter();
const userStore = useUserStore();
const loading = ref(false);                                   // 控制表格加载动画
const tickets = ref<Ticket[]>([]);                            // 当前页的工单数据
const error = ref(false);                                     // 【新增】请求失败时为 true，显示错误状态

const keyword = ref("");                                      // 【新增】搜索筛选条件
const filterStatus = ref("");
const filterAssetId = ref<number | undefined>(undefined);
const dateRange = ref<[Date, Date] | null>(null);

const fetchTickets = async () => {
  error.value = false;
  loading.value = true;
  try {
    const res = await getTickets({ 
      page: currentPage.value, 
      page_size: pageSize.value,
      keyword: keyword.value || undefined,           
      status: filterStatus.value || undefined,      
      asset_id: filterAssetId.value, 
      start_date: dateRange.value?.[0]?.toISOString(),
      end_date: dateRange.value?.[1]?.toISOString(),
      order_by: sortBy.value,                        
      order: sortOrder.value                            
    });
    tickets.value = res.data.data;        // 之前是 res.data
    total.value = res.data.total;         // 之前是手动估算的
    
  } catch {
    error.value = true;
    ElMessage.error("获取工单列表失败");
  } finally {
    loading.value = false;
  }
};

// 从 composable 里取分页和排序
const {
  currentPage,
  pageSize,
  total,
  sortBy,
  sortOrder,
  handlePageChange,
  handleSizeChange,
  handleSortChange
} = useTableQuery(fetchTickets)  // ← fetchTickets 在下面定义，先声明再传入

// 【新增】点搜索按钮时重置到第一页再拉取
const handleSearch = () => {
  currentPage.value = 1;
  fetchTickets();
};

// 【新增】重置所有筛选条件
const handleReset = () => {
  keyword.value = "";
  filterStatus.value = "";
  filterAssetId.value = undefined;
  dateRange.value = null;
  currentPage.value = 1;
  fetchTickets();
};

const handleApprove = async (row: Ticket) => {
  // 先弹出确认框，防止误操作
  await ElMessageBox.confirm(`确认通过工单「${row.title}」？`, "提示", {
    confirmButtonText: "确认", cancelButtonText: "取消", type: "warning"
  });

  // 【新增】乐观更新：先在前端改状态，用户立刻看到变化，不用等后端响应
  const target = tickets.value.find(t => t.id === row.id);
  if (target) target.status = "approved";

  try {
    //throw new Error("测试回滚"); 
    //← 到时候加这一行测试乐观更新功能，效果应该是那条工单的状态瞬间变成"已审批"
    // 紧接着状态变回原来的值
    await approveTicket(row.id);
    ElMessage.success("审批成功");
  } catch {
    // 【新增】请求失败时回滚：把状态改回审批前的值
    if (target) target.status = row.status;
    ElMessage.error("审批失败");
  }
};

// 页面挂载时自动拉取第一页数据
onMounted(fetchTickets);
</script>

<template>
  <div>
    <!-- 页头：标题 + 创建按钮 -->
    <div class="page-header">
      <h2>工单列表</h2>
      <el-button type="primary" @click="router.push('/tickets/create')">+ 创建工单</el-button>
    </div>

<!-- 【新增】搜索筛选栏 -->
  <div class="search-bar">
    <el-input
      v-model="keyword"
      placeholder="搜索工单标题"
      style="width:200px"
      clearable
      @keyup.enter="handleSearch"
    />
    <el-select
      v-model="filterStatus"
      placeholder="状态筛选"
      style="width:150px"
      clearable
    >
      <el-option
        v-for="(label, value) in TICKET_STATUS_MAP"
        :key="value"
        :label="label"
        :value="value"
      />
    </el-select>
    <el-date-picker
      v-model="dateRange"
      type="daterange"
      range-separator="至"
      start-placeholder="开始日期"
      end-placeholder="结束日期"
      style="width:280px"
    />
    <el-button type="primary" @click="handleSearch">搜索</el-button>
    <el-button @click="handleReset">重置</el-button>
  </div>

    <!-- 【新增】错误状态：请求失败时显示，提供重试入口 -->
    <div v-if="error">
      <el-empty description="加载失败，请稍后重试">
        <el-button @click="fetchTickets">重试</el-button>
      </el-empty>
    </div>

    <!-- 【新增】空状态：请求成功但没有数据时显示 -->
    <el-empty
      v-else-if="!loading && tickets.length === 0"
      description="暂无工单"
    />

    <!-- 工单表格，loading 时显示加载动画 -->
    <!-- 【修改】原来直接渲染表格，现在加了 v-else，只在有数据时显示 -->
    <el-table v-else :data="tickets" v-loading="loading" border stripe @sort-change="handleSortChange">
      <el-table-column prop="id" label="ID" width="70" sortable="custom" />
      <el-table-column prop="title" label="标题" min-width="150" />
      <!-- show-overflow-tooltip：内容过长时悬浮显示完整文本 -->
      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />

      <!-- 状态列：用 StatusTag 组件渲染带颜色的状态标签 -->
      <el-table-column prop="status" label="状态" width="100" sortable="custom">
        <template #default="{ row }">
          <StatusTag :status="row.status" :status-map="TICKET_STATUS_MAP" />
        </template>
      </el-table-column>

      <el-table-column prop="created_by_id" label="提交人" width="100" sortable="custom" />

      <!-- 时间列：用 formatTime 工具函数格式化时间戳 -->
      <el-table-column prop="created_at" label="创建时间" width="180" sortable="custom">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>

      <!-- 操作列：固定在右侧不随横向滚动消失 -->
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="router.push(`/tickets/${row.id}`)">查看</el-button>
          <!-- 审批按钮：仅管理员可见，且工单状态必须是 submitted -->
          <el-button
            v-if="userStore.userInfo?.is_admin && row.status === 'submitted'"
            link type="success"
            @click="handleApprove(row)"
          >审批</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页器：右对齐，支持切换页码和每页条数 -->
    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50]"
        :total="total"
        layout="total, sizes, prev, pager, next"
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
      />
    </div>
  </div>
</template>

<style scoped>
/*
 * scoped 表示这里的样式只作用于当前组件，不会影响其他页面
 * 即使别的组件也有 .pagination 这个类名，也不会互相干扰
 */
.pagination {
  margin-top: 20px;          /* 和上方表格保持 20px 间距 */
  display: flex;             /* 开启 flex 布局 */
  justify-content: flex-end; /* 让分页器靠右对齐 */
}
.search-bar {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 16px;
}
</style>