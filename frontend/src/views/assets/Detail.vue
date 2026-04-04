<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, type FormInstance } from "element-plus";
import { getAsset, updateAsset } from "@/api/assets";
import type { Asset } from "@/types/asset";
import { formatTime } from "@/utils/format";

const route = useRoute();
const router = useRouter();
const loading = ref(false);
const asset = ref<Asset | null>(null);
const editing = ref(false);
const formRef = ref<FormInstance>();

const editForm = ref({ name: "", asset_type: "", serial_number: "", location: "", description: "" });

const fetchAsset = async () => {
  loading.value = true;
  try {
    const res = await getAsset(Number(route.params.id));
    asset.value = res.data;
  } catch {
    ElMessage.error("获取资产详情失败");
  } finally {
    loading.value = false;
  }
};

const startEdit = () => {
  if (!asset.value) return;
  editForm.value = {
    name: asset.value.name,
    asset_type: asset.value.asset_type,
    serial_number: asset.value.serial_number,
    location: asset.value.location,
    description: asset.value.description
  };
  editing.value = true;
};

const saveEdit = async () => {
  if (!formRef.value || !asset.value) return;
  await formRef.value.validate(async valid => {
    if (!valid) return;
    loading.value = true;
    try {
      await updateAsset(asset.value!.id, editForm.value);
      ElMessage.success("保存成功");
      editing.value = false;
      fetchAsset();
    } catch {
      ElMessage.error("保存失败");
    } finally {
      loading.value = false;
    }
  });
};

onMounted(fetchAsset);
</script>

<template>
  <div v-loading="loading">
    <div class="page-header">
      <el-button link @click="router.push('/assets')">← 返回列表</el-button>
      <h2>资产详情</h2>
      <div style="display:flex; gap:8px">
        <el-button v-if="!editing" @click="startEdit">编辑</el-button>
        <template v-if="editing">
          <el-button type="primary" @click="saveEdit">保存</el-button>
          <el-button @click="editing = false">取消</el-button>
        </template>
      </div>
    </div>

    <el-card v-if="asset && !editing">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="资产ID">{{ asset.id }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ asset.asset_type }}</el-descriptions-item>
        <el-descriptions-item label="名称" :span="2">{{ asset.name }}</el-descriptions-item>
        <el-descriptions-item label="序列号">{{ asset.serial_number || "无" }}</el-descriptions-item>
        <el-descriptions-item label="位置">{{ asset.location || "无" }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ asset.description || "无" }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatTime(asset.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatTime(asset.updated_at) }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card v-if="asset && editing">
      <el-form ref="formRef" :model="editForm" label-width="80px">
        <el-form-item label="名称" :rules="[{ required: true, message: '请输入名称' }]">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="类型" :rules="[{ required: true, message: '请输入类型' }]">
          <el-input v-model="editForm.asset_type" />
        </el-form-item>
        <el-form-item label="序列号"><el-input v-model="editForm.serial_number" /></el-form-item>
        <el-form-item label="位置"><el-input v-model="editForm.location" /></el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>