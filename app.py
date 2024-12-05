import streamlit as st
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
from pyvis.network import Network
import tempfile
import os
from datetime import datetime

# 設置頁面配置
st.set_page_config(page_title="阿茲海默症臨床決策支持系統", layout="wide")

# 定義全局顏色映射
COLOR_MAP = {
    'Disease': '#FF6B6B',
    'Stage': '#45B7D1',
    'Symptom': '#4ECDC4',
    'Treatment': '#96CEB4',
    'Drug': '#FFEEAD',
    'Therapy': '#D4A5A5',
    'Evidence': '#FFE66D',
    'Effectiveness': '#98FB98',
    'SideEffect': '#FFB6C1',
    'Monitoring': '#DDA0DD',
    'Condition': '#E6E6FA',
    'Population': '#98FB98',
    'Dosage': '#DEB887'
}

# 讀取數據
@st.cache_data
def load_data():
    df = pd.read_csv('alzheimer_kg.csv')
    return df

def create_schema_visualization(df):
    """創建知識圖譜schema的視覺化"""
    net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="black")
    
    # 獲取所有唯一的節點類型和關係類型
    node_types = set(df['x_type'].unique()) | set(df['y_type'].unique())
    relations = df.groupby(['x_type', 'y_type', 'relation']).size().reset_index()
    
    # 添加節點
    for node_type in node_types:
        color = COLOR_MAP.get(node_type, '#CCCCCC')
        net.add_node(node_type, label=node_type, color=color, size=30)
    
    # 添加邊
    for _, row in relations.iterrows():
        net.add_edge(row['x_type'], row['y_type'], 
                    title=row['relation'], 
                    label=row['relation'],
                    value=row[0])  # 使用關係數量作為邊的粗細
    
    return net

def get_first_value(df, conditions, default="資料不可用"):
    """安全地獲取DataFrame中符合條件的第一個值"""
    try:
        result = df.copy()
        for condition in conditions:
            result = result.loc[condition]
        if len(result) > 0:
            return result.iloc[0] if isinstance(result, pd.Series) else result['y_name'].iloc[0]
        return default
    except Exception as e:
        print(f"Error in get_first_value: {e}")
        return default

def get_values(df, conditions):
    """安全地獲取DataFrame中符合條件的所有值"""
    try:
        result = df.copy()
        for condition in conditions:
            result = result.loc[condition]
        return result['y_name'].unique() if len(result) > 0 else []
    except Exception as e:
        print(f"Error in get_values: {e}")
        return []

def display_source_info(df, item_name=None, relation=None):
    """顯示資料來源信息"""
    if item_name:
        sources = df[
            (df['x_name'] == item_name) | 
            (df['y_name'] == item_name)
        ][['source_type', 'source_link', 'source_date']].drop_duplicates()
    elif relation:
        sources = df[
            df['relation'] == relation
        ][['source_type', 'source_link', 'source_date']].drop_duplicates()
    else:
        sources = df[['source_type', 'source_link', 'source_date']].drop_duplicates()
    
    st.caption("資料來源")
    for _, source in sources.iterrows():
        date_str = source['source_date']
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            days_old = (datetime.now() - date_obj).days
            if days_old < 180:
                status = "🟢"
            elif days_old < 365:
                status = "🟡"
            else:
                status = "🔴"
        except:
            status = "⚪"
        st.caption(f"{status} {source['source_type']}: [{source['source_link']}]({source['source_link']}) ({source['source_date']})")

