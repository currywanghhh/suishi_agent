# 🎯 项目结构整理完成

## 📁 新的目录结构

```
agent/
├── data_generation/          # 📊 数据生成工具集
│   ├── create_knowledge_base.py
│   ├── generate_for_l1.py
│   ├── generate_single_level.py
│   ├── generate_sub_levels.py
│   ├── generate_l4_content.py
│   ├── test_l4_interaction.py
│   ├── config.py
│   ├── .env
│   └── README.md
│
├── web_app/                  # 🌐 Web 应用
│   ├── wu_xing_advisor/      # Django 项目配置
│   ├── advisor/              # 主应用（视图、模板）
│   ├── manage.py
│   ├── db.sqlite3
│   ├── .env
│   └── README.md
│
├── .env                      # 共享环境变量
├── config.py                 # 共享配置
├── requirements.txt          # Python 依赖
├── README.md                 # 项目主文档
├── MATCHING_PROCESS_EXPLANATION.md
├── QUICKSTART.md
└── STRUCTURE.md             # 本文档
```

## 🎯 各文件夹用途

### `data_generation/` - 数据生成工具集

**用途**: 生成和管理知识库数据（L1-L4 层级结构和内容）

**常用命令**:
```powershell
cd data_generation

# 创建数据库表
python create_knowledge_base.py

# 生成完整知识库
python generate_for_l1.py

# 生成 L4 详细内容
python generate_l4_content.py

# 测试内容
python test_l4_interaction.py
```

**详细文档**: [`data_generation/README.md`](./data_generation/README.md)

---

### `web_app/` - Web 应用

**用途**: 运行 Django 前后端，提供聊天式决策建议界面

**常用命令**:
```powershell
cd web_app

# 运行数据库迁移
python manage.py migrate

# 启动开发服务器
python manage.py runserver

# 访问: http://127.0.0.1:8000/
```

**详细文档**: [`web_app/README.md`](./web_app/README.md)

---

## 🚀 典型工作流程

### 1. 首次设置（完整流程）

```powershell
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量（编辑根目录 .env）
# 填写数据库连接和 API 密钥

# 3. 生成数据
cd data_generation
python create_knowledge_base.py
python generate_for_l1.py
python generate_l4_content.py

# 4. 运行 Web 应用
cd ../web_app
python manage.py migrate
python manage.py runserver
```

### 2. 只生成新数据

```powershell
cd data_generation

# 生成单个层级
python generate_single_level.py --level 2 --max 10

# 或为特定 L1 生成子树
python generate_for_l1.py --l1 "Career"
```

### 3. 只运行 Web 应用

```powershell
cd web_app
python manage.py runserver
```

---

## 📝 环境变量配置

根目录的 `.env` 文件会被两个文件夹共享使用：

```env
# 数据库配置
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=wu_xing_advisor

# LLM API 配置
SILICON_FLOW_API_KEY=your_api_key

# Django 配置（仅 web_app 需要）
DJANGO_SECRET_KEY=your-secret-key
DEBUG=True
```

**注意**: `data_generation/` 和 `web_app/` 内也有各自的 `.env` 副本，方便独立运行。

---

## 🔧 开发建议

### 修改生成配置

编辑 `data_generation/config.py` 或根目录的 `config.py`：

```python
L2_CONFIG = {"max_per_parent": 10}
L3_CONFIG = {"max_per_parent": 8}
L4_CONFIG = {"max_per_parent": 6}
```

### 修改 Web 应用

- **前端**: 编辑 `web_app/advisor/templates/advisor/index.html`
- **后端逻辑**: 编辑 `web_app/advisor/views.py`
- **路由**: 编辑 `web_app/advisor/urls.py`

### 查看匹配流程

阅读 [`MATCHING_PROCESS_EXPLANATION.md`](./MATCHING_PROCESS_EXPLANATION.md) 了解：
- 为什么需要 4 次 LLM 调用
- 如何优化响应速度
- 向量检索替代方案

---

## ✅ 整理完成清单

- ✅ 数据生成脚本移至 `data_generation/`
- ✅ Django 前后端移至 `web_app/`
- ✅ 为两个文件夹创建独立的 README
- ✅ 更新主 README 反映新结构
- ✅ 复制配置文件到两个文件夹
- ✅ 保留原有文档（MATCHING_PROCESS_EXPLANATION.md 等）

---

## 📞 快速帮助

- **生成数据相关**: 查看 [`data_generation/README.md`](./data_generation/README.md)
- **Web 应用相关**: 查看 [`web_app/README.md`](./web_app/README.md)
- **匹配流程**: 查看 [`MATCHING_PROCESS_EXPLANATION.md`](./MATCHING_PROCESS_EXPLANATION.md)
- **项目概述**: 查看 [`README.md`](./README.md)

---

**现在目录结构清晰多了！🎉**
