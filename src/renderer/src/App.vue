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
}

#app {
  width: 100%;
  height: 100%;
}

.app-container {
  height: 100%;
  padding: 10px;
}
</style>
