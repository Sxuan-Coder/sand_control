import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

document.documentElement.style.setProperty('--el-color-primary', '#1357ea')
document.documentElement.style.setProperty('--el-color-warning', '#d2000f')
document.documentElement.style.setProperty('--el-color-success', '#00983f')

const app = createApp(App)

app.use(router)
app.use(store)
app.use(ElementPlus, {
  locale: zhCn,
  config: {
    theme: {
      colors: {
        primary: '#1357ea',
        warning: '#d2000f',
        success: '#00983f'
      }
    }
  }
})

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.mount('#app')
