import streamlit as st
from src.utils.data_loader import load_data
from src.tabs import (
    quick_guide,
    case_assessment,
    drug_safety,
    treatment_recommendations,
    clinical_monitoring,
    treatment_comparison,
    schema_visualization
)

# 設置頁面配置
st.set_page_config(page_title="阿茲海默症臨床決策支援系統", layout="wide")

def main():
    st.title("阿茲海默症臨床決策支援系統")
    
    # 添加數據來源選擇
    st.sidebar.title("數據來源設置")
    data_source = st.sidebar.radio(
        "選擇知識圖譜數據來源",
        ["使用預設數據", "上傳自定義數據"]
    )
    
    nodes_file = None
    relationships_file = None
    if data_source == "上傳自定義數據":
        nodes_file = st.sidebar.file_uploader(
            "上傳節點數據 (nodes.csv)",
            type=['csv'],
            help="請上傳Neo4j格式的節點文件，必須包含 nodeID:ID、name 和 type 列"
        )
        relationships_file = st.sidebar.file_uploader(
            "上傳關係數據 (relationships.csv)",
            type=['csv'],
            help="請上傳Neo4j格式的關係文件，必須包含 START_ID、END_ID 和 TYPE 列"
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
            st.sidebar.info("請上傳Neo4j格式的CSV文件或選擇使用預設數據")
    
    # 載入數據
    data = load_data(nodes_file, relationships_file)
    nodes_df, relationships_df = data if data is not None else (None, None)
    
    if nodes_df is None or relationships_df is None:
        st.error("無法載入數據。請確保：\n" + 
                "1. CSV文件不是空的\n" +
                "2. 文件格式正確（UTF-8編碼的CSV）\n" +
                "3. 節點文件包含 nodeID:ID、name 和 type:LABEL 列\n" +
                "4. 關係文件包含 :START_ID、:END_ID 和 :TYPE 列")
        st.stop()
    
    # Debug information
    st.write("Debug - Relationship columns:", relationships_df.columns.tolist())
    
    # 顯示數據統計資訊
    st.sidebar.markdown("---")
    st.sidebar.subheader("數據統計")
    st.sidebar.write(f"節點總數: {len(nodes_df)}")
    st.sidebar.write(f"關係總數: {len(relationships_df)}")
    st.sidebar.write(f"節點類型數: {len(nodes_df['type'].unique())}")
    st.sidebar.write(f"關係類型數: {len(relationships_df['TYPE'].unique())}")
    
    # 側邊欄：功能選擇
    st.sidebar.title("功能選擇")
    function_option = st.sidebar.selectbox(
        "選擇功能",
        ["1. 快速診療指引",
         "2. 個案評估與治療",
         "3. 用藥安全查詢",
         "4. 治療建議",
         "5. 臨床監測追蹤",
         "6. 治療方案比較",
         "7. 知識圖譜Schema"]
    )
    
    try:
        if "1. 快速診療指引" in function_option:
            quick_guide.render(data)
        elif "2. 個案評估與治療" in function_option:
            case_assessment.render(data)
        elif "3. 用藥安全查詢" in function_option:
            drug_safety.render(data)
        elif "4. 治療建議" in function_option:
            treatment_recommendations.render(data)
        elif "5. 臨床監測追蹤" in function_option:
            clinical_monitoring.render(data)
        elif "6. 治療方案比較" in function_option:
            treatment_comparison.render(data)
        elif "7. 知識圖譜Schema" in function_option:
            schema_visualization.render(data)
    except Exception as e:
        st.error(f"渲染頁面時發生錯誤: {str(e)}")
        st.error("請檢查數據格式是否正確，或嘗試重新載入頁面")

if __name__ == "__main__":
    main() 