# MedGraphRAG：基于知识图谱与 RAG 的中文医疗问答系统

MedGraphRAG 是一个结合 **知识图谱 (Neo4j)**、**向量检索 (Milvus)** 和 **大语言模型 (LLM)** 的中文医疗问答系统。  
后端使用 FastAPI，前端是一个纯 HTML/JS 的聊天页面，支持可视化展示多源检索路径。

---

## 主要功能

- **多源知识融合**
  - 医疗知识图谱（疾病–症状–药品–科室等实体关系，基于 Neo4j）
  - 文本语料向量检索（病例、文档、说明书等，基于 Milvus）
  - PDF 文档分层检索（父子文档 + 向量检索）
  - 大模型回答与推理（如 DeepSeek）

- **清晰的模块划分**
  - `config/`：集中配置管理，支持环境变量
  - `core/`：Embedding、LLM、向量库、缓存、知识图谱等基础能力
  - `services/`：Agent 服务、图谱服务等业务逻辑
  - `api/`：FastAPI 路由与中间件（按需扩展）
  - `web/`：前端聊天界面（静态 HTML）

- **本地化与可扩展**
  - `storage/models/` 下预留本地模型权重目录，可扩展为纯本地推理
  - `storage/databases/` 下使用本地文件存储 Milvus 数据
  - `data/` 下集中管理原始数据、词典和处理后数据

更细粒度的模块说明，见 `docs/` 目录下各个模块文档（如 `config.md`、`core.md`、`services.md` 等）。

---

## 目录结构概览（当前项目）

```bash
MedGraphRAG/
├── requirements.txt            # 依赖管理
├── start.sh                    # 一键启动脚本（启动两大服务并自动打开浏览器）
├── api/                        # API 层（FastAPI 路由与中间件，可选入口）
├── config/                     # 配置管理（环境变量 + 默认值）
├── core/                       # 核心能力（模型 / 向量库 / 图谱 / 缓存等）
├── services/                   # 服务层（Agent 服务、图服务）
├── data/                       # 数据文件（原始 / 处理后 / 词典）
├── storage/                    # 本地数据库 / 模型 / 日志 / PID 等
├── utils/                      # 工具函数（文档加载、文本切分等）
├── web/                        # 前端静态页面（`index.html` 医疗问答界面）
├── scripts/                    # Python 启动脚本（被 `start.sh` 调用）
├── tests/                      # 测试用例（占位）
└── docs/                       # 文档（当前目录）
```

各模块的详细说明文档：

- `docs/config.md`：配置模块说明
- `docs/core.md`：核心能力模块说明（Embedding / LLM / 向量库 / 图谱等）
- `docs/services.md`：服务层说明（Agent 服务、图服务）
- `docs/api.md`：API 层与路由说明
- `docs/data.md`：数据目录与词典说明
- `docs/storage.md`：存储目录说明（databases / models / logs / pids）
- `docs/utils.md`：工具模块说明
- `docs/web_and_scripts.md`：前端页面与启动脚本说明

---

## 环境准备

### 1. 基础依赖

- Python 3.8+
- Neo4j 数据库（用于知识图谱）
- Milvus（向量数据库，当前使用本地文件存储）
- Redis（可选，用于缓存）
- 足够磁盘空间（本地模型权重 + 向量库 + 日志）

### 2. 安装 Python 依赖

在项目根目录执行：

```bash
pip install -r requirements.txt
```

建议使用虚拟环境（如 `venv` 或 `conda`）：

```bash
python -m venv .venv
source .venv/bin/activate        # Windows 使用 .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 配置环境变量 / API Key

当前主要配置集中在 `config/settings.py`，支持从环境变量中读取：

- LLM 与 Embedding 相关：
  - `DEEPSEEK_API_KEY`
  - `ZHIPU_API_KEY`
- Neo4j：
  - `NEO4J_URI`
  - `NEO4J_USER`
  - `NEO4J_PASSWORD`
- Redis（可选）：
  - `REDIS_HOST` / `REDIS_PORT` / `REDIS_PASSWORD`
- 服务端口：
  - `AGENT_SERVICE_PORT`（默认 8103）
  - `GRAPH_SERVICE_PORT`（默认 8101）

你可以通过系统环境变量设置这些值，或直接修改 `settings.py` 中的默认值（不推荐在生产环境中硬编码敏感信息）。

---

## 启动服务

### 方式一：使用一键启动脚本（推荐）

在项目根目录执行：

```bash
chmod +x start.sh        # 第一次使用需要赋予执行权限
./start.sh
```

该脚本会：

1. 自动选择 Python 解释器（默认 `python3.11`，可通过环境变量 `PYTHON_CMD` 覆盖）；  
2. 后台启动两个服务：
   - Agent 服务（`scripts/start_agent.py`，默认端口 8103）
   - 图服务（`scripts/start_graph_service.py`，默认端口 8101）
3. 等待端口就绪；
4. 在 macOS 上自动通过 `open http://localhost:8103/` 打开浏览器；
5. 监控服务进程，脚本退出时尝试清理子进程。

