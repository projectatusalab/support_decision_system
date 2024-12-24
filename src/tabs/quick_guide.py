import streamlit as st
import pandas as pd
from utils.data_loader import get_value_with_source, get_values_with_sources
from urllib.parse import urlparse

def get_source_organization(url):
    """根據URL判斷來源組織/國家"""
    domain = urlparse(url).netloc.lower()
    
    source_mapping = {
        'nice.org.uk': 'NICE (英國)',
        'alz.org': 'Alzheimer\'s Association (美國)',
        'nhmrc.gov.au': 'NHMRC (澳洲)',
        'neurology-jp.org': 'Japanese Society of Neurology (日本)',
        'dgppn.de': 'DGPPN (德國)',
        'vghtc.gov.tw': 'VGHTC (台灣)',
        'health.tainan.gov.tw': 'Tainan City (台灣)',
        'medicines.org.uk': 'MHRA (英國)',
        'pubmed.ncbi.nlm.nih.gov': 'PubMed (美國)',
        'academic.oup.com': 'Oxford Academic (英國)',
        'cochranelibrary.com': 'Cochrane Library (國際)',
        'alzheimer.ca': 'Alzheimer Society (加拿大)'
    }
    
    for key, value in source_mapping.items():
        if key in domain:
            return value
    return '其他來源'

def is_treatment_recommended(treatment, stage, df):
    """判斷治療方案是��建議用於特定階段"""
    stage_treatments = df[
        (df['x_name'] == stage) &
        (df['relation'] == 'STAGE_TREATMENT') &
        (df['y_name'] == treatment)
    ]
    return len(stage_treatments) > 0

def get_applicable_stages(treatment, df):
    """獲取治療方案適用的所有階段"""
    stages = df[
        (df['y_name'] == treatment) &
        (df['relation'] == 'STAGE_TREATMENT')
    ]['x_name'].unique()
    return stages

