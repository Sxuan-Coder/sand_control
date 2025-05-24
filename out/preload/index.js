"use strict";
const electron = require("electron");
const preload = require("@electron-toolkit/preload");
const api = {
  // 定义版本信息
  version: "1.0.0",
  // 定义应用运行环境
  env: process.env.NODE_ENV,
  // 定义基础 API URL
  baseUrl: process.env.NODE_ENV === "development" ? "http://localhost:8000" : "http://127.0.0.1:8000"
};
if (process.contextIsolated) {
  try {
    electron.contextBridge.exposeInMainWorld("electron", preload.electronAPI);
    electron.contextBridge.exposeInMainWorld("api", api);
  } catch (error) {
    console.error(error);
  }
} else {
  window.electron = preload.electronAPI;
  window.api = api;
}
