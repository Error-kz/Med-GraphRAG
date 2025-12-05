"""
Redis缓存客户端
统一管理Redis连接和缓存操作
"""
import json
import redis
from datetime import datetime
from config.settings import settings


def get_redis_client() -> redis.Redis:
    """
    创建Redis客户端连接池
    
    Returns:
        Redis客户端实例
    """
    pool = redis.ConnectionPool(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD,
        max_connections=settings.REDIS_MAX_CONNECTIONS
    )
    r = redis.Redis(connection_pool=pool)
    
    # 测试连接
    try:
        r.ping()
        print("Redis连接成功")
    except redis.exceptions.ConnectionError:
        print("Redis连接失败")
    
    return r


def cache_set(r: redis.Redis, question: str, answer: str, expire: int = 3600):
    """
    将问答对保存到Redis数据库
    
    Args:
        r: Redis客户端实例
        question: 问题
        answer: 答案
        expire: 过期时间（秒），默认3600秒
    """
    r.hset('qa', question, answer)
    r.expire('qa', expire)


def cache_get(r: redis.Redis, question: str) -> bytes:
    """
    通过问题获取答案
    
    Args:
        r: Redis客户端实例
        question: 问题
        
    Returns:
        答案（bytes类型），如果不存在返回None
    """
    return r.hget('qa', question)


def save_conversation_history(r: redis.Redis, session_id: str, question: str, answer: str, expire: int = 86400):
    """
    保存对话历史到Redis
    使用List结构存储，每个元素是JSON格式的对话记录
    
    Args:
        r: Redis客户端实例
        session_id: 会话ID
        question: 用户问题
        answer: 助手回答
        expire: 过期时间（秒），默认86400秒（24小时）
        
    Returns:
        tuple: (new_session_id, should_create_new)
            - new_session_id: 如果达到10条，返回新的session_id，否则返回None
            - should_create_new: 是否需要创建新会话（达到10条时为True）
    """
    # 构建对话记录
    conversation_record = {
        'question': question,
        'answer': answer,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 使用List结构存储，key格式：chat:history:{session_id}
    key = f'chat:history:{session_id}'
    
    # 将对话记录追加到列表末尾
    r.rpush(key, json.dumps(conversation_record, ensure_ascii=False))
    
    # 限制历史记录数量，只保留最近10条
    max_history = 10
    list_length = r.llen(key)
    
    # 检查是否达到10条（保存后检查）
    should_create_new = False
    new_session_id = None
    
    if list_length >= max_history:
        # 达到10条，需要创建新会话
        should_create_new = True
        # 生成新的session_id
        import uuid
        new_session_id = str(uuid.uuid4())
        
        # 将当前会话保存到历史记录中（使用第一个问题作为标题）
        first_record = r.lindex(key, 0)
        if first_record:
            first_data = json.loads(first_record)
            first_question = first_data.get('question', '新对话')
        else:
            first_question = question
        save_session_to_history(r, session_id, first_question)
    
    # 设置过期时间
    r.expire(key, expire)
    
    return new_session_id, should_create_new


def save_session_to_history(r: redis.Redis, session_id: str, first_question: str = None):
    """
    将会话保存到历史记录列表中
    
    Args:
        r: Redis客户端实例
        session_id: 会话ID
        first_question: 会话的第一个问题（用作标题）
    """
    # 获取会话信息
    key = f'chat:history:{session_id}'
    history_list = r.lrange(key, 0, -1)
    
    if not history_list:
        return
    
    # 如果没有提供第一个问题，从历史记录中获取
    if not first_question:
        first_record = json.loads(history_list[0])
        first_question = first_record.get('question', '新对话')
    
    # 获取最后一条记录的时间作为更新时间
    last_record = json.loads(history_list[-1])
    update_time = last_record.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # 构建会话信息
    session_info = {
        'session_id': session_id,
        'title': first_question[:50] if len(first_question) > 50 else first_question,  # 标题最多50字符
        'update_time': update_time,
        'message_count': len(history_list)
    }
    
    # 保存到会话列表，使用Sorted Set按时间排序
    sessions_key = 'chat:sessions:list'
    r.zadd(sessions_key, {json.dumps(session_info, ensure_ascii=False): datetime.now().timestamp()})
    
    # 限制历史会话数量，只保留最近50个
    max_sessions = 50
    session_count = r.zcard(sessions_key)
    if session_count > max_sessions:
        # 删除最旧的会话
        r.zremrangebyrank(sessions_key, 0, session_count - max_sessions - 1)
    
    # 设置过期时间（30天）
    r.expire(sessions_key, 2592000)


def get_conversation_history_list(r: redis.Redis, limit: int = 50):
    """
    获取历史会话列表
    
    Args:
        r: Redis客户端实例
        limit: 返回的最大数量，默认50
        
    Returns:
        list: 会话信息列表，按时间倒序排列
    """
    sessions_key = 'chat:sessions:list'
    
    # 从Sorted Set中获取，按时间戳倒序（最新的在前）
    sessions = r.zrevrange(sessions_key, 0, limit - 1)
    
    result = []
    for session_json in sessions:
        try:
            session_info = json.loads(session_json)
            result.append(session_info)
        except:
            continue
    
    return result


def get_session_conversations(r: redis.Redis, session_id: str):
    """
    获取指定会话的所有对话记录
    
    Args:
        r: Redis客户端实例
        session_id: 会话ID
        
    Returns:
        list: 对话记录列表，每个元素包含 question, answer, timestamp
    """
    key = f'chat:history:{session_id}'
    history_list = r.lrange(key, 0, -1)
    
    result = []
    for record_json in history_list:
        try:
            record = json.loads(record_json)
            result.append(record)
        except:
            continue
    
    return result

