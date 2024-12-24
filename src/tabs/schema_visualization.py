import streamlit as st
import pandas as pd
import tempfile
import os
from src.utils.visualization import create_schema_visualization
from src.constants import COLOR_MAP

def render_schema_details(df):
    """渲染Schema詳細資訊"""
    st.subheader("Schema詳細資訊")
    
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

def render(df):
    """渲染知識圖譜Schema頁面"""
    st.header("知識圖譜Schema")
    
    # 顯示schema統計資訊
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
    
    # 顯示圖例
    st.sidebar.subheader("節點類型圖例")
    for node_type, color in COLOR_MAP.items():
        st.sidebar.markdown(
            f'<div style="display: flex; align-items: center;">'
            f'<div style="width: 20px; height: 20px; background-color: {color}; margin-right: 10px;"></div>'
            f'{node_type}</div>',
            unsafe_allow_html=True
        )
    
    render_schema_details(df) 