def main():
    st.title("阿茲海默症臨床決策支持系統")
    
    # 載入數據
    df = load_data()
    
    # 側邊欄：功能選擇
    st.sidebar.title("功能選單")
    function_option = st.sidebar.selectbox(
        "選擇功能",
        ["1. 快速診療指引",
         "2. 個案評估與治療",
         "3. 用藥安全查詢",
         "4. 整合性照護建議",
         "5. 臨床監測追蹤",
         "6. 知識圖譜Schema"]
    )
    
    if "1. 快速診療指引" in function_option:
        st.header("快速診療指引")
        
        # 快速MMSE評分工具
        st.subheader("MMSE快速評估")
        mmse_score = st.number_input("MMSE分數", 0, 30, 20)
        
        # 根據MMSE自動判斷疾病階段
        if mmse_score >= 21:
            current_stage = "Mild (MMSE 21-26)"
            st.info("📋 目前處於輕度階段")
        elif mmse_score >= 10:
            current_stage = "Moderate (MMSE 10-20)"
            st.warning("📋 目前處於中度階段")
        else:
            current_stage = "Severe (MMSE <10)"
            st.error("📋 目前處於重度階段")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 顯示當前階段的主要症狀臨床表現
            st.write("### 主要臨床表現")
            symptoms = df[
                (df['x_name'] == current_stage) & 
                (df['relation'] == 'HAS_SYMPTOM')
            ]['y_name'].unique()
            if len(symptoms) > 0:
                for symptom in symptoms:
                    st.write(f"- {symptom}")
            else:
                st.write("暫無相關症狀資料")
            
            # 顯示建議的評估工具
            st.write("### 建議評估工具")
            st.write("- MMSE (Mini-Mental State Examination)")
            st.write("- CDR (Clinical Dementia Rating)")
            st.write("- ADL (Activities of Daily Living)")
        
        with col2:
            # 顯示首選治療建議
            st.write("### 首選治療建議")
            treatments = df[
                (df['x_name'] == current_stage) & 
                (df['relation'] == 'FIRST_LINE_TREATMENT')
            ]['y_name'].unique()
            
            if len(treatments) > 0:
                for treatment in treatments:
                    evidence = get_first_value(
                        df,
                        [
                            (df['x_name'] == treatment),
                            (df['relation'] == 'EVIDENCE_LEVEL')
                        ],
                        "證據等級未知"
                    )
                    st.write(f"- {treatment}")
                    st.caption(f"  證據等級: {evidence}")
            else:
                st.write("暫無治療建議資料")
        
        # 顯示警示事項
        st.write("### ⚠️ 重要警示事項")
        st.write("1. 需排除可逆性失智")
        st.write("2. 評估共病狀況")
        st.write("3. 注意用藥安全")
        
        display_source_info(df, current_stage)
    
    elif "2. 個案評估與治療" in function_option:
        st.header("個案評估與治療")
        
        # 病人基本資料輸入
        col1, col2, col3 = st.columns(3)
        with col1:
            age = st.number_input("年齡", 0, 120, 75)
        with col2:
            mmse = st.number_input("MMSE分數", 0, 30, 20)
        with col3:
            has_cardiac_issues = st.checkbox("有心臟疾病病史")
            has_renal_issues = st.checkbox("有腎功能不全")
        
        # 自動判斷疾病階段和建議
        if mmse >= 21:
            stage = "Mild (MMSE 21-26)"
        elif mmse >= 10:
            stage = "Moderate (MMSE 10-20)"
        else:
            stage = "Severe (MMSE <10)"
        
        st.write(f"### 目前疾病階段{stage}")
        
        # 分欄顯評估結果和建議
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### 建議治療方案")
            
            # 藥物治療建議
            treatments = get_values(df, [
                (df['x_name'] == stage),
                (df['relation'] == 'FIRST_LINE_TREATMENT')
            ])
            
            if len(treatments) > 0:
                for treatment in treatments:
                    st.write(f"#### {treatment}")
                    
                    # 檢查禁忌症
                    drug = get_first_value(df, [
                        (df['x_name'] == treatment),
                        (df['relation'] == 'USES_DRUG')
                    ])
                    
                    if drug != "資料不可用":
                        contraindications = get_values(df, [
                            (df['x_name'] == drug),
                            (df['relation'] == 'CONTRAINDICATION')
                        ])
                        
                        # 顯示警告
                        if has_cardiac_issues and any("cardiac" in str(c).lower() for c in contraindications):
                            st.error("⚠️ 注意：病人有心臟疾病病史，使用本藥物需��慎評估")
                        if has_renal_issues and any("renal" in str(c).lower() for c in contraindications):
                            st.error("⚠️ 注意：病人有腎功能不全，使用本藥物需謹慎評估")
                    
                    # 顯示用藥建議
                    dosage = get_first_value(df, [
                        (df['x_name'] == treatment),
                        (df['relation'] == 'HAS_DOSAGE')
                    ])
                    st.write(f"- 建議劑量：{dosage}")
                    
                    effectiveness = get_first_value(df, [
                        (df['x_name'] == treatment),
                        (df['relation'] == 'HAS_EFFECTIVENESS')
                    ])
                    st.write(f"- 預期療效：{effectiveness}")
            else:
                st.write("暫無治療建議資料")
        
        with col2:
            # 非藥物治療建議
            st.write("### 建議非藥物治療")
            therapies = get_values(df, [
                (df['x_name'] == stage),
                (df['relation'] == 'RECOMMENDED_THERAPY')
            ])
            
            if len(therapies) > 0:
                for therapy in therapies:
                    st.write(f"#### {therapy}")
                    effectiveness = get_first_value(df, [
                        (df['x_name'] == therapy),
                        (df['relation'] == 'HAS_EFFECTIVENESS')
                    ])
                    st.write(f"- 預期效果：{effectiveness}")
            else:
                st.write("暫無非藥物治療建議資料")
        
        # 監測建議
        st.write("### 監測建議")
        monitoring_items = get_values(df, [
            (df['relation'] == 'MONITORING_REQUIRED')
        ])
        
        if len(monitoring_items) > 0:
            for item in monitoring_items:
                st.write(f"- {item}")
        else:
            st.write("暫無監測建議資料")
        
        display_source_info(df, stage)
    
    elif "3. 用藥安全查詢" in function_option:
        st.header("用藥安全查詢")
        
        # 藥物選擇
        drugs = df[df['y_type'] == 'Drug']['y_name'].unique()
        if len(drugs) > 0:
            selected_drug = st.selectbox("選擇要查詢的藥物", drugs)
            
            if selected_drug:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("### 用藥資訊")
                    # 顯示使用該藥物的治療方案
                    treatments = df[
                        (df['relation'] == 'USES_DRUG') & 
                        (df['y_name'] == selected_drug)
                    ]['x_name'].unique()
                    
                    if len(treatments) > 0:
                        for treatment in treatments:
                            st.write(f"#### {treatment}")
                            # 劑量資訊
                            dosage = get_first_value(
                                df,
                                [
                                    (df['x_name'] == treatment),
                                    (df['relation'] == 'HAS_DOSAGE')
                                ],
                                "劑量資訊不可用"
                            )
                            st.write(f"- 建議劑量：{dosage}")
                            
                            # 適用族群
                            populations = df[
                                (df['x_name'] == treatment) & 
                                (df['relation'] == 'FOR_POPULATION')
                            ]['y_name'].unique()
                            if len(populations) > 0:
                                st.write("- 適用族群：")
                                for p in populations:
                                    st.write(f"  * {p}")
                    else:
                        st.write("暫無治療方案料")
                
                with col2:
                    # 安全性資訊
                    st.write("### ⚠️ 安全性資訊")
                    
                    # 禁忌症
                    contraindications = df[
                        (df['x_name'] == selected_drug) & 
                        (df['relation'] == 'CONTRAINDICATION')
                    ]['y_name'].unique()
                    if len(contraindications) > 0:
                        st.write("#### 禁忌症")
                        for c in contraindications:
                            st.error(f"- {c}")
                    
                    # 副作用
                    side_effects = df[
                        (df['x_name'] == selected_drug) & 
                        (df['relation'] == 'HAS_SIDE_EFFECT')
                    ]['y_name'].unique()
                    if len(side_effects) > 0:
                        st.write("#### 常見副作用")
                        for se in side_effects:
                            st.warning(f"- {se}")
                
                # 監測要求
                st.write("### 📋 監測要求")
                monitoring = df[df['relation'] == 'MONITORING_REQUIRED']['y_name'].unique()
                if len(monitoring) > 0:
                    for m in monitoring:
                        st.info(f"- {m}")
                else:
                    st.write("暫無監測要求資料")
                
                display_source_info(df, selected_drug)
        else:
            st.write("暫無藥物資料")
    
    elif "4. 整合性照護建議" in function_option:
        st.header("整合性照護建議")
        
        # 選擇疾病階段
        stages = df[df['relation'] == 'HAS_STAGE']['y_name'].unique()
        if len(stages) > 0:
            selected_stage = st.selectbox("選擇疾病階段", stages)
            
            if selected_stage:
                col1, col2 = st.columns(2)
                
                with col1:
                    # 藥物治療建議
                    st.write("### 藥物治療策略")
                    treatments = df[
                        (df['x_name'] == selected_stage) & 
                        (df['relation'] == 'FIRST_LINE_TREATMENT')
                    ]['y_name'].unique()
                    
                    if len(treatments) > 0:
                        for treatment in treatments:
                            st.write(f"#### {treatment}")
                            drug = get_first_value(
                                df,
                                [
                                    (df['x_name'] == treatment),
                                    (df['relation'] == 'USES_DRUG')
                                ],
                                "藥物資訊不可用"
                            )
                            st.write(f"- 使用藥物：{drug}")
                            
                            effectiveness = get_first_value(
                                df,
                                [
                                    (df['x_name'] == treatment),
                                    (df['relation'] == 'HAS_EFFECTIVENESS')
                                ],
                                "療效資訊不可用"
                            )
                            st.write(f"- 預期效果：{effectiveness}")
                    else:
                        st.write("暫無藥物治療建議資料")
                
                with col2:
                    # 非藥物介入
                    st.write("### 非藥物介入")
                    therapies = df[
                        (df['x_name'] == selected_stage) & 
                        (df['relation'] == 'RECOMMENDED_THERAPY')
                    ]['y_name'].unique()
                    
                    if len(therapies) > 0:
                        for therapy in therapies:
                            st.write(f"#### {therapy}")
                            effectiveness = get_first_value(
                                df,
                                [
                                    (df['x_name'] == therapy),
                                    (df['relation'] == 'HAS_EFFECTIVENESS')
                                ],
                                "療效資訊不可用"
                            )
                            st.write(f"- 預期效果：{effectiveness}")
                    else:
                        st.write("暫無非藥物介入建議資料")
                
                # 整體照護建議
                st.write("### 整體照護重點")
                st.write("1. 定期評估認知功能和日常生活能力")
                st.write("2. 注意營養狀況和體重變化")
                st.write("3. 預防跌倒和其他意外")
                st.write("4. 照顧者支持和衛教")
                st.write("5. 定期回診追蹤")
                
                # 照顧者指導
                st.write("### 照顧者指導重點")
                st.write("1. 安全環境布置")
                st.write("2. 日常活動安排")
                st.write("3. 溝通技巧")
                st.write("4. 緊急狀況處理")
                st.write("5. 照顧者壓力管理")
                
                display_source_info(df, selected_stage)
        else:
            st.write("暫無疾病階段資料")
    
    elif "5. 臨床監測追蹤" in function_option:
        st.header("臨床監測追蹤")
        
        # 建立監測時程表
        st.subheader("監測時程表")
        
        # 藥物治療監測
        st.write("### 藥物治療監測")
        treatments = df[df['relation'] == 'MONITORING_REQUIRED']['x_name'].unique()
        
        if len(treatments) > 0:
            for treatment in treatments:
                st.write(f"#### {treatment}")
                monitoring_items = df[
                    (df['x_name'] == treatment) & 
                    (df['relation'] == 'MONITORING_REQUIRED')
                ]['y_name'].unique()
                
                if len(monitoring_items) > 0:
                    for item in monitoring_items:
                        st.info(f"- {item}")
                else:
                    st.write("暫無監測項目資料")
        else:
            st.write("暫無藥物治療監測資料")
        
        # 疾病進展監測
        st.write("### 疾病進展監測")
        st.write("#### 定期評估項��")
        st.write("1. 認知功能 (MMSE)")
        st.write("   - 頻率：每6個月")
        st.write("   - 注意事項：記錄分數變化趨勢")
        
        st.write("2. 日常生活功能 (ADL)")
        st.write("   - 頻率：每6個月")
        st.write("   - 注意事項：特別注意自我照顧能力變化")
        
        st.write("3. 行為和精神症狀")
        st.write("   - 頻率：每3個月或視需要")
        st.write("   - 注意事項：記錄新發生的症狀")
        
        # 副作用監測
        st.write("### 副作用監測")
        st.write("#### 需特別注意的症")
        st.write("1. 消化道症狀")
        st.write("2. 心血管症狀")
        st.write("3. 精神行為症狀")
        st.write("4. 跌倒風險")
        
        # 照顧者負荷評估
        st.write("### 照顧者負荷評估")
        st.write("1. 照顧者壓力量表")
        st.write("2. 照顧者身心狀況評估")
        st.write("3. 社會支持需求評估")
        
        display_source_info(df, relation='MONITORING_REQUIRED')
    
    elif "6. 知識圖譜Schema" in function_option:
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
        
        # 使用 tabs 來組織不同類型的節點關係
        tabs = st.tabs(sorted(relations['x_type'].unique()))
        
        for i, x_type in enumerate(sorted(relations['x_type'].unique())):
            with tabs[i]:
                st.write(f"### 從 {x_type} 出發的關係")
                type_relations = relations[relations['x_type'] == x_type]
                
                # 創建一個更易讀的表格
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
                
                # 顯示來源信息
                st.write("#### 數據來源")
                sources = df[df['x_type'] == x_type][['source_type', 'source_date']].drop_duplicates()
                for _, source in sources.iterrows():
                    st.write(f"- {source['source_type']} (更新日期: {source['source_date']})")
        
        # 顯示圖例
        st.sidebar.subheader("節點類型圖例")
        for node_type, color in COLOR_MAP.items():
            st.sidebar.markdown(
                f'<div style="display: flex; align-items: center;">'
                f'<div style="width: 20px; height: 20px; background-color: {color}; margin-right: 10px;"></div>'
                f'{node_type}</div>',
                unsafe_allow_html=True
            )

if __name__ == "__main__":
    main() 