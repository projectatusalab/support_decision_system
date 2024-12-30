import streamlit as st
from utils.data_loader import get_node_by_id, get_connected_nodes

def render_drug_treatment_strategy(nodes_df, relationships_df, stage_id):
    """渲染藥物治療策略部分"""
    st.write("### 藥物治療策略")
    
    # 獲取一線治療方案
    treatment_relations = relationships_df[
        (relationships_df[':START_ID'] == stage_id) &
        (relationships_df[':TYPE'] == 'FIRST_LINE_TREATMENT')
    ]
    
    treatments = []
    for _, rel in treatment_relations.iterrows():
        treatment_name, _ = get_node_by_id(nodes_df, rel[':END_ID'])
        if treatment_name:
            treatments.append(treatment_name)
    
    if treatments:
        for treatment in treatments:
            st.write(f"#### {treatment}")
            
            # 獲取使用的藥物
            treatment_id = nodes_df[nodes_df['name'] == treatment]['nodeID:ID'].iloc[0]
            drug_relations = relationships_df[
                (relationships_df[':START_ID'] == treatment_id) &
                (relationships_df[':TYPE'] == 'USES_DRUG')
            ]
            
            if not drug_relations.empty:
                drug_name, _ = get_node_by_id(nodes_df, drug_relations.iloc[0][':END_ID'])
                st.write(f"- 使用藥物：{drug_name if drug_name else '無資料'}")
            
            # 獲取預期效果
            effectiveness_relations = relationships_df[
                (relationships_df[':START_ID'] == treatment_id) &
                (relationships_df[':TYPE'] == 'HAS_EFFECTIVENESS')
            ]
            
            if not effectiveness_relations.empty:
                effect_name, _ = get_node_by_id(nodes_df, effectiveness_relations.iloc[0][':END_ID'])
                st.write(f"- 預期效果：{effect_name if effect_name else '無資料'}")
    else:
        st.info("暫無藥物治療建議資料")

def render_non_drug_interventions(nodes_df, relationships_df, stage_id):
    """渲染非藥物介入部分"""
    st.write("### 非藥物介入")
    
    # 獲取建議的治療方案
    therapy_relations = relationships_df[
        (relationships_df[':START_ID'] == stage_id) &
        (relationships_df[':TYPE'] == 'RECOMMENDED_THERAPY')
    ]
    
    therapies = []
    for _, rel in therapy_relations.iterrows():
        therapy_name, _ = get_node_by_id(nodes_df, rel[':END_ID'])
        if therapy_name:
            therapies.append(therapy_name)
    
    if therapies:
        for therapy in therapies:
            st.write(f"#### {therapy}")
            
            # 獲取預期效果
            therapy_id = nodes_df[nodes_df['name'] == therapy]['nodeID:ID'].iloc[0]
            effectiveness_relations = relationships_df[
                (relationships_df[':START_ID'] == therapy_id) &
                (relationships_df[':TYPE'] == 'HAS_EFFECTIVENESS')
            ]
            
            if not effectiveness_relations.empty:
                effect_name, _ = get_node_by_id(nodes_df, effectiveness_relations.iloc[0][':END_ID'])
                st.write(f"- 預期效果：{effect_name if effect_name else '無資料'}")
    else:
        st.info("暫無非藥物介入建議資料")

def render(data):
    """渲染治療建議頁面"""
    st.header("治療建議")
    
    nodes_df, relationships_df = data
    
    # 獲取所有疾病階段
    stage_nodes = nodes_df[nodes_df['type:LABEL'] == 'Stage']
    
    if not stage_nodes.empty:
        stage_names = stage_nodes['name'].tolist()
        selected_stage = st.selectbox("選擇疾病階段", stage_names)
        
        if selected_stage:
            # 獲取選中階段的ID
            stage_id = stage_nodes[stage_nodes['name'] == selected_stage]['nodeID:ID'].iloc[0]
            
            col1, col2 = st.columns(2)
            
            with col1:
                render_drug_treatment_strategy(nodes_df, relationships_df, stage_id)
            
            with col2:
                render_non_drug_interventions(nodes_df, relationships_df, stage_id)
    else:
        st.info("暫無疾病階段資料") 