<template>
  <div class="receipt-container">
    <el-card class="receipt-card">
      <template #header>
        <div class="card-header">
          <span>QSL回执确认</span>
        </div>
      </template>
      
      <el-form
        ref="receiptForm"
        :model="receiptData"
        :rules="rules"
        label-width="120px"
        class="receipt-form"
        @submit.prevent="submitReceipt"
      >
        <el-form-item label="呼号" prop="callSign">
          <el-input
            v-model="receiptData.callSign"
            placeholder="请输入您的业余无线电呼号"
            size="large"
            :prefix-icon="User"
            @keydown.enter.prevent="submitReceipt"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            @click="submitReceipt"
            :loading="loading"
            class="submit-btn"
          >
            确认回执
          </el-button>
        </el-form-item>
      </el-form>

      <el-divider>说明</el-divider>
      
      <el-alert
        title="使用说明"
        type="info"
        :closable="false"
        show-icon
      >
        <template #default>
          <p>1. 请输入您的完整业余无线电呼号</p>
          <p>2. 点击"确认回执"按钮确认您已收到QSL卡片</p>
          <p>3. 系统将自动记录您的回执时间</p>
        </template>
      </el-alert>
    </el-card>

    <!-- 成功提示对话框 -->
    <el-dialog
      v-model="successDialogVisible"
      title="回执成功"
      width="500px"
      center
    >
      <div style="text-align: center;">
        <el-icon size="60" color="#67C23A">
          <SuccessFilled />
        </el-icon>
        <p style="margin-top: 20px; font-size: 16px;">
          呼号 <strong>{{ submittedCallSign }}</strong> 的回执已成功记录！
        </p>
        
        <el-divider>回邮地址信息</el-divider>
        
        <el-card class="address-card">
          <div class="address-info">
            <p><strong>回邮地址：</strong>安徽省滁州市天长市汊涧镇汊北村汊北卫生院</p>
            <p><strong>呼号：</strong>BH6ATV</p>
            <p><strong>手机号：</strong>18055031132</p>
            <p><strong>邮编：</strong>239321</p>
          </div>
        </el-card>
        
        <p style="margin-top: 15px; font-size: 14px; color: #666;">
          请将您的QSL卡片回邮到以上地址，谢谢！
        </p>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button type="primary" @click="successDialogVisible = false">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 呼号未找到提醒对话框 -->
    <el-dialog
      v-model="notFoundDialogVisible"
      title="呼号未找到"
      width="500px"
      center
    >
      <div style="text-align: center;">
        <el-icon size="60" color="#F56C6C">
          <WarningFilled />
        </el-icon>
        <p style="margin-top: 20px; font-size: 16px;">
          未找到呼号 <strong>{{ notFoundCallSign }}</strong>，呼号是否输入错误？
        </p>
        
        <el-divider>请检查</el-divider>
        
        <el-card class="tips-card">
          <div class="tips-info">
            <p><strong>请确认：</strong></p>
            <p>• 呼号输入是否正确</p>
            <p>• 是否和管理员申请QSL</p>
            <p>• 呼号是否与提供给管理员的一致</p>
          </div>
        </el-card>
        
        <p style="margin-top: 15px; font-size: 14px; color: #666;">
          如确认呼号正确，请联系管理员
        </p>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="notFoundDialogVisible = false">
            取消
          </el-button>
          <el-button type="primary" @click="retryInput">
            重新输入
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { User, SuccessFilled, WarningFilled } from '@element-plus/icons-vue'
import { apiService } from '../api'

export default {
  name: 'Receipt',
  components: {
    User,
    SuccessFilled,
    WarningFilled
  },
  setup() {
    const receiptData = reactive({
      callSign: ''
    })

    const loading = ref(false)
    const successDialogVisible = ref(false)
    const notFoundDialogVisible = ref(false)
    const receiptForm = ref()
    const submittedCallSign = ref('')
    const notFoundCallSign = ref('')

    const rules = {
      callSign: [
        { required: true, message: '请输入呼号', trigger: 'blur' },
        { min: 3, max: 20, message: '呼号长度应在3-20个字符之间', trigger: 'blur' },
        { pattern: /^[A-Za-z0-9]+$/, message: '呼号只能包含字母和数字', trigger: 'blur' }
      ]
    }

    const submitReceipt = async () => {
      try {
        const valid = await receiptForm.value.validate()
        if (!valid) return

        loading.value = true
        
        const response = await apiService.receipt(receiptData.callSign.toUpperCase())
        
        if (response.data.status === 200) {
          submittedCallSign.value = receiptData.callSign.toUpperCase()
          successDialogVisible.value = true
          receiptData.callSign = ''
          receiptForm.value.resetFields()
        } else {
          ElMessage.error('回执失败，请检查呼号是否正确')
        }
      } catch (error) {
        console.error('回执失败:', error)
        if (error.response?.status === 404) {
          notFoundCallSign.value = receiptData.callSign.toUpperCase()
          notFoundDialogVisible.value = true
        } else {
          ElMessage.error('回执失败，请稍后重试')
        }
      } finally {
        loading.value = false
      }
    }

    const retryInput = () => {
      notFoundDialogVisible.value = false
      receiptData.callSign = ''
      receiptForm.value.resetFields()
    }

    return {
      receiptData,
      rules,
      loading,
      successDialogVisible,
      notFoundDialogVisible,
      receiptForm,
      submittedCallSign,
      notFoundCallSign,
      submitReceipt,
      retryInput,
      User,
      SuccessFilled,
      WarningFilled
    }
  }
}
</script>

<style scoped>
.receipt-container {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  min-height: 80vh;
  padding: 40px 20px;
}

.receipt-card {
  width: 100%;
  max-width: 600px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
}

.receipt-form {
  padding: 20px 0;
}

.submit-btn {
  width: 100%;
  height: 50px;
  font-size: 18px;
  font-weight: bold;
}

.el-alert {
  margin-top: 20px;
}

.el-alert p {
  margin: 5px 0;
  line-height: 1.5;
}

.address-card {
  margin: 20px 0;
  text-align: left;
}

.address-info p {
  margin: 8px 0;
  font-size: 14px;
  line-height: 1.6;
}

.address-info strong {
  color: #409eff;
}

.tips-card {
  margin: 20px 0;
  text-align: left;
}

.tips-info p {
  margin: 8px 0;
  font-size: 14px;
  line-height: 1.6;
}

.tips-info strong {
  color: #F56C6C;
}
</style>
