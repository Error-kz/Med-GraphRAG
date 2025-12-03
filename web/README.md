## web 模块说明（前端）

`web` 目录存放的是**前端静态页面**，目前主要是一个单页聊天界面 `index.html`。

- **路径**：`web/index.html`
- **主要功能**
  - 提供“AI 医学问答助手”的对话界面；
  - 展示用户和机器人对话气泡；
  - 展示多源检索路径（向量检索 / PDF 检索 / 知识图谱查询）的可视化信息；
  - 展示最终回答以及知识图谱查询置信度等。

- **与后端的交互方式**
  - 在页面底部的 `<script>` 中定义：
    - `const API_URL = window.location.origin + '/';`
  - 当用户点击“发送”或按回车时：
    - 使用 `fetch(API_URL, { method: 'POST', body: JSON.stringify({ question }) })`；
    - 即向当前域名的根路径 `POST /` 发送问题；
    - 对应后端 `services/agent_service.py` 中的 `@app.post("/")` 接口。
  - 页面展示：
    - `search_stages`：每个检索阶段的状态（成功 / 失败 / 无结果）与部分结果摘要；
    - `search_path`：实际使用到的检索链路；
    - `response`：最终回答内容。

> 启动方式：通过 `start.sh` 启动 Agent 服务后，浏览器访问 `http://localhost:8103/` 即可加载此页面。

---

## scripts 模块说明（启动脚本）

`scripts` 目录存放的是**服务启动与维护脚本**，主要用于简化开发和部署。

- **目录结构**
  - `scripts/`
    - `__init__.py`
    - `start_agent.py`
    - `start_graph_service.py`

---

### start_agent.py

- **作用**：启动主 Agent 服务。
- **关键点**
  - 把项目根目录加入 `sys.path`，确保包导入正常；
  - 从 `services.agent_service` 导入 `app`；
  - 从 `config.settings` 读取 `AGENT_SERVICE_PORT`；
  - 使用 `uvicorn.run(app, host="0.0.0.0", port=settings.AGENT_SERVICE_PORT, workers=1)` 启动服务。

> 一般不单独调用，更多通过根目录下的 `start.sh` 间接启动。

---

### start_graph_service.py

- **作用**：启动图服务（NL2Cypher + Neo4j 查询）。
- **关键点**
  - 同样通过 `uvicorn.run` 启动 FastAPI 应用；
  - 端口从 `settings.GRAPH_SERVICE_PORT` 读取（默认 `8101`）；
  - 对外提供 `/generate`、`/validate`、`/execute` 等接口，供 Agent 服务调用。

---

### 根目录 start.sh 与 scripts 的关系

- 根目录的 `start.sh` 是“一键启动脚本”，内部会：
  - 选择合适的 Python 命令（如 `python3.11`）；
  - 后台启动 `scripts/start_agent.py` 与 `scripts/start_graph_service.py` 两个服务；
  - 监测端口是否就绪；
  - 在 macOS 上自动打开浏览器访问 Agent 页面；
  - 在退出时尝试清理子进程。

> 推荐在开发和体验时优先使用：  
> `./start.sh`  
> 这样可以同时启动前后端，并直接打开浏览器。


