# QSL回执管理系统

## 项目简介
QSL回执管理系统是一个用于管理和记录业余无线电爱好者QSL回执的Web应用程序。用户可以通过输入呼号来查询回执状态，管理员可以在后台管理回执记录。

## 安装步骤
1. 克隆项目到本地：
    ```bash
    git clone https://github.com/yourusername/ham_qsl_receipt.git
    cd ham_qsl_receipt
    ```

2. 创建并激活虚拟环境：
    ```bash
    python -m venv venv
    source venv/bin/activate  # 对于Windows用户，使用 `venv\Scripts\activate`
    ```

3. 安装依赖：
    ```bash
    pip install -r requirements.txt
    ```

4. 运行应用程序：
    ```bash
    python main.py
    ```

5. 在浏览器中打开 `http://127.0.0.1:5000` 访问应用程序。

## 使用说明
### 用户界面
- 用户可以在主页输入呼号并查询回执状态。
- 如果呼号存在于数据库中，系统会返回相应的回执信息。

### 管理员界面
- 管理员可以通过 `/admin` 路由访问管理后台。
- 管理员可以查看所有回执记录，并根据状态进行筛选。
- 管理员可以添加新的呼号记录，删除现有记录，或更新记录的回执状态。

## 主要功能
- **呼号查询**：用户可以输入呼号查询回执状态。
- **记录管理**：管理员可以添加、删除和更新呼号记录。
- **状态筛选**：管理员可以根据回执状态筛选记录。
- **时间戳转换**：记录的创建时间和更新时间会自动转换为可读格式。

## 贡献
欢迎对本项目进行贡献！如果有任何建议或问题，请提交issue或pull request。

## 许可证
本项目采用MIT许可证，详情请参阅LICENSE文件。