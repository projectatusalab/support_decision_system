import streamlit as st
import pandas as pd
from utils.data_loader import get_value_with_source, get_values_with_sources

def create_comparison_table(df, treatments):
    """創建治療方案比較表"""
    comparison_data = []
    
    for treatment in treatments:
        # 獲取基本資訊
        drug, drug_source = get_value_with_source(df, [
            (df['x_name'] == treatment),
            (df['relation'] == 'USES_DRUG')
        ])
        
        effectiveness, eff_source = get_value_with_source(df, [
            (df['x_name'] == treatment),
            (df['relation'] == 'HAS_EFFECTIVENESS')
        ])
        
        dosage, dosage_source = get_value_with_source(df, [
            (df['x_name'] == treatment),
            (df['relation'] == 'HAS_DOSAGE')
        ])
        
        # 獲取副作用
        side_effects = []
        if drug != "資料不可用":
            side_effects_with_sources = get_values_with_sources(df, [
                (df['x_name'] == drug),
                (df['relation'] == 'HAS_SIDE_EFFECT')
            ])
            side_effects = [se[0] for se in side_effects_with_sources]
        
        # 獲取禁忌症
        contraindications = []
        if drug != "資料不可用":
            contraindications_with_sources = get_values_with_sources(df, [
                (df['x_name'] == drug),
                (df['relation'] == 'CONTRAINDICATION')
            ])
            contraindications = [c[0] for c in contraindications_with_sources]
        
        # 獲取適用階段
        stages_with_sources = get_values_with_sources(df, [
            (df['y_name'] == treatment),
            (df['relation'] == 'FIRST_LINE_TREATMENT')
        ], 'x_name')
        stages = [s[0] for s in stages_with_sources]
        
        comparison_data.append({
            '治療方案': treatment,
            '使用藥物': drug,
            '適用階段': ', '.join(stages) if stages else '不明',
            '建議劑量': dosage,
            '預期效果': effectiveness,
            '副作用': ', '.join(side_effects) if side_effects else '無資料',
            '禁忌症': ', '.join(contraindications) if contraindications else '無資料'
        })
    
    return pd.DataFrame(comparison_data)

def render_treatment_details(df, treatment):
    """渲染治療方案詳細資訊"""
    with st.expander(f"📋 {treatment} 詳細資訊"):
        # 基本資訊
        drug, drug_source = get_value_with_source(df, [
            (df['x_name'] == treatment),
            (df['relation'] == 'USES_DRUG')
        ])
        st.write(f"#### 使用藥物：{drug}")
        st.caption(f"來源：{drug_source}")
        
        # 適用階段
        stages_with_sources = get_values_with_sources(df, [
            (df['y_name'] == treatment),
            (df['relation'] == 'FIRST_LINE_TREATMENT')
        ], 'x_name')
        if stages_with_sources:
            st.write("#### 適用階段")
            for stage, source in stages_with_sources:
                st.write(f"- {stage}")
                st.caption(f"來源：{source}")
        
        # 療效信息
        effectiveness, eff_source = get_value_with_source(df, [
            (df['x_name'] == treatment),
            (df['relation'] == 'HAS_EFFECTIVENESS')
        ])
        st.write(f"#### 預期效果：{effectiveness}")
        st.caption(f"來源：{eff_source}")
        
        # 副作用
        if drug != "資料不可用":
            side_effects_with_sources = get_values_with_sources(df, [
                (df['x_name'] == drug),
                (df['relation'] == 'HAS_SIDE_EFFECT')
            ])
            if side_effects_with_sources:
                st.write("#### 副作用")
                for side_effect, source in side_effects_with_sources:
                    st.write(f"- {side_effect}")
                    st.caption(f"來源：{source}")

def render(df):
    """渲染治療方案比較頁面"""
    st.header("治療方案比較")
    
    # 獲取所有治療方案
    all_treatments = df[
        (df['relation'] == 'FIRST_LINE_TREATMENT') | 
        (df['relation'] == 'SECOND_LINE_TREATMENT')
    ]['y_name'].unique()
    
    if len(all_treatments) == 0:
        st.info("暫無治療方案資料")
        return
    
    # 選擇要比較的治療方案
    selected_treatments = st.multiselect(
        "選擇要比較的治療方案",
        all_treatments,
        default=list(all_treatments)[:2] if len(all_treatments) >= 2 else list(all_treatments)
    )
    
    if selected_treatments:
        # 創建比較表
        comparison_df = create_comparison_table(df, selected_treatments)
        
        # 顯示比較表
        st.write("### 治療方案比較表")
        st.dataframe(
            comparison_df.set_index('治療方案'),
            use_container_width=True
        )
        
        # 顯示詳細資訊
        st.write("### 詳細資訊")
        for treatment in selected_treatments:
            render_treatment_details(df, treatment)
    else:
        st.warning("請選擇至少一個治療方案進行比較") 