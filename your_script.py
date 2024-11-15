import json
import sys
import time
from DrissionPage import ChromiumPage
import pandas as pd
from tqdm import tqdm
from urllib.parse import quote
import os
import json

def search(keyword):
    try:
        page = ChromiumPage()
        page.get(f'https://www.xiaohongshu.com/search_result?keyword={keyword}&source=web_search_result_notes')
        return page
    except Exception as e:
        print(f"Error during search: {e}")
        return None

def convert_like_count(like_str):
    if '万' in like_str:
        return int(float(like_str.replace('万', '').strip()) * 10000)
    elif '亿' in like_str:
        return int(float(like_str.replace('亿', '').strip()) * 100000000)
    else:
        return int(like_str.strip())

def get_info(section):
    try:
        note_link = section.ele('tag:a', timeout=0).link
        footer = section.ele('.footer', timeout=0)
        title = footer.ele('.title', timeout=0).text
        author_wrapper = footer.ele('.author-wrapper')
        author = author_wrapper.ele('.author').text
        author_link = author_wrapper.ele('tag:a', timeout=0).link
        author_img = author_wrapper.ele('tag:img', timeout=0).link

        try:
            like_str = footer.ele('.like-wrapper like-active').text
            like = convert_like_count(like_str)
        except Exception:
            like = 0

        return [title, author, note_link, author_link, author_img, like]
    except Exception as e:
        print(f"Error getting info: {e}")
        return None

def page_scroll_down(page):
    page.scroll.to_bottom()

def craw(times, keyword):
    contents = []
    page = search(keyword)

    if page is None:
        return contents

    for _ in range(times):
        sections = page.eles('.note-item', timeout=10)
        if not sections:
            break
        
        for section in sections:
            info = get_info(section)
            if info:
                contents.append(info)
        
        page_scroll_down(page)
        time.sleep(2)

    return contents

def save_to_excel(data):
    if not data:
        return "没有可保存的数据。"

    name = ['title', 'author', 'note_link', 'author_link', 'author_img', 'like']
    
    filtered_data = [entry for entry in data if entry is not None]
    
    if not filtered_data:
        return "没有有效的数据可保存。"
    
    try:
        df = pd.DataFrame(filtered_data, columns=name)
        df = df.drop_duplicates()
        df = df.sort_values(by='like', ascending=False)
        output_path = os.path.join(os.getcwd(), 'output.xlsx')
        df.to_excel(output_path, index=False)
        return f"数据已成功保存到 {output_path}"
    except Exception as e:
        return f"保存数据时出错: {str(e)}"

def save_results(data, query):
    output_path = os.path.join(os.getcwd(), 'search_results.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({'query': query, 'results': data}, f, ensure_ascii=False, indent=2)
    return output_path

def main(query):
    try:
        keyword_temp_code = quote(query.encode('utf-8'))
        keyword_encode = quote(keyword_temp_code.encode('gb2312'))

        contents = craw(5, keyword_encode)  # 将这里的参数从 1 改为 5
        excel_result = save_to_excel(contents)
        
        # 保存结果到 JSON 文件
        json_path = save_results(contents, query)

        results = "\n".join([f"标题: {item[0]}\n作者: {item[1]}\n笔记链接: {item[2]}\n作者链接: {item[3]}\n作者头像: {item[4]}\n点赞数: {item[5]}\n" for item in contents[:5]])
        
        return f"您搜索的内容是：{query}\n\n搜索结果：\n\n{results}\n\n{excel_result}\n\nJSON结果保存在：{json_path}"
    except Exception as e:
        return f"搜索出错：{str(e)}"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = sys.argv[1]
        result = main(query)
        print(result)
    else:
        print("没有提供搜索查询")
