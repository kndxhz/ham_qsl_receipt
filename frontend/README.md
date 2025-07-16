# HAM QSL Receipt Frontend

这是一个基于Vue 3的HAM QSL回执管理系统前端应用。

## 功能特性

### 普通用户界面 (/)
- QSL回执确认功能
- 简洁易用的界面
- 实时验证和反馈

### 管理员界面 (/admin)
- 密码保护 (密码: passw0rd)
- 添加新的QSL记录
- 查看和管理所有记录
- AI自动处理地址信息
- 查看超期未回执记录
- 管理需要补发的记录
- 记录状态管理

## 安装和运行

### 前提条件
- Node.js (版本 14+)
- npm 或 yarn

### 安装依赖
```bash
cd frontend
npm install
```

### 运行开发服务器
```bash
npm run dev
```

访问 http://localhost:3000

### 构建生产版本
```bash
npm run build
```

## 项目结构

```
frontend/
├── src/
│   ├── api/           # API服务
│   ├── components/    # Vue组件
│   │   ├── Receipt.vue    # 普通用户回执页面
│   │   └── Admin.vue      # 管理员页面
│   ├── App.vue        # 主应用组件
│   └── main.js        # 应用入口
├── index.html         # HTML模板
├── package.json       # 项目配置
└── vite.config.js     # Vite配置
```

## 使用说明

### 普通用户
1. 访问根路径 `/`
2. 输入您的业余无线电呼号
3. 点击"确认回执"按钮

### 管理员
1. 访问 `/admin` 路径
2. 输入管理员密码: `passw0rd`
3. 使用各个选项卡管理QSL记录：
   - **添加记录**: 添加新的QSL记录
   - **记录管理**: 查看所有记录，使用AI处理地址
   - **超期记录**: 查看超过一个月未回执的记录
   - **补发列表**: 查看需要补发的记录

## 技术栈

- Vue 3
- Vue Router 4
- Element Plus
- Axios
- Vite

## API接口

前端通过代理访问后端API (Flask应用运行在端口5000)：
- `/api/*` 请求会被代理到 `http://localhost:5000/*`

## 注意事项

1. 确保后端Flask应用正在运行 (端口5000)
2. 管理员密码是硬编码的 `passw0rd`，生产环境中应该修改
3. 前端开发服务器运行在端口3000
