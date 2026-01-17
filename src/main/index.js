import { app, shell, BrowserWindow, ipcMain } from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import { spawn } from 'child_process'
// import icon from '../../resources/icon.png?asset' // 暂时注释掉，图标文件不存在
import axios from 'axios'

// 存储Python进程的引用
let pythonProcess = null

// 启动Python服务器函数并返回Promise
function startPythonServer() {
  return new Promise((resolve, reject) => {
    try {
      // 获取Python脚本的路径 - 使用动态路径
      const pythonScriptPath = join(__dirname, '..', '..', 'src', 'main', 'python', 'api', 'app.py')
      console.log('Python脚本路径:', pythonScriptPath)

      // 设置环境变量确保输出中文
      const env = Object.assign({}, process.env)
      env.PYTHONIOENCODING = 'utf-8'
      env.PYTHONUNBUFFERED = '1' // 禁用缓冲，确保输出实时显示
      env.PYTHONUTF8 = '1' // 强制使用UTF-8编码

      // 启动Python进程
      pythonProcess = spawn('python', [
        pythonScriptPath
      ], {
        env: env,
        // 在Windows上指定编码
        windowsHide: true,
        windowsVerbatimArguments: false
      })

      // 标记服务器是否已启动
      let serverStarted = false

      // 监听Python进程的输出
      pythonProcess.stdout.on('data', (data) => {
        try {
          // 尝试使用utf8解码
          const output = data.toString('utf8')
          console.log(`Python服务器输出: ${output}`)

          // 检查输出中是否包含服务器启动成功的信息
          if (output.includes('Uvicorn running on') || output.includes('Application startup complete')) {
            if (!serverStarted) {
              serverStarted = true
              console.log('Python服务器已成功启动')
              resolve(pythonProcess)
            }
          }
        } catch (error) {
          console.error('解析Python输出时出错:', error)
        }
      })

      // 监听Python进程的错误
      pythonProcess.stderr.on('data', (data) => {
        try {
          // 尝试使用utf8解码
          const errorOutput = data.toString('utf8')
          console.error(`Python服务器错误: ${errorOutput}`)

          // 如果在错误输出中也能检测到服务器启动（某些框架会在stderr输出启动信息）
          if (errorOutput.includes('Uvicorn running on') || errorOutput.includes('Application startup complete')) {
            if (!serverStarted) {
              serverStarted = true
              console.log('Python服务器已成功启动')
              resolve(pythonProcess)
            }
          }
        } catch (error) {
          console.error('解析Python错误输出时出错:', error)
        }
      })

      // 监听Python进程退出
      pythonProcess.on('close', (code) => {
        console.log(`Python服务器进程退出，退出码: ${code}`)
        pythonProcess = null
        if (!serverStarted) {
          reject(new Error(`Python服务器启动失败，退出码: ${code}`))
        }
      })

      // 设置超时，防止无限等待
      setTimeout(() => {
        if (!serverStarted) {
          console.log('Python服务器启动超时，继续执行...')
          serverStarted = true
          resolve(pythonProcess) // 超时后也继续执行，避免应用卡死
        }
      }, 15000) // 15秒超时，给服务器更多启动时间

    } catch (error) {
      console.error('启动Python服务器时出错:', error)
      reject(error)
    }
  })
}

function createWindow() {
  // 创建浏览器窗口
  const mainWindow = new BrowserWindow({
    width: 900,
    height: 670,
    show: false,
    autoHideMenuBar: true,
    title: '砂级配软件',
    ...(process.platform === 'linux' ? { icon } : {}),
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      webSecurity: false, // 关闭网络安全限制，允许跨域请求
      allowRunningInsecureContent: true // 允许运行不安全的内容
    }
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
  })

  // 设置CSP头，允许连接到本地API服务器
  mainWindow.webContents.session.webRequest.onHeadersReceived((details, callback) => {
    callback({
      responseHeaders: {
        ...details.responseHeaders,
        'Content-Security-Policy': ["default-src 'self' 'unsafe-inline' http://localhost:* http://127.0.0.1:*; img-src 'self' data: http://localhost:* http://127.0.0.1:*; connect-src 'self' http://localhost:* http://127.0.0.1:*"]
      }
    })
  })


  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  // 基于electron-vite cli的渲染器热模块替换(HMR)
  // 在开发环境中加载远程URL，在生产环境中加载本地html文件
  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

// 添加ipcMain处理程序
ipcMain.handle('get-app-path', () => {
  return app.getAppPath()
})

ipcMain.handle('check-file-exists', async (event, filePath) => {
  try {
    await fs.access(filePath, fs.constants.F_OK)
    return true
  } catch {
    return false
  }
})

