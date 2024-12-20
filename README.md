# 阿茲海默症臨床決策支持系統

這個系統是一個基於知識圖譜的臨床決策支持工具，旨在協助醫生進行阿茲海默症的診斷和治療決策。系統整合了多個來源的醫學知識，包括臨床指南、系統性綜述和專家共識。

## Live Demo

Try the app at: [![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://supportdecisionsystem.streamlit.app/)

## 功能特點

### 1. 快速診療指引
- MMSE評分輔助判斷
- 疾病階段自動判定
- 主要臨床表現展示
- 首選治療建議

### 2. 個案評估與治療
- 病人基本資料評估
- 共病狀況考量
- 個人化治療建議
- 用藥安全提醒

### 3. 用藥安全查詢
- 藥物資訊查詢
- 禁忌症提示
- 副作用說明
- 用藥監測建議

### 4. 治療建議
- 階段性治療策略
- 藥物治療方案
- 非藥物介入建議
- 療效評估指標

### 5. 臨床監測追蹤
- 治療反應監測
- 副作用監測
- 定期評估建議
- 停藥條件說明

### 6. 治療方案比較
- 多方案並列比較
- 療效對比分析
- 安全性比較
- 適用條件對照

### 7. 知識圖譜Schema
- 知識結構可視化
- 關係類型統計
- 數據來源追溯
- 實例數據展示

## 系統需求

- Python 3.8+
- 相關套件版本要求：
  - streamlit==1.24.0
  - pandas==2.0.3
  - networkx==3.1
  - plotly==5.15.0
  - pyvis==0.3.2

## 安裝說明

1. clone專案

2. 安裝所需套件：
```bash
pip install -r requirements.txt
```

3. 運行應用程式：
```bash
streamlit run app.py
```

## 數據格式說明

系統使用CSV格式的知識圖譜數據，必要欄位包括：

- `x_name`: 起始節點名稱
- `x_type`: 起始節點類型
- `relation`: 關係類型
- `y_name`: 目標節點名稱
- `y_type`: 目標節點類型
- `source_type`: 來源類型
- `source_link`: 來源連結
- `source_date`: 來源日期

## 自定義數據使用說明

1. 準備符合格式的CSV文件：
   - 使用UTF-8編碼
   - 包含所有必要欄位
   - 日期格式為YYYY-MM-DD
   - 避免空行和重複數據

2. 通過系統界面上傳：
   - 選擇"上傳自定義數據"
   - 選擇CSV文件
   - 系統會自動驗證格式並載入

3. 數據驗證規則：
   - 檢查必要欄位是否存在
   - 驗證日期格式
   - 清理空白和重複數據
   - 自動填充缺失值

## 注意事項

1. 數據安全：
   - 定期備份知識圖譜數據
   - 妥善保管數據來源資訊
   - 注意數據的時效性

2. 系統使用：
   - 建議使用現代瀏覽器訪問
   - 保持網絡連接穩定
   - 定期更新知識庫

3. 臨床應用：
   - 系統建議僅供參考
   - 需結合臨床實際情況
   - 遵循醫療機構規範

## 常見問題解答

Q: 如何更新知識圖譜數據？
A: 可以通過上傳新的CSV文件來更新數據，系統會自動進行格式驗證和數據清理。

Q: 系統支援哪些數據來源？
A: 系統可以整合多種來源的數據，包括臨床指南、系統性綜述、專家共識等，只要符合規定的CSV格式即可。

Q: 如何處理數據中的空值？
A: 系統會自動使用預設值填充空值，包括來源類型、連結和日期等。

