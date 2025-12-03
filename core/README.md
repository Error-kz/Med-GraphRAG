## core 模块说明

`core` 模块封装了项目的**底层通用能力**，包括 Embedding、LLM、向量库、缓存、知识图谱等，是上层业务服务的基础。

- **目录结构**
  - `core/`
    - `__init__.py`
    - `models/`：模型相关封装（Embedding / LLM）
    - `vector_store/`：向量数据库（Milvus）封装
    - `cache/`：缓存（Redis）封装
    - `graph/`：知识图谱（Neo4j）相关封装

---

### models 子模块

- **路径**：`core/models/`
- **职责**：统一管理和封装模型，避免在业务代码中直接操作底层模型类。
- **主要文件**
  - `embeddings.py`
    - 封装 Zhipu / 其他 Embedding 模型为统一接口 `ZhipuAIEmbeddings`。
    - 负责把文本转换成稠密向量，并可用于 Milvus 等向量库。
  - `llm.py`
    - 封装大语言模型客户端，例如 DeepSeek、Qwen 等。
    - 提供创建客户端的工厂方法 `create_deepseek_client`，以及生成回答的高层函数 `generate_deepseek_answer`。

**典型用法（示意）**：
- 服务层通过 `create_deepseek_client()` 获取 LLM 客户端。
- 通过 `generate_deepseek_answer(client, prompt)` 统一生成回答。
- 避免在服务里直接拼接底层 HTTP 调用或 SDK 调用。

---

### vector_store 子模块

- **路径**：`core/vector_store/`
- **职责**：封装与 Milvus 的交互逻辑，提供更高层的“向量检索”接口。
- **主要文件**
  - `milvus_client.py`
    - 负责连接 Milvus、本地向量数据库文件、索引参数配置等。
    - 给上层提供：
      - 写入文档（向量化 + 建索引）
      - 相似度检索（`similarity_search` 等）

在 `services/agent_service.py` 中，已经直接通过 `langchain_milvus.Milvus` + Embedding 构建了向量存储和检索器；如需扩展统一封装，可以在 `milvus_client.py` 中抽象常用操作。

---

### cache 子模块

- **路径**：`core/cache/`
- **职责**：统一管理 Redis 连接与常用缓存操作，避免在业务层到处维护 Redis 客户端。
- **主要文件**
  - `redis_client.py`
    - 基于 `config.settings` 中的 Redis 配置，创建 Redis 连接池 / 客户端。
    - 可根据需要封装：简单 KV 缓存、TTL 设置、业务级缓存封装等。

当前项目中 Redis 为可选依赖，主要用于缓存加速，实际使用场景可以按需要扩展。

---

### graph 子模块

- **路径**：`core/graph/`
- **职责**：封装与 Neo4j 知识图谱和 NL2Cypher 相关的所有逻辑。
- **主要文件（部分）**
  - `models.py`
    - 定义图谱中的实体、关系等抽象模型（如疾病、症状、药物、科室等）。
  - `neo4j_client.py`
    - 基于 `config.neo4j_config` 或 `config.settings` 中的配置，创建 Neo4j 驱动。
    - 封装图谱查询、Cypher 执行、结果解析等。
  - `prompts.py`
    - 存放与 NL2Cypher 或图谱问答相关的 Prompt 模板，供 LLM 使用。
  - `schemas.py`
    - 定义请求 / 响应的数据结构（如 Pydantic 模型），用于 FastAPI 等。
  - `validators.py`
    - 提供对 Cypher、查询参数等的校验逻辑，提升安全性和稳定性。

**典型流程**（结合 `services/graph_service.py`）：
1. 接收自然语言问题；
2. 使用 `prompts.py` 中模板 + LLM 生成 Cypher；
3. 使用 `neo4j_client.py` 执行查询；
4. 使用 `models.py` / `schemas.py` 解析结果；
5. 将结构化结果返回给 Agent 服务或前端。