ipcMain.handle('read-file', async (event, filePath) => {
  try {
    console.log('尝试读取文件:', filePath)
    const data = await fs.readFile(filePath)
    console.log('文件读取成功，大小:', data.length)
    return data
  } catch (error) {
    console.error('读取文件出错:', error)
    return null
  }
})

// 当Electron完成初始化并准备创建浏览器窗口时将调用此方法
// 某些API只能在此事件发生后使用
app.whenReady().then(() => {
  // 为Windows设置应用程序用户模型ID
  electronApp.setAppUserModelId('com.electron')


  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  // IPC测试
  ipcMain.on('ping', () => console.log('pong'))

  // 处理网络请求
  ipcMain.handle('fetch-data', async (event, url) => {
    try {
      console.log(`正在请求URL: ${url}`)
      const response = await fetch(url)
      const data = await response.text()
      return { success: true, data }
    } catch (error) {
      console.error(`请求失败: ${error.message}`)
      return { success: false, error: error.message }
    }
  })

  // 创建 axios 实例用于 API 调用
  const api = axios.create({
    baseURL: 'http://127.0.0.1:8000',
    timeout: 5000,
    headers: {
      'Content-Type': 'application/json'
    }
  })

  // 通用 API 调用处理程序
  ipcMain.handle('api-call', async (event, { endpoint, method, data, params }) => {
    try {
      console.log(`主进程 API 调用: ${method.toUpperCase()} ${endpoint}`)
      let response

      switch (method.toLowerCase()) {
        case 'get':
          response = await api.get(endpoint, { params })
          break
        case 'post':
          response = await api.post(endpoint, data)
          break
        case 'put':
          response = await api.put(endpoint, data)
          break
        case 'delete':
          response = await api.delete(endpoint, { data })
          break
        default:
          throw new Error(`不支持的方法: ${method}`)
      }

      return { success: true, data: response.data }
    } catch (error) {
      console.error(`API 调用失败 (${endpoint}): ${error.message}`)
      return {
        success: false,
        error: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText
      }
    }
  })

  // 获取图片 URL
  ipcMain.handle('get-image-url', async (event, { imagePath }) => {
    return `http://127.0.0.1:8000/images/file?path=${encodeURIComponent(imagePath)}`
  })

  // 读取处理结果 JSON 文件
  ipcMain.handle('read-processing-results', async () => {
    try {
      const fs = require('fs').promises
      const resultsPath = join(__dirname, '..', '..', 'src', 'main', 'python', 'results', 'processing_results.json')
      console.log('读取处理结果文件:', resultsPath)
      const data = await fs.readFile(resultsPath, 'utf-8')
      return { success: true, data: JSON.parse(data) }
    } catch (error) {
      console.error('读取处理结果失败:', error)
      return { success: false, error: error.message }
    }
  })

  // 获取本地图片的 base64 数据
  ipcMain.handle('read-local-image', async (event, imagePath) => {
    try {
      const fs = require('fs').promises
      console.log('读取本地图片:', imagePath)
      const data = await fs.readFile(imagePath)
      const base64 = data.toString('base64')
      const ext = imagePath.split('.').pop().toLowerCase()
      const mimeType = ext === 'png' ? 'image/png' : ext === 'jpg' || ext === 'jpeg' ? 'image/jpeg' : 'image/png'
      return { success: true, data: `data:${mimeType};base64,${base64}` }
    } catch (error) {
      console.error('读取图片失败:', error)
      return { success: false, error: error.message }
    }
  })

  // 测试服务器连接
  ipcMain.handle('test-server-connection', async () => {
    try {
      const response = await api.get('/hello')
      return { success: true, message: '服务器连接成功', data: response.data }
    } catch (error) {
      console.error('服务器连接失败:', error)
      return { success: false, message: '服务器连接失败', error: error.message }
    }
  })

  // 打开图像处理窗口
  ipcMain.handle('open-image-processing-window', () => {
    const imageProcessingWindow = new BrowserWindow({
      width: 1400,
      height: 900,
      show: false,
      autoHideMenuBar: true,
      title: '图像处理展示',
      backgroundColor: '#0a0e27',
      webPreferences: {
        preload: join(__dirname, '../preload/index.js'),
        sandbox: false,
        webSecurity: false,
        allowRunningInsecureContent: true
      }
    })

    imageProcessingWindow.on('ready-to-show', () => {
      imageProcessingWindow.show()
    
    })

    // 设置CSP头
    imageProcessingWindow.webContents.session.webRequest.onHeadersReceived((details, callback) => {
      callback({
        responseHeaders: {
          ...details.responseHeaders,
          'Content-Security-Policy': ["default-src 'self' 'unsafe-inline' http://localhost:* http://127.0.0.1:*; img-src 'self' data: http://localhost:* http://127.0.0.1:*; connect-src 'self' http://localhost:* http://127.0.0.1:*"]
        }
      })
    })

    // 加载图像处理页面（使用普通路由，不带 #）
    const imageProcessingUrl = is.dev && process.env['ELECTRON_RENDERER_URL']
      ? process.env['ELECTRON_RENDERER_URL'] + '/image-processing'
      : 'file://' + join(__dirname, '../renderer/index.html')
    
    console.log('正在加载图像处理窗口:', imageProcessingUrl)
    
    if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
      imageProcessingWindow.loadURL(process.env['ELECTRON_RENDERER_URL'] + '/image-processing')
    } else {
      imageProcessingWindow.loadFile(join(__dirname, '../renderer/index.html'))
    }

    // 监听加载错误
    imageProcessingWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
      console.error('图像处理窗口加载失败:', errorCode, errorDescription)
    })

    // 监听加载完成
    imageProcessingWindow.webContents.on('did-finish-load', () => {
      console.log('图像处理窗口加载完成')
      // 获取当前 URL 用于调试
      const currentUrl = imageProcessingWindow.webContents.getURL()
      console.log('当前窗口 URL:', currentUrl)
    })

    // 监听导航事件
    imageProcessingWindow.webContents.on('did-navigate', (event, url) => {
      console.log('窗口导航到:', url)
      // 如果被重定向到其他页面，强制回到图像处理页面
      if (is.dev && !url.includes('/image-processing') && !url.includes('/login')) {
        console.log('检测到非预期导航，重新加载图像处理页面')
        imageProcessingWindow.loadURL(process.env['ELECTRON_RENDERER_URL'] + '/image-processing')
      }
    })

    return { success: true }
  })

  // 讯飞星火大模型 API
  ipcMain.handle('chat-with-xfyun', async (event, { userMessage }) => {
    try {
      // 讯飞星火大模型 API 配置
      const XFYUN_API_URL = 'http://127.0.0.1:8000/xfyun-api/v1/chat/completions' // 使用代理路径
      const AUTH_TOKEN = 'pFKHvqJefKoFYrsZVvqJ:QneWSeXeqoeefFUBsAcV'

      // 构建请求体
      const requestBody = {
        model: '4.0Ultra',
        messages: [
          {
            role: 'user',
            content: userMessage
          }
        ],
        stream: false
      }

      // 请求头设置
      const headers = {
        Authorization: `Bearer ${AUTH_TOKEN}`,
        'Content-Type': 'application/json'
      }

      // 发送POST请求
      const response = await axios.post(XFYUN_API_URL, requestBody, { headers })

      // 返回响应内容
      if (response.data && response.data.choices && response.data.choices.length > 0) {
        return { success: true, content: response.data.choices[0].message.content }
      } else {
        throw new Error('无效的API响应格式')
      }
    } catch (error) {
      console.error('调用讯飞星火大模型API失败:', error)
      return { success: false, error: error.message }
    }
  })

  // 启动Python服务器，等待服务器启动完成后再创建窗口
  console.log('正在启动Python服务器...')
  startPythonServer()
    .then(() => {
      console.log('Python服务器已启动，现在创建窗口...')
      createWindow()

      // 添加IPC处理程序，允许渲染进程请求API状态
      ipcMain.handle('check-api-status', async () => {
        try {
          // 简单的HTTP请求检查API是否可用
          const response = await fetch('http://127.0.0.1:8000/hello')
          const data = await response.json()
          return { success: true, data }
        } catch (error) {
          return { success: false, error: error.message }
        }
      })
    })
    .catch((error) => {
      console.error('Python服务器启动失败:', error)
      // 即使Python服务器启动失败，也创建窗口，但可能某些功能不可用
      console.log('尽管Python服务器启动失败，仍然创建窗口...')
      createWindow()
    })

  app.on('activate', function () {
    // 在macOS上，当点击dock图标并且没有其他窗口打开时，
    // 通常在应用程序中重新创建一个窗口
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

// 在应用退出前关闭Python进程
app.on('will-quit', () => {
  if (pythonProcess) {
    console.log('正在关闭Python服务器进程...')
    // 在Windows上使用SIGTERM可能不起作用，使用kill()
    pythonProcess.kill()
    pythonProcess = null
  }
})

// 当所有窗口关闭时退出应用，除了在macOS上。在macOS上，
// 应用程序及其菜单栏通常会保持活动状态，直到用户使用Cmd + Q显式退出
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// 在此文件中，您可以包含应用程序特定的主进程代码的其余部分
// 您也可以将它们放在单独的文件中，并在此处引入
