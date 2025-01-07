import pandas as pd
from datetime import datetime
import streamlit as st
import io
import os
from .neo4j_loader import load_data_from_neo4j

def get_data_path(environment='dev'):
    """Get the correct data path based on the environment
    
    Args:
        environment: 'dev' or 'prod'
    
    Returns:
        str: Path to the data directory
    """
    base_path = 'data'
    if environment not in ['dev', 'prod']:
        raise ValueError("Environment must be either 'dev' or 'prod'")
    return os.path.join(base_path, environment)

def validate_neo4j_nodes(df):
    """驗證節點數據框是否包含所需列"""
    required_columns = {'node_id', 'name', 'type'}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f"缺少必要的列: {', '.join(missing_columns)}")
    return True

def validate_neo4j_relationships(df):
    """驗證關係數據框是否包含所需列"""
    required_columns = {'subject', 'object', 'predicate'}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f"缺少必要的列: {', '.join(missing_columns)}")
    return True

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
def load_data(nodes_file=None, relationships_file=None, environment='dev'):
    """載入Neo4j格式的知識圖譜數據
    
    Args:
        nodes_file: 節點文件（可選）
        relationships_file: 關係文件（可選）
        environment: 數據環境，'dev' 或 'prod'（預設為'dev'）
    
    Returns:
        tuple: (nodes_df, relationships_df) Neo4j格式的節點和關係數據框
    """
    try:
        # If files are provided, read from them
        if nodes_file is not None and relationships_file is not None:
            nodes_df = pd.read_csv(nodes_file)
            relationships_df = pd.read_csv(relationships_file)
            
            # Validate data format
            try:
                validate_neo4j_nodes(nodes_df)
                validate_neo4j_relationships(relationships_df)
            except ValueError as e:
                st.error(str(e))
                return None, None
                
            return nodes_df, relationships_df
            
        # Otherwise, load from Neo4j
        return load_data_from_neo4j(environment)
        
    except Exception as e:
        st.error(f"讀取數據時發生錯誤: {str(e)}")
        return None, None 