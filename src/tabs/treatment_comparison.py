import streamlit as st
import pandas as pd
from utils.data_loader import get_node_by_id, get_connected_nodes

def render_treatment_details(nodes_df, relationships_df, treatment_id):
    """渲染治療方案詳細資訊"""
    # 獲取藥物資訊
    drug_relations = relationships_df[
        (relationships_df[':START_ID'] == treatment_id) &
        (relationships_df[':TYPE'] == 'USES_DRUG')
    ]
    
    drugs = []
    for _, rel in drug_relations.iterrows():
        drug_name, _ = get_node_by_id(nodes_df, rel[':END_ID'])
        if drug_name:
            drugs.append(drug_name)
    
    if drugs:
        st.write("#### 使用藥物")
        for drug in drugs:
            st.write(f"- {drug}")
    
    # 獲取效果資訊
    effectiveness_relations = relationships_df[
        (relationships_df[':START_ID'] == treatment_id) &
        (relationships_df[':TYPE'] == 'HAS_EFFECTIVENESS')
    ]
    
    if not effectiveness_relations.empty:
        st.write("#### 預期效果")
        for _, rel in effectiveness_relations.iterrows():
            effect_name, _ = get_node_by_id(nodes_df, rel[':END_ID'])
            if effect_name:
                st.write(f"- {effect_name}")
    
    # 獲取副作用資訊
    side_effect_relations = relationships_df[
        (relationships_df[':START_ID'] == treatment_id) &
        (relationships_df[':TYPE'] == 'HAS_SIDE_EFFECT')
    ]
    
    if not side_effect_relations.empty:
        st.write("#### 可能副作用")
        for _, rel in side_effect_relations.iterrows():
            effect_name, _ = get_node_by_id(nodes_df, rel[':END_ID'])
            if effect_name:
                st.warning(f"- {effect_name}")
    
    # 獲取適用階段
    stage_relations = relationships_df[
        (relationships_df[':END_ID'] == treatment_id) &
        (relationships_df[':TYPE'] == 'STAGE_TREATMENT')
    ]
    
    stages = []
    for _, rel in stage_relations.iterrows():
        stage_name, _ = get_node_by_id(nodes_df, rel[':START_ID'])
        if stage_name:
            stages.append(stage_name)
    
    if stages:
        st.write("#### 適用階段")
        for stage in stages:
            st.write(f"- {stage}")

def render(data):
    """渲染治療方案比較頁面"""
    st.header("治療方案比較")
    
    nodes_df, relationships_df = data
    
    # 獲取所有治療方案
    treatment_nodes = nodes_df[nodes_df['type:LABEL'] == 'Treatment']
    
    if not treatment_nodes.empty:
        # 選擇要比較的治療方案
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("治療方案 A")
            treatment_a = st.selectbox(
                "選擇第一個治療方案",
                treatment_nodes['name'].tolist(),
                key="treatment_a"
            )
            if treatment_a:
                treatment_a_id = treatment_nodes[treatment_nodes['name'] == treatment_a]['nodeID:ID'].iloc[0]
                render_treatment_details(nodes_df, relationships_df, treatment_a_id)
        
        with col2:
            st.subheader("治療方案 B")
            # 過濾掉已選擇的治療方案
            available_treatments = treatment_nodes[treatment_nodes['name'] != treatment_a]['name'].tolist()
            treatment_b = st.selectbox(
                "選擇第二個治療方案",
                available_treatments,
                key="treatment_b"
            )
            if treatment_b:
                treatment_b_id = treatment_nodes[treatment_nodes['name'] == treatment_b]['nodeID:ID'].iloc[0]
                render_treatment_details(nodes_df, relationships_df, treatment_b_id)
    else:
        st.info("暫無治療方案資料") 