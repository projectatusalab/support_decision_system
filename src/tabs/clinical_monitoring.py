import streamlit as st
from utils.data_loader import get_node_by_id, get_connected_nodes

def render_monitoring_requirements(nodes_df, relationships_df):
    """渲染監測要求部分"""
    st.write("### 藥物治療監測")
    
    # 獲取所有監測要求
    monitoring_relations = relationships_df[relationships_df[':TYPE'] == 'MONITORING_REQUIRED']
    monitoring_items = []
    
    for _, rel in monitoring_relations.iterrows():
        item_name, _ = get_node_by_id(nodes_df, rel[':END_ID'])
        if item_name:
            monitoring_items.append(item_name)
    
    if monitoring_items:
        for item in monitoring_items:
            st.info(f"- {item}")
    else:
        st.info("暫無監測要求資料")

def render_stop_conditions(nodes_df, relationships_df):
    """渲染停藥條件部分"""
    st.write("### 停藥條件")
    
    # 獲取所有停藥條件
    stop_relations = relationships_df[relationships_df[':TYPE'] == 'STOP_TREATMENT_CONDITION']
    stop_conditions = []
    
    for _, rel in stop_relations.iterrows():
        condition_name, _ = get_node_by_id(nodes_df, rel[':END_ID'])
        if condition_name:
            stop_conditions.append(condition_name)
    
    if stop_conditions:
        for condition in stop_conditions:
            st.warning(f"- {condition}")
    else:
        st.info("暫無停藥條件資料")

def render_follow_up_schedule(nodes_df, relationships_df):
    """渲染追蹤時程部分"""
    st.write("### 追蹤時程建議")
    
    # 獲取所有追蹤時程
    schedule_relations = relationships_df[relationships_df[':TYPE'] == 'FOLLOW_UP_SCHEDULE']
    schedules = []
    
    for _, rel in schedule_relations.iterrows():
        schedule_name, _ = get_node_by_id(nodes_df, rel[':END_ID'])
        if schedule_name:
            schedules.append(schedule_name)
    
    if schedules:
        for schedule in schedules:
            st.write(f"- {schedule}")
    else:
        st.info("暫無追蹤時程建議資料")

def render(data):
    """渲染臨床監測追蹤頁面"""
    st.header("臨床監測追蹤")
    
    nodes_df, relationships_df = data
    
    # 分三欄顯示不同類型的監測資訊
    col1, col2, col3 = st.columns(3)
    
    with col1:
        render_monitoring_requirements(nodes_df, relationships_df)
    
    with col2:
        render_stop_conditions(nodes_df, relationships_df)
    
    with col3:
        render_follow_up_schedule(nodes_df, relationships_df) 