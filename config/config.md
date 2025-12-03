## config 模块说明

`config` 模块负责**集中管理所有配置**，避免在代码中到处硬编码常量，便于在不同环境（本地 / 测试 / 生产）之间切换。

- **总体职责**
  - 统一读取环境变量与默认配置
  - 管理第三方服务连接信息（Neo4j、Redis 等）
  - 提供全局可用的 `settings` 实例

- **主要文件**
  - `settings.py`  
    - 定义 `Settings` 类，封装所有配置项，例如：
      - LLM / Embedding 相关 API Key：`DEEPSEEK_API_KEY`、`ZHIPU_API_KEY`
      - Neo4j 连接：`NEO4J_URI`、`NEO4J_USER`、`NEO4J_PASSWORD`
      - Redis 连接：`REDIS_HOST`、`REDIS_PORT` 等
      - Milvus 本地数据库文件路径：`MILVUS_AGENT_DB`、`PDF_AGENT_DB`
      - 服务端口：`AGENT_SERVICE_PORT`、`GRAPH_SERVICE_PORT`
      - 模型、数据、日志等路径
    - 通过 `os.getenv` 允许环境变量覆盖默认值。
    - 文件末尾创建全局实例：`settings = Settings()`，其余模块直接 `from config.settings import settings` 使用。
  - `neo4j_config.py`  
    - 在旧代码基础上，提供 Neo4j 连接配置的兼容写法（如 `NEO4J_CONFIG` 字典），便于部分历史模块沿用。

- **使用建议**
  - 新增配置项时，统一在 `Settings` 中增加字段，并给出合理默认值。
  - 外部代码**不要**直接读取环境变量，而是优先使用 `settings`，保持配置集中管理。
  - 如需区分环境（dev / prod），建议通过环境变量控制，而不是写多套配置文件。


