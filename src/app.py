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
    
    uploaded_file = None
    if data_source == "上傳自定義數據":
        uploaded_file = st.sidebar.file_uploader(
            "上傳知識圖譜CSV文件",
            type=['csv'],
            help="請上傳包含正確列名的CSV文件(最大1000MB)。必要的列包括：x_name, x_type, relation, y_name, y_type, source_type, source_link, source_date"
        )
        
        if uploaded_file:
            st.sidebar.success("文件上傳成功！")
            # 顯示數據預覽按鈕
            if st.sidebar.button("預覽上傳的數據"):
                df = load_data(uploaded_file)
                if df is not None:
                    st.sidebar.dataframe(df.head(), use_container_width=True)
                # 重置文件指針
                uploaded_file.seek(0)
        else:
            st.sidebar.info("請上傳CSV文件或選擇使用預設數據")
    
    # 載入數據
    df = load_data(uploaded_file)
    
    if df is None:
        st.error("無法載入數據。請確保：\n" + 
                "1. CSV文件不是空的\n" +
                "2. 文件格式正確（UTF-8編碼的CSV）\n" +
                "3. 包含所有必要的列\n" +
                "4. 數據格式正確")
        st.stop()
    
    # 顯示數據統計資訊
    st.sidebar.markdown("---")
    st.sidebar.subheader("數據統計")
    st.sidebar.write(f"節點總數: {len(set(df['x_name'].unique()) | set(df['y_name'].unique()))}")
    st.sidebar.write(f"關係總數: {len(df)}")
    st.sidebar.write(f"節點類型數: {len(set(df['x_type'].unique()) | set(df['y_type'].unique()))}")
    st.sidebar.write(f"關係類型數: {len(df['relation'].unique())}")
    
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
            quick_guide.render(df)
        elif "2. 個案評估與治療" in function_option:
            case_assessment.render(df)
        elif "3. 用藥安全查詢" in function_option:
            drug_safety.render(df)
        elif "4. 治療建議" in function_option:
            treatment_recommendations.render(df)
        elif "5. 臨床監測追蹤" in function_option:
            clinical_monitoring.render(df)
        elif "6. 治療方案比較" in function_option:
            treatment_comparison.render(df)
        elif "7. 知識圖譜Schema" in function_option:
            schema_visualization.render(df)
    except Exception as e:
        st.error(f"渲染頁面時發生錯誤: {str(e)}")
        st.error("請檢查數據格式是否正確，或嘗試重新載入頁面")

if __name__ == "__main__":
    main() 