日志输出默认在：

- `storage/logs/agent_service_simple.log`
- `storage/logs/graph_service_simple.log`

### 方式二：手动启动（开发调试）

你也可以在两个终端窗口分别启动：

```bash
cd /path/to/MedGraphRAG

# 启动 Agent 服务（负责前端页面 + 医学问答接口）
python scripts/start_agent.py

# 启动图服务（负责 NL2Cypher + 知识图谱查询）
python scripts/start_graph_service.py
```

---

## 访问方式

### 前端聊天页面

启动 Agent 服务后，在浏览器中访问：

```text
http://localhost:8103/
```

该页面提供：

- 医学问答聊天对话框；
- 示例问题按钮；
- 每次问答的 **多源检索路径可视化**：
  - 向量检索（Milvus）
  - PDF 检索（ParentDocumentRetriever）
  - 知识图谱查询（Neo4j）
- 知识图谱查询生成的 Cypher 语句和置信度展示。

前端通过：

- `API_URL = window.location.origin + '/'`
- 对当前域名的根路径发起 `POST /` 请求  

对应后端 `services/agent_service.py` 中的：

- `@app.get("/")`：返回 `web/index.html` 页面  
- `@app.post("/")`：接收 `{"question": "..."}`，执行检索 + LLM 生成回答

### API 直接调用

示例：医学问答接口

```bash
curl -X POST "http://localhost:8103/" \
  -H "Content-Type: application/json" \
  -d '{"question": "感冒了有什么症状？"}'
```

示例：服务信息接口

```bash
curl "http://localhost:8103/api/info"
```

图服务还提供 `/generate`、`/validate`、`/execute` 等接口，详细见 `services/graph_service.py` 与 `docs/services.md`。

---

## 架构概览（简要）

- **`config/` – 配置管理**
  - `settings.py` 提供全局 `settings` 实例，统一管理 Neo4j / Redis / Milvus / 模型路径 / 端口等配置。

- **`core/` – 核心能力**
  - `models/`：Embedding 与 LLM 封装（如 `ZhipuAIEmbeddings`、DeepSeek 客户端）
  - `vector_store/`：Milvus 相关封装
  - `cache/`：Redis 客户端封装
  - `graph/`：Neo4j 客户端、图结构模型、NL2Cypher Prompt、校验等

- **`services/` – 业务服务**
  - `agent_service.py`：整合向量检索 + PDF 检索 + 知识图谱 + LLM，提供单一 `/` 问答接口
  - `graph_service.py`：负责 NL2Cypher 生成、验证和执行，供 Agent 服务通过 HTTP 调用

- **`web/` – 前端页面**
  - `index.html`：单页应用，使用原生 JS 调用后端 API 并展示检索过程与结果

- **`scripts/` – 启动脚本**
  - `start_agent.py` / `start_graph_service.py`：分别启动两个 FastAPI 服务
  - 配合根目录 `start.sh` 形成一键启动方案

更详细的说明请查阅 `docs` 目录下各模块文档。

---

## 开发与调试建议

- 使用虚拟环境管理依赖，避免与系统 Python 冲突；
- 修改配置优先通过环境变量或 `settings.py`，不要在业务代码中硬编码；
- 日志文件位于 `storage/logs/`，遇到问题时优先检查这里；
- 如果需要扩展能力（例如新增数据源、替换 LLM），建议：
  - 在 `core/` 中增加对应封装；
  - 在 `services/` 中调整业务流程；
  - 在 `web/` 中按需增加前端展示。

如在使用过程中有新的模块或流程，可在 `docs` 下新增对应说明文档并在本文件中补充链接。 