import os
import re
import time
import datetime
from tqdm import tqdm 
import pandas as pd
import requests

# 以手動更新取得的urls，再利用 requests 取得於實價登錄網站取回 JSON 資料並回傳 DataFrame


def fetch_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # 若有錯誤狀況，會引發例外
        data = response.json()
        return pd.DataFrame(data)
    except Exception as e:
        print(f"取得資料時發生錯誤：{e}")
        return pd.DataFrame()  # 回傳空的 DataFrame
    

# 合併dataframe
def combined_df(url, input_time):
    # 建立一個空的列表存放各區的 DataFrame
    df_list = []
    city_counts = {}  # 用於記錄每個縣市的資料筆數
    
    # 建立進度條但不顯示縣市名稱
    pbar = tqdm(url.items(), total=len(url))
    
    # 迴圈走訪所有 URL，並新增表示地區和輸入時間的欄位
    for city_name, uni_url in pbar:
        # 更新進度條描述以顯示目前處理的縣市名稱
        pbar.set_description(f"處理 {city_name} 中")
        
        df_temp = fetch_data(uni_url)
        if not df_temp.empty:
            df_temp["city_name"] = city_name      # 加入來源區域欄位，便於後續分析
            df_temp["input_time"] = input_time    # 加入從變數名稱提取的時間
            
            # 記錄此縣市的資料筆數
            row_count = len(df_temp)
            city_counts[city_name] = row_count
            
            # 在進度條中顯示筆數信息
            pbar.set_description(f"處理 {city_name} 中 (找到 {row_count} 筆)")
            
        df_list.append(df_temp)
        time.sleep(1)  # 每次發出請求後暫停 1 秒

    # 利用 pd.concat 合併所有 DataFrame（重置索引）
    combined_df = pd.concat(df_list, ignore_index=True)
    
    # 顯示每個縣市的資料筆數
    print("\n各縣市資料筆數統計:")
    for city, count in city_counts.items():
        print(f"{city}: {count} 筆")
    
    # 顯示合併後的總筆數
    total_rows = len(combined_df)
    print(f"\n合併後資料總筆數: {total_rows} 筆")
    
    return combined_df


# 由坐落地址欄位折分出行政區
def parse_admin_region(address):
    # 若不是字串或字串長度為0，直接回傳 None 或空值
    if not isinstance(address, str) or not address:
        return None
    
    # 判斷第二個字是否為「區」
    # 注意：Python 字串的索引從 0 開始
    if len(address) >= 2 and address[1] == "區":
        return address[:2]
    # 判斷第三個字是否為「區」
    elif len(address) >= 3 and address[2] == "區":
        return address[:3]
    # 其餘情況取前三個字
    elif len(address) >= 3:
        return address[:3]
    else:
        # 若字串不足三個字，就直接回傳原字串
        return address
    

# 定義一個函式來解析銷售期間，回傳 (自售期間, 代銷期間)
def parse_sale_period(s: str):
    # 預設為 None 或空字串
    self_period = None
    agent_period = None

    # 利用正規表達式找出自售期間：匹配 "自售:" 後面所有字串，直到遇到 ";" 或 "代銷:" 或字串結尾
    self_match = re.search(r"自售:(.*?)(?=;|代銷:|$)", s)
    if self_match:
        self_period = self_match.group(1).strip()

    # 利用正規表達式找出代銷期間：匹配 "代銷:" 後面所有字串，直到遇到 ";" 或字串結尾
    agent_match = re.search(r"代銷:(.*?)(?=;|$)", s)
    if agent_match:
        agent_period = agent_match.group(1).strip()

    return self_period, agent_period


# 定義函式：尋找自售期間及代銷期間的起始日，若沒有則回傳 None
def find_first_sale_time(text):
    if not isinstance(text, str):
        return None
    match = re.search(r"\d{7}", text)
    if match:
        return match.group(0)  # 取出第一個符合 7 位數字的字串
    return None


# 定義函式：依據規則決定建案的「銷售起始時間」
def sales_start_time(row):
    self_time = row["自售起始時間"]
    agent_time = row["代銷起始時間"]
    
    # Rule 1: 若其中一個有值、另一個為空，則取有值的那一個
    if pd.isna(self_time) and not pd.isna(agent_time):
        return agent_time
    elif pd.isna(agent_time) and not pd.isna(self_time):
        return self_time
    # Rule 2: 如果兩者皆有值，轉為數值比較，取較小者（轉回字串）
    elif not pd.isna(self_time) and not pd.isna(agent_time):
        try:
            self_val = int(self_time)
            agent_val = int(agent_time)
            return str(min(self_val, agent_val))
        except Exception:
            return ""
    # Rule 3: 如果兩者皆無值，則檢查「銷售期間」是否包含"備查"
    elif pd.isna(self_time) and pd.isna(agent_time):
        sales_period = row["銷售期間"]
        if isinstance(sales_period, str) and "備查" in sales_period:
            return row["備查完成日期"]
        else:
            return row["建照核發日"]
    # Rule 4: 其餘情況，回傳空值
    else:
        return ""