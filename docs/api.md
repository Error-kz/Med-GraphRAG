## api 模块说明

`api` 模块是整个系统对外暴露的 **HTTP 接口层**，基于 FastAPI 实现。  
它负责：
- 初始化 FastAPI 应用；
- 挂载中间件（CORS、日志等）；
- 按功能拆分路由（Agent 接口 / 图谱接口等）；
- 将请求转发到 `services` 层进行实际处理。

> 说明：当前仓库中已存在 `api/` 目录与路由文件，但主入口服务主要集中在 `services/agent_service.py` 与 `services/graph_service.py`。未来如果需要统一入口（如 `uvicorn api.main:app`），可以在 `api/` 下增加一个总入口模块。

---

### 目录结构

- `api/`
  - `__init__.py`
  - `middleware.py`：全局中间件（如 CORS、请求日志等）
  - `routes/`
    - `__init__.py`
    - `agent.py`：Agent / 医疗问答相关接口
    - `graph.py`：知识图谱 / NL2Cypher 相关接口

---

### middleware.py

统一配置 FastAPI 的中间件，例如：

- **CORS（跨域设置）**
  - 允许前端页面（本地或不同域名）访问 API；
  - 常见配置包括：
    - `allow_origins`：允许的来源（如 `*` 或指定域名）；
    - `allow_methods`：允许的 HTTP 方法（如 `GET, POST, OPTIONS` 等）；
    - `allow_headers`：允许的请求头。
- **请求 / 响应日志**
  - 可在此处添加统一的访问日志记录；
  - 便于线上排障与性能分析。

> 实际中，在 `services/agent_service.py` 中已经直接添加了 CORS 中间件；未来可考虑把公共逻辑迁移到 `api/middleware.py` 中，统一管理。

---

### routes/agent.py

封装“医学问答 / Agent 能力”的 HTTP 路由，典型职责：

- 定义 `/agent/...` 或类似前缀的接口；
- 接收前端请求参数（问题文本、会话 ID、用户信息等）；
- 调用 `services.agent_service` 中的核心逻辑；
- 返回统一结构的 JSON 响应。

对于当前项目：
- 如果你希望通过 `api` 层统一暴露接口，可以在路由中简单包装 `services.agent_service.app` 的逻辑；
- 也可以直接在 `routes/agent.py` 中编写更细粒度的接口（如仅向量检索调试接口）。

---

### routes/graph.py

封装“知识图谱 / 图数据库”相关接口，典型职责：

- 提供 `NL2Cypher` 调试入口（例如 `/graph/generate`）；
- 封装 Neo4j 查询接口，转发到 `services.graph_service`；
- 提供图谱结构、节点统计、关系统计等辅助接口（如后续扩展）。

与 `services.graph_service` 的关系：
- `graph_service.py` 可以看作“图谱领域服务”的实现；
- `routes/graph.py` 可以按需将其包装为 RESTful API，供前端或其他服务调用。


