import pandas as pd
from datetime import datetime
import streamlit as st
from .neo4j_loader import load_data_from_neo4j

def get_node_by_id(nodes_df, node_id):
    """根據節點ID獲取節點名稱和類型"""
    node = nodes_df[nodes_df['node_id'] == node_id]
    if not node.empty:
        return node.iloc[0]['name'], node.iloc[0]['type']
    return None, None

def get_connected_nodes(nodes_df, relationships_df, node_id, direction='both'):
    """獲取與指定節點相連的所有節點
    
    Args:
        nodes_df: 節點數據框
        relationships_df: 關係數據框
        node_id: 目標節點ID
        direction: 關係方向，可選值為 'outgoing'、'incoming' 或 'both'
    """
    connected_nodes = []
    
    if direction in ['outgoing', 'both']:
        outgoing = relationships_df[relationships_df['subject'] == node_id]
        for _, rel in outgoing.iterrows():
            target_name, target_type = get_node_by_id(nodes_df, rel['object'])
            if target_name:
                connected_nodes.append({
                    'id': rel['object'],
                    'name': target_name,
                    'type': target_type,
                    'relationship': rel['predicate'],
                    'direction': 'outgoing'
                })
    
    if direction in ['incoming', 'both']:
        incoming = relationships_df[relationships_df['object'] == node_id]
        for _, rel in incoming.iterrows():
            source_name, source_type = get_node_by_id(nodes_df, rel['subject'])
            if source_name:
                connected_nodes.append({
                    'id': rel['subject'],
                    'name': source_name,
                    'type': source_type,
                    'relationship': rel['predicate'],
                    'direction': 'incoming'
                })
    
    return connected_nodes

def get_nodes_by_type(nodes_df, node_type):
    """獲取指定類型的所有節點"""
    return nodes_df[nodes_df['type'] == node_type]

def get_relationships_by_type(relationships_df, relationship_type):
    """獲取指定類型的所有關係"""
    return relationships_df[relationships_df['predicate'] == relationship_type]

@st.cache_data
def load_data():
    """載入Neo4j格式的知識圖譜數據
    
    Returns:
        tuple: (nodes_df, relationships_df) Neo4j格式的節點和關係數據框
    """
    try:
        # Load from Neo4j
        return load_data_from_neo4j()
        
    except Exception as e:
        st.error(f"讀取數據時發生錯誤: {str(e)}")
        return None, None 