def render(df):
    """渲染快速診療指引頁面"""
    st.header("快速診療指引")
    
    # 初始化 session state
    if 'mmse_score' not in st.session_state:
        st.session_state.mmse_score = 20
    
    # 快速MMSE評分工具
    st.subheader("MMSE快速評估")
    st.session_state.mmse_score = st.number_input(
        "MMSE分數", 
        0, 30, 
        st.session_state.mmse_score,
        help="請輸入病人的MMSE評分 (0-30分)"
    )
    
    # 根據MMSE自動判斷疾病階段
    if st.session_state.mmse_score >= 21:
        current_stage = "Mild (MMSE 21-26)"
        st.info("📋 輕度階段")
    elif st.session_state.mmse_score >= 10:
        current_stage = "Moderate (MMSE 10-20)"
        st.warning("📋 中度階段")
    else:
        current_stage = "Severe (MMSE <10)"
        st.error("📋 重度階段")
    
    st.write("### 治療建議")
    
    # 獲取所有可能的治療方案
    all_treatments = df[
        (df['relation'] == 'DRUG_TREATMENT') &
        (df['x_type'] == 'Treatment')
    ]['x_name'].unique()
    
    # 創建治療方案數據表
    treatments_data = []
    
    # 添加所有治療方案數據
    for treatment in all_treatments:
        # 獲取藥物資訊
        drug_treatments = df[
            (df['x_name'] == treatment) &
            (df['relation'] == 'DRUG_TREATMENT')
        ]
        drugs = ', '.join(drug_treatments['y_name'].tolist()) if not drug_treatments.empty else '無'
        
        # 獲取證據等級
        evidence_levels = df[
            (df['x_name'] == treatment) &
            (df['relation'] == 'TREATMENT_EVIDENCE_LEVEL')
        ]
        evidence = evidence_levels['y_name'].iloc[0] if not evidence_levels.empty else '無資料'
        
        # 獲取來源資訊
        source_info = df[
            (df['x_name'] == treatment) &
            (df['relation'] == 'DRUG_TREATMENT')
        ].iloc[0]
        
        # 獲取來源組織
        source_org = get_source_organization(source_info['source_link'])
        
        # 獲取適用階段
        applicable_stages = get_applicable_stages(treatment, df)
        stages_text = ', '.join([stage.replace('(MMSE', '').replace(')', '') for stage in applicable_stages])
        
        treatments_data.append({
            '建議': is_treatment_recommended(treatment, current_stage, df),
            '治療方案': treatment,
            '使用藥物': drugs,
            '適用階段': stages_text,
            '證據等級': evidence,
            '來源組織': source_org,
            '來源連結': f"[查看來源]({source_info['source_link']})",
            '更新日期': source_info['source_date']
        })
    
    if treatments_data:
        # 創建DataFrame
        treatments_df = pd.DataFrame(treatments_data)
        
        # 過濾控制
        col1, col2, col3 = st.columns([2, 1, 1])
        
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
        
        with col3:
            # 國家/組織過濾
            available_orgs = sorted(treatments_df['來源組織'].unique())
            selected_orgs = st.multiselect(
                "選擇來源國家/組織",
                options=available_orgs,
                default=available_orgs,
                key="org_filter"
            )
        
        # 應用過濾器
        filtered_df = treatments_df[
            (
                (treatments_df['治療方案'].str.contains(search_term, case=False, na=False)) |
                (treatments_df['使用藥物'].str.contains(search_term, case=False, na=False))
            ) &
            (treatments_df['來源組織'].isin(selected_orgs))
        ]
        
        if show_recommended:
            filtered_df = filtered_df[filtered_df['建議'] == True]
        
        # 顯示過濾後的結果統計
        st.caption(f"顯示 {len(filtered_df)} 筆結果 (共 {len(treatments_df)} 筆)")
        
        # 添加排序選項
        sort_col, sort_order = st.columns([2, 1])
        with sort_col:
            sort_by = st.selectbox(
                "排序依據",
                options=['治療方案', '證據等級', '來源組織', '更新日期'],
                key="sort_by"
            )
        with sort_order:
            ascending = st.checkbox("升序排列", value=True, key="sort_order")
        
        # 應用排序
        filtered_df = filtered_df.sort_values(by=sort_by, ascending=ascending)
        
        # 顯示互動���表格
        st.dataframe(
            filtered_df,
            column_config={
                "建議": st.column_config.CheckboxColumn(
                    "建議",
                    help="✓ 表示當前階段建議的治療方案",
                    default=False,
                    disabled=True,
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
                "來源組織": st.column_config.TextColumn(
                    "來源組織",
                    width="medium",
                    help="指引發布組織/國家"
                ),
                "來源連結": st.column_config.LinkColumn(
                    "來源連結",
                    width="small",
                    help="點擊查看原始來源"
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
        
        # 添加 Schema 資訊表格
        st.write("### Schema 統計資訊")
        
        # 獲取所有關係類型的統計
        all_relations = df.groupby(['x_type', 'relation', 'y_type']).size().reset_index(name='關係數量')
        
        # 創建 Schema 資訊表格數據
        schema_data = []
        for _, row in all_relations.iterrows():
            # 獲取當前關係類型的所有關係
            current_relations = df[
                (df['x_type'] == row['x_type']) &
                (df['relation'] == row['relation']) &
                (df['y_type'] == row['y_type'])
            ]
            
            # 計算建議數量（僅針對Treatment類型）
            if row['y_type'] == 'Treatment':
                recommended_count = len(filtered_df[filtered_df['建議'] == True])
                total_count = len(filtered_df)
                recommended_info = f"{recommended_count}/{total_count}"
            else:
                recommended_info = '-'
            
            schema_data.append({
                '來源節點': row['x_type'],
                '關係類型': row['relation'],
                '目標節點': row['y_type'],
                '關係總數': row['關係數量'],
                '當前階段建議數': recommended_info
            })
        
        # 顯示 Schema 資訊表格
        if schema_data:
            schema_df = pd.DataFrame(schema_data)
            
            # 添加排序選項
            schema_sort_col, schema_sort_order = st.columns([2, 1])
            with schema_sort_col:
                schema_sort_by = st.selectbox(
                    "Schema 排序依據",
                    options=['關係類型', '目標節點', '關係總數'],
                    key="schema_sort_by"
                )
            with schema_sort_order:
                schema_ascending = st.checkbox("Schema 升序排列", value=True, key="schema_sort_order")
            
            # 應用排序
            schema_df = schema_df.sort_values(by=schema_sort_by, ascending=schema_ascending)
            
            # 顯示表格
            st.dataframe(
                schema_df,
                column_config={
                    "來源節點": st.column_config.TextColumn(
                        "來源節點",
                        width="small",
                        help="關係的起始節點類型"
                    ),
                    "關係類型": st.column_config.TextColumn(
                        "關係類型",
                        width="medium",
                        help="節點間的關係類型"
                    ),
                    "目標節點": st.column_config.TextColumn(
                        "目標節點",
                        width="small",
                        help="關係的目標節點類型"
                    ),
                    "關係總數": st.column_config.NumberColumn(
                        "關係總數",
                        width="small",
                        help="該類型關係的總數",
                        format="%d"
                    ),
                    "當前階段建議數": st.column_config.TextColumn(
                        "當前階段建議數",
                        width="small",
                        help="當前過濾條件下的建議數量/總數"
                    )
                },
                hide_index=True,
                use_container_width=True
            )
            
            # 顯示統計摘要
            treatment_row = schema_df[schema_df['目標節點'] == 'Treatment'].iloc[0]
            recommended_count = int(treatment_row['當前階段建議數'].split('/')[0])
            total_count = int(treatment_row['當前階段建議數'].split('/')[1])
            
            st.caption(
                f"總共有 {len(schema_df)} 種關係類型。"
                f"當前階段 ({current_stage}) 在過濾條件下建議 {recommended_count} 個治療方案 (共 {total_count} 個可選方案)。"
            )
    else:
        st.info("暫無相關資料") 