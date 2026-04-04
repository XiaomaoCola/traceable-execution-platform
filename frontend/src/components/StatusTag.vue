<script setup lang="ts">
defineProps<{
  status: string
  statusMap: Record<string, { label: string; type: string }>
}>()
</script>

<template>
  <el-tag :type="statusMap[status]?.type as any">
    {{ statusMap[status]?.label || status }}
  </el-tag>
</template>