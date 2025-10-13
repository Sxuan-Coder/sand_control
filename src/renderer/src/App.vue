<template>
  <div class="app-container">
    <router-view />
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
html,
body {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  background: #001529;
  overflow: hidden;
}

/* 全局隐藏所有滚动条 - Webkit浏览器 (Chrome, Safari, Edge, Electron) */
::-webkit-scrollbar {
  width: 0 !important;
  height: 0 !important;
  display: none !important;
}

::-webkit-scrollbar-track {
  display: none !important;
}

::-webkit-scrollbar-thumb {
  display: none !important;
}

/* 隐藏滚动条 - Firefox */
* {
  scrollbar-width: none !important;
}

/* 隐藏滚动条 - IE/Edge */
* {
  -ms-overflow-style: none !important;
}

#app {
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.app-container {
  height: 100%;
  padding: 10px;
  overflow: hidden;
}

/* Element Plus 组件滚动条隐藏 */
.el-scrollbar__wrap {
  overflow-x: hidden !important;
}

.el-scrollbar__wrap::-webkit-scrollbar {
  display: none !important;
}

/* 表格滚动条隐藏 */
.el-table__body-wrapper::-webkit-scrollbar {
  display: none !important;
}

/* 下拉框滚动条隐藏 */
.el-select-dropdown__wrap::-webkit-scrollbar {
  display: none !important;
}
</style>
