import pandas as pd
from datetime import datetime
import streamlit as st
import io
import os

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

def safe_read_neo4j_csv(file_path):
    """安全地讀取Neo4j格式的CSV文件，並統一列名格式"""
    try:
        df = pd.read_csv(file_path)
        
        # 統一節點文件的列名
        if 'NODE_ID' in df.columns:
            df = df.rename(columns={
                'NODE_ID': 'node_id',
                'TYPE': 'type',
                'NAME': 'name'
            })
        
        # 統一關係文件的列名
        if 'START_ID' in df.columns:
            df = df.rename(columns={
                'START_ID': 'subject',
                'END_ID': 'object',
                'TYPE': 'predicate'
            })
        
        return df
    except Exception as e:
        print(f"Error reading {file_path}: {str(e)}")
        return None

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

def load_source_properties(environment='dev'):
    """載入來源節點的屬性資料
    
    Args:
        environment: 'dev' or 'prod'
    
    Returns:
        dict: 包含來源節點屬性的字典，以source node_id為key
    """
    try:
        data_dir = get_data_path(environment)
        properties_path = os.path.join(data_dir, 'input', '3_other_resources_property.csv')
        
        if not os.path.exists(properties_path):
            print(f"Warning: Source properties file not found at {properties_path}")
            return {}
        
        properties_df = pd.read_csv(properties_path)
        
        # 創建屬性字典，使用's_'前綴的ID作為key
        properties_dict = {}
        for _, row in properties_df.iterrows():
            external_id = row['external_source_id']
            # Remove any leading zeros from the number part
            number_part = str(int(external_id.split('_')[1]))
            source_id = 's_' + number_part  # Convert 'es_1' to 's_1'
            
            properties_dict[source_id] = {
                'source_primary': row['source_primary'],
                'source_secondary': row['source_secondary'],
                'name': row['name'],
                'source_link': row['source_link'],
                'source_date': row['source_date'],
                'pubmed_id': row['pubmed_id'],
                'country_of_origin': row['country_of_origin']
            }
        
        return properties_dict
    except Exception as e:
        print(f"Error loading source properties: {str(e)}")
        return {}

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
        data_dir = get_data_path(environment)
        output_dir = os.path.join(data_dir, 'output')
        
        # 檢查目錄是否存在
        if not os.path.exists(output_dir):
            st.error(f"數據目錄不存在: {output_dir}")
            return None, None
        
        # 載入來源節點屬性
        source_properties = load_source_properties(environment)
        
        # 如果沒有提供文件，使用預設文件
        if nodes_file is None and relationships_file is None:
            nodes_path = os.path.join(output_dir, 'nodes.csv')
            relationships_path = os.path.join(output_dir, 'relationships.csv')
            
            nodes_df = safe_read_neo4j_csv(nodes_path)
            if nodes_df is None:
                st.error(f"讀取節點文件時發生錯誤 (環境: {environment})")
                return None, None
            
            # 為Source類型的節點添加屬性
            if 'type' in nodes_df.columns:
                # Case-insensitive check for source nodes
                source_nodes = nodes_df[nodes_df['type'].str.lower() == 'source']
                
                for idx in source_nodes.index:
                    node_id = nodes_df.loc[idx, 'node_id']
                    if node_id in source_properties:
                        props = source_properties[node_id]
                        # 直接添加所需的屬性到DataFrame
                        for key, value in props.items():
                            if key not in nodes_df.columns:
                                nodes_df[key] = None  # 先創建列
                        nodes_df.loc[idx, list(props.keys())] = list(props.values())  # 更新所有屬性
            relationships_df = safe_read_neo4j_csv(relationships_path)
            if relationships_df is None:
                st.error(f"讀取關係文件時發生錯誤 (環境: {environment})")
                return None, None
            
            # 驗證數據格式
            try:
                validate_neo4j_nodes(nodes_df)
                validate_neo4j_relationships(relationships_df)
            except ValueError as e:
                st.error(str(e))
                return None, None
            
            return nodes_df, relationships_df
        
        # 如果提供了文件，讀取上傳的文件
        if nodes_file is not None:
            nodes_df = safe_read_neo4j_csv(nodes_file)
            if nodes_df is None:
                st.error("讀取上傳的節點文件時發生錯誤")
                return None, None
            
            # 為Source類型的節點添加屬性
            if 'type' in nodes_df.columns:
                source_nodes = nodes_df[nodes_df['type'] == 'Source']
                for idx in source_nodes.index:
                    node_id = nodes_df.loc[idx, 'node_id']
                    if node_id in source_properties:
                        props = source_properties[node_id]
                        # 直接添加所需的屬性到DataFrame
                        for key, value in props.items():
                            if key not in nodes_df.columns:
                                nodes_df[key] = None  # 先創建列
                        nodes_df.loc[idx, list(props.keys())] = list(props.values())  # 更新所有屬性
        else:
            nodes_path = os.path.join(output_dir, 'nodes.csv')
            nodes_df = safe_read_neo4j_csv(nodes_path)
            if nodes_df is None:
                st.error(f"讀取預設節點文件時發生錯誤 (環境: {environment})")
                return None, None
        
        if relationships_file is not None:
            relationships_df = safe_read_neo4j_csv(relationships_file)
            if relationships_df is None:
                st.error("讀取上傳的關係文件時發生錯誤")
                return None, None
        else:
            relationships_path = os.path.join(output_dir, 'relationships.csv')
            relationships_df = safe_read_neo4j_csv(relationships_path)
            if relationships_df is None:
                st.error(f"讀取預設關係文件時發生錯誤 (環境: {environment})")
                return None, None
        
        # 驗證數據格式
        try:
            validate_neo4j_nodes(nodes_df)
            validate_neo4j_relationships(relationships_df)
        except ValueError as e:
            st.error(str(e))
            return None, None
        
        return nodes_df, relationships_df
        
    except Exception as e:
        st.error(f"讀取文件時發生錯誤: {str(e)}")
        return None, None 