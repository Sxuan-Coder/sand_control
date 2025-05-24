<template>
  <div class="login-page">
    <!-- 粒子背景 -->
    <div id="particles-js" class="particles-container"></div>

    <!-- 登录区域 -->
    <div class="login-container">
      <!-- 左侧信息区 -->
      <div class="login-info">
        <div class="logo-area">
          <div class="logo-icon">
            <el-icon><Monitor /></el-icon>
          </div>
        </div>
        <h1 class="system-title">砂石级配实验监控平台</h1>
        <p class="system-subtitle">Sand Gradation Experiment Monitoring System</p>
        <div class="info-features">
          <div class="feature-item">
            <el-icon><DataAnalysis /></el-icon>
            <span>实时数据监控</span>
          </div>
          <div class="feature-item">
            <el-icon><PictureFilled /></el-icon>
            <span>高精度图像分析</span>
          </div>
          <div class="feature-item">
            <el-icon><Histogram /></el-icon>
            <span>专业数据报表</span>
          </div>
        </div>
      </div>

      <!-- 右侧登录表单 -->
      <div class="login-form-area">
        <div class="login-form-container">
          <h2 class="welcome-text">欢迎使用</h2>
          <p class="login-desc">请使用您的账号密码登录系统</p>

          <el-form
            ref="loginFormRef"
            :model="loginForm"
            :rules="loginRules"
            class="login-form"
            size="large"
          >
            <el-form-item prop="username">
              <el-input
                v-model="loginForm.username"
                placeholder="用户名"
                :prefix-icon="User"
                clearable
                @keyup.enter="handleLogin"
              />
            </el-form-item>

            <el-form-item prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="密码"
                :prefix-icon="Lock"
                show-password
                clearable
                @keyup.enter="handleLogin"
              />
            </el-form-item>

            <div class="login-options">
              <el-checkbox v-model="rememberMe">记住我</el-checkbox>
              <el-button type="text" class="forgot-password">忘记密码?</el-button>
            </div>

            <el-form-item>
              <el-button
                type="primary"
                class="login-button"
                :loading="loading"
                @click="handleLogin"
              >
                登录系统
              </el-button>
            </el-form-item>
          </el-form>

          <div class="login-footer">
            <p class="version-info">系统版本 V1.0.0</p>
            <p class="copyright">2025 砂石级配实验监控平台 - 版权所有</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  User,
  Lock,
  Monitor,
  DataAnalysis,
  PictureFilled,
  Histogram
} from '@element-plus/icons-vue'

const router = useRouter()
const loginFormRef = ref(null)
const loading = ref(false)
const rememberMe = ref(false)

// 登录表单数据
const loginForm = reactive({
  username: '',
  password: ''
})

// 表单验证规则
const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度应为3-20个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度应为6-20个字符', trigger: 'blur' }
  ]
}

// 处理登录
const handleLogin = () => {
  loginFormRef.value.validate((valid) => {
    if (!valid) return

    loading.value = true

    // 模拟登录请求
    setTimeout(() => {
      // 验证用户名和密码
      if (loginForm.username === 'admin' && loginForm.password === '123456') {
        // 登录成功
        ElMessage({
          message: '登录成功，正在进入系统...',
          type: 'success',
          duration: 2000
        })

        // 存储登录状态
        localStorage.setItem('isLoggedIn', 'true')
        if (rememberMe.value) {
          localStorage.setItem('username', loginForm.username)
        } else {
          localStorage.removeItem('username')
        }

        // 跳转到仪表盘页面
        setTimeout(() => {
          router.push('/dashboard')
        }, 1000)
      } else {
        // 登录失败
        ElMessage({
          message: '用户名或密码错误',
          type: 'error',
          duration: 2000
        })
      }

      loading.value = false
    }, 1500)
  })
}

// 检查是否有记住的用户名
const checkRememberedUser = () => {
  const rememberedUsername = localStorage.getItem('username')
  if (rememberedUsername) {
    loginForm.username = rememberedUsername
    rememberMe.value = true
  }
}

// 初始化粒子背景
const initParticles = () => {
  // 动态加载particles.js
  const script = document.createElement('script')
  script.src = 'https://cdn.jsdelivr.net/particles.js/2.0.0/particles.min.js'
  script.onload = () => {
    window.particlesJS('particles-js', {
      particles: {
        number: {
          value: 80,
          density: {
            enable: true,
            value_area: 800
          }
        },
        color: {
          value: '#00a8ff'
        },
        shape: {
          type: 'circle',
          stroke: {
            width: 0,
            color: '#000000'
          }
        },
        opacity: {
          value: 0.3,
          random: true,
          anim: {
            enable: true,
            speed: 1,
            opacity_min: 0.1,
            sync: false
          }
        },
        size: {
          value: 3,
          random: true,
          anim: {
            enable: true,
            speed: 2,
            size_min: 0.1,
            sync: false
          }
        },
        line_linked: {
          enable: true,
          distance: 150,
          color: '#00a8ff',
          opacity: 0.2,
          width: 1
        },
        move: {
          enable: true,
          speed: 1,
          direction: 'none',
          random: true,
          straight: false,
          out_mode: 'out',
          bounce: false,
          attract: {
            enable: false,
            rotateX: 600,
            rotateY: 1200
          }
        }
      },
      interactivity: {
        detect_on: 'canvas',
        events: {
          onhover: {
            enable: true,
            mode: 'grab'
          },
          onclick: {
            enable: true,
            mode: 'push'
          },
          resize: true
        },
        modes: {
          grab: {
            distance: 140,
            line_linked: {
              opacity: 0.5
            }
          },
          push: {
            particles_nb: 4
          }
        }
      },
      retina_detect: true
    })
  }
  document.body.appendChild(script)
}

