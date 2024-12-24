import streamlit as st
from utils.data_loader import get_value_with_source, get_values_with_sources

def render_drug_treatment_strategy(df, stage):
    """渲染藥物治療策略部分"""
    st.write("### 藥物治療策略")
    treatments_with_sources = get_values_with_sources(df, [
        (df['x_name'] == stage),
        (df['relation'] == 'FIRST_LINE_TREATMENT')
    ])
    
    if treatments_with_sources:
        for treatment, source in treatments_with_sources:
            st.write(f"#### {treatment}")
            st.caption(f"來源: {source}")
            
            drug, drug_source = get_value_with_source(df, [
                (df['x_name'] == treatment),
                (df['relation'] == 'USES_DRUG')
            ])
            st.write(f"- 使用藥物：{drug}")
            st.caption(f"來源: {drug_source}")
            
            effectiveness, eff_source = get_value_with_source(df, [
                (df['x_name'] == treatment),
                (df['relation'] == 'HAS_EFFECTIVENESS')
            ])
            st.write(f"- 預期效果：{effectiveness}")
            st.caption(f"來源: {eff_source}")
    else:
        st.info("暫無藥物治療建議資料")

def render_non_drug_interventions(df, stage):
    """渲染非藥物介入部分"""
    st.write("### 非藥物介入")
    therapies_with_sources = get_values_with_sources(df, [
        (df['x_name'] == stage),
        (df['relation'] == 'RECOMMENDED_THERAPY')
    ])
    
    if therapies_with_sources:
        for therapy, source in therapies_with_sources:
            st.write(f"#### {therapy}")
            st.caption(f"來源: {source}")
            
            effectiveness, eff_source = get_value_with_source(df, [
                (df['x_name'] == therapy),
                (df['relation'] == 'HAS_EFFECTIVENESS')
            ])
            st.write(f"- 預期效果：{effectiveness}")
            st.caption(f"來源: {eff_source}")
    else:
        st.info("暫無非藥物介入建議資料")

def render(df):
    """渲染治療建議頁面"""
    st.header("治療建議")
    
    # 使用已存在的 MMSE 分數
    mmse_score = st.session_state.get('mmse_score', 20)
    
    # 根據MMSE判斷疾病階段
    if mmse_score >= 21:
        current_stage = "Mild (MMSE 21-26)"
    elif mmse_score >= 10:
        current_stage = "Moderate (MMSE 10-20)"
    else:
        current_stage = "Severe (MMSE <10)"
    
    stages = df[df['relation'] == 'HAS_STAGE']['y_name'].unique()
    if len(stages) > 0:
        selected_stage = st.selectbox("選擇疾病階段", stages)
        
        if selected_stage:
            col1, col2 = st.columns(2)
            
            with col1:
                render_drug_treatment_strategy(df, selected_stage)
            
            with col2:
                render_non_drug_interventions(df, selected_stage)
    else:
        st.info("暫無疾病階段資料") 