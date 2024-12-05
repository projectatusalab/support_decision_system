import streamlit as st
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
from pyvis.network import Network
import tempfile
import os

# 設置頁面配置
st.set_page_config(page_title="醫療知識圖譜決策支持系統", layout="wide")

# 讀取數據
@st.cache_data
def load_data():
    df = pd.read_csv('alzheimer_kg.csv')
    return df

# 創建知識圖譜
def create_knowledge_graph(df, central_node=None, filter_type=None):
    G = nx.Graph()
    
    for _, row in df.iterrows():
        if filter_type and row['y_type'] != filter_type:
            continue
        # 添加節點
        G.add_node(row['x_name'], 
                  node_type=row['x_type'],
                  source=row['x_source'])
        G.add_node(row['y_name'], 
                  node_type=row['y_type'],
                  source=row['y_source'])
        # 添加邊
        G.add_edge(row['x_name'], 
                  row['y_name'], 
                  relationship=row['display_relation'])
    
    return G

def create_network_visualization(G):
    net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="black")
    
    # 為不同類型的節點設置不同的顏色
    color_map = {
        'Disease': '#FF6B6B',
        'Symptom': '#4ECDC4',
        'Treatment': '#45B7D1',
        'Diagnostic Test': '#96CEB4',
        'Biomarker': '#FFEEAD',
        'Gene': '#D4A5A5',
        'Risk Factor': '#FFE66D'
    }
    
    for node in G.nodes():
        node_type = G.nodes[node]['node_type']
        color = color_map.get(node_type, '#CCCCCC')
        net.add_node(node, label=node, title=node_type, color=color)
    
    for edge in G.edges():
        net.add_edge(edge[0], edge[1], title=G.edges[edge]['relationship'])
    
    return net

def create_schema_visualization(df):
    # 創建schema圖
    net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="black")
    
    # 獲取所有唯一的節點類型
    node_types = set(df['x_type'].unique()) | set(df['y_type'].unique())
    
    # 為節點類型設置顏色
    color_map = {
        'Disease': '#FF6B6B',
        'Symptom': '#4ECDC4',
        'Treatment': '#45B7D1',
        'Diagnostic Test': '#96CEB4',
        'Biomarker': '#FFEEAD',
        'Gene': '#D4A5A5',
        'Risk Factor': '#FFE66D',
        'Side Effect': '#FFB6C1',
        'Evidence Level': '#98FB98',
        'Condition': '#DDA0DD',
        'Drug': '#87CEEB',
        'Intervention': '#F0E68C'
    }
    
    # 添加節點
    for node_type in node_types:
        color = color_map.get(node_type, '#CCCCCC')
        net.add_node(node_type, label=node_type, color=color, size=30)
    
    # 獲取所有唯一的關係類型
    relations = df.groupby(['x_type', 'y_type', 'relation']).size().reset_index()
    
    # 添加邊
    for _, row in relations.iterrows():
        net.add_edge(row['x_type'], row['y_type'], title=row['relation'], label=row['relation'])
    
    return net

