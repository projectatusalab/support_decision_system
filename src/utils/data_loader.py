import pandas as pd
from datetime import datetime
import streamlit as st
import io
import os

def validate_neo4j_nodes(df):
    """驗證Neo4j節點數據格式是否正確"""
    required_columns = ['nodeID:ID', 'name', 'type']
    
    # 檢查必要的列是否存在
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return False, f"缺少必要的列: {', '.join(missing_columns)}"
    
    # 檢查是否有空值
    null_counts = df[required_columns].isnull().sum()
    if null_counts.any():
        null_columns = null_counts[null_counts > 0].index.tolist()
        return False, f"以下列包含空值: {', '.join(null_columns)}"
    
    # 檢查ID是否唯一
    if df['nodeID:ID'].duplicated().any():
        return False, "nodeID:ID 必須是唯一的"
    
    return True, "數據格式正確"

def validate_neo4j_relationships(df):
    """驗證Neo4j關係數據格式是否正確"""
    required_columns = ['START_ID', 'END_ID', 'TYPE']
    
    # 檢查必要的列是否存在
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return False, f"缺少必要的列: {', '.join(missing_columns)}"
    
    # 檢查是否有空值
    null_counts = df[required_columns].isnull().sum()
    if null_counts.any():
        null_columns = null_counts[null_counts > 0].index.tolist()
        return False, f"以下列包含空值: {', '.join(null_columns)}"
    
    return True, "數據格式正確"

def safe_read_neo4j_csv(file_path_or_buffer, is_node_file=True):
    """安全地讀取Neo4j格式的CSV文件"""
    try:
        # 讀取文件內容
        if isinstance(file_path_or_buffer, str):
            if not os.path.exists(file_path_or_buffer):
                return None, "找不到指定的文件"
            if os.path.getsize(file_path_or_buffer) == 0:
                return None, "文件是空的"
            df = pd.read_csv(file_path_or_buffer)
        else:
            if not file_path_or_buffer:
                return None, "上傳的文件是空的"
            df = pd.read_csv(file_path_or_buffer)
        
        if df.empty:
            return None, "CSV文件沒有數據"
        
        # 驗證數據格式
        is_valid, message = validate_neo4j_nodes(df) if is_node_file else validate_neo4j_relationships(df)
        if not is_valid:
            return None, message
        
        # 移除每個欄位中的前後空白
        for column in df.columns:
            if df[column].dtype == 'object':
                df[column] = df[column].str.strip()
        
        # 移除完全重複的行
        df = df.drop_duplicates()
        
        return df, None
        
    except Exception as e:
        return None, f"讀取文件時發生錯誤: {str(e)}"

@st.cache_data
def load_data(nodes_file=None, relationships_file=None):
    """載入Neo4j格式的知識圖譜數據
    
    Args:
        nodes_file: 節點文件（可選）
        relationships_file: 關係文件（可選）
    
    Returns:
        tuple: (nodes_df, relationships_df) Neo4j格式的節點和關係數據框
    """
    try:
        # 如果沒有提供文件，使用預設文件
        if nodes_file is None and relationships_file is None:
            nodes_df, error = safe_read_neo4j_csv('data/nodes.csv', is_node_file=True)
            if error:
                st.error(f"讀取節點文件時發生錯誤: {error}")
                return None, None
                
            relationships_df, error = safe_read_neo4j_csv('data/relationships.csv', is_node_file=False)
            if error:
                st.error(f"讀取關係文件時發生錯誤: {error}")
                return None, None
                
            return nodes_df, relationships_df
            
        # 如果提供了文件，讀取上傳的文件
        if nodes_file is not None:
            nodes_df, error = safe_read_neo4j_csv(nodes_file, is_node_file=True)
            if error:
                st.error(f"讀取上傳的節點文件時發生錯誤: {error}")
                return None, None
        else:
            nodes_df, error = safe_read_neo4j_csv('data/nodes.csv', is_node_file=True)
            if error:
                st.error(f"讀取預設節點文件時發生錯誤: {error}")
                return None, None
                
        if relationships_file is not None:
            relationships_df, error = safe_read_neo4j_csv(relationships_file, is_node_file=False)
            if error:
                st.error(f"讀取上傳的關係文件時發生錯誤: {error}")
                return None, None
        else:
            relationships_df, error = safe_read_neo4j_csv('data/relationships.csv', is_node_file=False)
            if error:
                st.error(f"讀取預設關係文件時發生錯誤: {error}")
                return None, None
        
        return nodes_df, relationships_df
        
    except Exception as e:
        st.error(f"讀取文件時發生錯誤: {str(e)}")
        return None, None

def get_node_by_id(nodes_df, node_id):
    """根據ID獲取節點信息"""
    try:
        node = nodes_df[nodes_df['nodeID:ID'] == node_id].iloc[0]
        return node['name'], node['type']
    except:
        return None, None

def get_connected_nodes(nodes_df, relationships_df, node_name, direction='both'):
    """獲取與指定節點相連的所有節點
    
    Args:
        nodes_df: 節點數據框
        relationships_df: 關係數據框
        node_name: 節點名稱
        direction: 方向，可以是 'out'、'in' 或 'both'
    
    Returns:
        list: 相連節點的列表，每個元素是 (node_name, node_type, relation_type) 的元組
    """
    try:
        # 找到節點ID
        node_id = nodes_df[nodes_df['name'] == node_name]['nodeID:ID'].iloc[0]
        connected_nodes = []
        
        # 獲取出向關係
        if direction in ['out', 'both']:
            out_relations = relationships_df[relationships_df['START_ID'] == node_id]
            for _, rel in out_relations.iterrows():
                end_name, end_type = get_node_by_id(nodes_df, rel['END_ID'])
                if end_name:
                    connected_nodes.append((end_name, end_type, rel['TYPE']))
        
        # 獲取入向關係
        if direction in ['in', 'both']:
            in_relations = relationships_df[relationships_df['END_ID'] == node_id]
            for _, rel in in_relations.iterrows():
                start_name, start_type = get_node_by_id(nodes_df, rel['START_ID'])
                if start_name:
                    connected_nodes.append((start_name, start_type, rel['TYPE']))
        
        return connected_nodes
    except Exception as e:
        print(f"Error in get_connected_nodes: {e}")
        return []

def get_nodes_by_type(nodes_df, node_type):
    """獲取指定類型的所有節點"""
    return nodes_df[nodes_df['type'] == node_type]['name'].tolist()

def get_relationships_by_type(nodes_df, relationships_df, relation_type):
    """獲取指定類型的所有關係"""
    relations = relationships_df[relationships_df['TYPE'] == relation_type]
    result = []
    for _, rel in relations.iterrows():
        start_name, start_type = get_node_by_id(nodes_df, rel['START_ID'])
        end_name, end_type = get_node_by_id(nodes_df, rel['END_ID'])
        if start_name and end_name:
            result.append((start_name, start_type, end_name, end_type))
    return result 