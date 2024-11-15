from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import logging
import json
import os
import google.generativeai as genai
import requests

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CORS(app)

# 设置你的 Gemini API 密钥
genai.configure(api_key="AIzaSyACzCVraXyyNSxly5oDPto-7mJkYRz3ahc")

def extract_note_contents(input_file='processed_results.json', output_file='combined_notes.txt'):
    try:
        app.logger.info(f"Attempting to extract contents from {input_file}")
        
        if not os.path.exists(input_file):
            app.logger.error(f"Input file {input_file} does not exist")
            return None

        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        app.logger.info(f"Loaded JSON data from {input_file}")
        
        if 'results' not in data or not isinstance(data['results'], list):
            app.logger.error("Invalid JSON structure: 'results' key not found or not a list")
            return None

        extracted_contents = []
        for i, item in enumerate(data['results']):
            if isinstance(item, list) and len(item) >= 7:
                extracted_contents.append(str(item[6]))  # 第7个元素的索引是6
                app.logger.debug(f"Extracted content from item {i}: {item[6][:100]}...")  # 打印前100个字符
            else:
                app.logger.warning(f"Item {i} does not have at least 7 elements")

        if not extracted_contents:
            app.logger.warning("No contents extracted")
            return None

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for content in extracted_contents:
                    f.write(content + '\n\n')  # 每个内容之间添加两个换行符以分隔
            
            app.logger.info(f"Contents extracted and saved to {output_file}")
            return output_file
        except IOError as e:
            app.logger.error(f"Error writing to output file: {str(e)}")
            return None

    except json.JSONDecodeError as e:
        app.logger.error(f"JSON decode error: {str(e)}")
        return None
    except Exception as e:
        app.logger.error(f"Error extracting contents: {str(e)}", exc_info=True)
        return None

@app.route('/ai-combine', methods=['POST'])
def ai_combine():
    try:
        app.logger.info("Starting AI combine process")
        
        # 首先执行 combine 操作
        combined_notes_file = extract_note_contents('processed_results.json', 'combined_notes.txt')
        if not combined_notes_file:
            return jsonify({'error': 'Failed to create combined notes'}), 500

        # 检查 combined_notes.txt 文件是否存在
        if not os.path.exists('combined_notes.txt'):
            app.logger.error("combined_notes.txt file not found")
            return jsonify({'error': 'combined_notes.txt file not found'}), 404

        # 读取 combined_notes.txt 文件
        with open('combined_notes.txt', 'r', encoding='utf-8') as f:
            content = f.read()

        if not content.strip():
            app.logger.error("combined_notes.txt is empty")
            return jsonify({'error': 'combined_notes.txt is empty'}), 400

        app.logger.info("Successfully read combined_notes.txt")

        # 准备请求数据
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"请分析并总结以下内容，并直接以HTML格式返回，不需要额外的转换。使用适当的HTML标签如<h1>, <h2>, <p>等来组织内容。请注意：不要生成目录，直接开始内容总结。\n\n{content}"
                        }
                    ]
                }
            ]
        }

        app.logger.info("Sending request to Gemini API")

        # 发送请求到 Gemini API
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent",
            params={"key": "AIzaSyACzCVraXyyNSxly5oDPto-7mJkYRz3ahc"},
            json=data,
            timeout=60  # 增加超时时间到60秒
        )

        # 检查响应
        response.raise_for_status()
        result = response.json()

        app.logger.info("Successfully received response from Gemini API")

        # 提取生成的HTML文本
        if 'candidates' in result and result['candidates'] and 'content' in result['candidates'][0]:
            generated_html = result['candidates'][0]['content']['parts'][0]['text']
        else:
            app.logger.error("Unexpected API response structure")
            return jsonify({'error': 'Unexpected API response structure'}), 500

        # 将生成的HTML保存到文件
        with open('ai_summary.html', 'w', encoding='utf-8') as f:
            f.write(generated_html)

        app.logger.info("Successfully saved generated HTML to ai_summary.html")

        return jsonify({'result': generated_html})

    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error in API request: {str(e)}", exc_info=True)
        return jsonify({'error': f"API request failed: {str(e)}"}), 500
    except Exception as e:
        app.logger.error(f"Unexpected error in AI combine: {str(e)}", exc_info=True)
        return jsonify({'error': f"An unexpected error occurred: {str(e)}"}), 500

