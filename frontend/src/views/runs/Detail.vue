<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { getRun } from "@/api/runs";
import type { Run } from "@/types/run";
import { RUN_STATUS_MAP } from "@/types/run";
import { formatTime } from "@/utils/format";
import StatusTag from "@/components/StatusTag.vue";

const route = useRoute();
const router = useRouter();
const loading = ref(false);
const run = ref<Run | null>(null);

const fetchRun = async () => {
  loading.value = true;
  try {
    const res = await getRun(Number(route.params.id));
    run.value = res.data;
  } catch {
    ElMessage.error("获取运行详情失败");
  } finally {
    loading.value = false;
  }
};

onMounted(fetchRun);
</script>

<template>
  <div v-loading="loading">
    <div class="page-header">
      <el-button link @click="router.push('/runs')">← 返回列表</el-button>
      <h2>运行详情</h2>
    </div>

    <el-card v-if="run">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="运行ID">{{ run.id }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <StatusTag :status="run.status" :status-map="RUN_STATUS_MAP" />
        </el-descriptions-item>
        <el-descriptions-item label="工单ID">{{ run.ticket_id }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ run.run_type }}</el-descriptions-item>
        <el-descriptions-item label="脚本ID" :span="2">{{ run.script_id }}</el-descriptions-item>
        <el-descriptions-item label="退出码">{{ run.exit_code ?? "无" }}</el-descriptions-item>
        <el-descriptions-item label="执行人ID">{{ run.executed_by_id }}</el-descriptions-item>
        <el-descriptions-item label="结果摘要" :span="2">{{ run.result_summary || "无" }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatTime(run.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatTime(run.updated_at) }}</el-descriptions-item>
      </el-descriptions>

      <div v-if="run.stdout_log" class="log-section">
        <h3>标准输出</h3>
        <pre class="log-box">{{ run.stdout_log }}</pre>
      </div>
      <div v-if="run.stderr_log" class="log-section">
        <h3>错误输出</h3>
        <pre class="log-box error">{{ run.stderr_log }}</pre>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.log-section { margin-top: 24px; }
.log-section h3 { font-size: 14px; color: #666; margin-bottom: 8px; }
.log-box {
  background: #1e1e1e; color: #d4d4d4;
  padding: 16px; border-radius: 6px;
  font-size: 13px; overflow-x: auto; white-space: pre-wrap;
}
.log-box.error { color: #f48771; }
</style>