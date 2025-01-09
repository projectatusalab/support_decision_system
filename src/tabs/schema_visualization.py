import streamlit as st
import pandas as pd
from utils.visualization import create_schema_visualization
from utils.data_loader import get_node_by_id
import plotly.express as px
import tempfile
import os
from utils.neo4j_loader import get_neo4j_loader

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
        relation_type_stats = relationships_df['predicate'].value_counts().reset_index()
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
                (relationships_df['subject'].isin(source_nodes['node_id'])) |
                (relationships_df['object'].isin(source_nodes['node_id']))
            ]
            
            # 統計每個來源的計數數量
            source_stats = []
            for _, source in source_nodes.iterrows():
                source_id = source['node_id']
                citation_count = len(source_relations[
                    (source_relations['subject'] == source_id) |
                    (source_relations['object'] == source_id)
                ])
                
                # 獲取被統計的節點類型統計
                cited_types = set()
                for _, rel in source_relations.iterrows():
                    if rel['subject'] == source_id:
                        node_name, node_type = get_node_by_id(nodes_df, rel['object'])
                        if node_type:
                            cited_types.add(node_type)
                    elif rel['object'] == source_id:
                        node_name, node_type = get_node_by_id(nodes_df, rel['subject'])
                        if node_type:
                            cited_types.add(node_type)
                
                # Use source_secondary for name if available
                source_name = source.get('source_secondary', source['name'])
                
                source_stats.append({
                    '來源名稱': source_name,
                    '計數': citation_count,
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
                        options=['來源名稱', '計數'],
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
                        "計數": st.column_config.NumberColumn(
                            "計數",
                            help="該來源的關聯總次數",
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
                    f"總計數 {source_df['計數'].sum()}，"
                    f"平均每個來源關聯 {source_df['計數'].mean():.2f} 次。"
                )
        else:
            st.info("暫無來源節點數據")
    
    with source_tabs[3]:
        st.write("### 來源名稱統計")
        
        # 獲取所有來源節點
        source_nodes = nodes_df[nodes_df['type'] == 'source']
        
        if not source_nodes.empty:
            # 創建treemap數據
            treemap_data = []
            for _, source in source_nodes.iterrows():
                source_id = source['node_id']
                primary = source.get('source_primary', 'Unknown')
                secondary = source.get('source_secondary', source.get('name', 'Unknown'))
                
                # 計算與該來源相關的節點數量
                related_nodes = set()
                related_relations = relationships_df[
                    (relationships_df['subject'] == source_id) |
                    (relationships_df['object'] == source_id)
                ]
                
                for _, rel in related_relations.iterrows():
                    if rel['subject'] == source_id:
                        related_nodes.add(rel['object'])
                    else:
                        related_nodes.add(rel['subject'])
                
                treemap_data.append({
                    'primary': primary,
                    'secondary': secondary,
                    'connected_nodes_count': len(related_nodes)
                })
            
            treemap_df = pd.DataFrame(treemap_data)
            
            # 顯示主要來源的圓餅圖
            st.write("#### 主要來源統計")
            primary_stats = treemap_df.groupby('primary')['connected_nodes_count'].sum().reset_index()
            primary_stats = primary_stats.sort_values('connected_nodes_count', ascending=False)
            
            fig_pie = px.pie(
                primary_stats,
                values='connected_nodes_count',
                names='primary',
                title='主要來源關聯節點數量分布',
                hover_data=['connected_nodes_count']
            )
            
            # 調整圓餅圖布局
            fig_pie.update_layout(
                height=500,
                margin=dict(t=30, l=10, r=10, b=10)
            )
            
            # 自定義hover文本
            fig_pie.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate="<b>%{label}</b><br>" +
                "關聯節點數量: %{customdata[0]}<br>" +
                "佔比: %{percent}<br>" +
                "<extra></extra>"
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
            
            # 顯示主要來源的詳細統計
            with st.expander("查看主要來源詳細統計"):
                st.dataframe(
                    primary_stats,
                    column_config={
                        "primary": st.column_config.TextColumn(
                            "主要來源",
                            help="主要來源名稱"
                        ),
                        "connected_nodes_count": st.column_config.NumberColumn(
                            "關聯節點數量",
                            help="該主要來源的關聯節點總數",
                            format="%d"
                        )
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                st.caption(
                    f"總共有 {len(primary_stats)} 個主要來源，"
                    f"總計關聯節點數量 {primary_stats['connected_nodes_count'].sum()}，"
                    f"平均每個主要來源關聯 {primary_stats['connected_nodes_count'].mean():.2f} 個節點。"
                )
            
            # 為每個主要來源創建單獨的treemap
            st.write("#### 各主要來源的次要來源分布")
            
            # 獲取所有主要來源
            primary_sources = sorted(treemap_df['primary'].unique())
            
            # 創建選擇框來選擇主要來源
            selected_primary = st.selectbox(
                "選擇主要來源查看詳細分布",
                options=primary_sources,
                format_func=lambda x: f"{x} (關聯節點數量: {primary_stats[primary_stats['primary'] == x]['connected_nodes_count'].iloc[0]})"
            )
            
            # 為選中的主要來源創建treemap
            filtered_df = treemap_df[treemap_df['primary'] == selected_primary]
            
            if not filtered_df.empty:
                fig_tree = px.treemap(
                    filtered_df,
                    path=[px.Constant(selected_primary), 'secondary'],
                    values='connected_nodes_count',
                    title=f'{selected_primary} 的次要來源分布',
                    custom_data=['connected_nodes_count']
                )
                
                # 自定義hover文本
                fig_tree.update_traces(
                    hovertemplate="<b>%{label}</b><br>" +
                    "關聯節點數量: %{customdata[0]}<br>" +
                    "<extra></extra>"
                )
                
                # 調整treemap布局
                fig_tree.update_layout(
                    height=500,
                    margin=dict(t=30, l=10, r=10, b=10)
                )
                
                st.plotly_chart(fig_tree, use_container_width=True)
                
                # 顯示該主要來源的詳細統計
                with st.expander(f"查看 {selected_primary} 的詳細統計"):
                    detailed_stats = filtered_df[['secondary', 'connected_nodes_count']].sort_values(
                        'connected_nodes_count', ascending=False
                    )
                    detailed_stats.columns = ['次要來源', '關聯節點數量']
                    st.dataframe(
                        detailed_stats,
                        hide_index=True,
                        use_container_width=True
                    )
                    
                    st.caption(
                        f"該主要來源共有 {len(detailed_stats)} 個次要來源，"
                        f"總計關聯節點數量 {detailed_stats['關聯節點數量'].sum()}，"
                        f"平均每個次要來源關聯 {detailed_stats['關聯節點數量'].mean():.2f} 個節點。"
                    )
            
            # 統計來源名稱出現次數
            name_counts = source_nodes['source_secondary'].fillna(source_nodes['name']).value_counts().reset_index()
            name_counts.columns = ['來源名稱', '出現次數']
            
            # 獲取每個來源關聯的節點類型統計
            source_type_stats = []
            for _, source in source_nodes.iterrows():
                source_id = source['node_id']
                source_name = source.get('source_secondary', source['name'])
                
                # 獲取與該來源相關的關係
                related_relations = relationships_df[
                    (relationships_df['subject'] == source_id) |
                    (relationships_df['object'] == source_id)
                ]
                
                # 統計相關節點的類型
                type_counts = {}
                for _, rel in related_relations.iterrows():
                    if rel['subject'] == source_id:
                        _, node_type = get_node_by_id(nodes_df, rel['object'])
                    else:
                        _, node_type = get_node_by_id(nodes_df, rel['subject'])
                    
                    if node_type:
                        type_counts[node_type] = type_counts.get(node_type, 0) + 1
                
                # 添加到統計數據中
                for node_type, count in type_counts.items():
                    source_type_stats.append({
                        '來源名稱': source_name,
                        '節點類型': node_type,
                        '計數': count
                    })
            
            if source_type_stats:
                # 創建DataFrame
                stats_df = pd.DataFrame(source_type_stats)
                
                # 創建熱力圖
                pivot_table = stats_df.pivot_table(
                    index='節點類型',
                    columns='來源名稱',
                    values='計數',
                    fill_value=0
                )
                
                # 顯示熱力圖
                st.write("#### 來源名稱與節點類型關聯關係")
                fig = px.imshow(
                    pivot_table,
                    labels=dict(x="來源名稱", y="節點類型", color="計數"),
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
                    
                    # 顯示節點類型統計
                    st.write("##### 節點類型統計")
                    type_summary = stats_df.groupby('節點類型')['計數'].sum().reset_index()
                    type_summary = type_summary.sort_values('計數', ascending=False)
                    st.dataframe(
                        type_summary,
                        column_config={
                            "節點類型": st.column_config.TextColumn(
                                "節點類型",
                                help="節點的類型"
                            ),
                            "計數": st.column_config.NumberColumn(
                                "計數",
                                help="該類型的關聯總次數",
                                format="%d"
                            )
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                
                # 顯示統計摘要
                total_sources = len(name_counts)
                total_types = len(type_summary)
                total_citations = type_summary['計數'].sum()
                st.caption(
                    f"總共有 {total_sources} 個不同的來源，"
                    f"關聯了 {total_types} 種不同的節點類型，"
                    f"總計數為 {total_citations}。"
                )

def render_schema_details(nodes_df, relationships_df):
    """渲染Schema詳細資訊"""
    st.write("### Schema 詳細資訊")
    
    # 顯示節點類型統計
    st.write("#### 節點類型統計")
    node_type_counts = nodes_df['type'].value_counts()
    st.bar_chart(node_type_counts)
    
    # 顯示關係類型統計
    st.write("#### 關係類型統計")
    rel_type_counts = relationships_df['predicate'].value_counts()
    st.bar_chart(rel_type_counts)
    
    # 顯示詳細統計表格
    with st.expander("查看詳細統計"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("節點類型分布")
            st.dataframe(
                node_type_counts.reset_index(),
                column_config={
                    "index": st.column_config.TextColumn(
                        "節點類型",
                        help="節點的類型"
                    ),
                    "type": st.column_config.NumberColumn(
                        "數量",
                        help="該類型的節點數量",
                        format="%d"
                    )
                },
                hide_index=True,
                use_container_width=True
            )
        
        with col2:
            st.write("關係類型分布")
            st.dataframe(
                rel_type_counts.reset_index(),
                column_config={
                    "index": st.column_config.TextColumn(
                        "關係類型",
                        help="關係的類型"
                    ),
                    "predicate": st.column_config.NumberColumn(
                        "數量",
                        help="該類型的關係數量",
                        format="%d"
                    )
                },
                hide_index=True,
                use_container_width=True
            )

def create_drug_source_heatmap(nodes_df, relationships_df, disease_node_id="n_4"):
    """創建藥物來源熱力圖"""
    # 使用Neo4j執行查詢
    loader = get_neo4j_loader()
    
    with loader.driver.session() as session:
        # 執行Cypher查詢
        query = """
        MATCH (d:disease{nodeID:$disease_id})-[r:indication]-(dr:drug)-[s:SOURCE]-(so:source)
        RETURN dr.name as drug_name, so.source_primary as source_primary, 
               so.source_secondary as source_secondary, count(*) as count
        """
        result = session.run(query, disease_id=disease_node_id)
        records = [dict(record) for record in result]
        
        if not records:
            return None
            
        # 創建DataFrame
        df = pd.DataFrame(records)
        
        # 創建多層次列標籤
        df['source'] = df.apply(lambda x: f"{x['source_primary']} - {x['source_secondary']}", axis=1)
        
        # 透過樞紐表創建熱力圖數據，交換index和columns
        pivot_df = df.pivot_table(
            values='count',
            index='source',  # 改為source作為行
            columns='drug_name',  # 改為drug_name作為列
            fill_value=0
        )
        
        return pivot_df

def render(data):
    """渲染知識圖譜Schema頁面"""
    st.header("知識圖譜Schema")
    
    nodes_df, relationships_df = data
    
    # 創建Schema視覺化
    st.write("### Schema 視覺化")
    schema_net = create_schema_visualization(data)
    
    # 創建臨時目錄並保存網絡圖
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = os.path.join(temp_dir, "temp_schema.html")
        schema_net.save_graph(temp_path)
        with open(temp_path, "r", encoding="utf-8") as f:
            schema_html = f.read()
        st.components.v1.html(schema_html, height=600)
    
    # 創建藥物來源熱力圖
    st.write("### 阿茲海默症藥物來源分布")
    pivot_df = create_drug_source_heatmap(nodes_df, relationships_df)
    
    if pivot_df is not None:
        # 創建熱力圖，交換x和y的標籤
        fig = px.imshow(
            pivot_df,
            labels=dict(x="藥物名稱", y="來源", color="計數"),
            aspect="auto",
            height=max(400, len(pivot_df) * 30)  # 根據來源數量調整高度
        )
        
        # 調整布局
        fig.update_layout(
            xaxis_tickangle=-45,  # 旋轉x軸標籤
            margin=dict(l=20, r=20, t=30, b=100),  # 調整邊距
            yaxis_title="來源",
            xaxis_title="藥物名稱",
            title="阿茲海默症藥物與來源關係分布"
        )
        
        # 顯示熱力圖
        st.plotly_chart(fig, use_container_width=True)
        
        # 顯示統計摘要
        total_sources = len(pivot_df)  # 現在是來源的數量
        total_drugs = len(pivot_df.columns)  # 現在是藥物的數量
        total_citations = pivot_df.sum().sum()
        
        st.caption(
            f"總共有 {total_drugs} 種藥物，"
            f"來自 {total_sources} 個不同的來源，"
            f"總計 {int(total_citations)} 個關聯。"
        )
        
        # 顯示詳細數據
        with st.expander("查看詳細數據"):
            st.dataframe(pivot_df)
    else:
        st.info("未找到阿茲海默症相關的藥物來源數據")
    
    # 顯示來源統計
    render_source_statistics(nodes_df, relationships_df)
    
    # 顯示Schema詳細資訊
    render_schema_details(nodes_df, relationships_df) 