"""HTML reporter (moved to src root)."""
import os
import html

def generate_html_report(results, hex_threshold, src_threshold, illegal_students=[], lab_name="Lab"):
    """
    Generates an HTML report from the plagiarism results.
    """
    # Write reports under repository root `reports/` directory
    # src/reporter.py -> repo root is one level up
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    reports_dir = os.path.join(base_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    output_file = os.path.join(reports_dir, f"{lab_name.replace(' ', '')}_plagiarism_report.html")
    
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
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
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
        </style>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
        <div class="container">
            <h1>{lab_name} - 程式碼比對報告</h1>
            <p>Total Suspicious Pairs: <strong>{total_pairs}</strong></p>
            
    """.format(lab_name=lab_name, total_pairs=len(results))
    
    # Add explanation section
    html_content += """
            <div style="margin: 20px 0; padding: 15px; background: #f0f8ff; border-left: 4px solid #3498db; border-radius: 4px;">
                <h3 style="margin-top: 0; color: #2c3e50; cursor: pointer;" onclick="toggleExplanation()">
                    📊 相似度演算法說明 <span id="toggle-icon">▼</span>
                </h3>
                <div id="explanation-content" style="display: none;">
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; margin-top: 10px;">
                        
                        <div style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <h4 style="color: #3498db; margin-top: 0;">🔷 Jaccard Similarity (集合相似度)</h4>
                            <p><strong>原理：</strong>比較兩個集合的交集與聯集的比例</p>
                            <p><strong>特性：</strong></p>
                            <ul style="margin: 5px 0; padding-left: 20px;">
                                <li>✅ 對順序不敏感</li>
                                <li>✅ 適合偵測複製貼上後重新排列的抄襲</li>
                                <li>❌ 對小幅修改敏感</li>
                            </ul>
                            <p><strong>適用情境：</strong>學生把程式碼片段打亂順序</p>
                        </div>
                        
                        <div style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <h4 style="color: #e67e22; margin-top: 0;">🔶 Cosine Similarity (餘弦相似度)</h4>
                            <p><strong>原理：</strong>將文字轉換成向量，計算兩個向量之間的夾角</p>
                            <p><strong>特性：</strong></p>
                            <ul style="margin: 5px 0; padding-left: 20px;">
                                <li>✅ 對文件長度不敏感</li>
                                <li>✅ 考慮詞彙的重要性</li>
                                <li>✅ 適合偵測邏輯結構相似但實作細節不同</li>
                            </ul>
                            <p><strong>適用情境：</strong>改了變數名稱和註解，但演算法一樣</p>
                        </div>
                        
                        <div style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <h4 style="color: #27ae60; margin-top: 0;">🔸 Levenshtein Distance (編輯距離)</h4>
                            <p><strong>原理：</strong>計算將一個字串轉換成另一個字串所需的最少編輯次數</p>
                            <p><strong>特性：</strong></p>
                            <ul style="margin: 5px 0; padding-left: 20px;">
                                <li>✅ 順序敏感</li>
                                <li>✅ 對小幅修改敏感</li>
                                <li>✅ 適合偵測幾乎完全複製但稍作修改</li>
                            </ul>
                            <p><strong>適用情境：</strong>只改了幾個數值或暫存器名稱</p>
                        </div>
                    </div>
                    
                    <div style="margin-top: 15px; padding: 10px; background: #fff3cd; border-radius: 4px;">
                        <strong>💡 為什麼使用三種演算法？</strong>
                        <p style="margin: 5px 0;">不同的抄襲手法會在不同的演算法中顯示高相似度。系統取三者的最大值作為判斷依據，以捕捉各種抄襲模式：</p>
                        <ul style="margin: 5px 0; padding-left: 20px;">
                            <li><strong>Jaccard 高、Levenshtein 低</strong> → 可能是重新排列程式碼</li>
                            <li><strong>Cosine 高、Jaccard 低</strong> → 可能是改寫但邏輯相同</li>
                            <li><strong>Levenshtein 高</strong> → 可能是幾乎完全複製</li>
                        </ul>
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
    
    sorted_results = sorted(results, key=verdict_priority)
    
    html_content += f"""
            <h2 style="margin-top: 30px;">詳細比對列表 ({len(sorted_results)} 組)</h2>
            <p style="color: #666;">Hex 任一相似度分數 >= {hex_threshold} 或 原始碼任一相似度分數 >= {src_threshold}</p>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Student 1</th>
                        <th>Student 2</th>
                        <th>Hex Max</th>
                        <th>Source Max</th>
                        <th>最終判定</th>
                        <th>Details</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    
    for i, res in enumerate(sorted_results):
        hex_comp = res.get('max_hex_sim', 0)
        src_comp = res.get('max_src_sim', 0)
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
        
        # JSON data for chart
        chart_data = {
            'source': [res['source_similarity']['jaccard'], res['source_similarity']['cosine'], res['source_similarity']['levenshtein']],
            'hex': [res['hex_similarity']['jaccard'], res['hex_similarity']['cosine'], res['hex_similarity']['levenshtein']]
        }
        import json
        chart_json = html.escape(json.dumps(chart_data))
        
        # Format scores with bold if exceeding threshold
        hex_display = f"<strong>{hex_comp:.2f}</strong>" if hex_comp > hex_threshold else f"{hex_comp:.2f}"
        src_display = f"<strong>{src_comp:.2f}</strong>" if src_comp > src_threshold else f"{src_comp:.2f}"
        
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

    html_content += """
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
            function generateLineNumbers(text) {
                const lines = text.split('\\n').length;
                let nums = "";
                for(let i=1; i<=lines; i++) {
                    nums += i + "\\n";
                }
                return nums;
            }

            let myChart = null;

            function openModal(id) {
                const data = document.getElementById('data-' + id);
                document.getElementById('s1-name').innerText = data.querySelector('.student1').innerText;
                document.getElementById('s2-name').innerText = data.querySelector('.student2').innerText;
                
                const code1 = data.querySelector('.code1').innerText;
                const code2 = data.querySelector('.code2').innerText;
                
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
                        labels: ['Jaccard', 'Cosine', 'Levenshtein'],
                        datasets: [
                            {
                                label: 'Source Code Similarity',
                                data: chartData.source,
                                backgroundColor: 'rgba(52, 152, 219, 0.6)',
                                borderColor: 'rgba(52, 152, 219, 1)',
                                borderWidth: 1
                            },
                            {
                                label: 'Hex Data Similarity',
                                data: chartData.hex,
                                backgroundColor: 'rgba(255, 159, 64, 0.6)',
                                borderColor: 'rgba(255, 159, 64, 1)',
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
                            }
                        },
                        plugins: {
                            title: {
                                display: true,
                                text: 'Similarity Metrics Comparison'
                            }
                        }
                    }
                });
                
                document.getElementById('myModal').style.display = "block";
            }

            function closeModal() {
                document.getElementById('myModal').style.display = "none";
            }
            
            window.onclick = function(event) {
                if (event.target == document.getElementById('myModal')) {
                    closeModal();
                }
            }
        </script>
    </body>
    </html>
    """
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Report generated: {output_file}")
