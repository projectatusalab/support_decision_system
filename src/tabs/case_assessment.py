import streamlit as st
from utils.data_loader import get_value_with_source, get_values_with_sources

def render_treatment_suggestions(df, stage, has_cardiac_issues, has_renal_issues):
    """渲染治療建議部分"""
    st.write("### 建議治療方案")
    
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
            
            if drug != "資料不可用":
                contraindications_with_sources = get_values_with_sources(df, [
                    (df['x_name'] == drug),
                    (df['relation'] == 'CONTRAINDICATION')
                ])
                
                for contraindication, contra_source in contraindications_with_sources:
                    if (has_cardiac_issues and "心" in contraindication) or \
                       (has_renal_issues and "腎" in contraindication):
                        st.error(f"⚠️ 警告: {contraindication}")
                        st.caption(f"來源: {contra_source}")
            
            dosage, dosage_source = get_value_with_source(df, [
                (df['x_name'] == treatment),
                (df['relation'] == 'HAS_DOSAGE')
            ])
            st.write(f"- 建議劑量：{dosage}")
            st.caption(f"來源: {dosage_source}")
    else:
        st.info("暫無治療建議資料")

def render_non_drug_therapy(df, stage):
    """渲染非藥物治療部分"""
    st.write("### 建議非藥物治療")
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
        st.info("暫無非藥物治療建議資料")

def render(df):
    """渲染個案評估與治療頁面"""
    st.header("個案評估與治療")
    
    # 使用已存在的 MMSE 分數
    mmse_score = st.session_state.get('mmse_score', 20)
    
    # 根據MMSE判斷疾病階段
    if mmse_score >= 21:
        current_stage = "Mild (MMSE 21-26)"
        st.info("📋 輕度階段")
    elif mmse_score >= 10:
        current_stage = "Moderate (MMSE 10-20)"
        st.warning("📋 中度階段")
    else:
        current_stage = "Severe (MMSE <10)"
        st.error("📋 重度階段")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        age = st.number_input("年齡", 0, 120, 75)
    with col2:
        has_cardiac_issues = st.checkbox("有心臟疾病病史")
        has_renal_issues = st.checkbox("有腎功能不全")
    
    col1, col2 = st.columns(2)
    
    with col1:
        render_treatment_suggestions(df, current_stage, has_cardiac_issues, has_renal_issues)
    
    with col2:
        render_non_drug_therapy(df, current_stage) 