import pandas as pd
import pyvis.network as net
from .data_loader import get_node_by_id
import os
import tempfile

# 定義節點類型的顏色映射
COLOR_MAP = {
    'disease': '#FF0000',  # 紅色
    'treatment': '#4ECDC4',  # 青色
    'drug': '#FF0000',  # 紅色
    'stage': '#4ECDC4',  # 綠色
    'effect/phenotype': '#CCCCCC',  # 黃色
    'side_effect': '#4ECDC4',  # 綠色
    'contraindication': '#CCCCCC',  # 淺紅色
    'guideline': '#4ECDC4',  # 綠色
    'source': '#4ECDC4',  # 綠色
    'evidence': '#4ECDC4',  # 綠色
    'dosage': '#4ECDC4',  # 綠色
    'symptom': '#4ECDC4',  # 綠色
    'therapy_effectiveness': '#4ECDC4',
    'population': '#4ECDC4',  # 綠色
    'step': '#4ECDC4',  # 綠色
    'therapy': '#4ECDC4',  # 綠色
    'duration': '#4ECDC4',  # 綠色
    'other': '#CCCCCC'  # 灰色 - 用於未定義的類型
}

def create_schema_visualization(data):
    """創建知識圖譜Schema的視覺化"""
    nodes_df, relationships_df = data
    
    # 創建網絡圖
    network = net.Network(
        height='600px',
        width='100%',
        bgcolor='#ffffff',
        font_color='black',
        directed=True
    )
    network.toggle_physics(True)
    network.toggle_drag_nodes(True)
    
    # 添加節點類型
    added_node_types = set()
    for _, node in nodes_df.iterrows():
        node_type = node['type'].lower()  # 轉換為小寫以匹配顏色映射
        if node_type not in added_node_types:
            network.add_node(
                node_type,
                label=node['type'],  # 保持原始大小寫顯示
                color=COLOR_MAP.get(node_type, COLOR_MAP['other']),
                size=30,
                title=f"節點類型: {node['type']}"
            )
            added_node_types.add(node_type)
    
    # 添加關係
    added_edges = set()
    for _, rel in relationships_df.iterrows():
        # 獲取起始和目標節點的類型
        start_node = nodes_df[nodes_df['node_id'] == rel['subject']]
        end_node = nodes_df[nodes_df['node_id'] == rel['object']]
        
        if not start_node.empty and not end_node.empty:
            start_type = start_node.iloc[0]['type'].lower()
            end_type = end_node.iloc[0]['type'].lower()
            edge_key = (start_type, rel['predicate'], end_type)
            
            if edge_key not in added_edges:
                network.add_edge(
                    start_type,
                    end_type,
                    label=rel['predicate'],
                    arrows='to',
                    color='#666666'
                )
                added_edges.add(edge_key)
    
    # 設置網絡圖的物理引擎參數
    network.set_options('''
        var options = {
            "physics": {
                "forceAtlas2Based": {
                    "gravitationalConstant": -100,
                    "centralGravity": 0.01,
                    "springLength": 200,
                    "springConstant": 0.08
                },
                "maxVelocity": 50,
                "minVelocity": 0.1,
                "solver": "forceAtlas2Based",
                "timestep": 0.35
            },
            "edges": {
                "smooth": {
                    "type": "continuous",
                    "forceDirection": "none"
                }
            },
            "interaction": {
                "hover": true,
                "navigationButtons": true,
                "keyboard": {
                    "enabled": true
                }
            }
        }
    ''')
    
    return network

def create_detail_visualization(data, center_node=None):
    """創建知識圖譜詳細視圖的視覺化
    
    Args:
        data: (nodes_df, relationships_df) 包含Neo4j格式的節點和關係數據框的元組
        center_node: 可選的中心節點ID
    """
    nodes_df, relationships_df = data
    
    # 創建網絡圖
    network = net.Network(
        height='600px',
        width='100%',
        bgcolor='#ffffff',
        font_color='black',
        directed=True
    )
    network.toggle_physics(True)
    network.toggle_drag_nodes(True)
    
    # 如果沒有指定中心節點，使用第一個節點
    if center_node is None and not nodes_df.empty:
        center_node = nodes_df.iloc[0]['node_id']
    
    if center_node is None:
        return network
    
    # 獲取與中心節點相關的所有關係
    center_relations = relationships_df[
        (relationships_df['subject'] == center_node) |
        (relationships_df['object'] == center_node)
    ]
    
    # 添加節點
    added_nodes = set()
    
    # 添加中心節點
    center_node_data = nodes_df[nodes_df['node_id'] == center_node].iloc[0]
    center_node_type = center_node_data['type'].lower()
    network.add_node(
        center_node,
        label=center_node_data['name'],
        color=COLOR_MAP.get(center_node_type, COLOR_MAP['other']),
        size=30,
        title=f"類型: {center_node_data['type']}"
    )
    added_nodes.add(center_node)
    
    # 添加相關節點和關係
    for _, rel in center_relations.iterrows():
        start_id = rel['subject']
        end_id = rel['object']
        
        # 添加起始節點
        if start_id not in added_nodes:
            start_node = nodes_df[nodes_df['node_id'] == start_id].iloc[0]
            start_type = start_node['type'].lower()
            network.add_node(
                start_id,
                label=start_node['name'],
                color=COLOR_MAP.get(start_type, COLOR_MAP['other']),
                size=25,
                title=f"類型: {start_node['type']}"
            )
            added_nodes.add(start_id)
        
        # 添加目標節點
        if end_id not in added_nodes:
            end_node = nodes_df[nodes_df['node_id'] == end_id].iloc[0]
            end_type = end_node['type'].lower()
            network.add_node(
                end_id,
                label=end_node['name'],
                color=COLOR_MAP.get(end_type, COLOR_MAP['other']),
                size=25,
                title=f"類型: {end_node['type']}"
            )
            added_nodes.add(end_id)
        
        # 添加關係
        network.add_edge(
            start_id,
            end_id,
            label=rel['predicate'],
            arrows='to',
            color='#666666'
        )
    
    # 設置網絡圖的物理引擎參數
    network.set_options('''
        var options = {
            "physics": {
                "forceAtlas2Based": {
                    "gravitationalConstant": -50,
                    "centralGravity": 0.01,
                    "springLength": 100,
                    "springConstant": 0.08
                },
                "maxVelocity": 50,
                "minVelocity": 0.1,
                "solver": "forceAtlas2Based",
                "timestep": 0.35
            },
            "edges": {
                "smooth": {
                    "type": "continuous",
                    "forceDirection": "none"
                }
            },
            "interaction": {
                "hover": true,
                "navigationButtons": true,
                "keyboard": {
                    "enabled": true
                }
            }
        }
    ''')
    
    return network 