# 主應用
def main():
    st.title("醫療知識圖譜決策支持系統")
    
    # 載入數據
    df = load_data()
    
    # 側邊欄：功能選擇
    st.sidebar.title("功能選單")
    function_option = st.sidebar.selectbox(
        "選擇功能",
        ["0. 知識圖譜Schema",
         "1. 診斷支持",
         "2. 治療決策支持",
         "3. 藥物建議與交互檢測",
         "4. 罕見病診療輔助",
         "5. 臨床決策透明化與溝通支持",
         "6. 臨床研究與教學輔助"]
    )
    
    # 主要內容區域
    if "0. 知識圖譜Schema" in function_option:
        st.header("知識圖譜Schema")
        
        # 顯示schema統計信息
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
        
        # 顯示詳細的schema信息
        st.subheader("Schema詳細信息")
        
        # 顯示所有關係類型及其連接的節點類型
        relations = df.groupby(['x_type', 'relation', 'y_type']).size().reset_index(name='count')
        relations = relations.sort_values(['x_type', 'relation', 'y_type'])
        
        # 格式化顯示
        for x_type in sorted(relations['x_type'].unique()):
            st.write(f"### {x_type}")
            type_relations = relations[relations['x_type'] == x_type]
            for _, row in type_relations.iterrows():
                st.write(f"- {row['relation']} → {row['y_type']} ({row['count']} instances)")
    
    elif "1. 診斷支持" in function_option:
        st.header("診斷支持")
        
        # 症狀檢查清單
        st.subheader("症狀檢查")
        symptoms = df[df['y_type'] == 'Symptom']['y_name'].unique()
        selected_symptoms = st.multiselect("選擇觀察到的症狀：", symptoms)
        
        if selected_symptoms:
            st.write("### 相關診斷建議")
            diagnostic_criteria = df[df['relation'] == 'diagnostic_criteria'][['y_name', 'y_source']].drop_duplicates()
            st.dataframe(diagnostic_criteria)
            
            # 顯示相關生物標記物
            st.write("### 建議檢測的生物標記物")
            biomarkers = df[df['relation'] == 'has_biomarker'][['y_name', 'y_source']].drop_duplicates()
            st.dataframe(biomarkers)

    elif "2. 治療決策支持" in function_option:
        st.header("治療決策支持")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("治療方案建議")
            treatments = df[df['y_type'].isin(['Treatment', 'Intervention'])][['y_name', 'y_source', 'relation']].drop_duplicates()
            st.dataframe(treatments)
            
            selected_treatment = st.selectbox("選擇治療方案查看詳細信息：", 
                                           treatments['y_name'].unique())
            
        with col2:
            if selected_treatment:
                st.subheader(f"{selected_treatment} 相關信息")
                # 顯示療效證據
                evidence = df[
                    (df['x_name'] == selected_treatment) & 
                    (df['relation'] == 'evidence_quality')
                ][['y_name', 'y_source']].drop_duplicates()
                st.write("### 療效證據")
                st.dataframe(evidence)
                
                # 顯示副作用
                side_effects = df[
                    (df['x_name'] == selected_treatment) & 
                    (df['relation'] == 'has_side_effect')
                ][['y_name', 'y_source']].drop_duplicates()
                st.write("### 可能的副作用")
                st.dataframe(side_effects)

    elif "3. 藥物建議與交互檢測" in function_option:
        st.header("藥物建議與交互檢測")
        
        # 藥物選擇
        medications = df[df['x_type'] == 'Treatment']['x_name'].unique()
        selected_medications = st.multiselect("選擇當前使用的藥物：", medications)
        
        if selected_medications:
            # 顯示藥物交互作用
            interactions = df[
                (df['x_name'].isin(selected_medications)) & 
                (df['relation'] == 'drug_interaction')
            ][['x_name', 'y_name', 'y_source']].drop_duplicates()
            
            st.subheader("藥物交互作用")
            st.dataframe(interactions)
            
            # 顯示禁忌症
            contraindications = df[
                (df['x_name'].isin(selected_medications)) & 
                (df['relation'] == 'contraindication')
            ][['x_name', 'y_name', 'y_source']].drop_duplicates()
            
            st.subheader("禁忌症")
            st.dataframe(contraindications)

    elif "4. 罕見病診療輔助" in function_option:
        st.header("罕見病診療輔助")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("生物標記物")
            biomarkers = df[df['relation'] == 'has_biomarker'][['y_name', 'y_source']].drop_duplicates()
            st.dataframe(biomarkers)
        
        with col2:
            st.subheader("基因關聯")
            genes = df[df['relation'] == 'genetic_association'][['y_name', 'y_source']].drop_duplicates()
            st.dataframe(genes)
        
        st.subheader("風險因素")
        risk_factors = df[df['relation'] == 'risk_factor'][['y_name', 'y_source']].drop_duplicates()
        st.dataframe(risk_factors)

    elif "5. 臨床決策透明化與溝通支持" in function_option:
        st.header("臨床決策透明化與溝通支持")
        
        # 過濾選項
        st.sidebar.subheader("知識圖譜過濾")
        filter_type = st.sidebar.selectbox(
            "按節點類型過濾",
            ["All"] + list(df['y_type'].unique())
        )
        
        # 創建和顯示知識圖譜
        G = create_knowledge_graph(df, filter_type=None if filter_type == "All" else filter_type)
        net = create_network_visualization(G)
        
        # 保存和顯示圖形
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp_file:
            net.save_graph(tmp_file.name)
            with open(tmp_file.name, 'r', encoding='utf-8') as f:
                html_data = f.read()
            st.components.v1.html(html_data, height=600)
            os.unlink(tmp_file.name)
        
        # 顯示圖例
        st.sidebar.subheader("圖例")
        st.sidebar.markdown("""
        - 🔴 Disease
        - 🟢 Symptom
        - 🔵 Treatment
        - 🟣 Diagnostic Test
        - 🟡 Biomarker
        - 🟤 Gene
        - 🟠 Risk Factor
        """)

    elif "6. 臨床研究與教學輔助" in function_option:
        st.header("臨床研究與教學輔助")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 按來源分類顯示知識
            st.subheader("知識來源分布")
            source_dist = df.groupby('x_source').size().reset_index(name='count')
            fig = go.Figure(data=[go.Pie(labels=source_dist['x_source'], values=source_dist['count'])])
            st.plotly_chart(fig)
        
        with col2:
            # 顯示最新研究證據
            st.subheader("Cochrane Library 最新證據")
            cochrane_evidence = df[df['x_source'] == 'Cochrane Review'][['relation', 'y_name', 'y_type']].drop_duplicates()
            st.dataframe(cochrane_evidence)
        
        # 添加教學資源部分
        st.subheader("教學資源")
        
        # 按類型顯示所有關係
        relation_types = df['relation'].unique()
        selected_relation = st.selectbox("選擇關係類型查看詳細信息：", relation_types)
        
        if selected_relation:
            st.write(f"### {selected_relation} 相關知識")
            relation_data = df[df['relation'] == selected_relation][['x_name', 'y_name', 'y_source']].drop_duplicates()
            st.dataframe(relation_data)

if __name__ == "__main__":
    main() 