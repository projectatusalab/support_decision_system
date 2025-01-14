# 阿茲海默症臨床決策支持系統

這個系統是一個基於知識圖譜的臨床決策支持工具，旨在協助醫生進行阿茲海默症的診斷和治療決策。系統整合了多個來源的醫學知識，包括臨床指南、系統性綜述和專家共識。

### 線上展示

在此試用: [![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://supportdecisionsystem.streamlit.app/)

### 功能特點

1. 快速診療指引
   - MMSE評分輔助判斷
   - 疾病階段自動判定
   - 主要臨床表現展示
   - 首選治療建議

2. 個案評估與治療
   - 病人基本資料評估
   - 共病狀況考量
   - 個人化治療建議
   - 用藥安全提醒

3. 用藥安全查詢
   - 藥物資訊查詢
   - 禁忌症提示
   - 副作用說明
   - 用藥監測建議

4. 治療建議
   - 階段性治療策略
   - 藥物治療方案
   - 非藥物介入建議
   - 療效評估指標

5. 臨床監測追蹤
   - 治療反應監測
   - 副作用監測
   - 定期評估建議
   - 停藥條件說明

6. 治療方案比較
   - 多方案並列比較
   - 療效對比分析
   - 安全性比較
   - 適用條件對照

7. 知識圖譜Schema
   - 知識結構可視化
   - 關係類型統計
   - 數據來源追溯
   - 實例數據展示

### 系統需求

- Python 3.8+
- Neo4j 資料庫 (4.4.x 版本)
- 相關套件版本要求：
  ```
  streamlit==1.28.2
  pandas==2.1.3
  networkx==3.2.1
  plotly==5.18.0
  pyvis==0.3.2
  neo4j==5.14.1
  ```

### 安裝說明

#### 方法一：使用 pip 安裝（推薦）

1. Clone 專案：
```bash
git clone <your-repository-url>
cd Support_Decision_System2
```

2. 建立並啟動虛擬環境（建議）：
```bash
python -m venv venv
source venv/bin/activate  # Unix/macOS系統
venv\Scripts\activate     # Windows系統
```

3. 安裝專案：
```bash
pip install -r requirements.txt
```

4. 設定配置：
```bash
cp config.py.example config.py
# 編輯 config.py，填入 Neo4j 資料庫認證資訊和其他設定
```

### Neo4j 資料庫設定

1. 安裝 Neo4j Desktop：
   - 從 [Neo4j 官網](https://neo4j.com/download/) 下載並安裝 Neo4j Desktop
   - 建議使用 4.4.x 版本

2. 建立新資料庫：
   - 開啟 Neo4j Desktop
   - 點擊 "New Project"
   - 在專案中點擊 "Add Database"
   - 選擇 "Create a Local Database"
   - 設定資料庫名稱（如：alzheimer_kg）
   - 選擇版本 4.4.x
   - 設定密碼

3. 資料庫設定：
   - 啟動資料庫
   - 點擊 "Manage"
   - 在 Settings 中加入以下設定：
     ```
     dbms.memory.heap.max_size=4G
     dbms.memory.pagecache.size=4G
     ```

4. 更新 config.py：
   ```python
   NEO4J_URI = "bolt://localhost:7687"
   NEO4J_USER = "neo4j"
   NEO4J_PASSWORD = "你的密碼"
   ```

### 資料匯入流程

#### 檔案結構說明
```
data/
├── dev/
│   ├── input/              # 原始資料存放處
│   │   ├── 1_kg.csv       # 知識圖譜基礎資料
│   │   ├── 2_cochranelibrary_triple.csv    # Cochrane文獻三元組
│   │   ├── 3_cochranelibrary_property.csv  # Cochrane文獻屬性
│   │   └── 3_other_resources_property.csv  # 其他資源屬性
│   ├── output/             # 處理後資料
│   └── temp/              # 暫存檔案
├── 1_Primekg2Neo4jTriple.py    # 資料預處理腳本
└── 2_Neo4jTripleImport2Neo4j.py # Neo4j資料匯入腳本
```

#### 資料匯入步驟

1. 資料預處理：
```bash
cd Support_Decision_System2
python data/1_Primekg2Neo4jTriple.py
```
此步驟會：
- 讀取 `data/dev/input/` 中的原始資料
- 進行資料清理和格式轉換
- 輸出處理後的檔案到 `data/dev/output/`

2. 將 `data/dev/output/` 中的處理後資料移動到 Neo4j 的 import 資料夾

3. 匯入 Neo4j：
```bash
python data/2_Neo4jTripleImport2Neo4j.py
```
此步驟會：
- 連接到 Neo4j 資料庫
- 建立節點和關係
- 建立索引以優化查詢效能

3. 驗證資料匯入：
- 開啟 Neo4j Browser (http://localhost:7474)
- 執行以下查詢確認資料是否正確匯入：
```cypher
MATCH (n) RETURN count(n);  // 檢查節點總數
MATCH ()-[r]->() RETURN count(r);  // 檢查關係總數
```
