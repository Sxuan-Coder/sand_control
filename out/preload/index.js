"use strict";
const electron = require("electron");
const preload = require("@electron-toolkit/preload");
const path = require("path");
({
  // 定义应用运行环境
  env: process.env.NODE_ENV,
  // 定义基础 API URL
  baseUrl: process.env.NODE_ENV === "development" ? "http://localhost:8000" : "http://127.0.0.1:8000"
});
try {
  electron.contextBridge.exposeInMainWorld("electron", preload.electronAPI);
  electron.contextBridge.exposeInMainWorld("api", {
    ipcRenderer: {
      invoke: (...args) => electron.ipcRenderer.invoke(...args)
    },
    path: {
      join: (...args) => path.join(...args)
    }
  });
  console.log("成功暴露API到渲染进程");
} catch (error) {
  console.error("暴露API失败:", error);
}
