import streamlit as st
from utils.data_loader import get_values_with_sources

def render_monitoring_requirements(df):
    """渲染監測要求部分"""
    st.write("### 藥物治療監測")
    monitoring_with_sources = get_values_with_sources(df, [
        (df['relation'] == 'MONITORING_REQUIRED')
    ])
    
    if monitoring_with_sources:
        for monitoring, source in monitoring_with_sources:
            st.info(f"- {monitoring}")
            st.caption(f"來源: {source}")
    else:
        st.info("暫無監測要求資料")

def render_stop_conditions(df):
    """渲染停藥條件部分"""
    st.write("### 停藥條件")
    stop_conditions_with_sources = get_values_with_sources(df, [
        (df['relation'] == 'STOP_TREATMENT_CONDITION')
    ])
    
    if stop_conditions_with_sources:
        for condition, source in stop_conditions_with_sources:
            st.warning(f"- {condition}")
            st.caption(f"來源: {source}")
    else:
        st.info("暫無停藥條件資料")

def render_follow_up_schedule(df):
    """渲染追蹤時程部分"""
    st.write("### 追��時程建議")
    schedules_with_sources = get_values_with_sources(df, [
        (df['relation'] == 'FOLLOW_UP_SCHEDULE')
    ])
    
    if schedules_with_sources:
        for schedule, source in schedules_with_sources:
            st.write(f"- {schedule}")
            st.caption(f"來源: {source}")
    else:
        st.info("暫無追蹤時程建議資料")

def render(df):
    """渲染臨床監測追蹤頁面"""
    st.header("臨床監測追蹤")
    
    # 分三欄顯示不同類型的監測資訊
    col1, col2, col3 = st.columns(3)
    
    with col1:
        render_monitoring_requirements(df)
    
    with col2:
        render_stop_conditions(df)
    
    with col3:
        render_follow_up_schedule(df) 