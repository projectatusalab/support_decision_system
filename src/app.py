import streamlit as st
from utils.data_loader import load_data
import tabs
import os
import sys

# Add project root to Python path to import config
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)
from config import NEO4J_CONFIG

# 設置頁面配置
st.set_page_config(page_title="阿茲海默症臨床決策支援系統", layout="wide")

def main():
    st.title("阿茲海默症臨床決策支援系統")
    
    # 添加數據來源設置
    st.sidebar.title("數據來源設置")
    
    # Neo4j連線設定
    with st.sidebar.expander("Neo4j 連線設定", expanded=False):
        st.session_state.neo4j_uri = st.text_input(
            "Neo4j URI",
            value=st.session_state.get('neo4j_uri', NEO4J_CONFIG["URI"]),
            help="Neo4j資料庫連線位址"
        )
        st.session_state.neo4j_user = st.text_input(
            "使用者名稱",
            value=st.session_state.get('neo4j_user', NEO4J_CONFIG["USER"]),
            help="Neo4j資料庫使用者名稱"
        )
        st.session_state.neo4j_password = st.text_input(
            "密碼",
            value=st.session_state.get('neo4j_password', NEO4J_CONFIG["PASSWORD"]),
            type="password",
            help="Neo4j資料庫密碼"
        )
    
    # 載入數據
    data = load_data()
    nodes_df, relationships_df = data if data is not None else (None, None)
    
    if nodes_df is None or relationships_df is None:
        st.error("無法載入數據。請確保：\n" + 
                "1. Neo4j資料庫連線正確\n" +
                "2. 資料庫中有正確格式的數據")
        st.stop()
    
    # 顯示數據統計資訊
    st.sidebar.markdown("---")
    st.sidebar.subheader("數據統計")
    st.sidebar.write(f"節點總數: {len(nodes_df)}")
    st.sidebar.write(f"關係總數: {len(relationships_df)}")
    st.sidebar.write(f"節點類型數: {len(nodes_df['type'].unique())}")
    st.sidebar.write(f"關係類型數: {len(relationships_df['predicate'].unique())}")
    
    # 側邊欄：功能選擇
    st.sidebar.title("功能選擇")
    function_option = st.sidebar.selectbox(
        "選擇功能",
        ["1. 快速診療指引",
         "2. 知識圖譜Schema"]
    )
    
    try:
        if "1. 快速診療指引" in function_option:
            tabs.quick_guide(data)
        elif "2. 知識圖譜Schema" in function_option:
            tabs.schema_visualization(data)
    except Exception as e:
        st.error(f"渲染頁面時發生錯誤: {str(e)}")
        st.error("請檢查數據格式是否正確，或嘗試重新載入頁面")

if __name__ == "__main__":
    main() 