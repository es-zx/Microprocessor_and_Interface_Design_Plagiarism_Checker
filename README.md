# 微處理機與介面設計 程式碼抄襲檢測

本工具用於比對學生繳交的組合語言/C 程式碼，整合 Token Sequence Similarity 與 Levenshtein Distance 兩種相似度演算法，並可選用 LLM 輔助判讀，輸出互動式 HTML 報告。

## 🌟 功能

- **多重比對來源**：同時分析原始碼與 hex 檔案
- **支援多種程式語言**：接受 .a51 (組合語言)、.asm (組合語言) 及 .c (C語言) 檔案
- **兩種相似度演算法**：
  - **Token Sequence Similarity (LCS)**：基於最長共同子序列，適合偵測指令順序相同但變數名稱改變的抄襲
  - **Levenshtein Distance**：字元層級編輯距離，適合偵測幾乎完全複製但稍作修改的抄襲
- **雙重篩選模式**：
  - **Threshold Mode**：基於相似度閾值篩選
  - **Top Percent Mode**：取相似度最高的前 N% 配對
- **Keil C51 編譯功能**（可選）：將 C 程式碼編譯成組語進行深度比對
- **無效提交偵測**：自動標記缺少必要檔案或格式不符的提交
- **檔案異常偵測系統**：
  - Hex 檔案：EOF 標記、格式錯誤、長度異常、資料不足
  - 原始碼：指令數量、關鍵指令、註解/空白行比例
- **LLM 輔助分析**（可選）：使用 Google Gemini 進行高階語意比對
- **判定邏輯**：
  - Hex 檔案完全相同 → 直接判定為抄襲
  - 其他可疑配對 → 優先使用 LLM 分析
  - LLM 不可用時 → 自動 fallback 到演算法判定（相似度 > 0.85）
- **HTML 報告**：生成包含詳細比對、圖表分析、異常警告的 HTML 報告


## 📁 專案架構

```
.
├── src/                          # 核心模組
│   ├── main.py                   # 主程式入口
│   ├── preprocessor.py           # 檔案爬取與前處理
│   ├── detector.py               # 相似度計算
│   ├── c51_compiler.py           # Keil C51 編譯模組
│   ├── llm_analyzer.py           # LLM 分析模組
│   └── reporter.py               # HTML 報告生成
├── tests/                        # 單元測試
│   ├── test_detector.py          # 演算法測試
│   ├── test_preprocessor.py      # 前處理測試
│   ├── test_c51_compiler.py      # 編譯功能測試
│   └── test_regression.py        # 回歸測試
├── docs/                         # 專案文件
│   └── incident_report_20251123.md  # C51 整合事件報告
├── reports/                      # 輸出報告路徑
│   └── Lab*_plagiarism_report.html
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
python-Levenshtein    # 用於 Levenshtein Distance 計算
tqdm                  # 進度條顯示
google-generativeai   # Google Gemini API（可選，僅在使用 LLM 時需要）
```

### 3. Keil C51 安裝（可選）

若要啟用 C 語言編譯功能，需安裝 Keil C51：
- 下載並安裝 Keil µVision 或獨立的 C51 工具鏈
- 建議安裝路徑：`C:\Keil_v5\C51` 或 `C:\Keil\C51`
- 系統會自動搜尋常見安裝路徑

## ⚙️ 設定與執行

### 基本設定

編輯 `src/main.py` 中的參數（第 366-400 行）：

