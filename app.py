import streamlit as st
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
from pyvis.network import Network
import tempfile
import os
from datetime import datetime

# 設置頁面配置
st.set_page_config(page_title="阿茲海默症臨床決策支持系統", layout="wide")

# 定義全局顏色映射
COLOR_MAP = {
    'Disease': '#FF6B6B',
    'Stage': '#45B7D1',
    'Symptom': '#4ECDC4',
    'Treatment': '#96CEB4',
    'Drug': '#FFEEAD',
    'Therapy': '#D4A5A5',
    'Evidence': '#FFE66D',
    'Effectiveness': '#98FB98',
    'SideEffect': '#FFB6C1',
    'Monitoring': '#DDA0DD',
    'Condition': '#E6E6FA',
    'Population': '#98FB98',
    'Dosage': '#DEB887',
    'Gene': '#DEB887'
}

# 讀取數據
@st.cache_data
def load_data():
    df = pd.read_csv('alzheimer_kg.csv')
    return df

def create_schema_visualization(df):
    """創建知識圖譜schema的視覺化"""
    net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="black")
    
    # 獲取所有唯一的節點類型和關係類型
    node_types = set(df['x_type'].unique()) | set(df['y_type'].unique())
    relations = df.groupby(['x_type', 'y_type', 'relation']).size().reset_index()
    
    # 添加節點
    for node_type in node_types:
        color = COLOR_MAP.get(node_type, '#CCCCCC')
        net.add_node(node_type, label=node_type, color=color, size=30)
    
    # 添加邊
    for _, row in relations.iterrows():
        net.add_edge(row['x_type'], row['y_type'], 
                    title=row['relation'], 
                    label=row['relation'],
                    value=row[0])
    
    return net

def get_value_with_source(df, conditions, value_col='y_name'):
    """獲取值及其來源"""
    try:
        result = df.copy()
        for condition in conditions:
            result = result.loc[condition]
        if len(result) > 0:
            row = result.iloc[0]
            value = row[value_col]
            source = f"[{row['source_type']}]({row['source_link']}) ({row['source_date']})"
            return value, source
        return "資料不可用", "無來源資料"
    except Exception as e:
        print(f"Error in get_value_with_source: {e}")
        return "資料不可用", "無來源資料"

def get_values_with_sources(df, conditions, value_col='y_name'):
    """獲取多個值及其來源"""
    try:
        result = df.copy()
        for condition in conditions:
            result = result.loc[condition]
        if len(result) > 0:
            values_with_sources = []
            for _, row in result.iterrows():
                value = row[value_col]
                source = f"[{row['source_type']}]({row['source_link']}) ({row['source_date']})"
                values_with_sources.append((value, source))
            return values_with_sources
        return []
    except Exception as e:
        print(f"Error in get_values_with_sources: {e}")
        return []

def create_comparison_table(df, treatments):
    """創建治療方案比較表"""
    comparison_data = []
    
    for treatment in treatments:
        # 獲取基本信息
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

