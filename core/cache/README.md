# cache 模块说明

`cache` 模块提供 Redis 缓存功能的统一封装，用于管理项目中的缓存操作。

## 目录结构

```
cache/
├── __init__.py
└── redis_client.py
```

## 主要功能

### Redis 客户端管理

- **统一连接管理**：通过连接池管理 Redis 连接，避免在业务代码中重复创建客户端
- **配置集成**：自动从 `config.settings` 读取 Redis 配置信息
- **连接测试**：初始化时自动测试连接，确保可用性

### 缓存操作

- **问答缓存**：提供问答对的缓存存储和检索功能
- **过期时间管理**：支持设置缓存过期时间（TTL）

## 主要文件

### redis_client.py

提供 Redis 客户端的创建和常用缓存操作：

#### `get_redis_client() -> redis.Redis`

创建并返回 Redis 客户端实例。

**功能**：
- 基于配置创建连接池
- 自动测试连接
- 返回可复用的 Redis 客户端

**配置项**（来自 `config.settings`）：
- `REDIS_HOST`：Redis 服务器地址
- `REDIS_PORT`：Redis 端口
- `REDIS_DB`：数据库编号
- `REDIS_PASSWORD`：密码（可选）
- `REDIS_MAX_CONNECTIONS`：最大连接数

#### `cache_set(r: redis.Redis, question: str, answer: str, expire: int = 3600)`

将问答对保存到 Redis。

**参数**：
- `r`：Redis 客户端实例
- `question`：问题文本
- `answer`：答案文本
- `expire`：过期时间（秒），默认 3600 秒（1小时）

**存储方式**：使用 Hash 结构，key 为 `'qa'`，field 为问题，value 为答案。

#### `cache_get(r: redis.Redis, question: str) -> bytes`

从 Redis 获取答案。

**参数**：
- `r`：Redis 客户端实例
- `question`：问题文本

**返回**：答案（bytes 类型），如果不存在返回 `None`。

## 使用示例

```python
from core.cache.redis_client import get_redis_client, cache_set, cache_get

# 创建 Redis 客户端
redis_client = get_redis_client()

# 缓存问答对
cache_set(redis_client, "什么是高血压？", "高血压是一种常见的心血管疾病...", expire=7200)

# 获取缓存的答案
cached_answer = cache_get(redis_client, "什么是高血压？")
if cached_answer:
    print(cached_answer.decode('utf-8'))
```

## 注意事项

1. **可选依赖**：Redis 为可选依赖，主要用于缓存加速，提升响应速度
2. **连接管理**：建议在应用启动时创建客户端，并在整个应用生命周期中复用
3. **错误处理**：如果 Redis 连接失败，函数会打印错误信息，但不会抛出异常，确保应用可以继续运行
4. **数据格式**：`cache_get` 返回的是 bytes 类型，需要根据需要进行解码

## 扩展建议

可以根据业务需求扩展以下功能：
- 支持更多类型的缓存操作（如列表、集合等）
- 实现缓存预热功能
- 添加缓存统计和监控
- 支持分布式缓存场景