```python
# 實驗資訊
LAB_NAME = "Lab test"              # 實驗幾，會顯示在報告標題

# 篩選模式選擇
FILTER_MODE = "threshold"          # "threshold" 或 "top_percent"

# 模式 1: Threshold（閾值篩選）
HEX_THRESHOLD = 0.7                # Hex 相似度閾值
SRC_THRESHOLD = 0.8                # 原始碼平均相似度閾值

# 模式 2: Top Percent（百分比篩選）
TOP_METRIC = "avg_score"           # "avg_score", "token_seq", 或 "levenshtein"
TOP_PERCENT = 0.05                 # 取前 5% 的配對

# C51 編譯設定
USE_KEIL_COMPILATION = False       # 是否啟用 C→ASM 編譯
KEIL_PATH = None                   # Keil 安裝路徑，None 則自動搜尋

# 資料路徑
root_path = os.path.join(repo_root, 'Moodle下載的目錄名稱')
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
- ✅ 速度快（約 500,000+ pairs/s）
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

#### 方式三：Keil C51 編譯模式

要啟用 C 語言到組語的深度比對：

1. **安裝 Keil C51**（µVision 或獨立安裝）

2. **設定編譯參數**：
   ```python
   USE_KEIL_COMPILATION = True  # 啟用 C→ASM 編譯
   KEIL_PATH = r"C:\Keil_v5\C51"  # 指定安裝路徑，或設為 None 自動搜尋
   ```

3. **執行程式**：
   ```powershell
   python src\main.py
   ```

當啟用 Keil 編譯功能時：
- ✅ C 程式碼會被編譯成 8051 組語
- ✅ 進行更深入的抄襲偵測（變數重新命名、結構重組仍能偵測）
- ✅ 比較編譯後的組語邏輯相似度
- ⚠️ 需要安裝 Keil C51 工具鏈
- ⚠️ 編譯速度會影響整體執行時間

## 📊 相似度演算法說明

### Token Sequence Similarity (LCS)

基於最長共同子序列（Longest Common Subsequence）的相似度計算。

**公式：**
```
Similarity = 2 × LCS_length / (len(tokens1) + len(tokens2))
```

**特性：**
- 將程式碼分割為 tokens（指令、變數名等）
- 計算兩個 token 序列的最長共同子序列
- 對指令順序敏感，但允許部分插入/刪除
- 適合偵測：複製後重新排列、插入無關程式碼的抄襲

**範例：**
```
程式 A: MOV A, #55H  LOOP: CPL P1  SJMP LOOP
程式 B: MOV A, #85   NOP   CPL P1  SJMP LOOP
LCS: [MOV, A, CPL, P1, SJMP, LOOP]
相似度 ≈ 0.86
```

### Levenshtein Distance

字元層級的編輯距離，計算將一個字串轉換為另一個字串所需的最少編輯次數。

**公式：**
```
Similarity = (len1 + len2 - distance) / (len1 + len2)
```

**特性：**
- 計算插入、刪除、替換操作的次數
- 對微小修改非常敏感
- 適合偵測：幾乎完全複製但改了少數字元的抄襲

**範例：**
```
程式 A: "mov a,#55h cpl p1"
程式 B: "mov a,#85  cpl p1"
距離: 2（55→85）
相似度 ≈ 0.91
```

## 🎯 篩選模式說明

### 模式 1: Threshold（閾值篩選）

**適用情境：** 已知抄襲行為的相似度範圍

**篩選邏輯：**
```python
if avg_score > SRC_THRESHOLD or hex_levenshtein > HEX_THRESHOLD:
    標記為可疑配對