@app.route('/search', methods=['POST'])
def search():
    app.logger.info("Received search request")
    data = request.json
    query = data.get('query', '')
    app.logger.info(f"Search query: {query}")
    
    try:
        # 执行 your_script.py
        app.logger.debug(f"Attempting to run your_script.py with query: {query}")
        result1 = subprocess.run(['python', 'your_script.py', query], capture_output=True, text=True)
        app.logger.info(f"First script output: {result1.stdout}")
        app.logger.debug(f"First script error (if any): {result1.stderr}")

        # 检查 search_results.json 是否生成
        json_file_path = 'search_results.json'
        if not os.path.exists(json_file_path):
            return jsonify({'error': 'search_results.json not found after running your_script.py'}), 404

        # 执行 second_script.py
        app.logger.debug("Attempting to run second_script.py")
        result2 = subprocess.run(['python', 'second_script.py', json_file_path], capture_output=True, text=True)
        app.logger.info(f"Second script output: {result2.stdout}")
        app.logger.debug(f"Second script error (if any): {result2.stderr}")

        # 检查 second_script.py 是否生成了新的 JSON 文件
        processed_json_file_path = 'processed_results.json'
        if not os.path.exists(processed_json_file_path):
            return jsonify({'error': 'Processed JSON file not found after running second_script.py'}), 404

        # 提取 note contents 并保存到 txt 文件
        combined_notes_file = extract_note_contents(processed_json_file_path)
        if not combined_notes_file:
            return jsonify({'error': 'Failed to extract note contents'}), 500

        # 读取并返回处理后的 JSON 数据
        with open(processed_json_file_path, 'r', encoding='utf-8') as f:
            processed_data = json.load(f)
        app.logger.debug(f"Processed JSON data structure: {json.dumps(processed_data, indent=2)[:500]}...")  # 打印前500个字符

        return jsonify({
            'processed_data': processed_data,
            'combined_notes_file': combined_notes_file
        })

    except Exception as e:
        app.logger.error(f"Error occurred: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/combine', methods=['POST'])
def combine():
    app.logger.info("Combine function called")
    try:
        app.logger.info("Starting combine operation")
        
        if not os.path.exists('processed_results.json'):
            error_msg = "processed_results.json file not found"
            app.logger.error(error_msg)
            return jsonify({'error': error_msg}), 404

        # 测试写入权限
        try:
            with open('combined_notes.txt', 'w') as f:
                f.write('Test write')
            os.remove('combined_notes.txt')  # 删除测试文件
            app.logger.info("Write permission test passed")
        except IOError as e:
            error_msg = f"Write permission test failed: {str(e)}"
            app.logger.error(error_msg)
            return jsonify({'error': error_msg}), 500

        combined_notes_file = extract_note_contents('processed_results.json', 'combined_notes.txt')
        if combined_notes_file:
            app.logger.info(f"Combined notes created successfully: {combined_notes_file}")
            return jsonify({'message': 'Combined notes created successfully', 'file': combined_notes_file})
        else:
            error_msg = "Failed to create combined notes. Check server logs for details."
            app.logger.error(error_msg)
            return jsonify({'error': error_msg}), 500
    except Exception as e:
        error_msg = f"Error in combine: {str(e)}"
        app.logger.error(error_msg, exc_info=True)
        return jsonify({'error': error_msg}), 500

@app.route('/get-ai-summary', methods=['GET'])
def get_ai_summary():
    try:
        with open('ai_summary.json', 'r', encoding='utf-8') as f:
            ai_summary = json.load(f)
        return jsonify(ai_summary)
    except Exception as e:
        app.logger.error(f"Error reading ai_summary.json: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to read AI summary'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)