import axios from 'axios'

const API_BASE = '/api'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  withCredentials: true  // 允许发送cookies
})

export const apiService = {
  // 管理员登录
  adminLogin(password) {
    return api.post('/admin/login', { password })
  },

  // 管理员登出
  adminLogout() {
    return api.post('/admin/logout')
  },

  // 验证管理员session
  adminVerify() {
    return api.get('/admin/verify')
  },

  // 添加记录
  addRecord(callSign, info) {
    return api.get('/add_record', {
      params: { call_sign: callSign, info }
    })
  },

  // 检查呼号是否存在
  checkCallSign(callSign) {
    return api.get('/check_callsign', {
      params: { call_sign: callSign }
    })
  },

  // 处理回执
  receipt(callSign) {
    return api.get('/receipt', {
      params: { call_sign: callSign }
    })
  },

  // 标记已发送
  markSent(callSign) {
    return api.get('/mark_sent', {
      params: { call_sign: callSign }
    })
  },

  // 标记需要补发
  resend(callSign) {
    return api.get('/resend', {
      params: { call_sign: callSign }
    })
  },

  // 标记已回执
  markReceived(callSign) {
    return api.get('/mark_received', {
      params: { call_sign: callSign }
    })
  },

  // 获取所有记录
  getAllRecords() {
    return api.get('/get_all_records')
  },

  // 获取超期记录
  getExpired() {
    return api.get('/get_expired')
  },

  // 获取需要补发的记录
  getResendList() {
    return api.get('/get_resend_list')
  },

  // AI分析地址
  llmProcess() {
    return api.get('/llm')
  },

  // AI分析指定呼号地址
  llmProcessSingle(callSign) {
    return api.get('/llm_single', {
      params: { call_sign: callSign }
    })
  },

  // 删除记录
  deleteRecord(callSign) {
    return api.get('/delete_record', {
      params: { call_sign: callSign }
    })
  },

  // 编辑记录
  editRecord(recordData) {
    return api.post('/edit_record', recordData)
  },

  // 获取邮编
  getZipCode(address) {
    return api.get('/zip_code', {
      params: { address }
    })
  }
}

export default api
