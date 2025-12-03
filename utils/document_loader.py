"""
文档加载工具
用于加载和预处理各种格式的文档
"""
import json
import uuid
import pandas as pd
from pathlib import Path
from langchain_core.documents import Document
from config.settings import settings


def prepare_document(file_paths: list = None) -> list:
    """
    从JSONL文件加载文档
    
    Args:
        file_paths: 文件路径列表，默认使用配置中的数据路径
        
    Returns:
        文档列表
    """
    if file_paths is None:
        file_paths = [
            f'{settings.DATA_RAW_PATH}/data.jsonl',
            f'{settings.DATA_RAW_PATH}/dialog.jsonl',
            f'{settings.DATA_RAW_PATH}/dev.jsonl'
        ]
    
    count = 0
    docs = []
    
    # 遍历所有文件路径
    for file_path in file_paths:
        if not file_path:
            continue
            
        try:
            # 根据文件名判断解析方式
            file_name = Path(file_path).name.lower()
            
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    content = json.loads(line.strip())
                    
                    # dev.jsonl 使用 prompt + chosen
                    if 'dev.jsonl' in file_name:
                        if 'prompt' in content and 'chosen' in content:
                            prompt = content['prompt'] + '\n' + content['chosen']
                        else:
                            print(f'警告: 文件 {file_path} 中缺少 prompt 或 chosen 字段，跳过该行')
                            continue
                    # 其他文件（data.jsonl, dialog.jsonl等）使用 query + response
                    else:
                        if 'query' in content and 'response' in content:
                            prompt = content['query'] + '\n' + content['response']
                        else:
                            print(f'警告: 文件 {file_path} 中缺少 query 或 response 字段，跳过该行')
                            continue
                    
                    temp_doc = Document(
                        page_content=prompt,
                        metadata={'doc_id': str(uuid.uuid4()), 'source': file_name}
                    )
                    docs.append(temp_doc)
                    count += 1
                    
        except FileNotFoundError:
            print(f'警告: 文件 {file_path} 不存在')
        except json.JSONDecodeError as e:
            print(f'警告: 文件 {file_path} 中JSON解析错误: {str(e)}')
        except Exception as e:
            print(f'警告: 处理文件 {file_path} 时出错: {str(e)}')
    
    print(f'已加载 {count} 条数据！！')
    return docs


def prepare_pdf_document(file_path: str = None) -> list:
    """
    从Excel文件加载PDF文档内容
    
    Args:
        file_path: Excel文件路径
        
    Returns:
        文档列表
    """
    if file_path is None:
        file_path = f'{settings.DATA_PROCESSED_PATH}/pdf_detailed_text.xlsx'
    
    try:
        df = pd.read_excel(file_path)
        
        # 删除空行
        df = df.dropna(subset=['text_content'])
        
        # 将DataFrame转化成LangChain文档
        documents = []
        for _, row in df.iterrows():
            # 确保text_content是字符串，且不为 NAN
            text_content = str(row['text_content']) if pd.notna(row['text_content']) else ''
            
            doc = Document(
                page_content=text_content,
                metadata={'doc_id': str(uuid.uuid4())}
            )
            documents.append(doc)
        
        print(f"成功加载 {len(documents)} 个文档")
        return documents
    except FileNotFoundError:
        print(f'警告: 文件 {file_path} 不存在')
        return []
    except Exception as e:
        print(f'加载PDF文档时出错: {str(e)}')
        return []

