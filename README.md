# HAM QSL 回执管理系统

为广大hams所设计的QSL一站式管理系统，包含后端API和前端Web界面。

## 项目特性

- **后端**: Flask API服务器，提供完整的QSL记录管理功能
- **前端**: Vue 3 + Element Plus 响应式Web界面
- **AI集成**: 使用DeepSeek AI自动处理地址信息
- **定时任务**: 自动检查超期未回执记录
- **多用户界面**: 普通用户回执页面 + 管理员控制台

## 快速启动

#### 启动后端
```bash
# 安装Python依赖
pip install -r requirements.txt

# 启动后端服务器
python main.py
```

#### 启动前端
```bash
# 安装Node.js依赖
cd frontend
npm install

# 启动前端开发服务器
npm run dev
```

## 访问地址

- **前端界面**: http://localhost:3000
  - 普通用户回执页面: http://localhost:3000/
  - 管理员界面: http://localhost:3000/admin
- **后端API**: http://localhost:5000

## 功能说明

### 普通用户功能
- 输入呼号确认QSL回执
- 简洁直观的操作界面

### 管理员功能
- 添加新的QSL记录
- 查看和管理所有记录
- AI自动处理地址信息
- 标记卡片发送状态
- 查看超期未回执记录
- 管理需要补发的记录

### 自动化功能
- 每天上午9点自动检查超期记录
- 邮件和微信提醒（需要自定义实现）
- AI智能地址解析

## 技术栈

### 后端
- Python 3.13
- Flask + Flask-CORS
- SQLite3
- OpenAI (DeepSeek)
- APScheduler
- BeautifulSoup4

### 前端
- Vue 3
- Vue Router 4
- Element Plus
- Axios
- Vite

## API文档
[点此查看完整API文档](https://apifox.com/apidoc/shared-43a9b07f-1fd2-4a34-973b-b83a1c4e994c)

## 配置说明

### AI配置
在 `main.py` 中修改AI配置：
```python
client = OpenAI(
    api_key="your-api-key",
    base_url="https://api.deepseek.com",
)
```

### 提醒功能
在 `main.py` 中实现邮件和微信提醒函数：
```python
def send_email_reminder(call_sign, message):
    # 实现邮件发送逻辑
    pass

def send_wechat_reminder(call_sign, message):
    # 实现微信发送逻辑
    pass
```

## 部署说明

### 生产环境部署
1. 构建前端生产版本：
   ```bash
   cd frontend
   npm run build
   ```

2. 配置Flask以服务静态文件
3. 修改管理员密码
4. 配置邮件和微信提醒

## 许可证

本项目采用开源许可证，详见 LICENSE 文件。