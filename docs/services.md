## services 模块说明

`services` 模块是项目的**服务层 / 业务层**，负责把底层能力（向量检索、PDF 检索、知识图谱、LLM 等）组合成完整的医疗问答与图谱服务。

- **目录结构**
  - `services/`
    - `agent_service.py`：主 Agent 服务（RAG + PDF + 知识图谱）
    - `graph_service.py`：图数据库服务（NL2Cypher + 执行 + 日志）
    - `legacy/`：旧服务实现保留目录

---

### agent_service.py

主 Agent 服务，是整个项目面向用户的一站式“医学问答入口”。

- **技术栈**
  - 框架：FastAPI
  - 向量检索：Milvus + LangChain
  - 文档检索：ParentDocumentRetriever（基于 Milvus）
  - 知识图谱：通过 HTTP 调用 `graph_service` 提供的接口
  - LLM：DeepSeek 等，通过 `core.models.llm` 封装

- **关键能力**
  1. **HTTP 服务与页面**
     - `@app.get("/")`：  
       - 如果存在 `web/index.html`，直接返回前端页面（聊天界面）。  
       - 否则返回服务状态信息和接口说明。
     - `@app.get("/api/info")`：返回服务元信息（名称、端口、可用接口等）。
  2. **医疗问答主接口**
     - `@app.post("/")`：核心接口，接收 JSON：`{"question": "xxx"}`。
     - 内部流程：
       1. 初始化 `search_stages` 与 `search_path`，用于记录各阶段检索情况；
       2. 使用 `milvus_vectorstore` 进行向量检索，获取与问题最相关的文本片段；
       3. 通过 `ParentDocumentRetriever` 对 PDF 文档进行检索，补充上下文；
       4. 调用图谱服务（`/generate`、`/validate`、`/execute`）进行知识图谱查询；
       5. 将文本检索结果、PDF 内容和知识图谱结果整合为统一 `context`；
       6. 构造 `SYSTEM_PROMPT` + `USER_PROMPT`，调用 LLM 生成最终回答；
       7. 返回结构化响应：
          - `response`：最终回答文本
          - `search_path`：执行过的检索阶段顺序
          - `search_stages`：每一阶段的状态、结果示例、置信度、Cypher 等
  3. **可观测性与健壮性**
     - 对每个阶段都有 `try / except`，在出错时记录错误并标记 `status: error`。
     - 对知识图谱调用有超时、连接异常处理，并支持主地址 + 备用地址。
     - 输出控制台日志，方便排查检索/图谱/LLM 相关问题。

---

### graph_service.py

图服务模块，聚焦在“自然语言 → Cypher → Neo4j 查询 → 结果解释”这条链路。

- **主要职责**
  - 提供 NL2Cypher 能力：将自然语言问题转换为 Neo4j Cypher 查询；
  - 验证生成的 Cypher 是否安全、合法；
  - 执行图数据库查询，并对结果进行结构化封装；
  - 记录图谱查询日志，便于后续分析/优化。

- **典型接口**（基于源码推断）
  - `POST /generate`：输入 `natural_language_query`，输出：
    - `cypher_query`：生成的查询语句
    - `confidence`：生成置信度
    - `validated`：是否通过基本验证
  - `POST /validate`：输入 `cypher_query`，返回是否安全、语法是否合理等信息。
  - `POST /execute`：输入 `cypher_query`，在 Neo4j 中执行，并返回：
    - `success`：是否执行成功
    - `records`：查询到的节点、关系、属性信息等

- **与 Agent 服务的配合**
  - `agent_service.py` 不直接执行 Cypher，而是通过 HTTP 调用 `graph_service` 这三个接口；
  - `graph_service` 专注在图谱相关的生成、校验、执行，职责更单一；
  - 查询结果在 `agent_service` 中被加工为易读的中文描述，然后参与最终回答生成。

---

### legacy 子目录

- **路径**：`services/legacy/`
- **作用**：保留历史版本的服务实现（旧 Agent / 爬虫等），便于：
  - 对照新旧架构；
  - 参考旧实现中的业务规则；
  - 避免因重构导致历史逻辑完全丢失。

- **使用建议**
  - 不建议在新代码中继续依赖 `legacy` 里的实现；
  - 如果确实需要某段旧逻辑，建议理解后迁移到新的模块结构中。


