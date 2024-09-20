import pandas as pd
import json


# 读取 JSON 文件
def read_search_counts(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        search_counts = json.load(f)
    return search_counts


# 主程序
def main():
    # 读取 search_counts.json
    search_counts = read_search_counts("search_counts.json")

    # 将 search_counts 转换为 DataFrame
    counts_df = pd.DataFrame(search_counts, columns=["Keyword", "RecentSearchCount"])

    # 读取 test-exces.xlsx
    original_df = pd.read_excel("test-exces.xlsx")

    # 添加 header
    original_df.columns = ["Keyword", "A", "B"]  # 假设原始数据有三列，给它们命名

    # 合并原始数据和搜索计数，保留原始数据
    merged_df = original_df.merge(counts_df, on="Keyword", how="left")

    # 保存到新的 Excel 文件
    merged_df.to_excel("merged_with_counts.xlsx", index=False)

    print("Merged results saved to merged_with_counts.xlsx")


if __name__ == "__main__":
    main()
