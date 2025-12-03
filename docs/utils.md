## utils 模块说明

`utils` 模块存放的是**通用工具函数**，与具体业务弱相关，但在多处模块中都会复用。

- **目录结构**
  - `utils/`
    - `__init__.py`
    - `document_loader.py`
    - `text_splitter.py`
    - `create_graph.py`

---

### document_loader.py

- **职责**：提供统一的“文档加载”工具方法，例如：
  - 从本地目录批量读取 PDF / TXT / Markdown 等文件；
  - 转换为统一的数据结构（如 LangChain 的 `Document` 对象）；
  - 处理编码问题、忽略无效文件等。

- **典型使用场景**
  - 构建 PDF 文档向量索引之前，先通过 `document_loader` 把原始文档读取成文本 / 片段；
  - 后续交给 `ParentDocumentRetriever` 与 Milvus 进行向量化和存储。

> 实际实现可在需要时扩展：支持更多格式、增加元数据（文件名、页码等）等。

---

### text_splitter.py

- **职责**：封装文本切分逻辑，避免在业务代码中到处写重复的切分参数。
- **典型内容**
  - 创建"父文档切分器"和"子文档切分器"，如：
    - `create_parent_splitter()`：按较大粒度切分，适合存入 Milvus 作为检索单元；
    - `create_child_splitter()`：按较小粒度切分，用于 Parent-Child 检索中的子块。
  - 内部可能基于 `RecursiveCharacterTextSplitter` 等 LangChain 工具。

- **在项目中的使用**
  - `services/agent_service.py` 中：
    - 通过 `create_child_splitter()`、`create_parent_splitter()` 生成切分器；
    - 配合 `ParentDocumentRetriever` 对 PDF 长文档进行层级切分与检索。

> 建议：如果后续需要调整段落长度、重叠大小等参数，优先在此文件中修改，统一影响全局。

---

### create_graph.py

- **职责**：从医疗数据 JSON 文件构建 Neo4j 知识图谱，包括节点创建和关系建立。
- **主要功能**
  - 解析医疗数据 JSON 文件（`data/raw/medical.json`）
  - 提取实体节点（疾病、药品、食物、症状、检查、科室、生产商等）
  - 提取实体关系（疾病-症状、疾病-药品、疾病-食物等）
  - 批量创建 Neo4j 节点和关系
  - 使用参数化查询确保安全性

#### 核心类：`MedicalGraph`

**初始化**

```python
from utils.create_graph import MedicalGraph

# 使用默认数据路径（config.settings.DATA_RAW_PATH/medical.json）
mg = MedicalGraph()

# 或指定自定义数据路径
mg = MedicalGraph(data_path="/path/to/medical.json")
```

**主要方法**

1. **`read_nodes()`**
   - 读取并解析医疗数据 JSON 文件
   - 提取所有节点类型和关系
   - 返回节点集合、疾病信息列表和关系列表的元组
   - 自动去重处理

2. **`create_graphnodes_and_graphrels()`**
   - 主入口方法，执行完整的图谱构建流程
   - 包括：
     - 读取数据
     - 创建所有类型的节点
     - 创建所有类型的关系
   - 自动连接和关闭 Neo4j 连接
   - 输出详细的统计信息

3. **`create_relationship(start_node, end_node, edges, rel_type, rel_name)`**
   - 创建实体之间的关联边
   - 自动去重处理
   - 使用参数化查询避免注入风险
   - 支持批量创建关系

#### 数据格式要求

输入文件应为 JSONL 格式（每行一个 JSON 对象），每个对象代表一种疾病，包含以下字段：

