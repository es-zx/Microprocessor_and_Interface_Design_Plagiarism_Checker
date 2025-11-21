# 微處理機與介面設計 程式碼抄襲檢測

本工具用於比對學生繳交的組合語言/C 程式碼，整合 Jaccard、Cosine、Levenshtein 三種相似度演算法，並可選用 LLM 輔助判讀，輸出互動式 HTML 報告。

## 🌟 功能

- **多重比對來源**：同時分析原始碼與 hex 檔案
- **三種相似度演算法**：
  - **Jaccard Similarity**：適合偵測複製貼上後重新排列的抄襲
  - **Cosine Similarity**：適合偵測改了變數名稱但演算法相同的抄襲
  - **Levenshtein Distance**：適合偵測幾乎完全複製但稍作修改的抄襲
- **LLM 輔助分析**（可選）：使用 Google Gemini 進行高階語意比對
- **智慧判定邏輯**：
  - Hex 檔案完全相同 → 直接判定為抄襲
  - 其他可疑配對 → 優先使用 LLM 分析
  - LLM 不可用時 → 自動 fallback 到演算法判定（相似度 > 0.85）
- **互動式報告**：生成包含詳細比對、圖表分析的 HTML 報告
- **無效提交偵測**：自動標記缺少必要檔案或格式不符的提交

## 📁 專案架構

```
plagiarism_check_v3/
├── src/                          # 核心模組
│   ├── main.py                   # 主程式入口
│   ├── preprocessor.py           # 檔案爬取與前處理
│   ├── detector.py               # 相似度計算
│   ├── llm_analyzer.py           # LLM 分析模組
│   └── reporter.py               # HTML 報告生成
├── reports/                      # 輸出報告路徑
│   └── Lab*_plagiarism_report.html
├── test_detector.py              # 偵測器單元測試
├── test_preprocessor.py          # 前處理器單元測試
├── requirements.txt              # 依賴套件清單
└── README.md                     # 本文件
```

## 🚀 安裝

### 1. 建立虛擬環境並安裝依賴

相關依賴套件請見 `requirements.txt`

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 依賴套件說明

```
scikit-learn          # 用於 Cosine Similarity 計算
python-Levenshtein    # 用於 Levenshtein Distance 計算
tqdm                  # 進度條顯示
google-generativeai   # Google Gemini API（可選，僅在使用 LLM 時需要）
```

## ⚙️ 設定與執行

### 基本設定

編輯 `src/main.py` 中的參數：

```python
# 第 197-202 行
lab_name = "Lab 5"              # Lab 編號，會顯示在報告標題
hex_threshold = 0.7             # Hex 相似度閾值
src_threshold = 0.8             # 原始碼相似度閾值

# root_path 指向作業資料根目錄
root_path = os.path.join(repo_root, '1141_E930600-程式碼與hex-20251120')
```

### 執行方式

#### 方式一：無 LLM 模式（純演算法分析）

**不需要設定 API Key**，直接執行：

```powershell
# Windows
python src\main.py

# macOS/Linux
python3 src/main.py
```

系統會自動偵測 LLM 不可用，並使用演算法分析：
- ✅ 速度快（約 1400+ pairs/s）
- ✅ 不需要網路連線
- ✅ 判定邏輯：相似度 > 0.85 → 抄襲

#### 方式二：LLM 輔助

**需要 Google Gemini API Key**

1. **取得 API Key**

2. **設定環境變數**：

   **Windows (PowerShell - 暫時設定):**
   ```powershell
   $env:GEMINI_API_KEY = 'your-api-key-here'
   ```

   **Windows (PowerShell - 永久設定):**
   ```powershell
   [System.Environment]::SetEnvironmentVariable('GEMINI_API_KEY', 'your-api-key-here', 'User')
   ```

   **macOS/Linux (Bash - 暫時設定):**
   ```bash
   export GEMINI_API_KEY='your-api-key-here'
   ```

   **macOS/Linux (永久設定):**
   ```bash
   echo 'export GEMINI_API_KEY="your-api-key-here"' >> ~/.bashrc
   source ~/.bashrc
   ```

3. **執行程式**：
   ```powershell
   python src\main.py
   ```

系統會使用 LLM 進行深度分析：
- ✅ 更準確的語意分析
- ✅ 能理解邏輯結構的相似性
- ⚠️ 速度較慢（約 2-3 pairs/s）
- ⚠️ 需要網路連線

## 📊 判定邏輯說明

### 篩選條件

配對會被標記為「可疑」的條件：
- Hex 任一相似度 ≥ 0.7 **或**
- 原始碼任一相似度 ≥ 0.8

### 判定規則

1. **規則 1：Hex 完全相同**
   - 條件：`max_hex_sim == 1.0`
   - 判定：**抄襲**（不呼叫 LLM）
   - 理由：Hex 檔案完全相同 (100%)

2. **規則 2：LLM 分析**（如果可用）
   - 條件：所有可疑配對（除了規則 1）
   - 判定：依據 LLM 回傳的 `is_plagiarized`
   - 理由：LLM 提供的 `reasoning`

3. **規則 3：演算法 Fallback**（LLM 不可用時）
   - 條件：`max(max_hex_sim, max_src_sim) > 0.85`
   - 判定：**抄襲**，否則為**未抄襲**
   - 理由：顯示演算法分析結果

4. **無效提交**
   - 條件：缺少 .a51 檔案或 hex 檔案為空
   - 判定：**無效提交**（但若已判定為抄襲則優先顯示抄襲）

## 📈 報告說明

### 報告內容

生成的 HTML 報告包含：

1. **相似度演算法說明**
   - 三種演算法的原理、特性、適用情境

2. **無效提交名單**
   - 列出所有提交格式不符的學生

3. **抄襲判定名單**
   - 列出所有被判定為抄襲的學生

4. **詳細比對列表**
   - 所有可疑配對的詳細資訊
   - 點擊可查看：
     - 📊 相似度圖表（三種演算法 × 兩種資料來源）
     - 🤖 分析結果（LLM 或演算法分析）
     - 💻 原始碼並排比對（含行號）
     - 🔢 Hex 資料比對



## 🧪 測試

執行單元測試：

```powershell
# 測試偵測器
python test_detector.py

# 測試前處理器
python test_preprocessor.py
```

## 🔧 進階設定

### 調整閾值

根據實際需求調整相似度閾值：

```python
# src/main.py 第 198-199 行
hex_threshold = 0.7    
src_threshold = 0.8    
```

### 修改 LLM 模型

```python
# src/llm_analyzer.py 第 70 行
model = genai.GenerativeModel('gemini-2.5-flash-lite')  # 可改為其他模型
```



**最後更新**：2025-11-21
