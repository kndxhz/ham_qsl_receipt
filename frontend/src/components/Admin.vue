<template>
  <div class="admin-container">
    <!-- 密码验证对话框 -->
    <el-dialog
      v-model="passwordDialogVisible"
      title="管理员验证"
      width="400px"
      center
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
    >
      <el-form @submit.prevent="verifyPassword">
        <el-form-item label="密码">
          <el-input
            v-model="password"
            type="password"
            placeholder="请输入管理员密码"
            show-password
            @keydown.enter.prevent="verifyPassword"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="goBack">返回</el-button>
          <el-button type="primary" @click="verifyPassword" :loading="verifying">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 管理员界面 -->
    <div v-if="authenticated" class="admin-content">
      <!-- 编辑记录对话框 -->
      <el-dialog
        v-model="editDialogVisible"
        title="编辑记录信息"
        width="600px"
        center
        :close-on-click-modal="false"
      >
        <el-form
          ref="editForm"
          :model="editData"
          :rules="editRules"
          label-width="100px"
        >
          <el-form-item label="呼号">
            <el-input v-model="editData.call_sign" disabled />
          </el-form-item>
          <el-form-item label="姓名" prop="name">
            <el-input v-model="editData.name" placeholder="请输入姓名" />
          </el-form-item>
          <el-form-item label="电话" prop="phone">
            <el-input v-model="editData.phone" placeholder="请输入电话号码" />
          </el-form-item>
          <el-form-item label="省份" prop="province">
            <el-input v-model="editData.province" placeholder="请输入省份" />
          </el-form-item>
          <el-form-item label="详细地址" prop="address">
            <el-input
              v-model="editData.address"
              type="textarea"
              :rows="3"
              placeholder="请输入详细地址"
            />
          </el-form-item>
          <el-form-item label="邮编" prop="zip_code">
            <el-input v-model="editData.zip_code" placeholder="请输入邮编" />
          </el-form-item>
          <el-form-item label="原始信息" prop="info">
            <el-input
              v-model="editData.info"
              type="textarea"
              :rows="4"
              placeholder="请输入原始地址信息"
            />
          </el-form-item>
        </el-form>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="editDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="saveEditRecord" :loading="editLoading">
              保存
            </el-button>
          </span>
        </template>
      </el-dialog>

      <el-card class="header-card">
        <template #header>
          <div class="card-header">
            <span>QSL管理员控制台</span>
            <el-button type="danger" @click="logout">退出</el-button>
          </div>
        </template>
      </el-card>

      <el-tabs v-model="activeTab" class="admin-tabs">
        <!-- 添加记录 -->
        <el-tab-pane label="添加记录" name="add">
          <el-card>
            <el-form
              ref="addForm"
              :model="addData"
              :rules="addRules"
              label-width="120px"
            >
              <el-form-item label="呼号" prop="callSign">
                <el-input 
                  v-model="addData.callSign" 
                  placeholder="请输入呼号"
                  @keydown.enter.prevent="addRecord"
                />
              </el-form-item>
              <el-form-item label="地址信息" prop="info">
                <el-input
                  v-model="addData.info"
                  type="textarea"
                  :rows="4"
                  placeholder="请输入完整地址信息，包括姓名、电话、地址等"
                />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="addRecord" :loading="addLoading">
                  添加记录
                </el-button>
                <el-button @click="resetAddForm">重置</el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </el-tab-pane>

        <!-- 记录管理 -->
        <el-tab-pane label="记录管理" name="records">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>所有记录</span>
                <div>
                  <el-button @click="loadRecords" :loading="recordsLoading">
                    刷新
                  </el-button>
                </div>
              </div>
            </template>

            <!-- 批量操作工具栏 -->
            <div class="batch-toolbar" v-if="selectedRecords.length > 0">
              <div class="selected-info">
                已选择 {{ selectedRecords.length }} 条记录
              </div>
              <div class="batch-actions">
                <el-button
                  size="small"
                  type="success"
                  @click="batchMarkAsSent"
                  :disabled="!canBatchMarkSent"
                >
                  批量标记已发送
                </el-button>
                <el-button
                  size="small"
                  type="warning"
                  @click="batchMarkAsResend"
                  :disabled="!canBatchMarkResend"
                >
                  批量标记补发
                </el-button>
                <el-button
                  size="small"
                  type="info"
                  @click="batchMarkAsReceived"
                  :disabled="!canBatchMarkReceived"
                >
                  批量标记回执
                </el-button>
                <el-button
                  size="small"
                  type="primary"
                  @click="batchProcessWithAI"
                  :loading="aiLoading"
                  :disabled="!canBatchProcessAI"
                >
                  AI处理地址
                </el-button>
                <el-button
                  size="small"
                  type="danger"
                  @click="batchDeleteRecords"
                  :loading="deleteLoading"
                >
                  删除记录
                </el-button>
                <el-button size="small" @click="clearSelection">
                  取消选择
                </el-button>
              </div>
            </div>

            <!-- 选择操作栏 -->
            <div class="selection-toolbar">
              <el-checkbox
                v-model="selectAll"
                :indeterminate="isIndeterminate"
                @change="handleSelectAllChange"
              >
                全选
              </el-checkbox>
              <el-button size="small" type="primary" link @click="selectInverse">
                反选
              </el-button>
              <el-button size="small" type="primary" link @click="clearSelection">
                清空选择
              </el-button>
            </div>
            
            <el-table 
              ref="recordsTable"
              :data="records" 
              stripe 
              style="width: 100%"
              @selection-change="handleSelectionChange"
              @row-contextmenu="handleRowContextMenu"
            >
              <el-table-column type="selection" width="55" />
              <el-table-column prop="call_sign" label="呼号" width="120" show-overflow-tooltip />
              <el-table-column prop="name" label="姓名" width="100" show-overflow-tooltip />
              <el-table-column prop="phone" label="电话" width="140" show-overflow-tooltip />
              <el-table-column prop="province" label="省份" width="100" show-overflow-tooltip />
              <el-table-column prop="address" label="地址" min-width="300" show-overflow-tooltip />
              <el-table-column prop="zip_code" label="邮编" width="100" />
              <el-table-column prop="status" label="状态" width="100">
                <template #default="scope">
                  <el-tag :type="getStatusType(scope.row.status)">
                    {{ getStatusText(scope.row.status) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="add_time" label="添加时间" width="160" />
              <el-table-column prop="send_time" label="发送时间" width="160" />
              <el-table-column prop="receipt_time" label="回执时间" width="160" />
              <el-table-column label="操作" width="280" fixed="right">
                <template #default="scope">
                  <el-button
                    size="small"
                    type="primary"
                    @click="editRecord(scope.row)"
                    title="编辑记录"
                  >
                    编辑
                  </el-button>
                  <el-button
                    v-if="scope.row.status === 'pending'"
                    size="small"
                    type="success"
                    @click="markAsSent(scope.row.call_sign)"
                  >
                    标记已发送
                  </el-button>
                  <el-button
                    v-if="scope.row.status === 'sent'"
                    size="small"
                    type="warning"
                    @click="markAsResend(scope.row.call_sign)"
                  >
                    需要补发
                  </el-button>
                  <el-button
                    v-if="scope.row.status === 'sent'"
                    size="small"
                    type="info"
                    @click="markAsReceived(scope.row.call_sign)"
                  >
                    标记已回执
                  </el-button>
                  <el-button
                    v-if="scope.row.status === 'resend'"
                    size="small"
                    type="success"
                    @click="markAsSent(scope.row.call_sign)"
                  >
                    标记已发送
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <!-- 右键菜单 -->
            <div
              v-if="contextMenuVisible"
              :style="contextMenuStyle"
              class="context-menu"
              @click.stop
            >
              <div class="context-menu-item" @click="editRecord(contextMenuRow)">
                <i class="el-icon-edit"></i>
                编辑记录
              </div>
              <div class="context-menu-divider"></div>
              <div class="context-menu-item" @click="markAsSent(contextMenuRow.call_sign)">
                <i class="el-icon-check"></i>
                标记已发送
              </div>
              <div class="context-menu-item" @click="markAsResend(contextMenuRow.call_sign)">
                <i class="el-icon-refresh"></i>
                标记补发
              </div>
              <div class="context-menu-item" @click="markAsReceived(contextMenuRow.call_sign)">
                <i class="el-icon-circle-check"></i>
                标记已回执
              </div>
              <div class="context-menu-item" @click="processSingleWithAI(contextMenuRow.call_sign)">
                <i class="el-icon-magic-stick"></i>
                AI处理地址
              </div>
              <div class="context-menu-divider"></div>
              <div class="context-menu-item" @click="selectSingleRow(contextMenuRow)">
                <i class="el-icon-plus"></i>
                选择此行
              </div>
              <div class="context-menu-item" @click="copyCallSign(contextMenuRow.call_sign)">
                <i class="el-icon-document-copy"></i>
                复制呼号
              </div>
              <div class="context-menu-divider"></div>
              <div class="context-menu-item context-menu-danger" @click="deleteSingleRecord(contextMenuRow.call_sign)">
                <i class="el-icon-delete"></i>
                删除记录
              </div>
            </div>
          </el-card>
        </el-tab-pane>

        <!-- 超期记录 -->
        <el-tab-pane label="超期记录" name="expired">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>超期未回执记录</span>
                <el-button @click="loadExpired" :loading="expiredLoading">
                  刷新
                </el-button>
              </div>
            </template>
            
            <el-table :data="expiredRecords" stripe style="width: 100%">
              <el-table-column prop="call_sign" label="呼号" width="120" />
              <el-table-column prop="add_time" label="添加时间" width="160" />
              <el-table-column prop="send_time" label="发送时间" width="160" />
              <el-table-column label="超期天数" width="120">
                <template #default="scope">
                  <el-tag type="danger">
                    {{ getDaysOverdue(scope.row.send_time) }} 天
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120">
                <template #default="scope">
                  <el-button
                    size="small"
                    type="warning"
                    @click="markAsResend(scope.row.call_sign)"
                  >
                    标记补发
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-tab-pane>

        <!-- 补发列表 -->
        <el-tab-pane label="补发列表" name="resend">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>需要补发的记录</span>
                <el-button @click="loadResendList" :loading="resendLoading">
                  刷新
                </el-button>
              </div>
            </template>
            
            <el-table :data="resendList" stripe style="width: 100%">
              <el-table-column prop="call_sign" label="呼号" width="120" />
              <el-table-column prop="add_time" label="添加时间" width="160" />
              <el-table-column prop="send_time" label="发送时间" width="160" />
              <el-table-column prop="reissue_time" label="补发标记时间" width="160" />
              <el-table-column label="操作" width="120">
                <template #default="scope">
                  <el-button
                    size="small"
                    type="success"
                    @click="markAsSent(scope.row.call_sign)"
                  >
                    标记已发送
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { apiService } from '../api'

export default {
  name: 'Admin',
  setup() {
    const router = useRouter()
    const passwordDialogVisible = ref(true)
    const authenticated = ref(false)
    const password = ref('')
    const verifying = ref(false)
    const activeTab = ref('add')

    // 添加记录相关
    const addData = reactive({
      callSign: '',
      info: ''
    })
    const addLoading = ref(false)
    const addForm = ref()

    // 记录管理相关
    const records = ref([])
    const recordsLoading = ref(false)
    const aiLoading = ref(false)
    const deleteLoading = ref(false)
    const recordsTable = ref()

    // 多选相关
    const selectedRecords = ref([])
    const selectAll = ref(false)
    const isIndeterminate = ref(false)

    // 右键菜单相关
    const contextMenuVisible = ref(false)
    const contextMenuStyle = ref({})
    const contextMenuRow = ref({})

    // 超期记录相关
    const expiredRecords = ref([])
    const expiredLoading = ref(false)

    // 补发列表相关
    const resendList = ref([])
    const resendLoading = ref(false)

    // 编辑记录相关
    const editDialogVisible = ref(false)
    const editLoading = ref(false)
    const editForm = ref()
    const editData = reactive({
      call_sign: '',
      name: '',
      phone: '',
      province: '',
      address: '',
      zip_code: '',
      info: ''
    })

    const editRules = {
      name: [
        { required: true, message: '请输入姓名', trigger: 'blur' }
      ],
      phone: [
        { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
      ],
      address: [
        { required: true, message: '请输入详细地址', trigger: 'blur' }
      ]
    }

    const addRules = {
      callSign: [
        { required: true, message: '请输入呼号', trigger: 'blur' }
      ],
      info: [
        { required: true, message: '请输入地址信息', trigger: 'blur' }
      ]
    }

    // 计算属性
    const canBatchMarkSent = computed(() => {
      return selectedRecords.value.some(record => record.status === 'pending' || record.status === 'resend')
    })

    const canBatchMarkResend = computed(() => {
      return selectedRecords.value.some(record => record.status === 'sent')
    })

    const canBatchMarkReceived = computed(() => {
      return selectedRecords.value.some(record => record.status === 'sent')
    })

    const canBatchProcessAI = computed(() => {
      return selectedRecords.value.some(record => !record.name || !record.phone || !record.address)
    })

    // 隐藏右键菜单
    const hideContextMenu = () => {
      contextMenuVisible.value = false
    }

    // 监听点击事件隐藏右键菜单
    onMounted(() => {
      document.addEventListener('click', hideContextMenu)
      document.addEventListener('contextmenu', hideContextMenu)
      // 检查是否已经登录
      checkAuthStatus()
    })

    const checkAuthStatus = async () => {
      try {
        const response = await apiService.adminVerify()
        if (response.data.status === 200) {
          authenticated.value = true
          passwordDialogVisible.value = false
          loadRecords()
        }
      } catch (error) {
        // 认证失败，保持登录对话框显示
        authenticated.value = false
        passwordDialogVisible.value = true
      }
    }

    const verifyPassword = async () => {
      if (!password.value.trim()) {
        ElMessage.error('请输入密码')
        return
      }

      try {
        verifying.value = true
        const response = await apiService.adminLogin(password.value)
        
        if (response.data.status === 200) {
          authenticated.value = true
          passwordDialogVisible.value = false
          password.value = ''
          ElMessage.success('登录成功')
          loadRecords()
        } else {
          ElMessage.error(response.data.message || '登录失败')
          password.value = ''
        }
      } catch (error) {
        console.error('登录失败:', error)
        if (error.response?.status === 401) {
          ElMessage.error('密码错误')
        } else {
          ElMessage.error('登录失败，请稍后重试')
        }
        password.value = ''
      } finally {
        verifying.value = false
      }
    }

    const goBack = () => {
      router.push('/')
    }

    const logout = async () => {
      try {
        await apiService.adminLogout()
        authenticated.value = false
        passwordDialogVisible.value = true
        password.value = ''
        ElMessage.success('已退出登录')
      } catch (error) {
        console.error('登出失败:', error)
        // 即使登出失败也清除本地状态
        authenticated.value = false
        passwordDialogVisible.value = true
        password.value = ''
      }
    }

    const addRecord = async () => {
      try {
        const valid = await addForm.value.validate()
        if (!valid) return

        addLoading.value = true
        const response = await apiService.addRecord(
          addData.callSign.toUpperCase(),
          addData.info
        )

        if (response.data.status === 200) {
          ElMessage.success('记录添加成功')
          resetAddForm()
          loadRecords()
        } else {
          ElMessage.error('添加失败')
        }
      } catch (error) {
        console.error('添加记录失败:', error)
        ElMessage.error('添加失败，请稍后重试')
      } finally {
        addLoading.value = false
      }
    }

    const resetAddForm = () => {
      addData.callSign = ''
      addData.info = ''
      addForm.value?.resetFields()
    }

    const loadRecords = async () => {
      try {
        recordsLoading.value = true
        const response = await apiService.getAllRecords()
        if (response.data.status === 200) {
          records.value = response.data.data
        }
      } catch (error) {
        console.error('加载记录失败:', error)
        ElMessage.error('加载记录失败')
      } finally {
        recordsLoading.value = false
      }
    }

    const processWithAI = async () => {
      try {
        aiLoading.value = true
        const response = await apiService.llmProcess()
        if (response.data.status === 200) {
          ElMessage.success('AI处理完成')
          loadRecords()
        } else {
          ElMessage.warning('没有需要处理的记录')
        }
      } catch (error) {
        console.error('AI处理失败:', error)
        ElMessage.error('AI处理失败')
      } finally {
        aiLoading.value = false
      }
    }

    const markAsSent = async (callSign) => {
      try {
        const response = await apiService.markSent(callSign)
        if (response.data.status === 200) {
          ElMessage.success('已标记为已发送')
          loadRecords()
          loadResendList() // 刷新补发列表
        }
      } catch (error) {
        console.error('标记失败:', error)
        ElMessage.error('标记失败')
      }
    }

    const markAsResend = async (callSign) => {
      try {
        await ElMessageBox.confirm(
          `确定要标记呼号 ${callSign} 需要补发吗？`,
          '确认操作',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )

        const response = await apiService.resend(callSign)
        if (response.data.status === 200) {
          ElMessage.success('已标记为需要补发')
          loadRecords()
          loadResendList()
        }
      } catch (error) {
        if (error !== 'cancel') {
          console.error('标记失败:', error)
          ElMessage.error('标记失败')
        }
      }
    }

    const markAsReceived = async (callSign) => {
      try {
        await ElMessageBox.confirm(
          `确定要标记呼号 ${callSign} 已回执吗？`,
          '确认操作',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'info'
          }
        )

        const response = await apiService.markReceived(callSign)
        if (response.data.status === 200) {
          ElMessage.success('已标记为已回执')
          loadRecords()
        } else {
          ElMessage.error(response.data.message || '标记失败')
        }
      } catch (error) {
        if (error !== 'cancel') {
          console.error('标记失败:', error)
          ElMessage.error('标记失败')
        }
      }
    }

    const loadExpired = async () => {
      try {
        expiredLoading.value = true
        const response = await apiService.getExpired()
        if (response.data.status === 200) {
          expiredRecords.value = response.data.data
        }
      } catch (error) {
        console.error('加载超期记录失败:', error)
        ElMessage.error('加载超期记录失败')
      } finally {
        expiredLoading.value = false
      }
    }

    const loadResendList = async () => {
      try {
        resendLoading.value = true
        const response = await apiService.getResendList()
        if (response.data.status === 200) {
          resendList.value = response.data.data
        }
      } catch (error) {
        console.error('加载补发列表失败:', error)
        ElMessage.error('加载补发列表失败')
      } finally {
        resendLoading.value = false
      }
    }

    const getStatusType = (status) => {
      const statusMap = {
        pending: 'warning',
        sent: 'success',
        received: 'info',
        resend: 'danger'
      }
      return statusMap[status] || 'info'
    }

    const getStatusText = (status) => {
      const statusMap = {
        pending: '待处理',
        sent: '已发送',
        received: '已回执',
        resend: '需补发'
      }
      return statusMap[status] || status
    }

    const getDaysOverdue = (sendTime) => {
      const sent = new Date(sendTime)
      const now = new Date()
      const diffTime = Math.abs(now - sent)
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
      return diffDays
    }

    // 多选处理方法
    const handleSelectionChange = (selection) => {
      selectedRecords.value = selection
      selectAll.value = selection.length === records.value.length && records.value.length > 0
      isIndeterminate.value = selection.length > 0 && selection.length < records.value.length
    }

    const handleSelectAllChange = (val) => {
      if (val) {
        recordsTable.value.clearSelection()
        records.value.forEach(row => {
          recordsTable.value.toggleRowSelection(row, true)
        })
      } else {
        recordsTable.value.clearSelection()
      }
    }

    const selectInverse = () => {
      const currentSelected = new Set(selectedRecords.value.map(r => r.call_sign))
      recordsTable.value.clearSelection()
      records.value.forEach(row => {
        if (!currentSelected.has(row.call_sign)) {
          recordsTable.value.toggleRowSelection(row, true)
        }
      })
    }

    const clearSelection = () => {
      recordsTable.value.clearSelection()
    }

    const selectSingleRow = (row) => {
      recordsTable.value.clearSelection()
      recordsTable.value.toggleRowSelection(row, true)
      hideContextMenu()
    }

    // 批量操作方法
    const batchMarkAsSent = async () => {
      const pendingRecords = selectedRecords.value.filter(record => record.status === 'pending' || record.status === 'resend')
      if (pendingRecords.length === 0) {
        ElMessage.warning('没有可标记为已发送的记录')
        return
      }

      try {
        await ElMessageBox.confirm(
          `确定要将 ${pendingRecords.length} 条记录标记为已发送吗？`,
          '批量操作确认',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )

        for (const record of pendingRecords) {
          await apiService.markSent(record.call_sign)
        }
        
        ElMessage.success(`已成功标记 ${pendingRecords.length} 条记录为已发送`)
        loadRecords()
        loadResendList() // 刷新补发列表
        clearSelection()
      } catch (error) {
        if (error !== 'cancel') {
          console.error('批量标记失败:', error)
          ElMessage.error('批量标记失败')
        }
      }
    }

    const batchMarkAsResend = async () => {
      const sentRecords = selectedRecords.value.filter(record => record.status === 'sent')
      if (sentRecords.length === 0) {
        ElMessage.warning('没有可标记为补发的记录')
        return
      }

      try {
        await ElMessageBox.confirm(
          `确定要将 ${sentRecords.length} 条记录标记为需要补发吗？`,
          '批量操作确认',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )

        for (const record of sentRecords) {
          await apiService.resend(record.call_sign)
        }
        
        ElMessage.success(`已成功标记 ${sentRecords.length} 条记录为需要补发`)
        loadRecords()
        loadResendList()
        clearSelection()
      } catch (error) {
        if (error !== 'cancel') {
          console.error('批量标记失败:', error)
          ElMessage.error('批量标记失败')
        }
      }
    }

    const batchMarkAsReceived = async () => {
      const sentRecords = selectedRecords.value.filter(record => record.status === 'sent')
      if (sentRecords.length === 0) {
        ElMessage.warning('没有可标记为已回执的记录')
        return
      }

      try {
        await ElMessageBox.confirm(
          `确定要将 ${sentRecords.length} 条记录标记为已回执吗？`,
          '批量操作确认',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'info'
          }
        )

        let successCount = 0
        for (const record of sentRecords) {
          try {
            const response = await apiService.markReceived(record.call_sign)
            if (response.data.status === 200) {
              successCount++
            }
          } catch (error) {
            console.error(`标记记录 ${record.call_sign} 失败:`, error)
          }
        }
        
        ElMessage.success(`已成功标记 ${successCount}/${sentRecords.length} 条记录为已回执`)
        loadRecords()
        clearSelection()
      } catch (error) {
        if (error !== 'cancel') {
          console.error('批量标记失败:', error)
          ElMessage.error('批量标记失败')
        }
      }
    }

    const batchProcessWithAI = async () => {
      const needProcessRecords = selectedRecords.value.filter(record => 
        !record.name || !record.phone || !record.address
      )
      
      if (needProcessRecords.length === 0) {
        ElMessage.warning('选中的记录都已处理过，无需AI分析')
        return
      }

      try {
        await ElMessageBox.confirm(
          `确定要对 ${needProcessRecords.length} 条记录进行AI地址分析吗？`,
          'AI处理确认',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'info'
          }
        )

        aiLoading.value = true
        let successCount = 0
        
        for (const record of needProcessRecords) {
          try {
            const response = await apiService.llmProcessSingle(record.call_sign)
            if (response.data.status === 200) {
              successCount++
            }
          } catch (error) {
            console.error(`处理记录 ${record.call_sign} 失败:`, error)
          }
        }
        
        ElMessage.success(`AI处理完成，成功处理 ${successCount}/${needProcessRecords.length} 条记录`)
        loadRecords()
        clearSelection()
      } catch (error) {
        if (error !== 'cancel') {
          console.error('AI批量处理失败:', error)
          ElMessage.error('AI批量处理失败')
        }
      } finally {
        aiLoading.value = false
      }
    }

    const batchDeleteRecords = async () => {
      if (selectedRecords.value.length === 0) {
        ElMessage.warning('请先选择要删除的记录')
        return
      }

      try {
        await ElMessageBox.confirm(
          `确定要删除选中的 ${selectedRecords.value.length} 条记录吗？此操作不可恢复！`,
          '危险操作确认',
          {
            confirmButtonText: '确定删除',
            cancelButtonText: '取消',
            type: 'error'
          }
        )

        deleteLoading.value = true
        let successCount = 0
        
        for (const record of selectedRecords.value) {
          try {
            const response = await apiService.deleteRecord(record.call_sign)
            if (response.data.status === 200) {
              successCount++
            }
          } catch (error) {
            console.error(`删除记录 ${record.call_sign} 失败:`, error)
          }
        }
        
        ElMessage.success(`删除完成，成功删除 ${successCount}/${selectedRecords.value.length} 条记录`)
        loadRecords()
        clearSelection()
      } catch (error) {
        if (error !== 'cancel') {
          console.error('批量删除失败:', error)
          ElMessage.error('批量删除失败')
        }
      } finally {
        deleteLoading.value = false
      }
    }

    const deleteSingleRecord = async (callSign) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除呼号 ${callSign} 的记录吗？此操作不可恢复！`,
          '危险操作确认',
          {
            confirmButtonText: '确定删除',
            cancelButtonText: '取消',
            type: 'error'
          }
        )

        const response = await apiService.deleteRecord(callSign)
        if (response.data.status === 200) {
          ElMessage.success(`记录 ${callSign} 已删除`)
          loadRecords()
        } else {
          ElMessage.error('删除失败')
        }
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除记录失败:', error)
          ElMessage.error('删除失败')
        }
      }
      hideContextMenu()
    }

    const processSingleWithAI = async (callSign) => {
      try {
        aiLoading.value = true
        const response = await apiService.llmProcessSingle(callSign)
        if (response.data.status === 200) {
          ElMessage.success(`呼号 ${callSign} 的地址信息已AI处理`)
          loadRecords()
        } else {
          ElMessage.warning('该记录无需处理或处理失败')
        }
      } catch (error) {
        console.error('AI处理失败:', error)
        ElMessage.error('AI处理失败')
      } finally {
        aiLoading.value = false
      }
      hideContextMenu()
    }

    // 右键菜单处理
    const handleRowContextMenu = (row, column, event) => {
      event.preventDefault()
      contextMenuRow.value = row
      contextMenuStyle.value = {
        position: 'fixed',
        left: event.clientX + 'px',
        top: event.clientY + 'px',
        zIndex: 9999
      }
      contextMenuVisible.value = true
    }

    const copyCallSign = async (callSign) => {
      try {
        await navigator.clipboard.writeText(callSign)
        ElMessage.success(`呼号 ${callSign} 已复制到剪贴板`)
      } catch (error) {
        ElMessage.error('复制失败')
      }
      hideContextMenu()
    }

    // 编辑记录相关方法
    const editRecord = (record) => {
      editData.call_sign = record.call_sign
      editData.name = record.name || ''
      editData.phone = record.phone || ''
      editData.province = record.province || ''
      editData.address = record.address || ''
      editData.zip_code = record.zip_code || ''
      editData.info = record.info || ''
      editDialogVisible.value = true
      hideContextMenu()
    }

    const saveEditRecord = async () => {
      try {
        const valid = await editForm.value.validate()
        if (!valid) return

        editLoading.value = true
        const response = await apiService.editRecord(editData)
        
        if (response.data.status === 200) {
          ElMessage.success('记录更新成功')
          editDialogVisible.value = false
          loadRecords()
        } else {
          ElMessage.error(response.data.message || '更新失败')
        }
      } catch (error) {
        console.error('更新记录失败:', error)
        ElMessage.error('更新失败，请稍后重试')
      } finally {
        editLoading.value = false
      }
    }

    return {
      passwordDialogVisible,
      authenticated,
      password,
      verifying,
      activeTab,
      addData,
      addLoading,
      addForm,
      addRules,
      records,
      recordsLoading,
      aiLoading,
      deleteLoading,
      recordsTable,
      selectedRecords,
      selectAll,
      isIndeterminate,
      canBatchMarkSent,
      canBatchMarkResend,
      canBatchMarkReceived,
      canBatchProcessAI,
      contextMenuVisible,
      contextMenuStyle,
      contextMenuRow,
      expiredRecords,
      expiredLoading,
      resendList,
      resendLoading,
      editDialogVisible,
      editLoading,
      editForm,
      editData,
      editRules,
      checkAuthStatus,
      verifyPassword,
      goBack,
      logout,
      addRecord,
      resetAddForm,
      loadRecords,
      processWithAI,
      markAsSent,
      markAsResend,
      markAsReceived,
      loadExpired,
      loadResendList,
      getStatusType,
      getStatusText,
      getDaysOverdue,
      handleSelectionChange,
      handleSelectAllChange,
      selectInverse,
      clearSelection,
      selectSingleRow,
      batchMarkAsSent,
      batchMarkAsResend,
      batchMarkAsReceived,
      batchProcessWithAI,
      batchDeleteRecords,
      deleteSingleRecord,
      processSingleWithAI,
      handleRowContextMenu,
      copyCallSign,
      editRecord,
      saveEditRecord
    }
  }
}
</script>

<style scoped>
.admin-container {
  padding: 20px;
  min-width: 1200px;
}

.admin-content {
  max-width: 1600px;
  margin: 0 auto;
  width: 95%;
}

.header-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 18px;
  font-weight: bold;
}

.admin-tabs {
  background: white;
  padding: 20px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.el-card {
  margin-bottom: 20px;
}

.el-table {
  margin-top: 20px;
}

.batch-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background: #f0f9ff;
  border: 1px solid #91caff;
  border-radius: 4px;
  margin-bottom: 10px;
}

.selected-info {
  font-size: 14px;
  color: #1890ff;
  font-weight: 500;
}

.batch-actions {
  display: flex;
  gap: 8px;
}

.selection-toolbar {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 10px 0;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 10px;
}

.context-menu {
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  padding: 5px 0;
  min-width: 120px;
}

.context-menu-item {
  padding: 8px 16px;
  font-size: 14px;
  color: #606266;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
}

.context-menu-item:hover {
  background: #f5f7fa;
  color: #409eff;
}

.context-menu-danger {
  color: #f56c6c !important;
}

.context-menu-danger:hover {
  background: #fef0f0 !important;
  color: #f56c6c !important;
}

.context-menu-divider {
  height: 1px;
  background: #e4e7ed;
  margin: 5px 0;
}
</style>
