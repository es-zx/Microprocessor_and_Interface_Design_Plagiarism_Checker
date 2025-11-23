"""HTML reporter (moved to src root)."""
import os
import html
import json

def generate_html_report(results, hex_threshold, src_threshold, illegal_students=[], anomaly_students=[], lab_name="Lab", 
                        filter_mode="threshold", top_metric="max_score", top_percent=0.05, use_keil_compilation=False):
    """
    Generates an HTML report from the plagiarism results.
    """
    # Write reports under repository root `reports/` directory
    # src/reporter.py -> repo root is one level up
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    reports_dir = os.path.join(base_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    output_file = os.path.join(reports_dir, f"{lab_name.replace(' ', '')}_plagiarism_report.html")
    
    # Format filter description
    if filter_mode == "threshold":
        filter_desc = f"Threshold Mode (Hex > {hex_threshold}, Source > {src_threshold})"
    else:
        filter_desc = f"Top Percent Mode (Top {top_percent*100}% by {top_metric})"

    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>微介程式碼比對報告 - {lab_name}</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f9; color: #333; }}
            h1 {{ text-align: center; color: #2c3e50; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; white-space: nowrap; }}
            th {{ background-color: #3498db; color: white; }}
            tr:hover {{ background-color: #f1f1f1; cursor: pointer; }}
            .score-high {{ color: #e74c3c; font-weight: bold; }}
            .score-med {{ color: #f39c12; font-weight: bold; }}
            .score-low {{ color: #27ae60; font-weight: bold; }}
            
            .illegal-section {{ margin-top: 40px; border-top: 2px solid #e74c3c; padding-top: 20px; }}
            .illegal-header {{ color: #c0392b; }}
            
            /* Modal styles */
            .modal {{ display: none; position: fixed; z-index: 1; left: 0; top: 0; width: 100%; height: 100%; overflow: auto; background-color: rgba(0,0,0,0.4); }}
            .modal-content {{ background-color: #fefefe; margin: 2% auto; padding: 20px; border: 1px solid #888; width: 85%; height: 90%; border-radius: 8px; display: flex; flex-direction: column; }}
            .close {{ color: #aaa; float: right; font-size: 28px; font-weight: bold; cursor: pointer; align-self: flex-end; }}
            .close:hover, .close:focus {{ color: black; text-decoration: none; cursor: pointer; }}
            
            .comparison-view {{ display: flex; flex: 1; gap: 20px; overflow: hidden; }}
            .code-block {{ flex: 1; display: flex; flex-direction: column; overflow: hidden; border: 1px solid #ddd; border-radius: 4px; }}
            .code-block h3 {{ margin: 10px; background: #eee; padding: 5px; border-radius: 4px; }}
            .code-container {{ flex: 1; overflow: auto; position: relative; background: #f8f8f8; display: flex; }}
            
            .line-numbers {{ 
                padding: 10px 5px; 
                background: #e0e0e0; 
                color: #888; 
                text-align: right; 
                font-family: monospace; 
                font-size: 14px; 
                line-height: 1.5;
                min-width: 40px;
                user-select: none;
            }}
            pre {{ 
                margin: 0; 
                padding: 10px; 
                font-family: 'Consolas', 'Monaco', monospace; 
                font-size: 14px; 
                line-height: 1.5; 
                white-space: pre; 
                overflow: visible; /* Let container handle scroll */
            }}
            
            .llm-analysis {{ background: #e8f6f3; padding: 15px; border-left: 5px solid #1abc9c; margin-bottom: 20px; }}
            .llm-title {{ font-weight: bold; color: #16a085; margin-bottom: 5px; }}
            
            .illegal-warning {{
                background-color: #ffebee;
                color: #c62828;
                padding: 10px;
                border: 1px solid #ef9a9a;
                margin: 10px;
                border-radius: 4px;
                font-weight: bold;
                text-align: center;
            }}
            
            .filter-info {{
                background-color: #e8f4f8;
                padding: 10px;
                border-radius: 4px;
                margin-bottom: 15px;
                border: 1px solid #bde0fe;
                color: #2c3e50;
            }}
            
            /* Anomaly section styles */
            .anomaly-section {{
                margin: 20px 0;
                padding: 15px;
                background: #fffbea;
                border-left: 4px solid #f39c12;
                border-radius: 4px;
            }}
            .anomaly-header {{
                margin-top: 0;
                color: #d68910;
            }}
            .anomaly-tag {{
                display: inline-block;
                padding: 2px 8px;
                margin: 2px;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
            }}
            .anomaly-warning {{
                background: #fff3cd;
                color: #856404;
                border: 1px solid #ffeaa7;
            }}
            .anomaly-error {{
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }}
            .view-btn {{
                padding: 5px 15px;
                background: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
            }}
            .view-btn:hover {{
                background: #2980b9;
            }}
        </style>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
        <div class="container">
            <h1>{lab_name} - 程式碼比對報告</h1>
            <div class="filter-info">
                <strong>篩選機制:</strong> {filter_desc} | 
                <strong>Total Suspicious Pairs:</strong> {total_pairs}
            </div>
            
    """.format(lab_name=lab_name, total_pairs=len(results), filter_desc=filter_desc)
    
    # Add explanation section
    html_content += """
            <div style="margin: 20px 0; padding: 15px; background: #f0f8ff; border-left: 4px solid #3498db; border-radius: 4px;">
                <h3 style="margin-top: 0; color: #2c3e50; cursor: pointer;" onclick="toggleExplanation()">
                    📊 相似度演算法說明 <span id="toggle-icon">▼</span>
                </h3>
                <div id="explanation-content" style="display: none;">
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; margin-top: 10px;">
                        
                        <div style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <h4 style="color: #f39c12; margin-top: 0;">🔶 Token Sequence Similarity (LCS)</h4>
                            <p><strong>原理：</strong>將程式碼視為 Token 序列，計算最長公共子序列 (Longest Common Subsequence)。</p>
                            <p><strong>特性：</strong></p>
                            <ul style="margin: 5px 0; padding-left: 20px;">
                                <li>✅ 順序敏感 - 專注於程式執行流程</li>
                                <li>✅ 允許插入 - 可偵測中間插入無關程式碼</li>
                                <li>✅ 結構導向 - 專注於指令序列而非文字</li>
                            </ul>
                            <p><strong>適用情境：</strong>改了變數名稱但保持相同的程式邏輯</p>
                        </div>
                        
                        <div style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <h4 style="color: #3498db; margin-top: 0;">🔷 Levenshtein Distance (編輯距離)</h4>
                            <p><strong>原理：</strong>計算將一個字串轉換為另一個字串所需的最少編輯次數（插入、刪除、替換）。</p>
                            <p><strong>特性：</strong></p>
                            <ul style="margin: 5px 0; padding-left: 20px;">
                                <li>✅ 順序敏感</li>
                                <li>✅ 對小幅修改敏感</li>
                                <li>✅ 適合偵測幾乎完全複製但稍作修改</li>
                            </ul>
                            <p><strong>適用情境：</strong>只改了幾個數值或暫存器名稱</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                function toggleExplanation() {
                    var content = document.getElementById('explanation-content');
                    var icon = document.getElementById('toggle-icon');
                    if (content.style.display === 'none') {
                        content.style.display = 'block';
                        icon.textContent = '▲';
                    } else {
                        content.style.display = 'none';
                        icon.textContent = '▼';
                    }
                }
            </script>
    """
    
    # Add anomaly section - between plagiarism and illegal submissions
    if anomaly_students:
        html_content += f"""
            <div class="anomaly-section">
                <h3 class="anomaly-header">⚠️ 檔案異常警告 ({len(anomaly_students)} 位學生)</h3>
                <p>以下學生的檔案存在異常，但仍參與抄襲比對分析。點擊「查看詳情」可檢視原始碼和 Hex 檔案。</p>
                <table style="width: 100%; margin-top: 10px;">
                    <thead>
                        <tr style="background: #f39c12;">
                            <th>Student</th>
                            <th>異常類型</th>
                            <th>詳細說明</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        for student in anomaly_students:
            # Determine anomaly types
            anomaly_types = []
            if student['hex_anomalies']:
                anomaly_types.append('Hex 檔案')
            if student['source_anomalies']:
                anomaly_types.append('原始碼')
            
            # Get summary of anomalies
            anomaly_summary = []
            for anom in student['hex_anomalies'][:2]:  # First 2 hex anomalies
                anomaly_summary.append(anom['message'])
            for anom in student['source_anomalies'][:2]:  # First 2 source anomalies
                anomaly_summary.append(anom['message'])
            
            summary_text = '、'.join(anomaly_summary)
            if len(student['hex_anomalies']) + len(student['source_anomalies']) > 4:
                summary_text += '...'
            
            html_content += f"""
                        <tr>
                            <td><strong>{html.escape(student['student'])}</strong></td>
                            <td>{' + '.join(anomaly_types)}</td>
                            <td>{html.escape(summary_text)}</td>
                            <td><button class="view-btn" onclick="openAnomalyModal('{html.escape(student['student'], quote=True)}')">查看詳情</button></td>
                        </tr>
                        
                        <!-- Hidden data for anomaly modal -->
                        <div id="anomaly-data-{html.escape(student['student'])}" style="display:none;">
                            <div class="src-content">{html.escape(student.get('original_source', ''))}</div>
                            <div class="hex-content">{html.escape(student.get('hex', ''))}</div>
                            <div class="anomalies-json">{html.escape(json.dumps(student['hex_anomalies'] + student['source_anomalies']))}</div>
                        </div>
            """
        html_content += """
                    </tbody>
                </table>
            </div>
        """
    
    # Add Illegal Submissions Section FIRST
    if illegal_students:
        html_content += f"""
            <div class="illegal-section" style="margin: 20px 0; padding: 15px; background: #fff3cd; border-left: 4px solid #f39c12; border-radius: 4px;">
                <h3 style="margin-top: 0; color: #e67e22;">⚠️ 無效提交名單 ({len(illegal_students)} 位學生)</h3>
                <p>以下學生提交的檔案不符合規定格式（.a51）或缺少/空白 hex 檔案。</p>
                <table style="width: 100%; margin-top: 10px;">
                    <thead>
                        <tr style="background: #f39c12;">
                            <th>Student</th>
                            <th>Reason</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        for student in illegal_students:
            html_content += f"""
                        <tr>
                            <td><strong>{html.escape(student['student'])}</strong></td>
                            <td>{html.escape(student['reason'])}</td>
                        </tr>
            """
        html_content += """
                    </tbody>
                </table>
            </div>
        """
    
    # Add plagiarism summary section - only student names
    plagiarized_pairs = [r for r in results if r.get('final_verdict') == '抄襲']
    if plagiarized_pairs:
        # Collect unique student names
        plagiarized_students = set()
        for pair in plagiarized_pairs:
            plagiarized_students.add(pair['student1'])
            plagiarized_students.add(pair['student2'])
        
        html_content += f"""
            <div style="margin: 20px 0; padding: 15px; background: #ffebee; border-left: 4px solid #e74c3c; border-radius: 4px;">
                <h3 style="margin-top: 0; color: #c0392b;">🚨 抄襲判定名單 ({len(plagiarized_students)} 位學生)</h3>
                <ul style="columns: 3; -webkit-columns: 3; -moz-columns: 3; list-style-type: disc; padding-left: 20px;">
        """
        for student in sorted(plagiarized_students):
            html_content += f"""
                    <li><strong>{html.escape(student)}</strong></li>
            """
        html_content += """
                </ul>
            </div>
        """
    
    
    # Sort results by verdict priority: 抄襲 > 非法提交 > 未抄襲
    # Sort results by verdict priority: 抄襲 > 非法提交 > 未抄襲
    # Always sort by verdict priority first, then by score (which is already sorted in results)
    def verdict_priority(res):
        verdict = res.get('final_verdict', '未知')
        if verdict == '抄襲':
            return 0
        elif verdict == '無效提交':
            return 1
        elif verdict == '未抄襲':
            return 2
        else:
            return 3
    
    # Python's sort is stable, so it preserves the score order for items with same verdict
    sorted_results = sorted(results, key=verdict_priority)
    
    # Generate description text based on filter mode
    if filter_mode == "threshold":
        description_text = f"Hex 任一相似度分數 >= {hex_threshold} 或 原始碼平均相似度分數 >= {src_threshold}"
    else:  # top_percent
        metric_name_map = {
            "token_seq": "Token Sequence",
            "levenshtein": "Levenshtein",
            "avg_score": "平均分數"
        }
        metric_display = metric_name_map.get(top_metric, top_metric)
        description_text = f"依據 {metric_display} 排序，取前 {top_percent*100}% 的配對組合"
    
    html_content += f"""
            <h2 style="margin-top: 30px;">詳細比對列表 ({len(sorted_results)} 組)</h2>
            <p style="color: #666;">{description_text}</p>
    """
    
    # Determine table headers based on filter mode
    hex_header = "Hex Score"  # Always use "Hex Score" for consistency
    src_header = "Source (Avg)"  # Default to average
    
    if filter_mode == "top_percent":
        if top_metric == "token_seq":
            src_header = "Source (Token Seq)"
        elif top_metric == "levenshtein":
            src_header = "Source (Levenshtein)"
        elif top_metric == "avg_score":
            src_header = "Source (Avg)"
    # In threshold mode, keep "Source (Avg)" as default
            
    html_content += f"""
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Student 1</th>
                        <th>Student 2</th>
                        <th>{hex_header}</th>
                        <th>{src_header}</th>
                        <th>最終判定</th>
                        <th>Details</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    
    for i, res in enumerate(sorted_results):
        hex_comp = res.get('max_hex_sim', 0)
        src_comp = res.get('avg_score', 0) # Default to average score
        
        # Override displayed scores if in top_percent mode with specific metric
        if filter_mode == "top_percent":
            if top_metric == "token_seq":
                src_comp = res['source_similarity']['token_seq']
                hex_comp = res.get('hex_levenshtein', 0)
            elif top_metric == "levenshtein":
                src_comp = res['source_similarity']['levenshtein']
                hex_comp = res.get('hex_levenshtein', 0)
            elif top_metric == "avg_score":
                src_comp = res.get('avg_score', 0)
                hex_comp = res.get('hex_levenshtein', 0)
        verdict = res.get('final_verdict', '未知')
        
        # Color coding for verdict
        if verdict == '抄襲':
            verdict_html = '<span style="color: #e74c3c; font-weight: bold;">🔴 抄襲</span>'
        elif verdict == '未抄襲':
            verdict_html = '<span style="color: #27ae60; font-weight: bold;">🟢 未抄襲</span>'
        elif verdict == '無效提交':
            verdict_html = '<span style="color: #f39c12; font-weight: bold;">⚠️ 無效提交</span>'
        else:  # 需人工審查 or 其他
            verdict_html = '<span style="color: #95a5a6; font-weight: bold;">🟡 未知</span>'
        
        # Escape strings for JS
        s1 = html.escape(res['student1'])
        s2 = html.escape(res['student2'])
        
        # Use original source if available, else cleaned
        code1_content = res.get('original_source1') or res.get('source_code1', 'Source not available')
        code2_content = res.get('original_source2') or res.get('source_code2', 'Source not available')
        
        code1 = html.escape(code1_content)
        code2 = html.escape(code2_content)
        hex1 = html.escape(res.get('hex_code1', 'Hex not available'))
        hex2 = html.escape(res.get('hex_code2', 'Hex not available'))
        
        llm_analysis = res.get('llm_analysis') or {}
        llm_reasoning = html.escape(llm_analysis.get('reasoning', ''))
        verdict_reason = html.escape(res.get('verdict_reason', ''))
        
        # Illegal status
        ill1 = "true" if res.get('illegal_submission1') else "false"
        reason1 = html.escape(res.get('illegal_reason1', ''))
        ill2 = "true" if res.get('illegal_submission2') else "false"
        reason2 = html.escape(res.get('illegal_reason2', ''))
        
        # JSON data for chart - restructured format
        chart_data = {
            'token_seq': [res['source_similarity']['token_seq'], 0],
            'levenshtein': [res['source_similarity']['levenshtein'], res['hex_levenshtein']]
        }
        chart_json = html.escape(json.dumps(chart_data))
        
        # Format scores with bold based on filter mode
        if filter_mode == "threshold":
            # Threshold mode: bold if exceeding threshold
            hex_display = f"<strong>{hex_comp:.2f}</strong>" if hex_comp > hex_threshold else f"{hex_comp:.2f}"
            src_display = f"<strong>{src_comp:.2f}</strong>" if src_comp > src_threshold else f"{src_comp:.2f}"
        else:  # top_percent mode
            # Top percent mode: bold top N% entries (based on rank)
            top_n = int(len(sorted_results) * top_percent)
            if top_n < 1:
                top_n = 1
            is_top = (i < top_n)
            hex_display = f"<strong>{hex_comp:.2f}</strong>" if is_top else f"{hex_comp:.2f}"
            src_display = f"<strong>{src_comp:.2f}</strong>" if is_top else f"{src_comp:.2f}"
        
        row = f"""
            <tr onclick="openModal('{i}')">
                <td>{i+1}</td>
                <td>{s1}</td>
                <td>{s2}</td>
                <td>{hex_display}</td>
                <td>{src_display}</td>
                <td>{verdict_html}</td>
                <td><button>View</button></td>
            </tr>
            
            <!-- Hidden data for modal -->
            <div id="data-{i}" style="display:none;">
                <div class="student1">{s1}</div>
                <div class="student2">{s2}</div>
                <div class="code1">{code1}</div>
                <div class="code2">{code2}</div>
                <div class="hex1">{hex1}</div>
                <div class="hex2">{hex2}</div>
                <div class="llm-reasoning">{llm_reasoning}</div>
                <div class="verdict-reason">{verdict_reason}</div>
                <div class="illegal1" data-is-illegal="{ill1}">{reason1}</div>
                <div class="illegal2" data-is-illegal="{ill2}">{reason2}</div>
                <div class="chart-data">{chart_json}</div>
            </div>
        """
        html_content += row

    html_content += """
                </tbody>
            </table>
    """

    html_content += r"""
        </div>
        
        <!-- Modal -->
        <div id="myModal" class="modal">
            <div class="modal-content">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <h2 id="modal-title" style="margin: 0;">Comparison</h2>
                    <span class="close" onclick="closeModal()" style="margin: 0;">&times;</span>
                </div>
                
                <div style="width: 100%; height: 250px; margin-bottom: 20px;">
                    <canvas id="comparisonChart"></canvas>
                </div>
                
                <div id="analysis-section" class="llm-analysis" style="max-height: 120px; overflow-y: auto; margin-bottom: 15px;">
                    <div class="llm-title" id="analysis-title">Analysis Result</div>
                    <div id="analysis-content"></div>
                </div>
                
                <div class="comparison-view">
                    <div class="code-block">
                        <h3 id="s1-name">Student 1</h3>
                        <div id="s1-warning" class="illegal-warning" style="display:none;"></div>
                        <div class="code-container">
                            <div class="line-numbers" id="ln1"></div>
                            <pre id="code1-view"></pre>
                        </div>
                        <h4 style="margin: 5px 10px;">Hex Data</h4>
                        <pre id="hex1-view" style="max-height: 60px; height: auto; margin: 0 10px 10px; overflow-y: auto; background: #f8f8f8; padding: 5px; border: 1px solid #ddd; border-radius: 4px;"></pre>
                    </div>
                    <div class="code-block">
                        <h3 id="s2-name">Student 2</h3>
                        <div id="s2-warning" class="illegal-warning" style="display:none;"></div>
                        <div class="code-container">
                            <div class="line-numbers" id="ln2"></div>
                            <pre id="code2-view"></pre>
                        </div>
                        <h4 style="margin: 5px 10px;">Hex Data</h4>
                        <pre id="hex2-view" style="max-height: 60px; height: auto; margin: 0 10px 10px; overflow-y: auto; background: #f8f8f8; padding: 5px; border: 1px solid #ddd; border-radius: 4px;"></pre>
                    </div>
                </div>
            </div>
        </div>

        <script>
            function removeComments(code) {
                // Remove assembly comments (;)
                code = code.replace(/;.*/g, '');
                
                // Remove C++ style comments (//)
                code = code.replace(/\/\/.*/g, '');
                
                // Remove C style block comments (/* */)
                code = code.replace(/\/\*[\s\S]*?\*\//g, '');
                
                // Remove empty lines and trim
                code = code.split('\n')
                    .map(line => line.trim())
                    .filter(line => line.length > 0)
                    .join('\n');
                
                return code;
            }
            
            function generateLineNumbers(text) {
                const lines = text.split('\n').length;
                let nums = "";
                for(let i=1; i<=lines; i++) {
                    nums += i + "\n";
                }
                return nums;
            }

            let myChart = null;

            function openModal(id) {
                const data = document.getElementById('data-' + id);
                document.getElementById('s1-name').innerText = data.querySelector('.student1').innerText;
                document.getElementById('s2-name').innerText = data.querySelector('.student2').innerText;
                
                const code1Raw = data.querySelector('.code1').innerText;
                const code2Raw = data.querySelector('.code2').innerText;
                
                // Remove comments from code before displaying
                const code1 = removeComments(code1Raw);
                const code2 = removeComments(code2Raw);
                
                document.getElementById('code1-view').innerText = code1;
                document.getElementById('code2-view').innerText = code2;
                
                document.getElementById('ln1').innerText = generateLineNumbers(code1);
                document.getElementById('ln2').innerText = generateLineNumbers(code2);
                
                document.getElementById('hex1-view').innerText = data.querySelector('.hex1').innerText;
                document.getElementById('hex2-view').innerText = data.querySelector('.hex2').innerText;
                
                
                // Handle Illegal Warnings
                const ill1 = data.querySelector('.illegal1');
                const ill2 = data.querySelector('.illegal2');
                
                if (ill1.dataset.isIllegal === "true") {
                    document.getElementById('s1-warning').style.display = 'block';
                    document.getElementById('s1-warning').innerText = ill1.innerText;
                } else {
                    document.getElementById('s1-warning').style.display = 'none';
                }
                
                if (ill2.dataset.isIllegal === "true") {
                    document.getElementById('s2-warning').style.display = 'block';
                    document.getElementById('s2-warning').innerText = ill2.innerText;
                } else {
                    document.getElementById('s2-warning').style.display = 'none';
                }
                
                
                // Handle Analysis Section - Always show either LLM or algorithm analysis
                const llmReasoning = data.querySelector('.llm-reasoning').innerText;
                const verdictReason = data.querySelector('.verdict-reason').innerText;
                
                if (llmReasoning) {
                    // LLM analysis available
                    document.getElementById('analysis-title').innerText = 'LLM Analysis';
                    document.getElementById('analysis-content').innerText = llmReasoning;
                } else if (verdictReason) {
                    // No LLM, show algorithm analysis
                    document.getElementById('analysis-title').innerText = 'Algorithm Analysis';
                    document.getElementById('analysis-content').innerText = verdictReason;
                } else {
                    // Fallback
                    document.getElementById('analysis-title').innerText = 'Analysis';
                    document.getElementById('analysis-content').innerText = 'No analysis available';
                }
                
                
                // Chart Generation
                const chartDataRaw = data.querySelector('.chart-data').innerText;
                const chartData = JSON.parse(chartDataRaw);
                
                const ctx = document.getElementById('comparisonChart').getContext('2d');
                
                if (myChart) {
                    myChart.destroy();
                }
                
                myChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: ['Source Code', 'Hex Data'],
                        datasets: [
                            {
                                label: 'Token Sequence',
                                data: chartData.token_seq,
                                backgroundColor: 'rgba(243, 156, 18, 0.7)',  // Orange
                                borderColor: 'rgba(243, 156, 18, 1)',
                                borderWidth: 1
                            },
                            {
                                label: 'Levenshtein',
                                data: chartData.levenshtein,
                                backgroundColor: 'rgba(52, 152, 219, 0.7)',  // Blue
                                borderColor: 'rgba(52, 152, 219, 1)',
                                borderWidth: 1
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                max: 1.0,
                                title: {
                                    display: true,
                                    text: 'Similarity Score'
                                }
                            },
                            x: {
                                title: {
                                    display: true,
                                    text: 'Comparison Type'
                                }
                            }
                        },
                        plugins: {
                            title: {
                                display: true,
                                text: 'Similarity Metrics Comparison'
                            },
                            legend: {
                                display: true,
                                position: 'top'
                            }
                        }
                    }
                });
                
                document.getElementById('myModal').style.display = "block";
            }

            function closeModal() {
                document.getElementById('myModal').style.display = "none";
            }
            
            function openAnomalyModal(studentName) {
                const dataDiv = document.getElementById('anomaly-data-' + studentName);
                if (!dataDiv) return;
                
                const srcContent = dataDiv.querySelector('.src-content').innerText;
                const hexContent = dataDiv.querySelector('.hex-content').innerText;
                const anomaliesJson = dataDiv.querySelector('.anomalies-json').innerText;
                const anomalies = JSON.parse(anomaliesJson);
                
                // Set title
                document.getElementById('anomaly-student-title').innerText = '檔案異常詳情 - ' + studentName;
                
                // Set source code with line numbers
                document.getElementById('anomaly-src-content').innerText = srcContent;
                const lines = srcContent.split('\n').length;
                let lineNumbers = '';
                for (let i = 1; i <= lines; i++) {
                    lineNumbers += i + '\n';
                }
                document.getElementById('anomaly-src-lines').innerText = lineNumbers;
                
                // Set hex content
                document.getElementById('anomaly-hex-content').innerText = hexContent;
                
                // Set anomalies list
                const listDiv = document.getElementById('anomaly-list');
                listDiv.innerHTML = '';
                
                anomalies.forEach(anom => {
                    const item = document.createElement('div');
                    item.className = 'anomaly-warning';
                    if (anom.severity === 'error') {
                        item.className = 'anomaly-error';
                    }
                    item.style.padding = '10px';
                    item.style.marginBottom = '10px';
                    item.style.borderRadius = '4px';
                    
                    let html = `<strong>[${anom.code}] ${anom.message}</strong>`;
                    if (anom.details) {
                        html += '<ul style="margin: 5px 0 0 20px; font-size: 12px;">';
                        for (const [key, value] of Object.entries(anom.details)) {
                            html += `<li>${key}: ${value}</li>`;
                        }
                        html += '</ul>';
                    }
                    item.innerHTML = html;
                    listDiv.appendChild(item);
                });
                
                document.getElementById('anomalyModal').style.display = "block";
            }
            
            function closeAnomalyModal() {
                document.getElementById('anomalyModal').style.display = "none";
            }
            
            window.onclick = function(event) {
                if (event.target == document.getElementById('myModal')) {
                    closeModal();
                }
                if (event.target == document.getElementById('anomalyModal')) {
                    closeAnomalyModal();
                }
            }
        </script>
        
        <!-- Anomaly Modal -->
        <div id="anomalyModal" class="modal">
            <div class="modal-content" style="width: 90%; height: 90%;">
                <span class="close" onclick="closeAnomalyModal()">&times;</span>
                <h2 id="anomaly-student-title" style="margin-top: 0; color: #d68910;">檔案異常詳情</h2>
                
                <div style="display: flex; flex: 1; gap: 20px; overflow: hidden;">
                    <!-- Source Code Column -->
                    <div class="code-block" style="flex: 1;">
                        <h3>原始碼</h3>
                        <div class="code-container">
                            <div class="line-numbers" id="anomaly-src-lines"></div>
                            <pre id="anomaly-src-content"></pre>
                        </div>
                    </div>
                    
                    <!-- Hex Data Column -->
                    <div class="code-block" style="flex: 1;">
                        <h3>Hex 檔案</h3>
                        <div class="code-container">
                            <pre id="anomaly-hex-content"></pre>
                        </div>
                    </div>
                    
                    <!-- Anomalies List Column -->
                    <div class="code-block" style="flex: 0 0 300px; background: #fffbea;">
                        <h3 style="background: #f39c12; color: white;">異常列表</h3>
                        <div id="anomaly-list" style="padding: 15px; overflow-y: auto;">
                            <!-- Anomalies will be inserted here -->
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Report generated: {output_file}")
