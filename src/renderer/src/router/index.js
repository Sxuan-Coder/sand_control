import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Login from '../views/Login.vue'
import SandGradingReport from '../components/SandGradingReport.vue'


const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true }
  },
  {
    path: '/sand-grading-report',
    name: 'SandGradingReport',
    component: SandGradingReport,
    meta: { requiresAuth: true }
  },

]

const router = createRouter({
  history: createWebHistory('/'),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true'

  // 如果页面需要认证且用户未登录，则重定向到登录页
  if (to.meta.requiresAuth && !isLoggedIn) {
    next({ name: 'Login' })
  }
  // 如果用户已登录且尝试访问登录页，则重定向到仪表盘
  else if (to.name === 'Login' && isLoggedIn) {
    next({ name: 'Dashboard' })
  }
  // 其他情况正常导航
  else {
    next()
  }
})

export default router
