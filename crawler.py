import requests
import pandas as pd
from tqdm import tqdm
from tqdm.contrib.concurrent import thread_map
import json
import time

import logging_config
import logging


# 读取 Excel 文件并去重
def read_excel(file_path):
    df = pd.read_excel(file_path)
    unique_keywords = set(df.iloc[:, 0].tolist())  # 提取并去重第一列
    return list(unique_keywords), df  # 返回去重的关键词和原始 DataFrame


# 请求 API，并添加重试机制
def fetch_data(keyword, retries=3):
    url = f"https://api.bom.ai/asyncapi/v1/getsipartinfos?keyword={keyword}"
    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "authorization": "JWT rKPbNK2Bb8bVOTuoxQ7Xe3MqmNL6O+YFUDwoPA/2KwUKh2+zmV3VL1rhMuoRwy3E+9ahWhOMmtQeC4OFIfcS9w==",
        "origin": "https://www.bom.ai",
        "referer": "https://www.bom.ai/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
    }

    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=100)
            response.raise_for_status()  # 检查请求是否成功
            return keyword, response.json()  # 返回关键字和响应
        except requests.exceptions.RequestException as e:
            logging.info(f"Error fetching {keyword}: {e}")
            if attempt < retries - 1:  # 如果不是最后一次尝试，等待再试
                time.sleep(2**attempt)  # 指数退避
            else:
                return keyword, {"Result": {"Data": {}}}  # 返回空数据以避免崩溃


# 处理 API 响应
def process_response(data):
    keyword, response = data
    search_count = ""
    try:
        search_count = response["Result"]["Data"]["ProductDetail"].get(
            "RecentSearchCount", ""
        )
        UnitPrice = response["Result"]["Data"]["ProductDetail"].get("UnitPrice", "")
        search_count = int(search_count) if search_count else 0

        logging.info(f"{keyword}: {search_count} {UnitPrice}")
    except Exception:
        logging.info(f"{keyword}: no search count")

    return keyword, search_count


# 主程序
def main():
    keywords, original_df = read_excel(
        "/home/deploy/projects/search_crawler/test-exces.xlsx"
    )
    logging.info("Unique Keywords:", keywords)

    # 使用线程池并行请求
    results = thread_map(fetch_data, keywords, max_workers=10)

    # 处理响应
    search_counts = [process_response(result) for result in results]

    # 保存请求结果和搜索计数为 JSON 文件
    with open("results.json", "w") as results_file:
        json.dump(results, results_file, ensure_ascii=False, indent=4)

    with open("search_counts.json", "w") as counts_file:
        json.dump(search_counts, counts_file, ensure_ascii=False, indent=4)

    # 创建 DataFrame
    count_df = pd.DataFrame(search_counts, columns=["Keyword", "RecentSearchCount"])

    # 合并原始数据和搜索计数，保留原始数据
    merged_df = original_df.merge(
        count_df, left_on=original_df.columns[0], right_on="Keyword", how="left"
    )

    # 保存到新的 Excel 文件，包含所有原始列和搜索计数
    merged_df.to_excel("merged_results.xlsx", index=False)

    logging.info("Results saved to merged_results.xlsx")
    logging.info("API results saved to results.json")
    logging.info("Search counts saved to search_counts.json")


if __name__ == "__main__":
    logging_config.setup_logging(__file__)
    main()