onMounted(() => {
  checkRememberedUser()
  initParticles()
})
</script>

<style scoped>
.login-page {
  width: 100vw;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #001529 0%, #001f3f 100%);
  position: relative;
  overflow: hidden;
}

.particles-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
}

.login-container {
  display: flex;
  width: 1000px;
  height: 600px;
  background: rgba(0, 33, 64, 0.4);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  box-shadow: 0 15px 50px rgba(0, 0, 0, 0.3);
  overflow: hidden;
  z-index: 2;
  animation: fadeIn 0.8s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 左侧信息区域 */
.login-info {
  flex: 1;
  background: linear-gradient(135deg, rgba(0, 168, 255, 0.1) 0%, rgba(0, 145, 234, 0.2) 100%);
  padding: 60px 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  overflow: hidden;
}

.login-info::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    radial-gradient(circle at 30% 20%, rgba(0, 168, 255, 0.15) 0%, transparent 50%),
    radial-gradient(circle at 70% 80%, rgba(0, 168, 255, 0.15) 0%, transparent 50%);
  z-index: -1;
}

.logo-area {
  margin-bottom: 30px;
}

.logo-icon {
  width: 80px;
  height: 80px;
  background: rgba(0, 168, 255, 0.1);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(0, 168, 255, 0.3);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}

.logo-icon :deep(svg) {
  width: 50px;
  height: 50px;
  color: #00a8ff;
  filter: drop-shadow(0 0 10px rgba(0, 168, 255, 0.7));
}

.system-title {
  font-size: 28px;
  font-weight: 600;
  color: #ffffff;
  margin: 0 0 10px 0;
  text-align: center;
  text-shadow: 0 0 20px rgba(0, 168, 255, 0.5);
  letter-spacing: 2px;
}

.system-subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  margin: 0 0 50px 0;
  text-align: center;
  letter-spacing: 1px;
}

.info-features {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 25px;
  margin-top: auto;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px 20px;
  background: rgba(0, 33, 64, 0.4);
  border-radius: 12px;
  border: 1px solid rgba(0, 168, 255, 0.15);
  transition: all 0.3s ease;
}

.feature-item:hover {
  transform: translateX(5px);
  background: rgba(0, 33, 64, 0.6);
  border-color: rgba(0, 168, 255, 0.3);
}

.feature-item :deep(svg) {
  font-size: 24px;
  color: #00a8ff;
}

.feature-item span {
  font-size: 16px;
  color: #ffffff;
  font-weight: 500;
}

/* 右侧登录表单区域 */
.login-form-area {
  width: 450px;
  background: rgba(0, 24, 48, 0.7);
  padding: 60px 40px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.login-form-container {
  width: 100%;
}

.welcome-text {
  font-size: 28px;
  font-weight: 600;
  color: #ffffff;
  margin: 0 0 10px 0;
}

.login-desc {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0 0 40px 0;
}

.login-form {
  width: 100%;
}

.login-form :deep(.el-input__wrapper) {
  background-color: rgba(0, 24, 48, 0.5);
  box-shadow: none;
  border: 1px solid rgba(0, 145, 255, 0.15);
  padding: 12px 15px;
  transition: all 0.3s ease;
}

.login-form :deep(.el-input__wrapper:hover),
.login-form :deep(.el-input__wrapper.is-focus) {
  border-color: rgba(0, 168, 255, 0.5);
  box-shadow: 0 0 10px rgba(0, 168, 255, 0.2);
}

.login-form :deep(.el-input__inner) {
  color: #e6f7ff;
  height: 24px;
  font-size: 16px;
}

.login-form :deep(.el-input__prefix-icon) {
  color: #00a8ff;
  font-size: 18px;
}

.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.login-options :deep(.el-checkbox__label) {
  color: rgba(255, 255, 255, 0.7);
}

.login-options :deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: #00a8ff;
  border-color: #00a8ff;
}

.forgot-password {
  color: #00a8ff;
  font-size: 14px;
}

.login-button {
  width: 100%;
  height: 50px;
  background: linear-gradient(90deg, #0088cc 0%, #00a8ff 100%);
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 1px;
  transition: all 0.3s ease;
  box-shadow: 0 5px 15px rgba(0, 168, 255, 0.3);
  margin-top: 10px;
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 168, 255, 0.4);
  background: linear-gradient(90deg, #00a8ff 0%, #33bbff 100%);
}

.login-button:active {
  transform: translateY(0);
}

.login-footer {
  margin-top: 50px;
  text-align: center;
}

.version-info {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  margin: 0 0 5px 0;
}

.copyright {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  margin: 0;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .login-container {
    width: 90%;
    height: auto;
    flex-direction: column;
  }

  .login-info {
    padding: 40px 30px;
  }

  .login-form-area {
    width: 100%;
    padding: 40px 30px;
  }
}

@media (max-width: 768px) {
  .login-info {
    display: none;
  }

  .login-form-area {
    border-radius: 16px;
  }
}
</style>
