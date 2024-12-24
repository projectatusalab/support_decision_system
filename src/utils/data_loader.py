import pandas as pd
from datetime import datetime
import streamlit as st
import io
import os

def validate_kg_data(df):
    """驗證上傳的知識圖譜數據格式是否正確"""
    required_columns = [
        'x_name', 'x_type', 'relation', 'y_name', 'y_type',
        'source_type', 'source_link', 'source_date'
    ]
    
    # 檢查必要的列是否存在
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return False, f"缺少必要的列: {', '.join(missing_columns)}"
    
    # 檢查是否有空值
    null_counts = df[required_columns].isnull().sum()
    if null_counts.any():
        null_columns = null_counts[null_counts > 0].index.tolist()
        return False, f"以下列包含空值: {', '.join(null_columns)}"
    
    # 檢查日期格式
    try:
        pd.to_datetime(df['source_date'])
    except:
        return False, "source_date 列的日期格式不正確，請使用 YYYY-MM-DD 格式"
    
    return True, "數據格式正確"

def safe_read_csv(file_path_or_buffer):
    """安全地讀取CSV文件，包含錯誤處理"""
    try:
        # 嘗試讀取文件的前幾行來檢查格式
        if isinstance(file_path_or_buffer, str):
            # 如果是文件路徑
            if not os.path.exists(file_path_or_buffer):
                return None, "找不到指定的文件"
            if os.path.getsize(file_path_or_buffer) == 0:
                return None, "文件是空的"
            
            # 讀取並預處理文件內容
            with open(file_path_or_buffer, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        else:
            # 如果是上傳的文件
            file_content = file_path_or_buffer.getvalue().decode('utf-8')
            if not file_content.strip():
                return None, "上傳的文件是空的"
            lines = file_content.splitlines()
            
        # 移除所有空行並重新組合內容
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        if not non_empty_lines:
            return None, "文件內容為空"
            
        # 檢查是否有標題行
        header = non_empty_lines[0]
        if not any(required_col in header for required_col in ['x_name', 'y_name', 'relation']):
            return None, "文件缺少必要的標題行"
            
        # 將處理後的內容轉換為 DataFrame
        processed_content = '\n'.join(non_empty_lines)
        df = pd.read_csv(io.StringIO(processed_content))
        
        if df.empty:
            return None, "CSV文件沒有數據"
        
        # 移除每個欄位中的前後空白
        for column in df.columns:
            if df[column].dtype == 'object':
                df[column] = df[column].str.strip()
        
        # 移除完全重複的行
        df = df.drop_duplicates()
        
        # 如果有空值，用特定值填充
        fill_values = {
            'source_type': '未知來源',
            'source_link': '#',
            'source_date': datetime.now().strftime('%Y-%m-%D')
        }
        df = df.fillna(fill_values)
        
        return df, None
        
    except pd.errors.EmptyDataError:
        return None, "CSV文件是空的或格式不正確"
    except pd.errors.ParserError:
        return None, "CSV文件格式不正確，請確保是有效的CSV格式"
    except UnicodeDecodeError:
        return None, "文件編碼不正確，請使用UTF-8編碼"
    except Exception as e:
        return None, f"讀取文件時發生錯誤: {str(e)}"

@st.cache_data
def load_data(uploaded_file=None):
    """載入知識圖譜數據，可以是上傳的文件或預設文件"""
    try:
        if uploaded_file is not None:
            # 讀取上傳的文件
            df, error_message = safe_read_csv(uploaded_file)
            if error_message:
                st.error(error_message)
                return None
                
            # 驗證數據格式
            is_valid, message = validate_kg_data(df)
            if not is_valid:
                st.error(f"上傳的文件格式不正確: {message}")
                return None
            return df
        else:
            # 讀取預設文件
            df, error_message = safe_read_csv('data/Alzheimer_and_guideline.csv')
            if error_message:
                st.error(f"無法讀取預設數據文件: {error_message}")
                return None
            return df
    except Exception as e:
        st.error(f"讀取文件時發生錯誤: {str(e)}")
        return None 

def get_value_with_source(df, conditions, value_col='y_name'):
    """獲取值及其來源"""
    try:
        result = df.copy()
        for condition in conditions:
            result = result.loc[condition]
        if len(result) > 0:
            row = result.iloc[0]
            value = row[value_col]
            source = f"[{row['source_type']}]({row['source_link']}) ({row['source_date']})"
            return value, source
        return "資料不可用", "無來源資料"
    except Exception as e:
        print(f"Error in get_value_with_source: {e}")
        return "資料不可用", "無來源資料"

def get_values_with_sources(df, conditions, value_col='y_name'):
    """獲取多個值及其來源"""
    try:
        result = df.copy()
        for condition in conditions:
            result = result.loc[condition]
        if len(result) > 0:
            values_with_sources = []
            for _, row in result.iterrows():
                value = row[value_col]
                source = f"[{row['source_type']}]({row['source_link']}) ({row['source_date']})"
                values_with_sources.append((value, source))
            return values_with_sources
        return []
    except Exception as e:
        print(f"Error in get_values_with_sources: {e}")
        return [] 