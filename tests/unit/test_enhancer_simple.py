"""
上下文增强功能简单测试 Demo
测试使用大模型进行实体提取
"""
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def test_enhancer_with_llm():
    """测试使用大模型提取实体"""
    print("=" * 60)
    print("测试: 使用大模型提取主题实体")
    print("=" * 60)
    
    try:
        from core.context.enhancer import (
            has_reference_pronouns,
            extract_entities_from_history,
            enhance_query_with_context
        )
        
        # 模拟对话历史
        history = [
            {
                'question': '感冒了有什么症状？',
                'answer': '感冒的常见症状包括发热、咳嗽、流鼻涕、头痛等。建议多休息、多喝水。',
                'timestamp': '2024-01-01 10:00:00'
            },
            {
                'question': '感冒怎么治疗？',
                'answer': '感冒的治疗方法包括多休息、多喝水、服用感冒药如布洛芬等。',
                'timestamp': '2024-01-01 10:05:00'
            }
        ]
        
        print("\n对话历史:")
        for i, record in enumerate(history, 1):
            print(f"  {i}. 问题: {record['question']}")
            print(f"     回答: {record['answer'][:60]}...")
        
        print("\n" + "-" * 60)
        print("步骤1: 检测指代性词语")
        print("-" * 60)
        
        test_queries = [
            "有什么特效药？",
            "怎么预防？",
            "严重吗？",
            "感冒了有什么症状？",  # 完整问题，不应增强
        ]
        
        for query in test_queries:
            has_ref = has_reference_pronouns(query)
            print(f"  问题: {query}")
            print(f"  包含指代: {has_ref}")
        
        print("\n" + "-" * 60)
        print("步骤2: 使用大模型提取主题实体")
        print("-" * 60)
        print("  正在调用大模型...")
        
        entities = extract_entities_from_history(history, max_history=5)
        
        print(f"\n  提取的实体:")
        print(f"    主题: {entities['topics']}")
        print(f"    疾病: {entities['diseases']}")
        print(f"    症状: {entities['symptoms']}")
        print(f"    药物: {entities['drugs']}")
        
        print("\n" + "-" * 60)
        print("步骤3: 问题增强")
        print("-" * 60)
        
        for query in test_queries:
            enhanced_query, was_enhanced = enhance_query_with_context(query, history)
            print(f"\n  原始问题: {query}")
            if was_enhanced:
                print(f"  ✅ 增强后: {enhanced_query}")
            else:
                print(f"  ➡️  未增强（问题完整或未找到主题）")
        
        print("\n" + "=" * 60)
        print("✅ 测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_enhancer_with_llm()

