<template>
    <div class="container" ref="container">
        <div v-if="isLoading" class="loading-overlay">
            <div class="loading-spinner"></div>
            <div class="loading-text">加载中...</div>
        </div>
        <div class="progress-bar">
            <div class="progress" :style="{ width: progress + '%' }"></div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useStore } from 'vuex'
import * as THREE from 'three'
import { FBXLoader } from 'three/examples/jsm/loaders/FBXLoader'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls'
import path from 'path'

// 状态和引用
const store = useStore()
const container = ref<HTMLDivElement>()
const isLoading = ref(true)

// 计算实验进度百分比
const progress = computed(() => {
    const status = store.state.systemStatus
    if (!status || !status.current_config || !status.current_config.total_groups) return 0
    return Math.round((status.current_group / status.current_config.total_groups) * 100)
})

// Three.js 变量
let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let controls: OrbitControls
let model: THREE.Object3D | null = null
let animationFrameId: number

// 初始化场景
const initScene = () => {
    if (!container.value) return

    // 创建场景
    scene = new THREE.Scene()
    scene.background = null // 透明背景

    // 创建相机
    const aspect = container.value.clientWidth / container.value.clientHeight
    camera = new THREE.PerspectiveCamera(45, aspect, 0.1, 1000)
    camera.position.set(100, 100, 100)
    camera.lookAt(0, 0, 0)

    // 创建渲染器
    renderer = new THREE.WebGLRenderer({ 
        antialias: true,
        alpha: true // 启用透明度
    })
    renderer.setSize(container.value.clientWidth, container.value.clientHeight)
    renderer.shadowMap.enabled = true
    container.value.appendChild(renderer.domElement)

    // 创建控制器
    controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
    controls.dampingFactor = 0.05

    // 添加光源
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5)
    scene.add(ambientLight)

    const directionalLight = new THREE.DirectionalLight(0xffffff, 1)
    directionalLight.position.set(10, 10, 10)
    scene.add(directionalLight)

    // 加载模型
    loadModel()

    // 开始动画循环
    animate()
}

// 加载FBX模型
const loadModel = () => {
    console.log('开始加载模型...')
    const loader = new FBXLoader()
    isLoading.value = true

    // 创建加载管理器
    const manager = new THREE.LoadingManager()
    manager.onProgress = (url, loaded, total) => {
        console.log(`加载进度: ${Math.round((loaded / total) * 100)}%`)
    }
    loader.manager = manager

    try {
        // 使用相对路径加载模型
        const modelPath = '/resources/equipment-0-2.fbx'
        console.log('模型路径:', modelPath)
        
        // 加载模型
        loader.load(
            modelPath,
            (fbx) => {
                console.log('模型加载成功:', fbx)
                
                model = fbx
                
                // 计算模型包围盒
                const box = new THREE.Box3().setFromObject(fbx)
                const center = box.getCenter(new THREE.Vector3())
                const size = box.getSize(new THREE.Vector3())

                // 根据模型大小计算合适的缩放
                const maxDim = Math.max(size.x, size.y, size.z)
                const scale = (50 * 2) / maxDim  // 放大两倍
                fbx.scale.set(scale, scale, scale)

                // 将模型居中
                fbx.position.set(
                    -center.x * scale,
                    -center.y * scale,
                    -center.z * scale
                )

                // 设置材质和阴影
                fbx.traverse((child) => {
                    if (child instanceof THREE.Mesh) {
                        child.castShadow = true
                        child.receiveShadow = true
                        if (child.material) {
                            child.material.side = THREE.DoubleSide
                        }
                    }
                })

                scene.add(fbx)
                isLoading.value = false
            },
            (xhr) => {
                console.log((xhr.loaded / xhr.total * 100) + '% loaded')
            },
            (error) => {
                console.error('加载模型出错:', error)
                isLoading.value = false
            }
        )
    } catch (error) {
        console.error('加载模型出错:', error)
        isLoading.value = false
    }
}

// 动画循环
const animate = () => {
    animationFrameId = requestAnimationFrame(animate)
    if (model) {
        // 模型绕Y轴旋转
        // model.rotation.y += 0.008 * 8
    }
    controls.update()
    renderer.render(scene, camera)
}

// 处理窗口大小变化
const onResize = () => {
    if (!container.value || !camera || !renderer) return

    const width = container.value.clientWidth
    const height = container.value.clientHeight

    camera.aspect = width / height
    camera.updateProjectionMatrix()
    renderer.setSize(width, height)
}

// 清理函数
const cleanup = () => {
    if (animationFrameId) {
        cancelAnimationFrame(animationFrameId)
    }
    if (renderer) {
        renderer.dispose()
    }
    if (model) {
        scene.remove(model)
    }
}

// 生命周期钩子
onMounted(() => {
    initScene()
    window.addEventListener('resize', onResize)
})

onUnmounted(() => {
    window.removeEventListener('resize', onResize)
    cleanup()
})
</script>

<style scoped>
.container {
    position: relative;
    width: 100%;
    height: 100%;
    background: transparent;
}

.progress-bar {
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 4px;
    background: rgba(0, 0, 0, 0.2);
    z-index: 10;
}

.progress {
    height: 100%;
    background: #67c23a;
    transition: width 0.3s ease;
    box-shadow: 0 0 10px rgba(103, 194, 58, 0.5);
}

.loading-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background-color: rgba(255, 255, 255, 0.5);
    z-index: 10;
}

.loading-spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #f3f3f3;
    border-top: 4px solid #3498db;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

.loading-text {
    margin-top: 10px;
    color: #333;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
</style>