import streamlit as st
from utils.data_loader import load_data
import tabs

# 設置頁面配置
st.set_page_config(page_title="阿茲海默症臨床決策支援系統", layout="wide")

def main():
    st.title("阿茲海默症臨床決策支援系統")
    
    # 添加數據來源設置
    st.sidebar.title("數據來源設置")
    
    # 添加環境選擇
    environment = st.sidebar.radio(
        "選擇數據環境",
        ["開發環境 (Development)", "生產環境 (Production)"],
        help="選擇要使用的數據環境：生產環境用於正式使用，開發環境用於測試"
    )
    
    # 轉換環境選擇為代碼值
    env_code = 'prod' if environment == "生產環境 (Production)" else 'dev'
    
    # Neo4j連線設定
    with st.sidebar.expander("Neo4j 連線設定", expanded=False):
        st.session_state.neo4j_uri = st.text_input(
            "Neo4j URI",
            value=st.session_state.get('neo4j_uri', 'neo4j://localhost:7687'),
            help="Neo4j資料庫連線位址"
        )
        st.session_state.neo4j_user = st.text_input(
            "使用者名稱",
            value=st.session_state.get('neo4j_user', 'neo4j'),
            help="Neo4j資料庫使用者名稱"
        )
        st.session_state.neo4j_password = st.text_input(
            "密碼",
            value=st.session_state.get('neo4j_password', 'alex12345'),
            type="password",
            help="Neo4j資料庫密碼"
        )
    
    data_source = st.sidebar.radio(
        "選擇知識圖譜數據來源",
        ["使用Neo4j資料庫", "上傳自定義數據"]
    )
    
    nodes_file = None
    relationships_file = None
    if data_source == "上傳自定義數據":
        nodes_file = st.sidebar.file_uploader(
            "上傳節點數據 (nodes.csv)",
            type=['csv'],
            help="請上傳Neo4j格式的節點文件，必須包含 node_id、name 和 type 列"
        )
        relationships_file = st.sidebar.file_uploader(
            "上傳關係數據 (relationships.csv)",
            type=['csv'],
            help="請上傳Neo4j格式的關係文件，必須包含 subject、predicate 和 object 列"
        )
        
        if nodes_file and relationships_file:
            st.sidebar.success("文件上傳成功！")
            # 顯示數據預覽按鈕
            if st.sidebar.button("預覽上傳的數據"):
                nodes_df, relationships_df = load_data(nodes_file, relationships_file)
                if nodes_df is not None and relationships_df is not None:
                    st.sidebar.write("節點數據預覽：")
                    st.sidebar.dataframe(nodes_df.head(), use_container_width=True)
                    st.sidebar.write("關係數據預覽：")
                    st.sidebar.dataframe(relationships_df.head(), use_container_width=True)
                # 重置文件指針
                nodes_file.seek(0)
                relationships_file.seek(0)
        else:
            st.sidebar.info("請上傳Neo4j格式的CSV文件或選擇使用Neo4j資料庫")
    
    # 載入數據
    data = load_data(nodes_file, relationships_file, environment=env_code)
    nodes_df, relationships_df = data if data is not None else (None, None)
    
    if nodes_df is None or relationships_df is None:
        st.error("無法載入數據。請確保：\n" + 
                "1. Neo4j資料庫連線正確\n" +
                "2. 資料庫中有正確格式的數據\n" +
                "3. 或上傳的CSV文件格式正確（UTF-8編碼的CSV）\n" +
                "4. 節點數據包含 node_id、name 和 type 列\n" +
                "5. 關係數據包含 subject、predicate 和 object 列")
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