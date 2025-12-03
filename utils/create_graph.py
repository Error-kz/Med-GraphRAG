"""
医疗知识图谱构建工具
从医疗数据JSON文件构建Neo4j知识图谱
"""
import os
import sys
import json
from typing import Dict, List, Tuple, Set
from pathlib import Path

# 将项目根目录添加到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.graph.neo4j_client import Neo4jClient
from config.settings import settings


class MedicalGraph:
    """医疗知识图谱构建类"""
    
    def __init__(self, data_path: str = None):
        """
        初始化医疗知识图谱构建器
        
        Args:
            data_path: 医疗数据JSON文件路径，如果为None则使用配置中的路径
        """
        if data_path is None:
            data_path = os.path.join(settings.DATA_RAW_PATH, 'medical.json')
        
        self.data_path = data_path
        self.client = Neo4jClient()
        
        # 验证数据文件是否存在
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"数据文件不存在: {self.data_path}")
    
    def read_nodes(self) -> Tuple[Set[str], Set[str], Set[str], Set[str], Set[str], 
                                    Set[str], Set[str], Set[str], Set[str], List[Dict], 
                                    List[List[str]], List[List[str]], List[List[str]], 
                                    List[List[str]], List[List[str]], List[List[str]], 
                                    List[List[str]], List[List[str]], List[List[str]], 
                                    List[List[str]], List[List[str]], List[List[str]]]:
        """
        读取医疗数据文件并解析节点和关系
        
        Returns:
            包含各种节点集合、疾病信息列表和关系列表的元组
        """
        # 节点集合
        drugs = []  # 药品
        foods = []  # 食物
        diseases = []  # 疾病
        symptoms = []  # 症状
        checks = []  # 检查
        departments = []  # 科室
        producers = []  # 生产商
        categories = []  # 分类
        treatments = []  # 治疗方式
        
        # 关系列表
        rels_recommandeat = []  # 疾病-推荐食物关系
        rels_recommanddrug = []  # 疾病-推荐药品关系
        rels_symptom = []  # 疾病-症状关系
        rels_department = []  # 科室-科室关系
        rels_noteat = []  # 疾病-忌吃关系
        rels_doeat = []  # 疾病-益吃关系
        rels_commanddrug = []  # 疾病-常用药品关系
        rels_check = []  # 疾病-检查关系
        rels_drug_producer = []  # 药品-生产商关系
        rels_acompany = []  # 疾病-并发症关系
        rels_category = []  # 疾病-科室关系
        rels_has_category = []  # 疾病-分类关系
        rels_treated_by = []  # 疾病-治疗方式关系
        
        # 疾病详细信息
        disease_info = []
        
        count = 0
        
        # 逐行读取文件
        with open(self.data_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                
                disease_dict = {}
                count += 1
                if count % 10 == 0:
                    print(f'已处理 {count} 条数据')
                
                try:
                    # 解析JSON数据
                    data_json = json.loads(line.strip())
                    disease = data_json.get('name', '')
                    
                    if not disease:
                        continue
                    
                    diseases.append(disease)
                    
                    # 初始化疾病字典
                    disease_dict['name'] = disease
                    disease_dict['desc'] = data_json.get('desc', '')
                    disease_dict['symptom'] = data_json.get('symptom', '')
                    disease_dict['prevent'] = data_json.get('prevent', '')
                    disease_dict['cause'] = data_json.get('cause', '')
                    disease_dict['easy_get'] = data_json.get('easy_get', '')
                    disease_dict['cure_way'] = data_json.get('cure_way', '')
                    disease_dict['cure_department'] = data_json.get('cure_department', '')
                    disease_dict['cure_lasttime'] = data_json.get('cure_lasttime', '')
                    disease_dict['cured_prob'] = data_json.get('cured_prob', '')
                    disease_dict['get_prob'] = data_json.get('get_prob', '')
                    # 添加缺失的字段
                    disease_dict['yibao_status'] = data_json.get('yibao_status', '')
                    disease_dict['get_way'] = data_json.get('get_way', '')
                    disease_dict['cost_money'] = data_json.get('cost_money', '')
                    disease_dict['category'] = data_json.get('category', [])
                    
                    # 处理症状
                    if 'symptom' in data_json and data_json['symptom']:
                        symptoms.extend(data_json['symptom'])
                        for symptom in data_json['symptom']:
                            rels_symptom.append([disease, symptom])
                    
                    # 处理并发症
                    if 'acompany' in data_json and data_json['acompany']:
                        for acompany in data_json['acompany']:
                            rels_acompany.append([disease, acompany])
                    
                    # 处理科室
                    if 'cure_department' in data_json and data_json['cure_department']:
                        cure_department = data_json['cure_department']
                        if isinstance(cure_department, list):
                            if len(cure_department) == 1:
                                rels_category.append([disease, cure_department[0]])
                            elif len(cure_department) == 2:
                                big = cure_department[0]
                                small = cure_department[1]
                                rels_department.append([small, big])
                                rels_category.append([disease, small])
                            
                            departments.extend(cure_department)
                            disease_dict['cure_department'] = cure_department
                    
                    # 处理常用药品
                    if 'common_drug' in data_json and data_json['common_drug']:
                        common_drug = data_json['common_drug']
                        for drug in common_drug:
                            rels_commanddrug.append([disease, drug])
                        drugs.extend(common_drug)
                    
                    # 处理推荐药品
                    if 'recommand_drug' in data_json and data_json['recommand_drug']:
                        recommand_drug = data_json['recommand_drug']
                        drugs.extend(recommand_drug)
                        for drug in recommand_drug:
                            rels_recommanddrug.append([disease, drug])
                    
                    # 处理食物相关
                    if 'not_eat' in data_json and data_json['not_eat']:
                        not_eat = data_json['not_eat']
                        for _not in not_eat:
                            rels_noteat.append([disease, _not])
                        foods.extend(not_eat)
                    
                    if 'do_eat' in data_json and data_json['do_eat']:
                        do_eat = data_json['do_eat']
                        for _do in do_eat:
                            rels_doeat.append([disease, _do])
                        foods.extend(do_eat)
                    
                    if 'recommand_eat' in data_json and data_json['recommand_eat']:
                        recommand_eat = data_json['recommand_eat']
                        for _recommand in recommand_eat:
                            rels_recommandeat.append([disease, _recommand])
                        foods.extend(recommand_eat)
                    
                    # 处理检查
                    if 'check' in data_json and data_json['check']:
                        check = data_json['check']
                        for _check in check:
                            rels_check.append([disease, _check])
                        checks.extend(check)
                    
                    # 处理药品详情和生产商
                    if 'drug_detail' in data_json and data_json['drug_detail']:
                        drug_detail = data_json['drug_detail']
                        for detail in drug_detail:
                            if '(' in detail and ')' in detail:
                                producer = detail.split('(')[0].strip()
                                drug_name = detail.split('(')[-1].replace(')', '').strip()
                                if producer and drug_name:
                                    rels_drug_producer.append([drug_name, producer])
                                    producers.append(producer)
                    
                    # 处理分类信息（category）
                    if 'category' in data_json and data_json['category']:
                        category_list = data_json['category']
                        if isinstance(category_list, list):
                            for category in category_list:
                                if category and category.strip():
                                    categories.append(category.strip())
                                    rels_has_category.append([disease, category.strip()])
                    
                    # 处理治疗方式（cure_way）- 创建 Treatment 节点和关系
                    if 'cure_way' in data_json and data_json['cure_way']:
                        cure_way_list = data_json['cure_way']
                        if isinstance(cure_way_list, list):
                            for treatment in cure_way_list:
                                if treatment and treatment.strip():
                                    treatments.append(treatment.strip())
                                    rels_treated_by.append([disease, treatment.strip()])
                    
                    disease_info.append(disease_dict)
                    
                except json.JSONDecodeError as e:
                    print(f'警告: 第 {count} 行JSON解析错误: {str(e)}')
                    continue
                except Exception as e:
                    print(f'警告: 处理第 {count} 行数据时出错: {str(e)}')
                    continue
        
        return (
            set(drugs), set(foods), set(checks), set(departments), 
            set(producers), set(symptoms), set(diseases), set(categories), 
            set(treatments), disease_info,
            rels_check, rels_recommandeat, rels_noteat, rels_doeat, 
            rels_department, rels_commanddrug, rels_drug_producer, 
            rels_recommanddrug, rels_symptom, rels_acompany, rels_category,
            rels_has_category, rels_treated_by
        )
    
    def create_graphnodes_and_graphrels(self):
        """创建知识图谱的节点和关系"""
        # 读取节点和关系数据
        (Drugs, Foods, Checks, Departments, Producers, Symptoms, Diseases, 
         Categories, Treatments, disease_info, rels_check, rels_recommandeat, 
         rels_noteat, rels_doeat, rels_department, rels_commanddrug, 
         rels_drug_producer, rels_recommanddrug, rels_symptom, rels_acompany, 
         rels_category, rels_has_category, rels_treated_by) = self.read_nodes()
        
        # 打印统计信息
        print('=' * 100)
        print('节点统计:')
        print(f'  Drugs: {len(Drugs)}')
        print(f'  Foods: {len(Foods)}')
        print(f'  Checks: {len(Checks)}')
        print(f'  Departments: {len(Departments)}')
        print(f'  Producers: {len(Producers)}')
        print(f'  Symptoms: {len(Symptoms)}')
        print(f'  Diseases: {len(Diseases)}')
        print(f'  Categories: {len(Categories)}')
        print(f'  Treatments: {len(Treatments)}')
        print('=' * 100)
        print('关系统计:')
        print(f'  rels_check: {len(rels_check)}')
        print(f'  rels_recommandeat: {len(rels_recommandeat)}')
        print(f'  rels_noteat: {len(rels_noteat)}')
        print(f'  rels_doeat: {len(rels_doeat)}')
        print(f'  rels_department: {len(rels_department)}')
        print(f'  rels_commanddrug: {len(rels_commanddrug)}')
        print(f'  rels_drug_producer: {len(rels_drug_producer)}')
        print(f'  rels_recommanddrug: {len(rels_recommanddrug)}')
        print(f'  rels_symptom: {len(rels_symptom)}')
        print(f'  rels_acompany: {len(rels_acompany)}')
        print(f'  rels_category: {len(rels_category)}')
        print(f'  rels_has_category: {len(rels_has_category)}')
        print(f'  rels_treated_by: {len(rels_treated_by)}')
        print('=' * 100)
        
        # 连接Neo4j
        if not self.client.connect():
            raise ConnectionError("无法连接到Neo4j数据库")
        
        try:
            # 创建疾病节点
            self._create_disease_nodes(disease_info)
            
            # 创建其他节点
            self._create_nodes('Drug', Drugs)
            self._create_nodes('Food', Foods)
            self._create_nodes('Symptom', Symptoms)
            self._create_nodes('Check', Checks)
            self._create_nodes('Department', Departments)
            self._create_nodes('Producer', Producers)
            self._create_nodes('Category', Categories)
            self._create_nodes('Treatment', Treatments)
            
            # 创建关系
            self.create_relationship('Disease', 'Food', rels_recommandeat, 'recommand_eat', '推荐食谱')
            self.create_relationship('Disease', 'Drug', rels_recommanddrug, 'recommand_drug', '推荐药品')
            self.create_relationship('Disease', 'Symptom', rels_symptom, 'has_symptom', '症状')
            self.create_relationship('Disease', 'Food', rels_noteat, 'not_eat', '忌吃')
            self.create_relationship('Disease', 'Food', rels_doeat, 'do_eat', '益吃')
            self.create_relationship('Disease', 'Drug', rels_commanddrug, 'command_drug', '常用药品')
            self.create_relationship('Disease', 'Check', rels_check, 'need_check', '诊断检查')
            self.create_relationship('Disease', 'Disease', rels_acompany, 'acompany_with', '并发症')
            self.create_relationship('Disease', 'Department', rels_category, 'belongs_to', '所属科室')
            self.create_relationship('Department', 'Department', rels_department, 'sub_department', '子科室')
            self.create_relationship('Drug', 'Producer', rels_drug_producer, 'drugs_of', '药品厂商')
            self.create_relationship('Disease', 'Category', rels_has_category, 'has_category', '所属分类')
            self.create_relationship('Disease', 'Treatment', rels_treated_by, 'treated_by', '治疗方式')
            
        finally:
            self.client.close()
    
    def _create_disease_nodes(self, disease_info: List[Dict]):
        """创建疾病节点"""
        print('开始创建疾病节点...')
        n, m = 0, 0
        
        if not self.client.driver:
            raise ConnectionError("Neo4j连接未建立")
        
        with self.client.driver.session() as session:
            for d in disease_info:
                try:
                    # 使用参数化查询避免注入风险
                    cypher = """
                    MERGE (a:Disease {name: $name})
                    SET a.desc = $desc,
                        a.prevent = $prevent,
                        a.cause = $cause,
                        a.easy_get = $easy_get,
                        a.cure_lasttime = $cure_lasttime,
                        a.cure_department = $cure_department,
                        a.cure_way = $cure_way,
                        a.cured_prob = $cured_prob,
                        a.get_prob = $get_prob,
                        a.yibao_status = $yibao_status,
                        a.get_way = $get_way,
                        a.cost_money = $cost_money,
                        a.category = $category
                    """
                    # 处理 category 列表，转换为字符串列表
                    category_list = d.get('category', [])
                    if isinstance(category_list, list):
                        category_str = str(category_list)
                    else:
                        category_str = str(category_list) if category_list else ''
                    
                    session.run(cypher, {
                        'name': d.get('name', ''),
                        'desc': d.get('desc', ''),
                        'prevent': d.get('prevent', ''),
                        'cause': d.get('cause', ''),
                        'easy_get': d.get('easy_get', ''),
                        'cure_lasttime': d.get('cure_lasttime', ''),
                        'cure_department': str(d.get('cure_department', '')),
                        'cure_way': str(d.get('cure_way', '')),
                        'cured_prob': d.get('cured_prob', ''),
                        'get_prob': d.get('get_prob', ''),
                        'yibao_status': d.get('yibao_status', ''),
                        'get_way': d.get('get_way', ''),
                        'cost_money': d.get('cost_money', ''),
                        'category': category_str
                    })
                    n += 1
                except Exception as e:
                    m += 1
                    print(f'创建疾病节点失败: {d.get("name", "未知")}, 错误: {str(e)}')
                
                if n % 500 == 0:
                    print(f'已创建 {n} 个疾病节点')
        
        print(f'疾病节点创建完成，成功: {n}, 失败: {m}')
        print('-' * 100)
    
    def _create_nodes(self, label: str, nodes: Set[str]):
        """创建指定标签的节点"""
        if not nodes:
            print(f'跳过创建 {label} 节点（无数据）')
            return
        
        print(f'开始创建 {label} 节点...')
        count, err = 0, 0
        
        if not self.client.driver:
            raise ConnectionError("Neo4j连接未建立")
        
        with self.client.driver.session() as session:
            for node_name in nodes:
                try:
                    # 使用参数化查询
                    cypher = f"MERGE (a:{label} {{name: $name}})"
                    session.run(cypher, {'name': node_name})
                    count += 1
                except Exception as e:
                    err += 1
                    print(f'创建 {label} 节点失败: {node_name}, 错误: {str(e)}')
        
        print(f'{label} 节点创建完成，成功: {count}, 失败: {err}')
        print('-' * 100)
    
    def create_relationship(self, start_node: str, end_node: str, edges: List[List[str]], 
                          rel_type: str, rel_name: str):
        """
        创建实体关联边
        
        Args:
            start_node: 起始节点标签
            end_node: 结束节点标签
            edges: 边列表，每个边是 [起始节点名称, 结束节点名称]
            rel_type: 关系类型
            rel_name: 关系名称
        """
        if not edges:
            print(f'跳过创建关系 {rel_name}（无数据）')
            return
        
        # 去重处理
        set_edges = []
        for edge in edges:
            if len(edge) == 2 and edge[0] and edge[1]:
                set_edges.append('###'.join(edge))
        
        unique_edges = list(set(set_edges))
        num_edges = len(unique_edges)
        print(f'开始创建关系: {rel_name}, 共 {num_edges} 条')
        
        if not self.client.driver:
            raise ConnectionError("Neo4j连接未建立")
        
        n, m = 0, 0
        with self.client.driver.session() as session:
            for edge_str in unique_edges:
                try:
                    edge = edge_str.split('###')
                    if len(edge) != 2:
                        continue
                    
                    p, q = edge[0], edge[1]
                    
                    # 使用参数化查询
                    cypher = f"""
                    MATCH (p:{start_node} {{name: $p_name}}), (q:{end_node} {{name: $q_name}})
                    MERGE (p)-[rel:{rel_type} {{name: $rel_name}}]->(q)
                    """
                    session.run(cypher, {
                        'p_name': p,
                        'q_name': q,
                        'rel_name': rel_name
                    })
                    n += 1
                except Exception as e:
                    m += 1
                    if m <= 10:  # 只打印前10个错误
                        print(f'创建关系失败: {edge_str}, 错误: {str(e)}')
                
                if n % 1000 == 0:
                    print(f'已处理 {n} 条关系')
        
        print(f'关系 {rel_name} 创建完成，成功: {n}, 失败: {m}')
        print('=' * 100)


if __name__ == '__main__':
    try:
        mg = MedicalGraph()
        print('开始创建知识图谱中的节点和关系...')
        mg.create_graphnodes_and_graphrels()
        print('知识图谱创建完成！')
    except Exception as e:
        print(f'创建知识图谱时发生错误: {str(e)}')
        raise
