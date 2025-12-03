## storage 模块说明

`storage` 目录用于存放**运行时产生或依赖的持久化资源**，包括本地数据库文件、模型权重、日志以及 PID 文件等。

- **总体职责**
  - 与代码 / 配置分离，专门存放“数据与状态”；
  - 方便在部署时挂载独立存储卷（如 Docker volume）；
  - 便于备份与清理。

---

### databases 子目录

- **路径**：`storage/databases/`
- **作用**：存放本地数据库文件，目前主要是 Milvus 的本地存储。
- **典型文件**
  - `milvus_agent.db`
    - 用于存放“Agent 相关向量检索”的向量数据；
    - 在 `services/agent_service.py` 中，通过：
      - `settings.MILVUS_AGENT_DB` → `storage/databases/milvus_agent.db`
      - 配合 `langchain_milvus.Milvus` 初始化向量存储。
  - `pdf_agent.db`
    - 用于存放 PDF 文档向量索引；
    - 与 `ParentDocumentRetriever` 搭配，用于长文档检索。

> 说明：这些文件会在构建向量索引时自动创建 / 更新；  
> 删除后需要重新跑数据导入脚本才能恢复索引。

---

### models 子目录

- **路径**：`storage/models/`
- **作用**：存放本地模型权重和相关配置文件。
- **典型子目录**
  - `bce-reranker-base_v1/`
    - 重排序模型（Reranker），用于对召回结果进行精排；
    - 包含 `config.json`、`pytorch_model.bin`、`tokenizer.json` 等。
  - `bert_pretrain/`
    - 预训练 BERT 模型，可用于词向量、特征抽取等场景。
  - `gpt2_chinese_base/`
    - 中文 GPT-2 模型权重与分词器配置。
  - `Qwen2.5-1.5B-Instruct/`
    - Qwen 系列指令微调模型本地权重；
    - 包含 `model.safetensors`、`tokenizer.json` 等 HuggingFace 格式文件。

> 说明：当前运行时主要使用的是远程 LLM（如 DeepSeek），本地模型目录可用于后续扩展或离线部署。

---

### logs 子目录

- **路径**：`storage/logs/`
- **作用**：集中存放各类运行日志，便于排障与追踪。
- **典型文件**
  - `agent_service.log` / `agent_service_simple.log`
    - Agent 服务启动与请求处理日志；
  - `graph_service.log` / `graph_service_simple.log`
    - 图服务相关日志；
  - `graph_query.log`
    - 知识图谱查询的详细记录，包含：
      - 生成的 Cypher；
      - 执行结果；
      - 错误信息等。

> 建议：在生产环境中结合日志轮转（logrotate）或集中式日志（ELK / Loki）进行管理。

---

### pids 子目录

- **路径**：`storage/pids/`
- **作用**：存放服务进程的 PID 文件，主要被 `start.sh` 一键启动脚本使用。
- **典型文件**
  - `agent_service.pid`
  - `graph_service.pid`

一键启动脚本通过 PID 文件判断服务是否已在运行、停止服务时需要杀掉哪些进程，从而避免重复启动或僵尸进程。


