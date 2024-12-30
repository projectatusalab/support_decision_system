import streamlit as st
from utils.data_loader import get_node_by_id, get_connected_nodes

def render_drug_info(nodes_df, relationships_df, drug_id):
    """渲染藥物資訊部分"""
    st.write("### 用藥資訊")
    
    # 獲取使用該藥物的治療方案
    treatments = []
    treatment_relations = relationships_df[
        (relationships_df[':END_ID'] == drug_id) &
        (relationships_df[':TYPE'] == 'USES_DRUG')
    ]
    
    for _, rel in treatment_relations.iterrows():
        treatment_name, _ = get_node_by_id(nodes_df, rel[':START_ID'])
        if treatment_name:
            treatments.append(treatment_name)
    
    if treatments:
        for treatment in treatments:
            st.write(f"#### {treatment}")
            
            # 獲取劑量信息
            dosage_relations = relationships_df[
                (relationships_df[':START_ID'] == drug_id) &
                (relationships_df[':TYPE'] == 'HAS_DOSAGE')
            ]
            
            if not dosage_relations.empty:
                dosage_name, _ = get_node_by_id(nodes_df, dosage_relations.iloc[0][':END_ID'])
                st.write(f"- 建議劑量：{dosage_name if dosage_name else '無資料'}")
    else:
        st.info("暫無用藥資訊")

def render_safety_info(nodes_df, relationships_df, drug_id):
    """渲染安全性資訊部分"""
    st.write("### ⚠️ 安全性資訊")
    
    # 禁忌症
    contraindications = []
    contraindication_relations = relationships_df[
        (relationships_df[':START_ID'] == drug_id) &
        (relationships_df[':TYPE'] == 'CONTRAINDICATION')
    ]
    
    for _, rel in contraindication_relations.iterrows():
        contra_name, _ = get_node_by_id(nodes_df, rel[':END_ID'])
        if contra_name:
            contraindications.append(contra_name)
    
    if contraindications:
        st.write("#### 禁忌症")
        for contraindication in contraindications:
            st.error(f"- {contraindication}")
    
    # 副作用
    side_effects = []
    side_effect_relations = relationships_df[
        (relationships_df[':START_ID'] == drug_id) &
        (relationships_df[':TYPE'] == 'HAS_SIDE_EFFECT')
    ]
    
    for _, rel in side_effect_relations.iterrows():
        effect_name, _ = get_node_by_id(nodes_df, rel[':END_ID'])
        if effect_name:
            side_effects.append(effect_name)
    
    if side_effects:
        st.write("#### 常見副作用")
        for side_effect in side_effects:
            st.warning(f"- {side_effect}")

def render(data):
    """渲染用藥安全查詢頁面"""
    st.header("用藥安全查詢")
    
    nodes_df, relationships_df = data
    
    # 獲取所有藥物節點
    drug_nodes = nodes_df[nodes_df['type:LABEL'] == 'Drug']
    
    if not drug_nodes.empty:
        drug_names = drug_nodes['name'].tolist()
        selected_drug = st.selectbox("選擇要查詢的藥物", drug_names)
        
        if selected_drug:
            # 獲取選中藥物的ID
            drug_id = drug_nodes[drug_nodes['name'] == selected_drug]['nodeID:ID'].iloc[0]
            
            col1, col2 = st.columns(2)
            
            with col1:
                render_drug_info(nodes_df, relationships_df, drug_id)
            
            with col2:
                render_safety_info(nodes_df, relationships_df, drug_id)
    else:
        st.info("暫無藥物資料") 