```json
{
  "name": "疾病名称",
  "desc": "疾病描述",
  "symptom": ["症状1", "症状2", ...],
  "prevent": "预防措施",
  "cause": "病因",
  "easy_get": "易感人群",
  "cure_way": "治疗方式",
  "cure_department": ["大科室", "小科室"],  // 或 ["科室"]
  "cure_lasttime": "治疗周期",
  "cured_prob": "治愈概率",
  "get_prob": "患病概率",
  "common_drug": ["常用药品1", "常用药品2", ...],
  "recommand_drug": ["推荐药品1", "推荐药品2", ...],
  "not_eat": ["忌吃食物1", "忌吃食物2", ...],
  "do_eat": ["益吃食物1", "益吃食物2", ...],
  "recommand_eat": ["推荐食物1", "推荐食物2", ...],
  "check": ["检查项目1", "检查项目2", ...],
  "acompany": ["并发症1", "并发症2", ...],
  "drug_detail": ["药品名(生产商)", ...]
}
```

#### 创建的节点类型

- **Disease（疾病）**：包含完整的疾病信息属性
- **Drug（药品）**：药品名称
- **Food（食物）**：食物名称
- **Symptom（症状）**：症状名称
- **Check（检查）**：检查项目名称
- **Department（科室）**：科室名称
- **Producer（生产商）**：药品生产商名称

#### 创建的关系类型

| 关系类型 | 起始节点 | 结束节点 | 说明 |
|---------|---------|---------|------|
| `has_symptom` | Disease | Symptom | 疾病-症状关系 |
| `recommand_drug` | Disease | Drug | 疾病-推荐药品关系 |
| `command_drug` | Disease | Drug | 疾病-常用药品关系 |
| `recommand_eat` | Disease | Food | 疾病-推荐食物关系 |
| `not_eat` | Disease | Food | 疾病-忌吃食物关系 |
| `do_eat` | Disease | Food | 疾病-益吃食物关系 |
| `need_check` | Disease | Check | 疾病-检查项目关系 |
| `acompany_with` | Disease | Disease | 疾病-并发症关系 |
| `belongs_to` | Disease | Department | 疾病-所属科室关系 |
| `sub_department` | Department | Department | 科室-子科室关系 |
| `drugs_of` | Drug | Producer | 药品-生产商关系 |

#### 使用示例

**基本使用**

```python
from utils.create_graph import MedicalGraph

# 创建图谱构建器
mg = MedicalGraph()

# 执行图谱构建（包括节点和关系）
mg.create_graphnodes_and_graphrels()
```

**作为脚本运行**

```bash
cd /path/to/MedGraphRAG
python utils/create_graph.py
```

#### 技术特性

1. **安全性**
   - 使用参数化 Cypher 查询，避免注入攻击
   - 自动验证数据文件存在性
   - 完善的异常处理机制

2. **性能优化**
   - 批量处理节点和关系
   - 自动去重处理
   - 进度提示（每 500 个节点或 1000 条关系）

3. **架构集成**
   - 使用 `core.graph.neo4j_client.Neo4jClient` 进行数据库连接
   - 使用 `config.settings` 管理数据路径
   - 符合项目整体架构规范

4. **错误处理**
   - 详细的错误日志输出
   - 跳过无效数据继续处理
   - 统计成功和失败数量

#### 注意事项

- **前置条件**：确保 Neo4j 数据库已启动并配置正确（见 `config/neo4j_config.py`）
- **数据文件**：默认数据文件路径为 `data/raw/medical.json`，可通过 `config.settings.DATA_RAW_PATH` 配置
- **数据格式**：输入文件必须是 JSONL 格式（每行一个 JSON 对象）
- **幂等性**：使用 `MERGE` 语句，重复运行不会创建重复节点
- **性能**：大数据量时建议在非高峰期运行，避免影响其他服务

#### 输出示例

运行时会输出详细的统计信息：

```
====================================================================================================
节点统计:
  Drugs: 1234
  Foods: 567
  Checks: 89
  Departments: 45
  Producers: 234
  Symptoms: 5678
  Diseases: 890
====================================================================================================
关系统计:
  rels_check: 1234
  rels_recommandeat: 2345
  ...
====================================================================================================
开始创建疾病节点...
已创建 500 个疾病节点
疾病节点创建完成，成功: 890, 失败: 0
...
知识图谱创建完成！
```


