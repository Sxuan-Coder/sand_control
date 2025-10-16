"use strict";
const electron = require("electron");
const path = require("path");
const utils = require("@electron-toolkit/utils");
const child_process = require("child_process");
const axios = require("axios");
let pythonProcess = null;
function startPythonServer() {
  return new Promise((resolve, reject) => {
    try {
      const pythonScriptPath = path.join(__dirname, "..", "..", "src", "main", "python", "api", "app.py");
      console.log("Python脚本路径:", pythonScriptPath);
      const env = Object.assign({}, process.env);
      env.PYTHONIOENCODING = "utf-8";
      env.PYTHONUNBUFFERED = "1";
      env.PYTHONUTF8 = "1";
      pythonProcess = child_process.spawn("python", [
        pythonScriptPath
      ], {
        env,
        // 在Windows上指定编码
        windowsHide: true,
        windowsVerbatimArguments: false
      });
      let serverStarted = false;
      pythonProcess.stdout.on("data", (data) => {
        try {
          const output = data.toString("utf8");
          console.log(`Python服务器输出: ${output}`);
          if (output.includes("Uvicorn running on") || output.includes("Application startup complete")) {
            if (!serverStarted) {
              serverStarted = true;
              console.log("Python服务器已成功启动");
              resolve(pythonProcess);
            }
          }
        } catch (error) {
          console.error("解析Python输出时出错:", error);
        }
      });
      pythonProcess.stderr.on("data", (data) => {
        try {
          const errorOutput = data.toString("utf8");
          console.error(`Python服务器错误: ${errorOutput}`);
          if (errorOutput.includes("Uvicorn running on") || errorOutput.includes("Application startup complete")) {
            if (!serverStarted) {
              serverStarted = true;
              console.log("Python服务器已成功启动");
              resolve(pythonProcess);
            }
          }
        } catch (error) {
          console.error("解析Python错误输出时出错:", error);
        }
      });
      pythonProcess.on("close", (code) => {
        console.log(`Python服务器进程退出，退出码: ${code}`);
        pythonProcess = null;
        if (!serverStarted) {
          reject(new Error(`Python服务器启动失败，退出码: ${code}`));
        }
      });
      setTimeout(() => {
        if (!serverStarted) {
          console.log("Python服务器启动超时，继续执行...");
          serverStarted = true;
          resolve(pythonProcess);
        }
      }, 15e3);
    } catch (error) {
      console.error("启动Python服务器时出错:", error);
      reject(error);
    }
  });
}
function createWindow() {
  const mainWindow = new electron.BrowserWindow({
    width: 900,
    height: 670,
    show: false,
    autoHideMenuBar: true,
    ...process.platform === "linux" ? { icon } : {},
    webPreferences: {
      preload: path.join(__dirname, "../preload/index.js"),
      sandbox: false,
      webSecurity: false,
      // 关闭网络安全限制，允许跨域请求
      allowRunningInsecureContent: true
      // 允许运行不安全的内容
    }
  });
  mainWindow.on("ready-to-show", () => {
    mainWindow.show();
  });
  mainWindow.webContents.session.webRequest.onHeadersReceived((details, callback) => {
    callback({
      responseHeaders: {
        ...details.responseHeaders,
        "Content-Security-Policy": ["default-src 'self' 'unsafe-inline' http://localhost:* http://127.0.0.1:*; img-src 'self' data: http://localhost:* http://127.0.0.1:*; connect-src 'self' http://localhost:* http://127.0.0.1:*"]
      }
    });
  });
  mainWindow.webContents.setWindowOpenHandler((details) => {
    electron.shell.openExternal(details.url);
    return { action: "deny" };
  });
  if (utils.is.dev && process.env["ELECTRON_RENDERER_URL"]) {
    mainWindow.loadURL(process.env["ELECTRON_RENDERER_URL"]);
  } else {
    mainWindow.loadFile(path.join(__dirname, "../renderer/index.html"));
  }
}
electron.ipcMain.handle("get-app-path", () => {
  return electron.app.getAppPath();
});
electron.ipcMain.handle("check-file-exists", async (event, filePath) => {
  try {
    await fs.access(filePath, fs.constants.F_OK);
    return true;
  } catch {
    return false;
  }
});
electron.ipcMain.handle("read-file", async (event, filePath) => {
  try {
    console.log("尝试读取文件:", filePath);
    const data = await fs.readFile(filePath);
    console.log("文件读取成功，大小:", data.length);
    return data;
  } catch (error) {
    console.error("读取文件出错:", error);
    return null;
  }
});
electron.app.whenReady().then(() => {
  utils.electronApp.setAppUserModelId("com.electron");
  electron.app.on("browser-window-created", (_, window) => {
    utils.optimizer.watchWindowShortcuts(window);
  });
  electron.ipcMain.on("ping", () => console.log("pong"));
  electron.ipcMain.handle("fetch-data", async (event, url) => {
    try {
      console.log(`正在请求URL: ${url}`);
      const response = await fetch(url);
      const data = await response.text();
      return { success: true, data };
    } catch (error) {
      console.error(`请求失败: ${error.message}`);
      return { success: false, error: error.message };
    }
  });
  const api = axios.create({
    baseURL: "http://127.0.0.1:8000",
    timeout: 5e3,
    headers: {
      "Content-Type": "application/json"
    }
  });
  electron.ipcMain.handle("api-call", async (event, { endpoint, method, data, params }) => {
    try {
      console.log(`主进程 API 调用: ${method.toUpperCase()} ${endpoint}`);
      let response;
      switch (method.toLowerCase()) {
        case "get":
          response = await api.get(endpoint, { params });
          break;
        case "post":
          response = await api.post(endpoint, data);
          break;
        case "put":
          response = await api.put(endpoint, data);
          break;
        case "delete":
          response = await api.delete(endpoint, { data });
          break;
        default:
          throw new Error(`不支持的方法: ${method}`);
      }
      return { success: true, data: response.data };
    } catch (error) {
      console.error(`API 调用失败 (${endpoint}): ${error.message}`);
      return {
        success: false,
        error: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText
      };
    }
  });
  electron.ipcMain.handle("get-image-url", async (event, { imagePath }) => {
    return `http://127.0.0.1:8000/images/file?path=${encodeURIComponent(imagePath)}`;
  });
  electron.ipcMain.handle("test-server-connection", async () => {
    try {
      const response = await api.get("/hello");
      return { success: true, message: "服务器连接成功", data: response.data };
    } catch (error) {
      console.error("服务器连接失败:", error);
      return { success: false, message: "服务器连接失败", error: error.message };
    }
  });
  electron.ipcMain.handle("open-image-processing-window", () => {
    const imageProcessingWindow = new electron.BrowserWindow({
      width: 1400,
      height: 900,
      show: false,
      autoHideMenuBar: true,
      title: "图像处理展示",
      backgroundColor: "#0a0e27",
      webPreferences: {
        preload: path.join(__dirname, "../preload/index.js"),
        sandbox: false,
        webSecurity: false,
        allowRunningInsecureContent: true
      }
    });
    imageProcessingWindow.on("ready-to-show", () => {
      imageProcessingWindow.show();
      if (utils.is.dev) {
        imageProcessingWindow.webContents.openDevTools();
      }
    });
    imageProcessingWindow.webContents.session.webRequest.onHeadersReceived((details, callback) => {
      callback({
        responseHeaders: {
          ...details.responseHeaders,
          "Content-Security-Policy": ["default-src 'self' 'unsafe-inline' http://localhost:* http://127.0.0.1:*; img-src 'self' data: http://localhost:* http://127.0.0.1:*; connect-src 'self' http://localhost:* http://127.0.0.1:*"]
        }
      });
    });
    const imageProcessingUrl = utils.is.dev && process.env["ELECTRON_RENDERER_URL"] ? process.env["ELECTRON_RENDERER_URL"] + "/image-processing" : "file://" + path.join(__dirname, "../renderer/index.html");
    console.log("正在加载图像处理窗口:", imageProcessingUrl);
    if (utils.is.dev && process.env["ELECTRON_RENDERER_URL"]) {
      imageProcessingWindow.loadURL(process.env["ELECTRON_RENDERER_URL"] + "/image-processing");
    } else {
      imageProcessingWindow.loadFile(path.join(__dirname, "../renderer/index.html"));
    }
    imageProcessingWindow.webContents.on("did-fail-load", (event, errorCode, errorDescription) => {
      console.error("图像处理窗口加载失败:", errorCode, errorDescription);
    });
    imageProcessingWindow.webContents.on("did-finish-load", () => {
      console.log("图像处理窗口加载完成");
      const currentUrl = imageProcessingWindow.webContents.getURL();
      console.log("当前窗口 URL:", currentUrl);
    });
    imageProcessingWindow.webContents.on("did-navigate", (event, url) => {
      console.log("窗口导航到:", url);
      if (utils.is.dev && !url.includes("/image-processing") && !url.includes("/login")) {
        console.log("检测到非预期导航，重新加载图像处理页面");
        imageProcessingWindow.loadURL(process.env["ELECTRON_RENDERER_URL"] + "/image-processing");
      }
    });
    return { success: true };
  });
  electron.ipcMain.handle("chat-with-xfyun", async (event, { userMessage }) => {
    try {
      const XFYUN_API_URL = "http://127.0.0.1:8000/xfyun-api/v1/chat/completions";
      const AUTH_TOKEN = "pFKHvqJefKoFYrsZVvqJ:QneWSeXeqoeefFUBsAcV";
      const requestBody = {
        model: "4.0Ultra",
        messages: [
          {
            role: "user",
            content: userMessage
          }
        ],
        stream: false
      };
      const headers = {
        Authorization: `Bearer ${AUTH_TOKEN}`,
        "Content-Type": "application/json"
      };
      const response = await axios.post(XFYUN_API_URL, requestBody, { headers });
      if (response.data && response.data.choices && response.data.choices.length > 0) {
        return { success: true, content: response.data.choices[0].message.content };
      } else {
        throw new Error("无效的API响应格式");
      }
    } catch (error) {
      console.error("调用讯飞星火大模型API失败:", error);
      return { success: false, error: error.message };
    }
  });
  console.log("正在启动Python服务器...");
  startPythonServer().then(() => {
    console.log("Python服务器已启动，现在创建窗口...");
    createWindow();
    electron.ipcMain.handle("check-api-status", async () => {
      try {
        const response = await fetch("http://127.0.0.1:8000/hello");
        const data = await response.json();
        return { success: true, data };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });
  }).catch((error) => {
    console.error("Python服务器启动失败:", error);
    console.log("尽管Python服务器启动失败，仍然创建窗口...");
    createWindow();
  });
  electron.app.on("activate", function() {
    if (electron.BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});
electron.app.on("will-quit", () => {
  if (pythonProcess) {
    console.log("正在关闭Python服务器进程...");
    pythonProcess.kill();
    pythonProcess = null;
  }
});
electron.app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    electron.app.quit();
  }
});
