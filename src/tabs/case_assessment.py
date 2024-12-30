import streamlit as st
from utils.data_loader import get_node_by_id, get_connected_nodes

def render_treatment_suggestions(nodes_df, relationships_df, stage_id, has_cardiac_issues, has_renal_issues):
    """渲染治療建議部分"""
    st.write("### 建議治療方案")
    
    # 獲取一線治療方案
    treatment_relations = relationships_df[
        (relationships_df[':START_ID'] == stage_id) &
        (relationships_df[':TYPE'] == 'FIRST_LINE_TREATMENT')
    ]
    
    treatments = []
    for _, rel in treatment_relations.iterrows():
        treatment_name, _ = get_node_by_id(nodes_df, rel[':END_ID'])
        if treatment_name:
            treatments.append((treatment_name, rel[':END_ID']))
    
    if treatments:
        for treatment_name, treatment_id in treatments:
            st.write(f"#### {treatment_name}")
            
            # 獲取使用的藥物
            drug_relations = relationships_df[
                (relationships_df[':START_ID'] == treatment_id) &
                (relationships_df[':TYPE'] == 'USES_DRUG')
            ]
            
            if not drug_relations.empty:
                drug_id = drug_relations.iloc[0][':END_ID']
                drug_name, _ = get_node_by_id(nodes_df, drug_id)
                
                if drug_name:
                    # 獲取禁忌症
                    contraindication_relations = relationships_df[
                        (relationships_df[':START_ID'] == drug_id) &
                        (relationships_df[':TYPE'] == 'CONTRAINDICATION')
                    ]
                    
                    for _, contra_rel in contraindication_relations.iterrows():
                        contra_name, _ = get_node_by_id(nodes_df, contra_rel[':END_ID'])
                        if contra_name:
                            if (has_cardiac_issues and "心" in contra_name) or \
                               (has_renal_issues and "腎" in contra_name):
                                st.error(f"⚠️ 警告: {contra_name}")
            
            # 獲取劑量建議
            dosage_relations = relationships_df[
                (relationships_df[':START_ID'] == treatment_id) &
                (relationships_df[':TYPE'] == 'HAS_DOSAGE')
            ]
            
            if not dosage_relations.empty:
                dosage_name, _ = get_node_by_id(nodes_df, dosage_relations.iloc[0][':END_ID'])
                st.write(f"- 建議劑量：{dosage_name if dosage_name else '無資料'}")
    else:
        st.info("暫無治療建議資料")

def render(data):
    """渲染個案評估頁面"""
    st.header("個案評估與治療")
    
    nodes_df, relationships_df = data
    
    # 使用已存在的 MMSE 分數
    mmse_score = st.session_state.get('mmse_score', 20)
    
    # 根據MMSE判斷疾病階段
    if mmse_score >= 21:
        current_stage = "Mild (MMSE 21-26)"
    elif mmse_score >= 10:
        current_stage = "Moderate (MMSE 10-20)"
    else:
        current_stage = "Severe (MMSE <10)"
    
    # 獲取所有疾病階段
    stage_nodes = nodes_df[nodes_df['type:LABEL'] == 'Stage']
    
    if not stage_nodes.empty:
        stage_names = stage_nodes['name'].tolist()
        selected_stage = st.selectbox("選擇疾病階段", stage_names, 
                                    index=stage_names.index(current_stage) if current_stage in stage_names else 0)
        
        # 共病評估
        st.subheader("共病評估")
        col1, col2 = st.columns(2)
        with col1:
            has_cardiac_issues = st.checkbox("有心臟疾病病史")
        with col2:
            has_renal_issues = st.checkbox("有腎臟功能問題")
        
        if selected_stage:
            # 獲取選中階段的ID
            stage_id = stage_nodes[stage_nodes['name'] == selected_stage]['nodeID:ID'].iloc[0]
            
            # 顯示治療建議
            render_treatment_suggestions(nodes_df, relationships_df, stage_id, 
                                      has_cardiac_issues, has_renal_issues)
    else:
        st.info("暫無疾病階段資料") 