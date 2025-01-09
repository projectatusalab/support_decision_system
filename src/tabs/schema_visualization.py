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
    source_tabs = st.tabs(["來源詳細統計", "來源名稱統計"])
    
    with source_tabs[0]:
        st.write("### 來源詳細統計")
        
        # 獲取所有來源節點
        source_nodes = nodes_df[nodes_df['type'] == 'source']
        
        if not source_nodes.empty:
            # Debug: 顯示可能的重複來源
            st.write("#### 來源節點原始數據檢查")
            debug_df = source_nodes[['node_id', 'name', 'source_primary', 'source_secondary']].copy()
            debug_df = debug_df[
                (debug_df['source_secondary'].str.contains('Cochrane Library', na=False)) |
                (debug_df['name'].str.contains('Cochrane Library', na=False)) |
                (debug_df['source_secondary'].str.contains('Evidence', na=False)) |
                (debug_df['name'].str.contains('Evidence', na=False))
            ]
            st.dataframe(debug_df)
            
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
                
                # Use source_secondary for name if available, also keep node_id for debugging
                source_name = source.get('source_secondary', source['name'])
                
                source_stats.append({
                    '來源名稱': source_name,
                    '節點ID': source_id,
                    '原始名稱': source['name'],
                    '主要來源': source.get('source_primary', ''),
                    '次要來源': source.get('source_secondary', ''),
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
                        options=['來源名稱', '計數', '主要來源', '次要來源'],
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
                        "節點ID": st.column_config.TextColumn(
                            "節點ID",
                            help="來源節點的唯一標識"
                        ),
                        "原始名稱": st.column_config.TextColumn(
                            "原始名稱",
                            help="節點的原始名稱"
                        ),
                        "主要來源": st.column_config.TextColumn(
                            "主要來源",
                            help="來源的主要分類"
                        ),
                        "次要來源": st.column_config.TextColumn(
                            "次要來源",
                            help="來源的次要分類"
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
    
    with source_tabs[1]:
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
            
            # 獲取所有主要來源，按關聯節點數量降序排序
            primary_sources = primary_stats['primary'].tolist()
            
            # 創建選擇框來選擇主要來源，使用排序後的列表
            selected_primary = st.selectbox(
                "選擇主要來源查看詳細分布",
                options=primary_sources,
                format_func=lambda x: f"{x} ({primary_stats[primary_stats['primary'] == x]['connected_nodes_count'].iloc[0]:,} 個關聯節點)"
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

def create_drug_source_heatmap(nodes_df, relationships_df, disease_node_id="n_4"):
    """創建藥物來源熱力圖"""
    # 使用Neo4j執行查詢
    loader = get_neo4j_loader()
    
    with loader.driver.session() as session:
        # 執行Cypher查詢，加入source_date
        query = """
        MATCH (d:disease{nodeID:$disease_id})-[r:indication]-(dr:drug)-[s:SOURCE]-(so:source)
        RETURN dr.name as drug_name, 
               so.source_primary as source_primary, 
               so.source_secondary as source_secondary,
               so.source_date as source_date,
               count(*) as count
        """
        result = session.run(query, disease_id=disease_node_id)
        records = [dict(record) for record in result]
        
        if not records:
            return None
            
        # 創建DataFrame
        df = pd.DataFrame(records)
        
        # 處理日期格式，如果日期為空則設為最早日期
        df['source_date'] = pd.to_datetime(df['source_date'], errors='coerce')
        df['source_date'] = df['source_date'].fillna(pd.Timestamp.min)
        
        # 創建多層次列標籤，包含日期
        df['source'] = df.apply(lambda x: (
            f"{x['source_primary']} - {x['source_secondary']} "
            f"({x['source_date'].strftime('%Y-%m-%d') if x['source_date'] != pd.Timestamp.min else 'No Date'})"
        ), axis=1)
        
        # 透過樞紐表創建熱力圖數據
        pivot_df = df.pivot_table(
            values='count',
            index='source',
            columns='drug_name',
            fill_value=0
        )
        
        # 按日期降序排序
        source_order = df.sort_values('source_date', ascending=False).drop_duplicates('source')['source']
        pivot_df = pivot_df.reindex(source_order)
        
        return pivot_df

def render(data):
    """渲染知識圖譜Schema頁面"""
    st.title("知識圖譜結構與統計分析")
    st.caption("本頁面提供知識圖譜的整體結構視覺化、統計分析以及來源分布情況")
    
    nodes_df, relationships_df = data
    
    # 創建主要標籤頁
    main_tabs = st.tabs([
        "圖譜結構", 
        "基礎統計", 
        "來源分布",
        "藥物來源"
    ])
    
    # Schema總覽標籤頁
    with main_tabs[0]:
        st.header("知識圖譜結構視覺化")
        st.subheader("節點類型與關係類型的互動式視圖")
        schema_net = create_schema_visualization(data)
        
        # 創建臨時目錄並保存網絡圖
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, "temp_schema.html")
            schema_net.save_graph(temp_path)
            with open(temp_path, "r", encoding="utf-8") as f:
                schema_html = f.read()
            st.components.v1.html(schema_html, height=600)
            
        st.info("👆 此視覺化展示了知識圖譜中各類型節點之間的關係結構。您可以：\n"
                "- 拖動節點調整布局\n"
                "- 懸停在節點或邊上查看詳細資訊")
    
    # 節點與關係統計標籤頁
    with main_tabs[1]:
        st.header("知識圖譜基礎統計")
        
        # 顯示總體統計
        st.subheader("整體規模")
        total_col1, total_col2, total_col3 = st.columns(3)
        with total_col1:
            st.metric("總節點數", f"{len(nodes_df):,}")
        with total_col2:
            st.metric("總關係數", f"{len(relationships_df):,}")
        with total_col3:
            st.metric("節點類型數", f"{len(nodes_df['type'].unique()):,}")
        
        st.markdown("---")
        
        # 創建兩列布局
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("節點類型分布")
            node_type_stats = nodes_df['type'].value_counts().reset_index()
            node_type_stats.columns = ['節點類型', '數量']
            
            # 創建樹狀圖
            fig_node = px.treemap(
                node_type_stats,
                path=['節點類型'],
                values='數量',
                custom_data=['數量'],
                color='數量',
                color_continuous_scale='Blues'
            )
            
            # 自定義hover文本
            fig_node.update_traces(
                hovertemplate="<b>%{label}</b><br>" +
                "數量: %{customdata[0]}<br>" +
                "佔比: %{percentParent:.1%}<br>" +
                "<extra></extra>"
            )
            
            # 調整布局
            fig_node.update_layout(
                height=400,
                margin=dict(t=0, l=0, r=0, b=0)
            )
            
            st.plotly_chart(fig_node, use_container_width=True)
            
            # 顯示詳細數據
            with st.expander("查看詳細數據"):
                st.dataframe(
                    node_type_stats,
                    column_config={
                        "節點類型": st.column_config.TextColumn(
                            "節點類型",
                            help="知識圖譜中的節點類型"
                        ),
                        "數量": st.column_config.NumberColumn(
                            "數量",
                            help="該類型的節點數量",
                            format="%d"
                        )
                    },
                    hide_index=True
                )
        
        with col2:
            st.subheader("關係類型分布")
            relation_type_stats = relationships_df['predicate'].value_counts().reset_index()
            relation_type_stats.columns = ['關係類型', '數量']
            
            # 創建樹狀圖
            fig_rel = px.treemap(
                relation_type_stats,
                path=['關係類型'],
                values='數量',
                custom_data=['數量'],
                color='數量',
                color_continuous_scale='Oranges'
            )
            
            # 自定義hover文本
            fig_rel.update_traces(
                hovertemplate="<b>%{label}</b><br>" +
                "數量: %{customdata[0]}<br>" +
                "佔比: %{percentParent:.1%}<br>" +
                "<extra></extra>"
            )
            
            # 調整布局
            fig_rel.update_layout(
                height=400,
                margin=dict(t=0, l=0, r=0, b=0)
            )
            
            st.plotly_chart(fig_rel, use_container_width=True)
            
            # 顯示詳細數據
            with st.expander("查看詳細數據"):
                st.dataframe(
                    relation_type_stats,
                    column_config={
                        "關係類型": st.column_config.TextColumn(
                            "關係類型",
                            help="知識圖譜中的關係類型"
                        ),
                        "數量": st.column_config.NumberColumn(
                            "數量",
                            help="該類型的關係數量",
                            format="%d"
                        )
                    },
                    hide_index=True
                )
    
    # 來源分析標籤頁
    with main_tabs[2]:
        st.header("知識圖譜來源分析")
        st.caption("分析知識圖譜中各個來源的分布情況及其關聯統計")
        render_source_statistics(nodes_df, relationships_df)
    
    # 藥物來源分析標籤頁
    with main_tabs[3]:
        st.header("阿茲海默症藥物來源分析")
        st.caption("針對阿茲海默症相關藥物的來源分布進行深入分析")
        pivot_df = create_drug_source_heatmap(nodes_df, relationships_df)
        
        if pivot_df is not None:
            # 顯示統計摘要
            st.subheader("概況統計")
            drug_col1, drug_col2, drug_col3 = st.columns(3)
            with drug_col1:
                st.metric("藥物數量", f"{len(pivot_df.columns):,}")
            with drug_col2:
                st.metric("來源數量", f"{len(pivot_df):,}")
            with drug_col3:
                st.metric("總關聯數", f"{int(pivot_df.sum().sum()):,}")
            
            st.markdown("---")
            
            st.subheader("藥物-來源關係熱力圖")
            st.caption("來源按日期降序排列，格式為：主要來源 - 次要來源 (日期)")
            
            # 創建熱力圖，交換x和y的標籤
            fig = px.imshow(
                pivot_df,
                labels=dict(x="藥物名稱", y="來源", color="關聯次數"),
                aspect="auto",
                height=max(400, len(pivot_df) * 30),  # 根據來源數量調整高度
                color_continuous_scale=[[0, 'white'],
                                     [0.01, 'rgb(49,130,189)'],
                                     [1, 'rgb(0,0,139)']]  # 從白色到深藍色
            )
            
            # 調整布局
            fig.update_layout(
                xaxis_tickangle=-45,  # 旋轉x軸標籤
                margin=dict(l=20, r=20, t=30, b=100),  # 調整邊距
                yaxis_title="來源",
                xaxis_title="藥物名稱"
            )
            
            # 添加網格線
            fig.update_traces(
                xgap=2,  # x方向的間距
                ygap=2,  # y方向的間距
            )
            
            # 顯示熱力圖
            st.plotly_chart(fig, use_container_width=True)
            
            # 顯示詳細數據
            with st.expander("查看詳細數據"):
                st.dataframe(pivot_df)
        else:
            st.info("未找到阿茲海默症相關的藥物來源數據") 