<script setup lang="ts">
import { ref, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { getTicketArtifacts, uploadArtifact, downloadArtifact } from "@/api/artifacts";
import type { Artifact } from "@/types/artifact";
import { formatTime, formatSize } from "@/utils/format";

const props = defineProps<{ ticketId: number }>();

const artifacts = ref<Artifact[]>([]);
const uploading = ref(false);
const uploadDescription = ref("");
const uploadType = ref("");

const fetchArtifacts = async () => {
  try {
    const res = await getTicketArtifacts(props.ticketId);
    artifacts.value = res.data.data; // 之前是 res.data.filter(a => !a.is_deleted)
  } catch {
    ElMessage.error("获取附件失败");
  }
};
const handleUpload = async (file: File) => {
  uploading.value = true;
  try {
    await uploadArtifact(props.ticketId, file, uploadType.value, uploadDescription.value);
    ElMessage.success("上传成功");
    uploadDescription.value = "";
    uploadType.value = "";
    fetchArtifacts();
  } catch {
    ElMessage.error("上传失败");
  } finally {
    uploading.value = false;
  }
  return false;
};

const handleDownload = async (artifact: Artifact) => {
  try {
    const res = await downloadArtifact(artifact.id);
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement("a");
    link.href = url;
    link.download = artifact.filename;
    link.click();
    window.URL.revokeObjectURL(url);
  } catch {
    ElMessage.error("下载失败");
  }
};

onMounted(fetchArtifacts);
</script>

<template>
  <el-card>
    <template #header><span>附件</span></template>
    <div class="upload-area">
      <el-input v-model="uploadType" placeholder="附件类型（选填）" style="width:180px" />
      <el-input v-model="uploadDescription" placeholder="附件描述（选填）" style="width:240px" />
      <el-upload :before-upload="handleUpload" :show-file-list="false" :disabled="uploading">
        <el-button type="primary" :loading="uploading">上传附件</el-button>
      </el-upload>
    </div>
    <el-table :data="artifacts" border style="margin-top:16px">
      <el-table-column prop="filename" label="文件名" min-width="150" />
      <el-table-column prop="artifact_type" label="类型" width="120" />
      <el-table-column prop="description" label="描述" min-width="150" show-overflow-tooltip />
      <el-table-column prop="size_bytes" label="大小" width="100">
        <template #default="{ row }">{{ formatSize(row.size_bytes) }}</template>
      </el-table-column>
      <el-table-column prop="created_at" label="上传时间" width="180">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleDownload(row)">下载</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="artifacts.length === 0" description="暂无附件" />
  </el-card>
</template>

<style scoped>
.upload-area { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
</style>