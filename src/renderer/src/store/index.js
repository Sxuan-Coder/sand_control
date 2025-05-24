import { createStore } from 'vuex'
import axios from 'axios'

// API基础URL，根据实际情况调整
const API_BASE_URL = 'http://127.0.0.1:8000'

export default createStore({
  state: {
    systemStatus: {
      is_running: false,
      current_config: null,
      start_time: null,
      elapsed_time: null,
      current_group: null,
      current_photo: null,
      remaining_sand: null
    },
    initialized: false,
    error: null,
    initializationError: null, // 新增初始化错误状态
    errorType: null, // 新增错误类型
    statusUpdateInterval: null
  },
  getters: {
    isRunning: (state) => state.systemStatus.is_running,
    systemStatus: (state) => state.systemStatus,
    isInitialized: (state) => state.initialized,
    error: (state) => state.error
  },
  mutations: {
    SET_SYSTEM_STATUS(state, status) {
      state.systemStatus = status
    },
    SET_INITIALIZED(state, value) {
      state.initialized = value
    },
    SET_ERROR(state, error) {
      state.error = error
    },
    CLEAR_ERROR(state) {
      state.error = null
      state.errorType = null
    },
    SET_INITIALIZATION_ERROR(state, { error, type }) {
      state.initializationError = error
      state.errorType = type
      state.initialized = false
    },
    CLEAR_INITIALIZATION_ERROR(state) {
      state.initializationError = null
      state.errorType = null
    },
    SET_STATUS_UPDATE_INTERVAL(state, interval) {
      state.statusUpdateInterval = interval
    }
  },
  actions: {
    // 获取系统状态
    async fetchSystemStatus({ commit }) {
      try {
        const response = await axios.get(`${API_BASE_URL}/status`)
        commit('SET_SYSTEM_STATUS', response.data)
        return response.data
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || '获取系统状态失败')
        throw error
      }
    },

    // 初始化系统
    async initialize({ commit }) {
      try {
        commit('CLEAR_ERROR')
        commit('CLEAR_INITIALIZATION_ERROR')
        const response = await axios.post(`${API_BASE_URL}/initialize`)
        commit('SET_INITIALIZED', true)
        return response.data
      } catch (error) {
        const errorMessage = error.response?.data?.detail || '系统初始化失败'
        let errorType = 'UNKNOWN'

        if (errorMessage.includes('串口') || errorMessage.includes('COM')) {
          errorType = 'SERIAL_PORT'
        } else if (errorMessage.includes('相机') || errorMessage.includes('设备未找到')) {
          errorType = 'CAMERA'
        } else if (errorMessage.includes('Socket') || errorMessage.includes('连接被拒绝')) {
          errorType = 'SOCKET'
        } else if (errorMessage.includes('Modbus') || errorMessage.includes('控制台')) {
          errorType = 'MODBUS'
        }

        commit('SET_INITIALIZATION_ERROR', {
          error: errorMessage,
          type: errorType
        })
        commit('SET_ERROR', errorMessage)
        throw error
      }
    },

    // 开始状态更新
    startStatusUpdate({ commit, state }) {
      if (state.statusUpdateInterval) {
        clearInterval(state.statusUpdateInterval)
      }

      const updateStatus = async () => {
        try {
          const response = await axios.get(`${API_BASE_URL}/status`)
          commit('SET_SYSTEM_STATUS', response.data)
        } catch (error) {
          console.error('获取状态更新失败:', error)
        }
      }

      // 立即更新一次
      updateStatus()

      // 设置定时更新
      const interval = setInterval(updateStatus, 1000) // 每秒更新一次
      commit('SET_STATUS_UPDATE_INTERVAL', interval)
    },

    // 停止状态更新
    stopStatusUpdate({ state, commit }) {
      if (state.statusUpdateInterval) {
        clearInterval(state.statusUpdateInterval)
        commit('SET_STATUS_UPDATE_INTERVAL', null)
      }
    },

    // 启动流程时开始状态更新
    async startProcess({ dispatch, commit }, config) {
      try {
        commit('CLEAR_ERROR')
        const response = await axios.post(`${API_BASE_URL}/process/start`, config)
        dispatch('startStatusUpdate') // 开始状态更新
        return response.data
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || '启动流程失败')
        throw error
      }
    },

    // 停止流程时停止状态更新
    async stopProcess({ dispatch, commit }) {
      try {
        commit('CLEAR_ERROR')
        const response = await axios.post(`${API_BASE_URL}/process/stop`)
        dispatch('stopStatusUpdate') // 停止状态更新
        return response.data
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || '停止流程失败')
        throw error
      }
    },

    // 配置相机
    async configureCamera({ commit }, config) {
      try {
        commit('CLEAR_ERROR')
        const response = await axios.post(`${API_BASE_URL}/camera/config`, config)
        return response.data
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || '配置相机失败')
        throw error
      }
    },

    // 测试给料
    async testFeeding({ commit }, amount = 1.0) {
      try {
        commit('CLEAR_ERROR')
        const response = await axios.post(`${API_BASE_URL}/test/feeding?amount=${amount}`)
        return response.data
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || '测试给料失败')
        throw error
      }
    },

    // 测试相机
    async testCamera({ commit }) {
      try {
        commit('CLEAR_ERROR')
        const response = await axios.post(`${API_BASE_URL}/test/camera`)
        return response.data
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || '测试相机失败')
        throw error
      }
    },

    // 测试清砂
    async testCleaning({ commit }) {
      try {
        commit('CLEAR_ERROR')
        const response = await axios.post(`${API_BASE_URL}/test/clean`)
        return response.data
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || '测试清砂失败')
        throw error
      }
    }
  }
})