def main():
    st.title("阿茲海默症臨床決策支持系統")
    
    # 載入數據
    df = load_data()
    
    # 側邊欄：功能選擇
    st.sidebar.title("功能選單")
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
    
    if "1. 快速診療指引" in function_option:
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
            # 顯示當前階段的主要症狀臨床表現
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
                st.write("��無相關症狀資料")
        
        with col2:
            # 顯示首選治療建議
            st.write("### 首選治療建議")
            treatments_with_sources = get_values_with_sources(df, [
                (df['x_name'] == current_stage),
                (df['relation'] == 'FIRST_LINE_TREATMENT')
            ])
            
            if treatments_with_sources:
                for treatment, source in treatments_with_sources:
                    st.write(f"- {treatment}")
                    st.caption(f"來源: {source}")
                    
                    # 獲取治療相關的藥物資訊
                    drug, drug_source = get_value_with_source(df, [
                        (df['x_name'] == treatment),
                        (df['relation'] == 'USES_DRUG')
                    ])
                    if drug != "資料不可用":
                        st.write(f"  使用藥物: {drug}")
                        st.caption(f"來源: {drug_source}")
            else:
                st.write("暫無治療建議資料")
    
    elif "2. 個案評估與治療" in function_option:
        st.header("個案評估與治療")
        
        # 病人基本資料輸入
        col1, col2, col3 = st.columns(3)
        with col1:
            age = st.number_input("年齡", 0, 120, 75)
        with col2:
            mmse = st.number_input("MMSE分數", 0, 30, 20)
        with col3:
            has_cardiac_issues = st.checkbox("有心臟疾病病史")
            has_renal_issues = st.checkbox("有腎功能不全")
        
        # 自動判斷疾病階段
        if mmse >= 21:
            stage = "Mild (MMSE 21-26)"
        elif mmse >= 10:
            stage = "Moderate (MMSE 10-20)"
        else:
            stage = "Severe (MMSE <10)"
        
        st.write(f"### 目前疾病階段: {stage}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### 建議治療方案")
            
            treatments_with_sources = get_values_with_sources(df, [
                (df['x_name'] == stage),
                (df['relation'] == 'FIRST_LINE_TREATMENT')
            ])
            
            if treatments_with_sources:
                for treatment, source in treatments_with_sources:
                    st.write(f"#### {treatment}")
                    st.caption(f"來源: {source}")
                    
                    # 藥物資訊
                    drug, drug_source = get_value_with_source(df, [
                        (df['x_name'] == treatment),
                        (df['relation'] == 'USES_DRUG')
                    ])
                    
                    if drug != "資料不可用":
                        # 禁忌症檢查
                        contraindications_with_sources = get_values_with_sources(df, [
                            (df['x_name'] == drug),
                            (df['relation'] == 'CONTRAINDICATION')
                        ])
                        
                        for contraindication, contra_source in contraindications_with_sources:
                            if (has_cardiac_issues and "心" in contraindication) or \
                               (has_renal_issues and "腎" in contraindication):
                                st.error(f"⚠️ 警告: {contraindication}")
                                st.caption(f"來源: {contra_source}")
                    
                    # 劑量資訊
                    dosage, dosage_source = get_value_with_source(df, [
                        (df['x_name'] == treatment),
                        (df['relation'] == 'HAS_DOSAGE')
                    ])
                    st.write(f"- 建議劑量：{dosage}")
                    st.caption(f"來源: {dosage_source}")
            else:
                st.write("暫無治療建議資料")
        
        with col2:
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
                st.write("暫無非藥物治療建議資料")
    
    elif "3. 用藥安全查詢" in function_option:
        st.header("用藥安全查詢")
        
        drugs = df[df['y_type'] == 'Drug']['y_name'].unique()
        if len(drugs) > 0:
            selected_drug = st.selectbox("選擇要查詢的藥物", drugs)
            
            if selected_drug:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("### 用藥資訊")
                    treatments_with_sources = get_values_with_sources(df, [
                        (df['relation'] == 'USES_DRUG'),
                        (df['y_name'] == selected_drug)
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
                
                with col2:
                    st.write("### ⚠️ 安全性資訊")
                    
                    # 禁忌症
                    contraindications_with_sources = get_values_with_sources(df, [
                        (df['x_name'] == selected_drug),
                        (df['relation'] == 'CONTRAINDICATION')
                    ])
                    if contraindications_with_sources:
                        st.write("#### 禁忌症")
                        for contraindication, source in contraindications_with_sources:
                            st.error(f"- {contraindication}")
                            st.caption(f"來源: {source}")
                    
                    # 副作用
                    side_effects_with_sources = get_values_with_sources(df, [
                        (df['x_name'] == selected_drug),
                        (df['relation'] == 'HAS_SIDE_EFFECT')
                    ])
                    if side_effects_with_sources:
                        st.write("#### 常見副作用")
                        for side_effect, source in side_effects_with_sources:
                            st.warning(f"- {side_effect}")
                            st.caption(f"來源: {source}")
    
    elif "4. 治療建議" in function_option:
        st.header("治療建議")
        
        stages = df[df['relation'] == 'HAS_STAGE']['y_name'].unique()
        if len(stages) > 0:
            selected_stage = st.selectbox("選擇疾病階段", stages)
            
            if selected_stage:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("### 藥物治療策略")
                    treatments_with_sources = get_values_with_sources(df, [
                        (df['x_name'] == selected_stage),
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
                        st.write("暫無藥物治療建議資料")
                
                with col2:
                    st.write("### ���藥物介入")
                    therapies_with_sources = get_values_with_sources(df, [
                        (df['x_name'] == selected_stage),
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
                        st.write("暫無非藥物介入建議資料")
    
    elif "5. 臨床監測追蹤" in function_option:
        st.header("臨床監測追蹤")
        
        # 藥物治療監測
        st.write("### 藥物治療監測")
        monitoring_with_sources = get_values_with_sources(df, [
            (df['relation'] == 'MONITORING_REQUIRED')
        ])
        
        if monitoring_with_sources:
            for monitoring, source in monitoring_with_sources:
                st.info(f"- {monitoring}")
                st.caption(f"來源: {source}")
        else:
            st.write("暫無監測要求資料")
        
        # 停藥條件
        st.write("### 停藥條件")
        stop_conditions_with_sources = get_values_with_sources(df, [
            (df['relation'] == 'STOP_TREATMENT_CONDITION')
        ])
        
        if stop_conditions_with_sources:
            for condition, source in stop_conditions_with_sources:
                st.warning(f"- {condition}")
                st.caption(f"來源: {source}")
        else:
            st.write("暫無停藥條件資料")
    
    elif "6. 治療方案比較" in function_option:
        st.header("治療方案比較")
        
        # 獲取所有治療方案
        all_treatments = df[
            (df['relation'] == 'FIRST_LINE_TREATMENT') | 
            (df['relation'] == 'SECOND_LINE_TREATMENT')
        ]['y_name'].unique()
        
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
                with st.expander(f"📋 {treatment} 詳細資訊"):
                    # 基本信息
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
                    
                    # 禁忌症
                    if drug != "資料不可用":
                        contraindications_with_sources = get_values_with_sources(df, [
                            (df['x_name'] == drug),
                            (df['relation'] == 'CONTRAINDICATION')
                        ])
                        if contraindications_with_sources:
                            st.write("#### 禁忌症")
                            for contraindication, source in contraindications_with_sources:
                                st.write(f"- {contraindication}")
                                st.caption(f"來源：{source}")
                    
                    # 監測要求
                    monitoring_with_sources = get_values_with_sources(df, [
                        (df['x_name'] == treatment),
                        (df['relation'] == 'MONITORING_REQUIRED')
                    ])
                    if monitoring_with_sources:
                        st.write("#### 監測要求")
                        for monitoring, source in monitoring_with_sources:
                            st.write(f"- {monitoring}")
                            st.caption(f"來源：{source}")
        else:
            st.warning("請選擇至少一個治療方案進行比較")
    
    elif "7. 知識圖譜Schema" in function_option:
        st.header("知識圖譜Schema")
        
        # 顯示schema統計信息
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("節點類型數量", len(set(df['x_type'].unique()) | set(df['y_type'].unique())))
        with col2:
            st.metric("關係類型數量", len(df['relation'].unique()))
        with col3:
            st.metric("總三元組數量", len(df))
        
        # 顯示schema圖
        st.subheader("Schema視覺化")
        net = create_schema_visualization(df)
        
        # 保存和顯示圖形
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp_file:
            net.save_graph(tmp_file.name)
            with open(tmp_file.name, 'r', encoding='utf-8') as f:
                html_data = f.read()
            st.components.v1.html(html_data, height=600)
            os.unlink(tmp_file.name)
        
        # 顯示詳細的schema信息
        st.subheader("Schema詳細信息")
        
        relations = df.groupby(['x_type', 'relation', 'y_type']).size().reset_index(name='count')
        relations = relations.sort_values(['x_type', 'relation', 'y_type'])
        
        tabs = st.tabs(sorted(relations['x_type'].unique()))
        
        for i, x_type in enumerate(sorted(relations['x_type'].unique())):
            with tabs[i]:
                st.write(f"### 從 {x_type} 出發的關係")
                type_relations = relations[relations['x_type'] == x_type]
                
                formatted_relations = []
                for _, row in type_relations.iterrows():
                    formatted_relations.append({
                        '來源節點': row['x_type'],
                        '關係類型': row['relation'],
                        '目標節點': row['y_type'],
                        '關係數量': row['count']
                    })
                
                if formatted_relations:
                    st.table(pd.DataFrame(formatted_relations))
                
                # 顯示示例數據
                st.write("#### 示例數據")
                examples = df[df['x_type'] == x_type].head(3)
                for _, example in examples.iterrows():
                    st.write(f"- {example['x_name']} --[{example['relation']}]--> {example['y_name']}")
                    st.caption(f"來源: [{example['source_type']}]({example['source_link']}) ({example['source_date']})")
        
        # 顯示圖例
        st.sidebar.subheader("節點類型圖例")
        for node_type, color in COLOR_MAP.items():
            st.sidebar.markdown(
                f'<div style="display: flex; align-items: center;">'
                f'<div style="width: 20px; height: 20px; background-color: {color}; margin-right: 10px;"></div>'
                f'{node_type}</div>',
                unsafe_allow_html=True
            )

if __name__ == "__main__":
    main() 