# 更新日志

本文档记录 MedGraphRAG 项目的所有重要版本更新。

## [1.0.0] - 2025-12-04

### 🎉 首个正式版本发布

MedGraphRAG 是一个基于知识图谱和向量检索的医疗问答系统，结合了结构化知识图谱查询和语义向量搜索的优势。

### ✨ 主要功能

#### 核心功能
- **知识图谱构建与查询**
  - 基于 Neo4j 的医疗知识图谱
  - 支持 NL2Cypher（自然语言转 Cypher 查询）
  - 自动查询验证和执行
  - 支持多种医疗实体关系查询

- **向量检索**
  - 基于 Milvus 的混合检索（Dense + Sparse）
  - RRF（Reciprocal Rank Fusion）融合算法
  - 支持语义相似度和关键词匹配

- **混合检索策略**
  - 以知识图谱为核心，向量检索为补充
  - 智能融合两路查询结果
  - 优先使用知识图谱的准确信息

- **问答服务**
  - FastAPI 后端服务
  - 支持流式和非流式响应
  - RESTful API 接口
  - 实时查询进度反馈

#### 技术特性
- **大语言模型集成**
  - DeepSeek LLM 支持
  - ZhipuAI Embeddings
  - 可配置的模型参数

- **数据管理**
  - 支持 JSONL 格式数据导入
  - 自动实体提取和关系构建
  - 批量数据处理

- **系统架构**
  - 模块化设计
  - 服务分离（Agent Service + Graph Service）
  - 配置化管理
  - 完整的日志系统

### 📦 技术栈

- **后端框架**: FastAPI
- **知识图谱**: Neo4j
- **向量数据库**: Milvus
- **大语言模型**: DeepSeek Chat
- **Embedding 模型**: ZhipuAI
- **缓存**: Redis（可选）
- **Python 版本**: 3.11+

### 📝 数据格式

- 医疗数据：JSONL 格式（`medical.jsonl`）
- 问答数据：JSONL 格式（`data.jsonl`, `dialog.jsonl`, `dev.jsonl`）

### 🔧 配置要求

- Neo4j 数据库连接
- Milvus 向量数据库
- DeepSeek API Key
- ZhipuAI API Key
- Redis（可选，用于缓存）

### 📚 文档

- 完整的技术文档（`docs/technical_workflow.md`）
- API 文档
- 模块说明文档
- 使用示例

### 🐛 已知问题

- 无

### 🔄 后续计划

- 版本 2.0 开发中...

---

## 版本说明

- **主版本号**: 重大功能更新或架构变更
- **次版本号**: 新功能添加
- **修订号**: Bug 修复和小幅改进

