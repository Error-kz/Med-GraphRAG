"""
文本分割工具
提供各种文本分割策略
"""
from langchain.text_splitter import RecursiveCharacterTextSplitter


def create_child_splitter(chunk_size: int = 200, chunk_overlap: int = 50) -> RecursiveCharacterTextSplitter:
    """
    创建子文档分割器（用于向量检索）
    
    Args:
        chunk_size: 块大小
        chunk_overlap: 重叠大小
        
    Returns:
        RecursiveCharacterTextSplitter实例
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
    )


def create_parent_splitter(chunk_size: int = 1000, chunk_overlap: int = 200) -> RecursiveCharacterTextSplitter:
    """
    创建父文档分割器（用于上下文检索）
    
    Args:
        chunk_size: 块大小
        chunk_overlap: 重叠大小
        
    Returns:
        RecursiveCharacterTextSplitter实例
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

