import streamlit as st
import pandas as pd
from utils.visualization import create_schema_visualization
from utils.data_loader import get_node_by_id
import plotly.express as px

def render_source_statistics(nodes_df, relationships_df):
    """渲染來源統計資訊"""
    st.write("### 數據來源統計")
    
    # 創建來源統計標籤頁
    source_tabs = st.tabs(["節點來源統計", "關係來源統計", "來源詳細統計", "來源名稱統計"])
    
    with source_tabs[0]:
        st.write("### 節點類型統計")
        
        # 計算每種類型的節點數量
        node_type_stats = nodes_df['type'].value_counts().reset_index()
        node_type_stats.columns = ['節點類型', '數量']
        
        # 顯示節點類型統計圖表
        st.bar_chart(node_type_stats.set_index('節點類型'))
        
        # 顯示詳細數據
        with st.expander("查看詳細數據"):
            st.dataframe(node_type_stats)
    
    with source_tabs[1]:
        st.write("### 關係類型統計")
        
        # 計算每種類型的關係數量
        relation_type_stats = relationships_df['TYPE'].value_counts().reset_index()
        relation_type_stats.columns = ['關係類型', '數量']
        
        # 顯示關係類型統計圖表
        st.bar_chart(relation_type_stats.set_index('關係類型'))
        
        # 顯示詳細數據
        with st.expander("查看詳細數據"):
            st.dataframe(relation_type_stats)
    
    with source_tabs[2]:
        st.write("### 來源詳細統計")
        
        # 獲取所有來源節點
        source_nodes = nodes_df[nodes_df['type'] == 'source']
        
        if not source_nodes.empty:
            # 獲取與來源相關的關係
            source_relations = relationships_df[
                (relationships_df['START_ID'].isin(source_nodes['nodeID:ID'])) |
                (relationships_df['END_ID'].isin(source_nodes['nodeID:ID']))
            ]
            
            # 統計每個來源的引用數量
            source_stats = []
            for _, source in source_nodes.iterrows():
                source_id = source['nodeID:ID']
                citation_count = len(source_relations[
                    (source_relations['START_ID'] == source_id) |
                    (source_relations['END_ID'] == source_id)
                ])
                
                # 獲取被引用的節點類型統計
                cited_types = set()
                for _, rel in source_relations.iterrows():
                    if rel['START_ID'] == source_id:
                        node_name, node_type = get_node_by_id(nodes_df, rel['END_ID'])
                        if node_type:
                            cited_types.add(node_type)
                    elif rel['END_ID'] == source_id:
                        node_name, node_type = get_node_by_id(nodes_df, rel['START_ID'])
                        if node_type:
                            cited_types.add(node_type)
                
                source_stats.append({
                    '來源名稱': source['name'],
                    '引用次數': citation_count,
                    '關聯節點類型': ', '.join(sorted(cited_types)) if cited_types else '無'
                })
            
            if source_stats:
                # 創建DataFrame並顯示
                source_df = pd.DataFrame(source_stats)
                
                # 添加排序選項
                sort_col, sort_order = st.columns([2, 1])
                with sort_col:
                    sort_by = st.selectbox(
                        "排序依據",
                        options=['來源名稱', '引用次數'],
                        key="source_sort_by"
                    )
                with sort_order:
                    ascending = st.checkbox("升序排列", value=True, key="source_sort_order")
                
                # 應用排序
                source_df = source_df.sort_values(by=sort_by, ascending=ascending)
                
                # 顯示表格
                st.dataframe(
                    source_df,
                    column_config={
                        "來源名稱": st.column_config.TextColumn(
                            "來源名稱",
                            help="引用來源的名稱"
                        ),
                        "引用次數": st.column_config.NumberColumn(
                            "引用次數",
                            help="該來源被引用的總次數",
                            format="%d"
                        ),
                        "關聯節點類型": st.column_config.TextColumn(
                            "關聯節點類型",
                            help="與該來源相關聯的節點類型"
                        )
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                # 顯示統計摘要
                st.caption(
                    f"總共有 {len(source_nodes)} 個來源，"
                    f"總引用次數 {source_df['引用次數'].sum()}，"
                    f"平均每個來源被引用 {source_df['引用次數'].mean():.2f} 次。"
                )
        else:
            st.info("暫無來源節點數據")
    
    with source_tabs[3]:
        st.write("### 來源名稱統計")
        
        # 獲取所有來源節點
        source_nodes = nodes_df[nodes_df['type'] == 'source']
        
        if not source_nodes.empty:
            # 統計來源名稱出現次數
            name_counts = source_nodes['name'].value_counts().reset_index()
            name_counts.columns = ['來源名稱', '出現次數']
            
            # 獲取每個來源引用的節點類型統計
            source_type_stats = []
            for _, source in source_nodes.iterrows():
                source_id = source['nodeID:ID']
                source_name = source['name']
                
                # 獲取與該來源相關的關係
                related_relations = relationships_df[
                    (relationships_df['START_ID'] == source_id) |
                    (relationships_df['END_ID'] == source_id)
                ]
                
                # 統計相關節點的類型
                type_counts = {}
                for _, rel in related_relations.iterrows():
                    if rel['START_ID'] == source_id:
                        _, node_type = get_node_by_id(nodes_df, rel['END_ID'])
                    else:
                        _, node_type = get_node_by_id(nodes_df, rel['START_ID'])
                    
                    if node_type:
                        type_counts[node_type] = type_counts.get(node_type, 0) + 1
                
                # 添加到統計數據中
                for node_type, count in type_counts.items():
                    source_type_stats.append({
                        '來源名稱': source_name,
                        '節點類型': node_type,
                        '引用次數': count
                    })
            
            if source_type_stats:
                # 創建DataFrame
                stats_df = pd.DataFrame(source_type_stats)
                
                # 創建熱力圖
                pivot_table = stats_df.pivot_table(
                    index='節點類型',
                    columns='來源名稱',
                    values='引用次數',
                    fill_value=0
                )
                
                # 顯示熱力圖
                st.write("#### 來源名稱與節點類型引用關係")
                fig = px.imshow(
                    pivot_table,
                    labels=dict(x="來源名稱", y="節點類型", color="引用次數"),
                    aspect="auto",
                    height=400
                )
                # 調整布局
                fig.update_layout(
                    xaxis_tickangle=-45,  # 旋轉x軸標籤
                    margin=dict(l=20, r=20, t=30, b=100)  # 調整邊距
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # 顯示詳細數據
                with st.expander("查看詳細數據"):
                    # 顯示來源名稱統計
                    st.write("##### 來源名稱出現次數")
                    st.dataframe(
                        name_counts,
                        column_config={
                            "來源名稱": st.column_config.TextColumn(
                                "來源名稱",
                                help="來源的名稱"
                            ),
                            "出現次數": st.column_config.NumberColumn(
                                "出現次數",
                                help="該來源名稱出現的次數",
                                format="%d"
                            )
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                    
                    # 顯示節點類型引用統計
                    st.write("##### 節點類型引用統計")
                    type_summary = stats_df.groupby('節點類型')['引用次數'].sum().reset_index()
                    type_summary = type_summary.sort_values('引用次數', ascending=False)
                    st.dataframe(
                        type_summary,
                        column_config={
                            "節點類型": st.column_config.TextColumn(
                                "節點類型",
                                help="節點的類型"
                            ),
                            "引用次數": st.column_config.NumberColumn(
                                "引用次數",
                                help="該類型被引用的總次數",
                                format="%d"
                            )
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                
                # 顯示統計摘要
                total_sources = len(name_counts)
                total_types = len(type_summary)
                total_citations = type_summary['引用次數'].sum()
                st.caption(
                    f"總共有 {total_sources} 個不同的來源，"
                    f"引用了 {total_types} 種不同的節點類型，"
                    f"總引用次數為 {total_citations}。"
                )

def render_schema_details(nodes_df, relationships_df):
    """渲染Schema詳細資訊"""
    st.write("### Schema 詳細資訊")
    
    # 獲取所有關係類型的統計
    schema_data = []
    for _, rel in relationships_df.groupby(['TYPE']).size().reset_index(name='關係數量').iterrows():
        # 獲取當前關係類型的所有關係
        current_relations = relationships_df[relationships_df['TYPE'] == rel['TYPE']]
        
        # 獲取起始和目標節點類型
        start_types = set()
        end_types = set()
        for _, curr_rel in current_relations.iterrows():
            _, start_type = get_node_by_id(nodes_df, curr_rel['START_ID'])
            _, end_type = get_node_by_id(nodes_df, curr_rel['END_ID'])
            if start_type and end_type:
                start_types.add(start_type)
                end_types.add(end_type)
        
        for start_type in start_types:
            for end_type in end_types:
                # 計算這種特定組合的關係數量
                specific_count = 0
                for _, curr_rel in current_relations.iterrows():
                    start_node = nodes_df[nodes_df['nodeID:ID'] == curr_rel['START_ID']]
                    end_node = nodes_df[nodes_df['nodeID:ID'] == curr_rel['END_ID']]
                    if not start_node.empty and not end_node.empty:
                        if start_node.iloc[0]['type'] == start_type and end_node.iloc[0]['type'] == end_type:
                            specific_count += 1
                
                schema_data.append({
                    '來源節點類型': start_type,
                    '關係類型': rel['TYPE'],
                    '目標節點類型': end_type,
                    '關係數量': specific_count
                })
    
    # 創建DataFrame並顯示
    if schema_data:
        schema_df = pd.DataFrame(schema_data)
        
        # 添加排序選項
        sort_col, sort_order = st.columns([2, 1])
        with sort_col:
            sort_by = st.selectbox(
                "排序依據",
                options=['來源節點類型', '關係類型', '目標節點類型', '關係數量'],
                key="schema_sort_by"
            )
        with sort_order:
            ascending = st.checkbox("升序排列", value=True, key="schema_sort_order")
        
        # 應用排序
        schema_df = schema_df.sort_values(by=sort_by, ascending=ascending)
        
        # 顯示表格
        st.dataframe(
            schema_df,
            column_config={
                "來源節點類型": st.column_config.TextColumn(
                    "來源節點類型",
                    help="關係的起始節點類型"
                ),
                "關係類型": st.column_config.TextColumn(
                    "關係類型",
                    help="節點間的關係類型"
                ),
                "目標節點類型": st.column_config.TextColumn(
                    "目標節點類型",
                    help="關係的目標節點類型"
                ),
                "關係數量": st.column_config.NumberColumn(
                    "關係數量",
                    help="該類型關係的數量",
                    format="%d"
                )
            },
            hide_index=True,
            use_container_width=True
        )
        
        # 顯示統計摘要
        st.caption(
            f"總共有 {len(nodes_df['type'].unique())} 種節點類型，"
            f"{len(relationships_df['TYPE'].unique())} 種關係類型，"
            f"以及 {len(schema_df)} 種不同的關係組合。"
        )

def render(data):
    """渲染知識圖譜Schema頁面"""
    st.header("知識圖譜Schema")
    
    nodes_df, relationships_df = data
    
    # 顯示Schema視覺化
    st.write("### Schema 視覺化")
    schema_net = create_schema_visualization(data)
    schema_net.save_graph("temp_schema.html")
    with open("temp_schema.html", "r", encoding="utf-8") as f:
        schema_html = f.read()
    st.components.v1.html(schema_html, height=600)
    
    # 顯示來源統計
    render_source_statistics(nodes_df, relationships_df)
    
    # 顯示Schema詳細資訊
    render_schema_details(nodes_df, relationships_df) 