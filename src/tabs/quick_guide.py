import streamlit as st
from utils.data_loader import get_value_with_source, get_values_with_sources

def render(df):
    """渲染快速診療指引頁面"""
    st.header("快速診療指引")
    
    # 快速MMSE評分工具
    st.subheader("MMSE快速評估")
    mmse_score = st.number_input("MMSE分數", 0, 30, 20)
    
    # 根據MMSE自動判斷疾病階段
    if mmse_score >= 21:
        current_stage = "Mild (MMSE 21-26)"
        st.info("📋 目前處於輕度階段")
    elif mmse_score >= 10:
        current_stage = "Moderate (MMSE 10-20)"
        st.warning("📋 目前處於中度階段")
    else:
        current_stage = "Severe (MMSE <10)"
        st.error("📋 目前處於重度階段")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### 主要臨床表現")
        symptoms_with_sources = get_values_with_sources(df, [
            (df['x_name'] == current_stage),
            (df['relation'] == 'HAS_SYMPTOM')
        ])
        
        if symptoms_with_sources:
            for symptom, source in symptoms_with_sources:
                st.write(f"- {symptom}")
                st.caption(f"來源: {source}")
        else:
            st.info("暫無相關症狀資料")
    
    with col2:
        st.write("### 首選治療建議")
        treatments_with_sources = get_values_with_sources(df, [
            (df['x_name'] == current_stage),
            (df['relation'] == 'FIRST_LINE_TREATMENT')
        ])
        
        if treatments_with_sources:
            for treatment, source in treatments_with_sources:
                st.write(f"- {treatment}")
                st.caption(f"來源: {source}")
                
                drug, drug_source = get_value_with_source(df, [
                    (df['x_name'] == treatment),
                    (df['relation'] == 'USES_DRUG')
                ])
                if drug != "資料不可用":
                    st.write(f"  使用藥物: {drug}")
                    st.caption(f"來源: {drug_source}")
        else:
            st.info("暫無治療建議資料") 