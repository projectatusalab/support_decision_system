import streamlit as st
import pandas as pd
from utils.data_loader import get_node_by_id

# 1. 定義疾病階段 group 與關鍵字 mapping
STAGE_MAPPING = {
    "初期": [
        "MCI", "Early", "Mild", "初期", "早期", "GDS 2", "GDS 3", "GDS 4", "GDS 5", "MMSE 21", "MMSE 22", "MMSE 23", "MMSE 24", "MMSE 25", "MMSE 26"
    ],
    "中期": [
        "Middle", "Moderate", "中期", "GDS 4", "GDS 5", "GDS 6", "MMSE 10", "MMSE 11", "MMSE 12", "MMSE 13", "MMSE 14", "MMSE 15", "MMSE 16", "MMSE 17", "MMSE 18", "MMSE 19", "MMSE 20"
    ],
    "晚期": [
        "Late", "Severe", "晚期", "GDS 7", "MMSE <10"
    ]
}

def match_stage_nodes(nodes_df, group_keywords):
    matched = []
    for name in nodes_df[nodes_df['type'].str.lower().str.contains('stage')]['name']:
        for kw in group_keywords:
            if kw.lower() in name.lower():
                matched.append(name)
                break
    # 也納入完全等於 group 名稱的節點（如"初期"、"中期"、"晚期"）
    for group_name in group_keywords:
        if group_name in nodes_df['name'].values:
            matched.append(group_name)
    return list(set(matched))

def normalize_stage_name(name):
    import re
    name = re.sub(r"\\(.*?\\)", "", name)
    return name.replace(" ", "").lower()

def is_treatment_recommended(treatment_id, stage_id, relationships_df):
    """判斷治療方案是否建議用於特定階段"""
    stage_treatments = relationships_df[
        (relationships_df['subject'] == stage_id) &
        (relationships_df['object'] == treatment_id) &
        (relationships_df['predicate'] == 'STAGE_TREATMENT')
    ]
    return len(stage_treatments) > 0

def is_treatment_effective_for_disease(treatment_id, disease_id, relationships_df):
    """判斷治療方案是否對疾病有效（is_effective==1）"""
    rels = relationships_df[
        (relationships_df['subject'] == disease_id) &
        (relationships_df['object'] == treatment_id) &
        (relationships_df['predicate'] == 'DISEASES_TREATMENT')
    ]
    if not rels.empty:
        return int(rels.iloc[0].get('is_effective', 0)) == 1
    return False

def get_applicable_stages(treatment_id, nodes_df, relationships_df):
    """獲取治療方案適用的所有階段"""
    stage_relations = relationships_df[
        (relationships_df['object'] == treatment_id) &
        (relationships_df['predicate'] == 'STAGE_TREATMENT')
    ]
    stages = []
    for _, rel in stage_relations.iterrows():
        stage_name, _ = get_node_by_id(nodes_df, rel['subject'])
        if stage_name:
            stages.append(stage_name)
    return stages

