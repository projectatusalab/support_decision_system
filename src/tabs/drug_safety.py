import streamlit as st
from utils.data_loader import get_value_with_source, get_values_with_sources

def render_drug_info(df, drug):
    """渲染藥物信息部分"""
    st.write("### 用藥資訊")
    treatments_with_sources = get_values_with_sources(df, [
        (df['relation'] == 'USES_DRUG'),
        (df['y_name'] == drug)
    ], 'x_name')
    
    if treatments_with_sources:
        for treatment, source in treatments_with_sources:
            st.write(f"#### {treatment}")
            st.caption(f"來源: {source}")
            
            dosage, dosage_source = get_value_with_source(df, [
                (df['x_name'] == treatment),
                (df['relation'] == 'HAS_DOSAGE')
            ])
            st.write(f"- 建議劑量：{dosage}")
            st.caption(f"來源: {dosage_source}")
    else:
        st.info("暫無用藥資訊")

def render_safety_info(df, drug):
    """渲染安全性信息部分"""
    st.write("### ⚠️ 安全性資訊")
    
    # 禁忌症
    contraindications_with_sources = get_values_with_sources(df, [
        (df['x_name'] == drug),
        (df['relation'] == 'CONTRAINDICATION')
    ])
    if contraindications_with_sources:
        st.write("#### 禁忌症")
        for contraindication, source in contraindications_with_sources:
            st.error(f"- {contraindication}")
            st.caption(f"來源: {source}")
    
    # 副作用
    side_effects_with_sources = get_values_with_sources(df, [
        (df['x_name'] == drug),
        (df['relation'] == 'HAS_SIDE_EFFECT')
    ])
    if side_effects_with_sources:
        st.write("#### 常見副作用")
        for side_effect, source in side_effects_with_sources:
            st.warning(f"- {side_effect}")
            st.caption(f"來源: {source}")

def render(df):
    """渲染用藥安全查詢頁面"""
    st.header("用藥安全查詢")
    
    drugs = df[df['y_type'] == 'Drug']['y_name'].unique()
    if len(drugs) > 0:
        selected_drug = st.selectbox("選擇要查詢的藥物", drugs)
        
        if selected_drug:
            col1, col2 = st.columns(2)
            
            with col1:
                render_drug_info(df, selected_drug)
            
            with col2:
                render_safety_info(df, selected_drug)
    else:
        st.info("暫無藥物資料") 