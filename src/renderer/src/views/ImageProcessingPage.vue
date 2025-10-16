<template>
  <div class="image-processing-page">
    <ImageProcessing />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import ImageProcessing from '../components/ImageProcessing.vue'

const route = useRoute()

onMounted(() => {
  console.log('=== 图像处理页面已挂载 ===')
  console.log('当前路由路径:', route.path)
  console.log('当前路由名称:', route.name)
  console.log('当前完整 URL:', window.location.href)
  console.log('=========================')
})
</script>

<style scoped>
.image-processing-page {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}
</style>

