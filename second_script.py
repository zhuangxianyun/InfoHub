import sys
import json
import os
import time
from DrissionPage import ChromiumPage

def get_note_content(note_link):
    try:
        print(f"访问笔记链接: {note_link}")
        page = ChromiumPage()
        page.get(note_link)
        time.sleep(2)  # 等待页面加载
        
        note_text_element = page.ele('.note-text', timeout=0)
        if note_text_element:
            note_content = note_text_element.text
            return note_content.strip()
        else:
            print("未找到 note-text 元素")
            return None

    except Exception as e:
        print(f"Error getting note content: {e}")
        return None

def process_results(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    query = data['query']
    results = data['results']
    
    updated_results = []
    for item in results:
        if item and len(item) > 2:
            note_link = item[2]
            note_content = get_note_content(note_link)
            item.append(note_content)  # 添加 note_content 到结果中
            updated_results.append(item)
    
    processed_data = {
        "query": query,
        "total_results": len(updated_results),
        "results": updated_results
    }
    
    return processed_data

def save_processed_results(data, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main(json_path):
    try:
        processed_data = process_results(json_path)
        output_path = os.path.join(os.getcwd(), 'processed_results.json')
        save_processed_results(processed_data, output_path)
        print(f"处理后的结果已保存到: {output_path}")
        
        print(f"查询 '{processed_data['query']}' 的结果分析:")
        print(f"总结果数: {processed_data['total_results']}")
        print("笔记链接和内容已保存到 JSON 文件中。")
    except Exception as e:
        print(f"处理结果时出错：{str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
        main(json_path)
    else:
        print("没有提供 JSON 文件路径")