def render(data):
    """渲染快速診療指引頁面"""
    st.markdown("""
        <style>
        .main-title { font-size: 1.7rem; font-weight: 400; color: #222; margin-bottom: 0.2em; letter-spacing: 1px; }
        .page-title { font-size: 1.7rem; font-weight: 400; color: #555; margin-bottom: 0.1em; letter-spacing: 0.5px; }
        .section-title { font-size: 1.25rem; font-weight: 400; color: #888; margin-bottom: 0.8em; letter-spacing: 0.5px; }
        .metric-label { color: #888; font-size: 1.1rem; margin-bottom: 0.1em; }
        .metric-value { font-size: 2.5rem; font-weight: 700; color: #222; }
        .metric-block { padding: 1.2em 0 1.2em 0; border-radius: 12px; background: #fafbfc; border: 1px solid #eee; text-align: center; margin-bottom: 0.5em; }
        </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="main-title">快速診療指引</div>', unsafe_allow_html=True)
    
    nodes_df, relationships_df = data
    
    # 檢查數據是否正確載入
    if nodes_df is None or relationships_df is None:
        st.error("無法載入數據，請確認數據來源設置是否正確")
        return
    
    # 檢查必要的節點類型是否存在
    required_node_types = {'Treatment', 'Stage'}  # Drug is optional
    existing_types = set(nodes_df['type'].unique())
    missing_types = required_node_types - existing_types
    if missing_types:
        st.error(f"數據缺少必要的節點類型: {', '.join(missing_types)}")
        return
    
    # 檢查必要的關係類型是否存在
    required_relations = {'STAGE_TREATMENT'}  # USES_DRUG and HAS_EVIDENCE_LEVEL are optional
    existing_relations = set(relationships_df['predicate'].unique())
    missing_relations = required_relations - existing_relations
    if missing_relations:
        st.error(f"數據缺少必要的關係類型: {', '.join(missing_relations)}")
        return
    
    # 初始化 session state
    if 'mmse_score' not in st.session_state:
        st.session_state.mmse_score = 20
    
    # 疾病選擇器
    disease_nodes = nodes_df[nodes_df['type'] == 'disease']
    if disease_nodes.empty:
        st.error("無法找到疾病節點，請確認數據")
        return
    disease_options = disease_nodes['name'].tolist()
    default_index = 0
    if "Alzheimer disease" in disease_options:
        default_index = disease_options.index("Alzheimer disease")
    selected_disease_name = st.selectbox("選擇疾病", disease_options, index=default_index)
    selected_disease_id = disease_nodes[disease_nodes['name'] == selected_disease_name]['node_id'].iloc[0]

    # 2. MMSE分數輸入改為三選一
    selected_stage_group = st.selectbox("選擇疾病階段", list(STAGE_MAPPING.keys()))
    current_stages = match_stage_nodes(nodes_df, STAGE_MAPPING[selected_stage_group])
    st.info(f"📋 當前階段: {selected_stage_group} ({'、'.join(current_stages)})")

    # 檢查階段是否存在於數據中
    stage_exists = nodes_df[nodes_df['name'].isin(current_stages)].shape[0] > 0
    if not stage_exists:
        st.error(f"在數據中找不到對應的疾病階段: {selected_stage_group}")
        return
        
    st.write("### 治療建議")
    
    # 獲取所有治療方案（包括 Therapy 和 Treatment）
    therapy_nodes = nodes_df[nodes_df['type'] == 'Therapy']
    treatment_nodes = nodes_df[nodes_df['type'] == 'Treatment']
    
    if len(therapy_nodes) == 0 and len(treatment_nodes) == 0:
        st.info("目前沒有可用的治療方案數據")
        return
        
    # 創建治療方案數據表
    treatments_data = []
    
    # 獲取當前階段的所有節點ID
    stage_ids = nodes_df[nodes_df['name'].isin(current_stages)]['node_id'].tolist()
    
    # 處理 Therapy 節點
    for _, therapy in therapy_nodes.iterrows():
        therapy_id = therapy['node_id']
        
        # 獲取藥物資訊
        drug_relations = relationships_df[
            (relationships_df['subject'] == therapy_id) &
            (relationships_df['predicate'] == 'DRUG_TREATMENT')
        ] if 'DRUG_TREATMENT' in existing_relations else pd.DataFrame()
        
        drugs = []
        for _, rel in drug_relations.iterrows():
            drug_name, _ = get_node_by_id(nodes_df, rel['object'])
            if drug_name:
                drugs.append(drug_name)
        drugs_text = ', '.join(drugs) if drugs else ''
        
        # 獲取證據等級
        evidence = ''
        evidence_relations = relationships_df[
            (relationships_df['subject'] == therapy_id) &
            (relationships_df['predicate'] == 'THERAPY_EVIDENCE_LEVEL')
        ] if 'THERAPY_EVIDENCE_LEVEL' in existing_relations else pd.DataFrame()
        
        if not evidence_relations.empty:
            evidence_node_id = evidence_relations.iloc[0]['object']
            evidence_node = nodes_df[nodes_df['node_id'] == evidence_node_id]
            if not evidence_node.empty:
                evidence = evidence_node.iloc[0]['name']
        
        # 獲取來源資訊
        source_relations = relationships_df[
            (relationships_df['subject'] == therapy_id) &
            (relationships_df['predicate'] == 'SOURCE')
        ]
        source = ''
        source_type = ''
        update_date = pd.Timestamp.now()
        
        if not source_relations.empty:
            source_node_id = source_relations.iloc[0]['object']
            source_node = nodes_df[nodes_df['node_id'] == source_node_id]
            if not source_node.empty:
                node_data = source_node.iloc[0]
                source = node_data.get('source_secondary', '')  # 來源單位名稱
                source_type = node_data.get('source_primary', '')  # 來源類型
                
                # 嘗試從來源節點獲取更新日期
                try:
                    source_date = node_data.get('source_date')
                    if source_date and pd.notna(source_date):
                        update_date = pd.to_datetime(source_date)
                except:
                    pass
        
        # 嘗試取得 Therapy 的 is_effective
        is_effective_val = None
        rels = relationships_df[
            (relationships_df['subject'] == selected_disease_id) &
            (relationships_df['object'] == therapy_id) &
            (relationships_df['predicate'] == 'DISEASES_THERAPY')
        ]
        if not rels.empty:
            is_effective_val = rels.iloc[0].get('is_effective', None)
        # 建議判斷（只有 is_effective_val 嚴格等於 1 才為 True）
        is_recommended = (is_effective_val == 1)
        # st.write('therapy_id:', therapy_id, 'selected_disease_id:', selected_disease_id)
        # st.write('DISEASES_THERAPY rels:', rels)
        treatments_data.append({
            '建議': is_recommended,
            '類型': 'Therapy',
            '治療方案': therapy['name'],
            '使用藥物': drugs_text,
            '適用階段': 'All Stages',
            '證據等級': evidence,
            '來源單位': source,
            '來源類型': source_type,
            '更新日期': update_date.strftime('%Y-%m-%d')
        })
    
    # 處理 Treatment 節點
    debug_info = []
    for _, treatment in treatment_nodes.iterrows():
        treatment_id = treatment['node_id']
        
        # 獲取藥物資訊
        drug_relations = relationships_df[
            (relationships_df['subject'] == treatment_id) &
            (relationships_df['predicate'] == 'DRUG_TREATMENT')
        ] if 'DRUG_TREATMENT' in existing_relations else pd.DataFrame()
        
        drugs = []
        for _, rel in drug_relations.iterrows():
            drug_name, _ = get_node_by_id(nodes_df, rel['object'])
            if drug_name:
                drugs.append(drug_name)
        drugs_text = ', '.join(drugs) if drugs else ''
        
        # 獲取適用階段
        applicable_stages = get_applicable_stages(treatment_id, nodes_df, relationships_df)
        # 標準化比對，允許部分比對
        normalized_current_stages = [normalize_stage_name(s) for s in current_stages]
        normalized_applicable_stages = [normalize_stage_name(s) for s in applicable_stages]
        is_applicable = any(
            any(ncs in nas or nas in ncs for ncs in normalized_current_stages)
            for nas in normalized_applicable_stages
        )
        stages_text = ', '.join(applicable_stages)
        
        # 獲取證據等級
        evidence = ''
        evidence_relations = relationships_df[
            (relationships_df['subject'] == treatment_id) &
            (relationships_df['predicate'] == 'TREATMENT_EVIDENCE_LEVEL')
        ] if 'TREATMENT_EVIDENCE_LEVEL' in existing_relations else pd.DataFrame()
        
        if not evidence_relations.empty:
            evidence_node_id = evidence_relations.iloc[0]['object']
            evidence_node = nodes_df[nodes_df['node_id'] == evidence_node_id]
            if not evidence_node.empty:
                evidence = evidence_node.iloc[0]['name']
        
        # 獲取來源資訊
        source_relations = relationships_df[
            (relationships_df['subject'] == treatment_id) &
            (relationships_df['predicate'] == 'SOURCE')
        ]
        source = ''
        source_type = ''
        update_date = pd.Timestamp.now()
        
        if not source_relations.empty:
            source_node_id = source_relations.iloc[0]['object']
            source_node = nodes_df[nodes_df['node_id'] == source_node_id]
            if not source_node.empty:
                node_data = source_node.iloc[0]
                source = node_data.get('source_secondary', '')  # 來源單位名稱
                source_type = node_data.get('source_primary', '')  # 來源類型
                
                # 嘗試從來源節點獲取更新日期
                try:
                    source_date = node_data.get('source_date')
                    if source_date and pd.notna(source_date):
                        update_date = pd.to_datetime(source_date)
                except:
                    pass
        
        # 取得 is_effective 值
        is_effective_val = None
        rels = relationships_df[
            (relationships_df['subject'] == selected_disease_id) &
            (relationships_df['object'] == treatment_id) &
            (relationships_df['predicate'] == 'DISEASES_TREATMENT')
        ]
        if not rels.empty:
            is_effective_val = rels.iloc[0].get('is_effective', None)
        # 建議判斷（只有 is_applicable 且 is_effective_val 嚴格等於 1 才為 True）
        is_recommended = (is_applicable and is_effective_val == 1)
        treatments_data.append({
            '建議': is_recommended,
            '類型': 'Treatment',
            '治療方案': treatment['name'],
            '使用藥物': drugs_text,
            '適用階段': stages_text if stages_text else '',
            '證據等級': evidence,
            '來源單位': source,
            '來源類型': source_type,
            '更新日期': update_date.strftime('%Y-%m-%d'),
            'is_effective': is_effective_val
        })
        debug_info.append({
            '治療方案': treatment['name'],
            '適用階段': applicable_stages,
            'current_stages': current_stages,
            'is_applicable': is_applicable,
            'is_effective_bool': is_effective_val
        })
    
    # 只保留 Therapy 或 is_applicable 為 True 的 Treatment
    treatments_data = [row for row in treatments_data if row['類型'] == 'Therapy' or (row['類型'] == 'Treatment' and row['is_effective'] == 1)]
    
    # debug: 顯示所有 Treatment 的適用階段與判斷結果
    #with st.expander("[Debug] Treatment 適用階段對照表"):
    #    st.dataframe(pd.DataFrame(debug_info))
    
    if treatments_data:
        # 創建DataFrame
        treatments_df = pd.DataFrame(treatments_data)
        treatments_df = treatments_df[treatments_df['is_effective'] == 1]
        
        # 過濾控制
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 搜尋框
            search_term = st.text_input(
                "搜尋治療方案或藥物",
                placeholder="輸入關鍵字搜尋...",
                key="search_box"
            )
        
        with col2:
            # 過濾建議項目
            show_recommended = st.checkbox("只顯示建議項目", key="recommended_filter")
        
        # 應用過濾器
        filtered_df = treatments_df[
            (treatments_df['治療方案'].str.contains(search_term, case=False, na=False)) |
            (treatments_df['使用藥物'].str.contains(search_term, case=False, na=False))
        ]
        
        if show_recommended:
            filtered_df = filtered_df[filtered_df['建議'] == True]
        
        # 顯示過濾後的結果統計
        st.caption(f"顯示 {len(filtered_df)} 筆結果 (共 {len(treatments_df)} 筆)")
        
        # 添加排序選項
        sort_by = st.selectbox(
            "排序依據",
            options=['類型', '治療方案', '證據等級', '來源單位', '來源類型', '更新日期'],
            key="sort_by"
        )
        
        # 應用排序
        filtered_df = filtered_df.sort_values(by=sort_by, ascending=True)
        
        # 顯示互動式表格
        st.dataframe(
            filtered_df.drop(columns=["is_effective"], errors="ignore"),
            column_config={
                "建議": st.column_config.CheckboxColumn(
                    "建議",
                    help="✓ 表示當前階段建議的治療方案",
                    default=False,
                    disabled=True,
                    width="small"
                ),
                "類型": st.column_config.TextColumn(
                    "類型",
                    help="治療方案的類型（Treatment 或 Therapy）",
                    width="small"
                ),
                "治療方案": st.column_config.TextColumn(
                    "治療方案",
                    width="medium",
                    help="治療方案名稱"
                ),
                "使用藥物": st.column_config.TextColumn(
                    "使用藥物",
                    width="medium",
                    help="治療方案使用的藥物"
                ),
                "適用階段": st.column_config.TextColumn(
                    "適用階段",
                    width="medium",
                    help="治療方案適用的疾病階段"
                ),
                "證據等級": st.column_config.TextColumn(
                    "證據等級",
                    width="small",
                    help="治療方案的證據等級"
                ),
                "來源單位": st.column_config.TextColumn(
                    "來源單位",
                    width="medium",
                    help="發布指引的單位名稱"
                ),
                "來源類型": st.column_config.TextColumn(
                    "來源類型",
                    width="small",
                    help="來源單位的類型"
                ),
                "更新日期": st.column_config.DateColumn(
                    "更新日期",
                    width="small",
                    help="資料最後更新日期",
                    format="YYYY/MM/DD"
                )
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("暫無相關資料") 