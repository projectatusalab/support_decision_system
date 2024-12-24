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

def render_source_statistics(df):
    """渲染來源統計資訊"""
    st.subheader("來源統計資訊")
    
    # 確保數據類型一致性
    df = df.copy()
    df['x_source'] = df['x_source'].fillna('').astype(str)
    df['y_source'] = df['y_source'].fillna('').astype(str)
    df['source_type'] = df['source_type'].fillna('未知來源').astype(str)
    
    # 統計 x_type 和 source_type 的關係，並包含原始來源資訊
    x_source_stats = df.groupby(['x_type', 'source_type'], as_index=False).agg(
        original_source=('x_source', lambda x: ', '.join(sorted(set(filter(None, x))))),
        count=('x_name', 'count')  # 使用 x_name 來計數
    )
    
    # 統計 y_type 和 source_type 的關係，並包含原始來源資訊
    y_source_stats = df.groupby(['y_type', 'source_type'], as_index=False).agg(
        original_source=('y_source', lambda x: ', '.join(sorted(set(filter(None, x))))),
        count=('y_name', 'count')  # 使用 y_name 來計數
    )
    
    # 創建兩個標籤頁來顯示統計結果
    source_tabs = st.tabs(["來源節點統計", "目標節點統計"])
    
    with source_tabs[0]:
        st.write("### 來源節點(x)與資料來源的關係")
        
        # 處理未知來源的原始來源資訊
        def format_source(row):
            if row['source_type'] == "未知來源" and row['original_source']:
                return f"{row['original_source']}"
            return row['source_type']
        
        x_source_stats['source_type'] = x_source_stats.apply(format_source, axis=1)
        
        # 創建樞紐表以準備堆疊條形圖數據
        pivot_data = x_source_stats.pivot(
            index='x_type',
            columns='source_type',
            values='count'
        ).fillna(0)
        
        # 按總數排序
        pivot_data['total'] = pivot_data.sum(axis=1)
        pivot_data = pivot_data.sort_values('total', ascending=True)
        pivot_data = pivot_data.drop('total', axis=1)
        
        # 繪製堆疊條形圖
        st.bar_chart(pivot_data)
        
        # 顯示詳細數據
        with st.expander("查看詳細數據"):
            st.dataframe(pivot_data)
    
    with source_tabs[1]:
        st.write("### 目標節點(y)與資料來源的關係")
        
        # 處理未知來源的原始來源資訊
        y_source_stats['source_type'] = y_source_stats.apply(format_source, axis=1)
        
        # 創建樞紐表以準備堆疊條形圖數據
        pivot_data = y_source_stats.pivot(
            index='y_type',
            columns='source_type',
            values='count'
        ).fillna(0)
        
        # 按總數排序
        pivot_data['total'] = pivot_data.sum(axis=1)
        pivot_data = pivot_data.sort_values('total', ascending=True)
        pivot_data = pivot_data.drop('total', axis=1)
        
        # 繪製堆疊條形圖
        st.bar_chart(pivot_data)
        
        # 顯示詳細數據
        with st.expander("查看詳細數據"):
            st.dataframe(pivot_data)

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
    render_source_statistics(df)  # 新增來源統計顯示 