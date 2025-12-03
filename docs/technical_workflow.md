# MedGraphRAG 技术流程文档

## 概述

本文档详细描述了 MedGraphRAG 系统从原始数据读取、知识图谱构建、向量数据库构建到最终检索结果生成的完整技术流程。

---

## 目录

1. [系统架构](#系统架构)
2. [数据准备阶段](#数据准备阶段)
3. [知识图谱构建阶段](#知识图谱构建阶段)
4. [向量数据库构建阶段](#向量数据库构建阶段)
5. [检索服务阶段](#检索服务阶段)
6. [完整流程示例](#完整流程示例)

---

## 系统架构

MedGraphRAG 采用混合检索架构，结合了向量检索和知识图谱查询两种方式：

```
┌─────────────────┐
│   用户查询      │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│      Agent Service              │
│  (主服务，协调检索流程)          │
└────────┬────────────────────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌──────────────────┐
│ Milvus  │ │  Graph Service    │
│ 向量库  │ │  (NL2Cypher)      │
└────┬────┘ └────────┬──────────┘
     │                │
     │                ▼
     │         ┌──────────────┐
     │         │   Neo4j      │
     │         │  图数据库    │
     │         └──────────────┘
     │
     ▼
┌─────────────────┐
│  结果融合       │
│  + LLM生成      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   最终答案      │
└─────────────────┘
```

---

## 数据准备阶段

### 1.1 数据源

系统使用以下数据源：

#### 原始数据文件
- **`data/raw/medical.json`**: 医疗知识图谱数据（JSONL格式）
  - 每行一个JSON对象，包含疾病及其相关实体信息
  - 字段包括：`name`, `desc`, `symptom`, `prevent`, `cause`, `common_drug`, `recommand_drug`, `not_eat`, `do_eat`, `recommand_eat`, `check`, `cure_department` 等

- **`data/raw/data.jsonl`**: 问答对话数据
  - 格式：`{"query": "问题", "response": "回答"}`

- **`data/raw/dialog.jsonl`**: 对话数据
  - 格式：`{"query": "问题", "response": "回答"}`

- **`data/raw/dev.jsonl`**: 开发集数据
  - 格式：`{"prompt": "提示", "chosen": "选择"}`

#### 数据字典文件
- `data/dict/disease.txt`: 疾病名称字典
- `data/dict/drug.txt`: 药品名称字典
- `data/dict/food.txt`: 食物名称字典
- `data/dict/symptom.txt`: 症状名称字典
- `data/dict/check.txt`: 检查项目字典
- `data/dict/department.txt`: 科室名称字典
- `data/dict/producer.txt`: 生产商名称字典
- `data/dict/deny.txt`: 否定词字典

### 1.2 数据格式示例

**medical.json 示例：**
```json
{
  "name": "感冒",
  "desc": "感冒是一种常见的上呼吸道感染...",
  "symptom": ["发热", "咳嗽", "流鼻涕"],
  "common_drug": ["阿司匹林", "布洛芬"],
  "recommand_drug": ["感冒灵", "板蓝根"],
  "not_eat": ["辛辣食物", "油腻食物"],
  "do_eat": ["清淡食物", "多喝水"],
  "recommand_eat": ["鸡汤", "姜茶"],
  "check": ["血常规", "胸部X光"],
  "cure_department": ["内科", "呼吸科"]
}
```

---

## 知识图谱构建阶段

### 2.1 构建流程

知识图谱构建由 `utils/create_graph.py` 中的 `MedicalGraph` 类完成。

#### 步骤1：读取和解析数据

**文件位置**: `utils/create_graph.py`

```python
def read_nodes(self):
    """
    读取医疗数据文件并解析节点和关系
    
    处理流程：
    1. 逐行读取 medical.json 文件
    2. 解析每行的 JSON 数据
    3. 提取节点类型：
       - Disease（疾病）
       - Drug（药品）
       - Food（食物）
       - Symptom（症状）
       - Check（检查）
       - Department（科室）
       - Producer（生产商）
    4. 提取关系类型：
       - has_symptom: 疾病-症状
       - recommand_drug: 疾病-推荐药品
       - command_drug: 疾病-常用药品
       - not_eat: 疾病-忌吃食物
       - do_eat: 疾病-益吃食物
       - recommand_eat: 疾病-推荐食物
       - need_check: 疾病-检查项目
       - belongs_to: 疾病-科室
       - acompany_with: 疾病-并发症
       - drugs_of: 药品-生产商
       - sub_department: 科室-子科室
    """
```

**关键代码逻辑：**
- 使用 `json.loads()` 解析每行数据
- 自动去重节点（使用 `set()`）
- 构建关系列表（`[起始节点, 结束节点]`）

#### 步骤2：创建节点

**节点类型：**

1. **疾病节点（Disease）**
   - 属性：`name`, `desc`, `prevent`, `cause`, `easy_get`, `cure_way`, `cure_department`, `cure_lasttime`, `cured_prob`, `get_prob`
   - 使用 `MERGE` 语句避免重复创建

2. **其他节点类型**
   - Drug（药品）
   - Food（食物）
   - Symptom（症状）
   - Check（检查）
   - Department（科室）
   - Producer（生产商）

**Cypher 查询示例：**
```cypher
// 创建疾病节点
MERGE (a:Disease {name: $name})
SET a.desc = $desc,
    a.prevent = $prevent,
    a.cause = $cause,
    ...

// 创建其他节点
MERGE (a:Drug {name: $name})
```

#### 步骤3：创建关系

**关系类型映射：**

| 关系类型 | 起始节点 | 结束节点 | 说明 |
|---------|---------|---------|------|
| `has_symptom` | Disease | Symptom | 疾病有症状 |
| `recommand_drug` | Disease | Drug | 疾病推荐药品 |
| `command_drug` | Disease | Drug | 疾病常用药品 |
| `not_eat` | Disease | Food | 疾病忌吃食物 |
| `do_eat` | Disease | Food | 疾病益吃食物 |
| `recommand_eat` | Disease | Food | 疾病推荐食物 |
| `need_check` | Disease | Check | 疾病需要检查 |
| `belongs_to` | Disease | Department | 疾病所属科室 |
| `acompany_with` | Disease | Disease | 疾病并发症 |
| `drugs_of` | Drug | Producer | 药品生产商 |
| `sub_department` | Department | Department | 科室层级关系 |

**Cypher 查询示例：**
```cypher
MATCH (p:Disease {name: $p_name}), (q:Symptom {name: $q_name})
MERGE (p)-[rel:has_symptom {name: $rel_name}]->(q)
```

#### 步骤4：执行构建

**执行命令：**
```bash
python utils/create_graph.py
```

**输出统计信息：**
```
节点统计:
  Drugs: 3828
  Foods: 4870
  Checks: 3353
  Departments: 54
  Producers: 17201
  Symptoms: 5998
  Diseases: 8807

关系统计:
  rels_check: ...
  rels_recommandeat: ...
  ...
```

---

## 向量数据库构建阶段

### 3.1 构建流程

向量数据库构建由 `utils/create_vector.py` 中的 `MilvusVectorBuilder` 类完成。

#### 步骤1：加载文档

**文件位置**: `utils/document_loader.py`

```python
def prepare_document(file_paths: list = None) -> list:
    """
    从JSONL文件加载文档
    
    处理流程：
    1. 读取 data.jsonl, dialog.jsonl, dev.jsonl
    2. 解析每行JSON数据
    3. 提取文本内容：
       - dev.jsonl: prompt + chosen
       - 其他: query + response
    4. 创建 LangChain Document 对象
    """
```

**文档格式：**
```python
Document(
    page_content="问题\n回答",
    metadata={'doc_id': 'uuid', 'source': 'data.jsonl'}
)
```

#### 步骤2：初始化向量存储

**文件位置**: `utils/create_vector.py`

**技术栈：**
- **Embedding模型**: ZhipuAI Embeddings（智谱AI）
- **向量数据库**: Milvus（本地文件数据库）
- **检索方式**: 混合检索（Dense + Sparse）

**索引配置：**
```python
# Dense向量索引（语义相似度）
dense_index = {
    'metric_type': 'IP',  # 内积
    'index_type': 'IVF_FLAT',
}

# Sparse向量索引（关键词匹配，BM25）
sparse_index = {
    'metric_type': 'BM25',
    'index_type': 'SPARSE_INVERTED_INDEX'
}
```

#### 步骤3：生成向量并存储

**处理流程：**

1. **初始化向量存储**
   ```python
   vectorstore = Milvus.from_documents(
       documents=init_docs[:10],  # 前10个文档初始化
       embedding=embedding_model,
       builtin_function=BM25BuiltInFunction(),
       index_params=[dense_index, sparse_index],
       vector_field=['dense', 'sparse'],
       connection_args={'uri': MILVUS_AGENT_DB}
   )
   ```

2. **批量添加文档**
   - 每5个文档为一批
   - 使用 `add_documents()` 批量插入
   - 避免请求过快（添加延迟）

#### 步骤4：执行构建

**执行命令：**
```bash
python utils/create_vector.py
```

**输出信息：**
```
开始构建 Milvus 向量数据库
[步骤1] 加载JSON文档...
✅ 成功加载 10000 条文档
[步骤2] 创建向量存储...
✅ 已创建 Milvus 索引完成！
```

---

## 检索服务阶段

### 4.1 服务架构

系统包含两个主要服务：

1. **Agent Service** (`services/agent_service.py`)
   - 主服务，处理用户查询
   - 协调向量检索和知识图谱查询
   - 生成最终答案

2. **Graph Service** (`services/graph_service.py`)
   - 知识图谱查询服务
   - 提供 NL2Cypher（自然语言转Cypher）功能
   - 执行Cypher查询并返回结果

### 4.2 Agent Service 流程

#### 步骤1：接收用户查询

**接口**: `POST /`

**请求格式：**
```json
{
  "question": "感冒了有什么症状？"
}
```

#### 步骤2：向量数据库检索

**代码位置**: `services/agent_service.py:170-195`

**检索流程：**

```python
# 使用混合检索（RRF - Reciprocal Rank Fusion）
recall_rerank_milvus = milvus_vectorstore.similarity_search(
    query,
    k=10,  # 返回前10个结果
    ranker_type='rrf',  # RRF融合算法
    ranker_params={'k': 100}  # 融合前100个候选
)
```

**RRF算法说明：**
- 结合Dense向量（语义相似度）和Sparse向量（关键词匹配）
- 使用倒数排名融合，提高检索准确性

**结果处理：**
```python
if recall_rerank_milvus:
    context = format_docs(recall_rerank_milvus)  # 格式化文档
    search_stages['milvus_vector']['status'] = 'success'
    search_stages['milvus_vector']['count'] = len(recall_rerank_milvus)
```

#### 步骤3：知识图谱查询

**代码位置**: `services/agent_service.py:197-360`

**查询流程：**

1. **调用Graph Service生成Cypher查询**
   ```python
   graph_response = requests.post(
       f"{GRAPH_API_URL}/generate",
       json={"natural_language_query": query}
   )
   ```

2. **获取Cypher查询**
   ```python
   cypher_query = graph_response.json()['cypher_query']
   # 示例: MATCH (p:Disease)-[r:has_symptom]-(s:Symptom) 
   #       WHERE p.name='感冒' RETURN s.name
   ```

3. **执行Cypher查询**
   ```python
   execute_response = requests.post(
       f"{GRAPH_API_URL}/execute",
       json={"cypher_query": cypher_query}
   )
   ```

4. **解析查询结果**
   ```python
   records = execute_response.json()['records']
   # 格式: [{'symptom': {'type': 'Node', 'labels': ['Symptom'], 
   #                     'properties': {'name': '发热'}}}, ...]
   ```

5. **格式化图谱结果**
   ```python
   graph_context = format_graph_results(records)
   # 输出: "【知识图谱查询结果】\n感冒的症状包括：发热、咳嗽、流鼻涕"
   ```

#### 步骤4：结果融合和LLM生成

**代码位置**: `services/agent_service.py:365-398`

**提示词构建：**

```python
SYSTEM_PROMPT = """
你是一个非常得力的医学助手, 你可以通过从数据库中检索出的信息找到问题的答案.

重要要求：
1. 优先使用知识图谱查询结果
2. 回答必须使用纯文本格式
3. 保持回答简洁、清晰、专业
"""

USER_PROMPT = f"""
利用介于<context>和</context>之间的从数据库中检索出的信息来回答问题.

<context>
{context}  # 向量检索结果
{graph_context}  # 知识图谱查询结果
</context>

<question>
{query}
</question>
"""
```

**生成答案：**
```python
response = generate_deepseek_answer(client_llm, SYSTEM_PROMPT + USER_PROMPT)
```

### 4.3 Graph Service 流程

#### 步骤1：NL2Cypher（自然语言转Cypher）

**文件位置**: `services/graph_service.py:161-182`

**流程：**

1. **构建系统提示词**
   ```python
   system_prompt = create_system_prompt(EXAMPLE_SCHEMA)
   # 包含图数据库模式、查询规则、示例等
   ```

2. **调用DeepSeek API生成Cypher**
   ```python
   response = client.chat.completions.create(
       model="deepseek-chat",
       messages=[
           {"role": "system", "content": system_prompt},
           {"role": "user", "content": natural_language}
       ],
       temperature=0.1,
       max_tokens=2048
   )
   ```

3. **清理Cypher查询**
   ```python
   cypher_query = clean_cypher_query(raw_query)
   # 移除markdown代码块、注释、修复语法错误等
   ```

#### 步骤2：查询验证

**文件位置**: `services/graph_service.py:292-327`

**验证器类型：**

1. **CypherValidator**（基于Neo4j）
   - 连接Neo4j数据库
   - 执行语法验证
   - 检查节点和关系是否存在

2. **RuleBasedValidator**（基于规则）
   - 检查Cypher语法
   - 验证节点标签和关系类型
   - 检查查询模式

#### 步骤3：执行查询

**文件位置**: `services/graph_service.py:203-256`

**执行流程：**

```python
def execute_cypher_query(cypher_query: str, driver):
    with driver.session() as session:
        result = session.run(cypher_query)
        
        records = []
        for record in result:
            record_dict = {}
            for key in record.keys():
                value = record[key]
                # 处理节点对象
                if hasattr(value, 'labels'):
                    record_dict[key] = {
                        'type': 'Node',
                        'labels': list(value.labels),
                        'properties': dict(value)
                    }
                # 处理关系对象
                elif hasattr(value, 'type'):
                    record_dict[key] = {
                        'type': 'Relationship',
                        'relationship_type': value.type,
                        'properties': dict(value)
                    }
                else:
                    record_dict[key] = value
            records.append(record_dict)
        
        return {
            "success": True,
            "records": records,
            "count": len(records),
            "execution_time": execution_time
        }
```

---

## 完整流程示例

### 示例：查询"感冒了有什么症状？"

#### 阶段1：数据准备（已完成）

- ✅ `medical.json` 已包含感冒相关数据
- ✅ 知识图谱已构建完成
- ✅ 向量数据库已构建完成

#### 阶段2：用户查询

```
用户输入: "感冒了有什么症状？"
```

#### 阶段3：向量检索

**检索结果：**
```
检索到10条相关文档：
1. "感冒是一种常见的上呼吸道感染，主要症状包括发热、咳嗽、流鼻涕..."
2. "感冒的症状通常包括鼻塞、打喷嚏、喉咙痛等..."
...
```

#### 阶段4：知识图谱查询

**步骤4.1：生成Cypher查询**

输入：`"感冒了有什么症状？"`

生成的Cypher：
```cypher
MATCH (p:Disease)-[r:has_symptom]-(s:Symptom) 
WHERE p.name='感冒' 
RETURN s.name
```

**步骤4.2：执行查询**

Neo4j执行结果：
```json
{
  "success": true,
  "records": [
    {"symptom": {"type": "Node", "labels": ["Symptom"], 
                 "properties": {"name": "发热"}}},
    {"symptom": {"type": "Node", "labels": ["Symptom"], 
                 "properties": {"name": "咳嗽"}}},
    {"symptom": {"type": "Node", "labels": ["Symptom"], 
                 "properties": {"name": "流鼻涕"}}}
  ],
  "count": 3
}
```

**步骤4.3：格式化结果**

```
【知识图谱查询结果】
感冒的症状包括：发热、咳嗽、流鼻涕
```

#### 阶段5：结果融合和生成

**上下文构建：**
```
<context>
[向量检索结果]
感冒是一种常见的上呼吸道感染，主要症状包括发热、咳嗽、流鼻涕...

【知识图谱查询结果】
感冒的症状包括：发热、咳嗽、流鼻涕
</context>

<question>
感冒了有什么症状？
</question>
```

**LLM生成答案：**
```
感冒的主要症状包括：

1. 发热：体温升高，通常为低热或中度发热
2. 咳嗽：干咳或有痰的咳嗽
3. 流鼻涕：鼻部分泌物增多，初期为清鼻涕，后期可能变为黏稠
4. 鼻塞：鼻腔阻塞，呼吸不畅
5. 打喷嚏：频繁打喷嚏
6. 喉咙痛：咽部不适或疼痛
7. 全身乏力：感觉疲倦、无力

这些症状通常在感染后1-3天出现，持续3-7天。如果症状严重或持续时间较长，建议及时就医。
```

#### 阶段6：返回结果

**响应格式：**
```json
{
  "response": "感冒的主要症状包括：...",
  "search_stages": {
    "milvus_vector": {
      "status": "success",
      "count": 10,
      "results": [...]
    },
    "knowledge_graph": {
      "status": "success",
      "count": 3,
      "cypher_query": "MATCH (p:Disease)-[r:has_symptom]-(s:Symptom) WHERE p.name='感冒' RETURN s.name",
      "confidence": 0.9
    }
  },
  "search_path": ["milvus_vector", "knowledge_graph"]
}
```

---

## 关键技术点

### 1. 混合检索策略

- **向量检索（Milvus）**：语义相似度检索，适合模糊查询
- **知识图谱（Neo4j）**：结构化查询，适合精确查询
- **RRF融合**：结合两种检索方式的优势

### 2. NL2Cypher技术

- 使用大语言模型（DeepSeek）将自然语言转换为Cypher查询
- 基于图数据库模式生成准确的查询语句
- 包含查询验证机制，确保查询安全性

### 3. 结果优先级

- **知识图谱结果优先**：结构化数据更准确
- **向量检索补充**：提供更丰富的上下文信息
- **LLM融合**：智能整合多种来源的信息

### 4. 性能优化

- **批量处理**：节点和关系批量创建
- **索引优化**：Neo4j和Milvus都使用合适的索引
- **缓存机制**：Redis缓存常用查询结果

---

## 总结

MedGraphRAG 系统通过以下步骤实现完整的检索流程：

1. **数据准备**：从原始JSON文件提取结构化数据
2. **知识图谱构建**：在Neo4j中构建医疗知识图谱
3. **向量数据库构建**：在Milvus中构建向量索引
4. **混合检索**：结合向量检索和知识图谱查询
5. **智能生成**：使用LLM融合多源信息生成答案

这种混合架构充分利用了结构化数据（知识图谱）和非结构化数据（向量检索）的优势，为用户提供准确、全面的医疗问答服务。

