## 🏥 MedGraphRAG：基于知识图谱 + RAG 的中文医疗问答系统

MedGraphRAG 是一个结合 **知识图谱 (Neo4j)**、**向量检索 (Milvus)** 和 **大语言模型 (LLM)** 的中文医疗问答系统。  
后端基于 FastAPI，前端为纯 HTML/JavaScript 聊天页面，支持可视化展示多源检索路径，适合作为 **教学 Demo** 或 **二次开发起点**。

---

## ✨ 特性一览

- **🔗 多源知识融合**
  - 🗺️ 医疗知识图谱：疾病–症状–药品–科室等实体关系（[Neo4j](https://neo4j.com/)）
  - 🔍 文本向量检索：病例、说明书、文档语料（[Milvus](https://milvus.io/)）
  - 🤖 大模型问答：如 [DeepSeek](https://www.deepseek.com/)，用于生成最终回答

- **📦 模块职责清晰**
  - ⚙️ [`config/`](../config/)：集中配置管理（环境变量 + 默认值）→ [查看文档](../config/README.md)
  - 🧩 [`core/`](../core/)：Embedding、LLM、向量库、缓存、知识图谱等基础能力 → [查看文档](../core/README.md)
  - 🚀 [`services/`](../services/)：Agent 服务、图谱服务等业务逻辑 → [查看文档](../services/README.md)
  - 🔌 [`api/`](../api/)：FastAPI 路由与中间件（可选扩展）→ [查看文档](../api/README.md)
  - 🎨 [`web/`](../web/)：前端聊天界面（静态 HTML）→ [查看文档](../web/README.md)

- **💾 本地化与可扩展**
  - 📁 [`storage/models/`](../storage/models/)：预留本地模型权重目录，可扩展为纯本地推理
  - 💿 [`storage/databases/`](../storage/databases/)：本地 Milvus 数据文件
  - 📊 [`data/`](../data/)：集中管理原始数据、词典和处理后数据 → [查看文档](../data/README.md)

- **🛠️ 工程化实践**
  - 🚀 一键启动脚本 [`start.sh`](../start.sh)
  - 📝 模块内 `README.md` 文档说明
  - 📂 日志、PID、数据库等均落在 [`storage/`](../storage/) 下，便于管理 → [查看文档](../storage/README.md)

更细粒度的模块说明见各模块目录下的 `README.md`，以及 [`docs/technical_workflow.md`](./technical_workflow.md) 中的技术流程说明。

---

## 📁 目录结构概览

```bash
MedGraphRAG/
├── requirements.txt            # 项目依赖
├── start.sh                    # 一键启动脚本（启动两大服务并自动打开浏览器）
├── api/                        # API 层（FastAPI 路由与中间件，可选入口）
├── config/                     # 配置管理（环境变量 + 默认值）
├── core/                       # 核心能力（模型 / 向量库 / 图谱 / 缓存等）
├── services/                   # 服务层（Agent 服务、图服务）
├── data/                       # 数据文件（原始 / 处理后 / 词典）
├── storage/                    # 本地数据库 / 模型 / 日志 / PID 等
├── utils/                      # 工具脚本（文档加载、文本切分等）
├── web/                        # 前端静态页面（`index.html` 医疗问答界面）
├── scripts/                    # Python 启动脚本（被 `start.sh` 调用）
├── tests/                      # 测试用例（占位）
└── docs/                       # 文档（本文件 + 技术流程）
```

### 📚 模块文档导航

常用子模块文档入口（点击可跳转到对应文档）：

- ⚙️ **配置模块**：[`config/README.md`](../config/README.md) | [配置文件](../config/settings.py)
- 🧩 **核心模块总览**：[`core/README.md`](../core/README.md)
  - 🤖 模型封装（LLM / Embedding）：[`core/models/README.md`](../core/models/README.md) | [代码](../core/models/)
  - 🔍 向量库（Milvus）：[`core/vector_store/README.md`](../core/vector_store/README.md) | [代码](../core/vector_store/milvus_client.py)
  - 💾 缓存（Redis）：[`core/cache/README.md`](../core/cache/README.md) | [代码](../core/cache/redis_client.py)
  - 🗺️ 知识图谱（Neo4j + NL2Cypher）：[`core/graph/README.md`](../core/graph/README.md) | [代码](../core/graph/)
- 🚀 **服务层**：[`services/README.md`](../services/README.md) | [Agent 服务](../services/agent_service.py) | [图服务](../services/graph_service.py)
- 🔌 **API 层**：[`api/README.md`](../api/README.md) | [路由代码](../api/routes/)
- 📊 **数据目录**：[`data/README.md`](../data/README.md) | [数据文件](../data/)
- 💿 **存储目录**：[`storage/README.md`](../storage/README.md) | [存储目录](../storage/)
- 🔧 **工具脚本**：[`utils/README.md`](../utils/README.md) | [工具代码](../utils/)
- 🎨 **前端与启动脚本**：[`web/README.md`](../web/README.md) | [`scripts/README.md`](../scripts/README.md) | [前端页面](../web/index.html) | [启动脚本](../start.sh)
- 📋 **整体技术流程**：[`docs/technical_workflow.md`](./technical_workflow.md)

---

## 🚀 环境准备

### 1️⃣ 基础依赖

- 🐍 Python 3.8+
- 🗺️ Neo4j 数据库（知识图谱）
- 🔍 Milvus（向量数据库，当前使用本地文件存储）
- 💾 Redis（可选，用于缓存问答）
- 💿 足够磁盘空间（本地模型权重 + 向量库 + 日志）

### 2️⃣ 安装 Python 依赖

在项目根目录执行：

```bash
pip install -r requirements.txt
```

推荐使用虚拟环境（`venv` 或 `conda`）：

```bash
python -m venv .venv
source .venv/bin/activate        # Windows 使用 .venv\Scripts\activate
pip install -r requirements.txt
```

### 3️⃣ 配置环境变量 / API Key

主要配置集中在 [`config/settings.py`](../config/settings.py)，支持从环境变量中读取：

- 🤖 LLM 与 Embedding：
  - 🔑 `DEEPSEEK_API_KEY`
  - 🔑 `ZHIPU_API_KEY`
- 🗺️ Neo4j：
  - 🔗 `NEO4J_URI`
  - 👤 `NEO4J_USER`
  - 🔒 `NEO4J_PASSWORD`
- 💾 Redis（可选）：
  - 🏠 `REDIS_HOST` / 🔌 `REDIS_PORT` / 🔒 `REDIS_PASSWORD`
- 🌐 服务端口：
  - 🚀 `AGENT_SERVICE_PORT`（默认 `8103`）
  - 🗺️ `GRAPH_SERVICE_PORT`（默认 `8101`）

> ⚠️ 建议通过系统环境变量配置敏感信息，**不推荐** 在代码中硬编码 API Key 和密码。

> 💡 详细配置说明请查看：[`config/README.md`](../config/README.md)

---

## 🎬 启动与运行

### 🚀 方式一：一键启动（推荐）

在项目根目录执行：

```bash
chmod +x start.sh        # 第一次使用需要赋予执行权限
./start.sh
```

该脚本会：

1. 🔍 自动选择 Python 解释器（默认 `python3.11`，可通过环境变量 `PYTHON_CMD` 覆盖）  
2. 🚀 后台启动两个服务：
   - 🤖 Agent 服务：[`scripts/start_agent.py`](../scripts/start_agent.py)（默认端口 `8103`）
   - 🗺️ 图服务：[`scripts/start_graph_service.py`](../scripts/start_graph_service.py)（默认端口 `8101`）
3. ⏳ 等待端口就绪
4. 🌐 在 macOS 上自动打开浏览器访问 `http://localhost:8103/`
5. 🔄 监控服务进程，脚本退出时尝试清理子进程

📝 日志输出默认位于：

- 📄 [`storage/logs/agent_service_simple.log`](../storage/logs/agent_service_simple.log)
- 📄 [`storage/logs/graph_service_simple.log`](../storage/logs/graph_service_simple.log)

> 📝 启动脚本说明：[`scripts/README.md`](../scripts/README.md) | [启动脚本源码](../start.sh)

### 🔧 方式二：手动启动（开发调试）

也可以在两个终端分别启动服务：

```bash
cd /path/to/MedGraphRAG

# 启动 Agent 服务（负责前端页面 + 医学问答接口）
python scripts/start_agent.py

# 启动图服务（负责 NL2Cypher + Neo4j 查询）
python scripts/start_graph_service.py
```

---

## 💻 使用方式

### 1️⃣ 前端聊天页面

启动 Agent 服务后，在浏览器访问：

```text
http://localhost:8103/
```

页面提供：

- 💬 医学问答聊天窗口
- 📋 示例问题按钮
- 🔍 多源检索路径可视化：
  - 🔎 向量检索（Milvus）
  - 📄 PDF 检索（ParentDocumentRetriever）
  - 🗺️ 知识图谱查询（Neo4j）
- 📊 知识图谱生成的 Cypher 语句与置信度展示

前端通过：

- `API_URL = window.location.origin + '/'`
- 向当前域名根路径发起 `POST /` 请求

对应后端 [`services/agent_service.py`](../services/agent_service.py) 中的：

- `@app.get("/")`：返回 [`web/index.html`](../web/index.html)
- `@app.post("/")`：接收 `{"question": "..."}`，执行多源检索 + LLM 生成回答

> 📖 前端详细说明：[`web/README.md`](../web/README.md) | 服务层说明：[`services/README.md`](../services/README.md)

### 2️⃣ 直接调用 API

医学问答接口示例：

```bash
curl -X POST "http://localhost:8103/" \
  -H "Content-Type: application/json" \
  -d '{"question": "感冒了有什么症状？"}'
```

服务信息接口示例：

```bash
curl "http://localhost:8103/api/info"
```

图服务还提供 `/generate`、`/validate`、`/execute` 等接口，详见 [`services/README.md`](../services/README.md) 与 [`services/graph_service.py`](../services/graph_service.py)。

---

## 🏗️ 架构概览

- ⚙️ **[`config/`](../config/) – 配置管理** → [文档](../config/README.md)
  - [`settings.py`](../config/settings.py) 暴露全局 `settings` 实例，统一管理 Neo4j / Redis / Milvus / 模型路径 / 端口等配置。

- 🧩 **[`core/`](../core/) – 核心能力** → [文档](../core/README.md)
  - 🤖 [`models/`](../core/models/)：Embedding 与 LLM 封装（如 `ZhipuAIEmbeddings`、DeepSeek 客户端）→ [文档](../core/models/README.md)
  - 🔍 [`vector_store/`](../core/vector_store/)：Milvus 向量库封装（混合检索：稠密 + 稀疏 BM25）→ [文档](../core/vector_store/README.md)
  - 💾 [`cache/`](../core/cache/)：Redis 客户端与问答缓存封装 → [文档](../core/cache/README.md)
  - 🗺️ [`graph/`](../core/graph/)：Neo4j 客户端、图模式定义、NL2Cypher Prompt、查询验证等 → [文档](../core/graph/README.md)

- 🚀 **[`services/`](../services/) – 业务服务** → [文档](../services/README.md)
  - 🤖 [`agent_service.py`](../services/agent_service.py)：整合向量检索 + PDF 检索 + 知识图谱 + LLM，提供统一 `/` 问答接口
  - 🗺️ [`graph_service.py`](../services/graph_service.py)：负责 NL2Cypher 生成、验证和执行，对外暴露图服务 API

- 🎨 **[`web/`](../web/) – 前端页面** → [文档](../web/README.md)
  - [`index.html`](../web/index.html)：单页应用（原生 JS），调用后端 API，展示检索路径和回答

- 🔧 **[`scripts/`](../scripts/) – 启动脚本** → [文档](../scripts/README.md)
  - [`start_agent.py`](../scripts/start_agent.py) / [`start_graph_service.py`](../scripts/start_graph_service.py)：分别启动两个 FastAPI 服务，配合根目录 [`start.sh`](../start.sh) 形成一键启动

更详细的架构与调用链说明，见 [`docs/technical_workflow.md`](./technical_workflow.md)。

---

## 🛠️ 开发与扩展建议

- 📦 **依赖管理**
  - 🐍 使用虚拟环境管理依赖，避免与系统 Python 冲突。
  - 📋 依赖列表：[`requirements.txt`](../requirements.txt)

- ⚙️ **配置管理**
  - 🔧 优先通过环境变量或 [`config/settings.py`](../config/settings.py) 修改配置，不在业务代码中硬编码。
  - 📖 配置说明：[`config/README.md`](../config/README.md)

- 🐛 **排错与日志**
  - 📝 日志位于 [`storage/logs/`](../storage/logs/)，遇到问题优先查看对应服务日志。
  - 📂 存储目录说明：[`storage/README.md`](../storage/README.md)

- 🚀 **功能扩展建议**
  - ➕ **新增数据源**：在 [`core/`](../core/) 中增加对应封装，在 [`services/`](../services/) 中组合调用，在 [`web/`](../web/) 中增加展示。
  - 🔄 **替换 / 新增 LLM**：在 [`core/models/`](../core/models/) 中封装新模型，在 Agent 逻辑中切换或路由。
  - 🗺️ **增强图谱**：在 [`data/`](../data/) 与 Neo4j 中补充实体与关系，同时更新 [`core/graph/models.py`](../core/graph/models.py) 中的模式描述。

如在使用过程中新增模块或流程，建议：

- 📝 在对应模块目录下补充或更新 `README.md`
- 📋 在 [`docs/technical_workflow.md`](./technical_workflow.md) 中补充技术流程
- 📌 如有重大改动，可在本文件中增加「变更记录 / Changelog」小节

---

## 📖 快速导航

- 🚀 [环境准备](#-环境准备) | 🎬 [启动与运行](#-启动与运行) | 💻 [使用方式](#-使用方式) | 🏗️ [架构概览](#️-架构概览)
- ⚙️ [配置模块文档](../config/README.md) | 🧩 [核心模块文档](../core/README.md) | 🚀 [服务层文档](../services/README.md)
- 📋 [技术流程文档](./technical_workflow.md) | 📁 [项目根目录](../)