```

其中 `avg_score = (token_seq + levenshtein) / 2`

**優點：**
- 明確的判定標準
- 容易調整敏感度
- 適合大多數情況

**設定範例：**
```python
FILTER_MODE = "threshold"
HEX_THRESHOLD = 0.7   # Hex 相似度 > 70% 視為可疑
SRC_THRESHOLD = 0.8   # 原始碼平均相似度 > 80% 視為可疑
```

### 模式 2: Top Percent（百分比篩選）

**適用情境：** 不確定閾值，想查看最相似的前 N% 配對

**篩選邏輯：**
1. 計算所有配對的相似度
2. 依指定 metric 排序
3. 取前 N% 的配對

**Metric 選項：**
- `avg_score`：Token Sequence 與 Levenshtein 的平均（推薦）
- `token_seq`：僅使用 Token Sequence Similarity
- `levenshtein`：僅使用 Levenshtein Distance

**優點：**
- 自動適應資料分布
- 確保總是有結果
- 適合探索性分析

**設定範例：**
```python
FILTER_MODE = "top_percent"
TOP_METRIC = "avg_score"  # 使用平均分數排序
TOP_PERCENT = 0.05        # 取前 5% 的配對
```

## 📈 報告說明

### 報告內容

生成的 HTML 報告包含：

1. **相似度演算法說明**
   - Token Sequence Similarity (LCS) 原理與特性
   - Levenshtein Distance 原理與特性

2. **檔案異常警告**（新增）
   - Hex 異常：EOF 缺失、格式錯誤、長度異常、資料不足
   - 原始碼異常：指令過少、缺少關鍵指令、註解/空白行過多
   - 點擊可查看詳細異常列表與原始檔案內容

3. **無效提交名單**
   - 列出所有提交格式不符的學生

4. **抄襲判定名單**
   - 列出所有被判定為抄襲的學生

5. **詳細比對列表**
   - 所有可疑配對的詳細資訊
   - 點擊可查看：
     - 📊 相似度圖表（兩種演算法 × 兩種資料來源）
     - 🤖 分析結果（LLM 或演算法分析）
     - 💻 原始碼並排比對（含行號）
     - 🔢 Hex 資料比對

## 🔧 判定邏輯

### 篩選條件

**Threshold Mode:**
- 條件：`avg_score > SRC_THRESHOLD` **或** `hex_levenshtein > HEX_THRESHOLD`

**Top Percent Mode:**
- 條件：依選定 metric 排序後的前 N% 配對

### 判定規則

1. **規則 1：Hex 完全相同**
   - 條件：`hex_levenshtein == 1.0`
   - 判定：**抄襲**（不呼叫 LLM）
   - 理由：Hex 檔案完全相同 (100%)

2. **規則 2：LLM 分析**（如果可用）
   - 條件：所有可疑配對（除了規則 1）
   - 判定：依據 LLM 回傳的 `is_plagiarized`
   - 理由：LLM 提供的 `reasoning`

3. **規則 3：演算法 Fallback**（LLM 不可用時）
   - 條件：`max(hex_levenshtein, avg_score) > 0.85`
   - 判定：**抄襲**，否則為**未抄襲**
   - 理由：顯示演算法分析結果

4. **無效提交**
   - 條件：缺少有效的原始碼檔案（預設為 .a51/.asm，若開啟 Keil 編譯則包含 .c）
   - 判定：**無效提交**（但若已判定為抄襲則優先顯示抄襲）

5. **檔案異常**（新增）
   - 條件：Hex 或原始碼存在異常（格式、長度、內容品質）
   - 判定：**異常警告**（不影響抄襲判定，僅提醒檢查）

## 🔧 進階設定

### 支援的檔案類型

- **組合語言**：`.a51`, `.asm`
- **C 語言**：`.c`
- **十六進位**：`.hex`

### 調整閾值

根據實際需求調整相似度閾值：

```python
# src/main.py 第 374-375 行
HEX_THRESHOLD = 0.7
SRC_THRESHOLD = 0.8
```

**建議值：**
- 嚴格模式：`HEX_THRESHOLD = 0.6`, `SRC_THRESHOLD = 0.7`
- 標準模式：`HEX_THRESHOLD = 0.7`, `SRC_THRESHOLD = 0.8`（預設）
- 寬鬆模式：`HEX_THRESHOLD = 0.8`, `SRC_THRESHOLD = 0.9`

### 選擇篩選模式

```python
# src/main.py 第 371 行
FILTER_MODE = "threshold"  # 或 "top_percent"
```

**選擇建議：**
- 使用 `threshold`：當你知道合理的相似度範圍
- 使用 `top_percent`：當你想探索最相似的配對，不確定閾值

### 啟用 Keil 編譯模式

```python
# src/main.py 第 383-384 行
USE_KEIL_COMPILATION = True    # 啟用 C→ASM 編譯（預設 False）
KEIL_PATH = r"C:\Keil_v5\C51"  # Keil 安裝路徑，設為 None 則自動搜尋
```

### 修改 LLM 模型

```python
# src/llm_analyzer.py 第 70 行
model = genai.GenerativeModel('gemini-2.0-flash-exp')  # 可改為其他模型
```


## 🧪 測試

執行單元測試：

```powershell
# 執行所有測試
python -m unittest discover -s tests -p "test_*.py" -v

# 或執行個別測試檔案
python tests/test_detector.py
python tests/test_preprocessor.py
python tests/test_c51_compiler.py
python tests/test_regression.py
```

**測試涵蓋範圍：**
- ✅ 相似度演算法（Token Sequence LCS 和 Levenshtein Distance）
- ✅ 檔案處理與清理
- ✅ Hex 驗證與異常偵測
- ✅ 原始碼異常偵測
- ✅ C51 編譯功能（使用 mock）
- ✅ 回歸測試（防止已修復的 bug 再次出現）

**測試統計：** 90+ 個測試，執行時間 < 0.05 秒

### 回歸測試

`test_regression.py` 包含針對已知問題的測試：
- UTF-16 編碼檔案處理
- 缺少 INCDIR 的編譯失敗
- 空 hex 檔案處理
- 缺少 EOF 標記的 hex 檔案
- 僅包含註解的組語檔案
- Unicode 學生姓名
- 特殊字元和 null bytes 處理

## 📚 技術文件

詳細的技術文件和整合報告請參閱 `docs/` 目錄：
- `incident_report_20251123.md`：C51 編譯器整合過程與問題解決報告


**最後更新**：2025-11-23
