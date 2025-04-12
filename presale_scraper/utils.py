# utils.py
# 工具函數

import os
import time
import re
import logging
from datetime import datetime

def ensure_dir(directory):
    """確保目錄存在，如果不存在則創建
    
    Args:
        directory: 目錄路徑
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
        logging.info(f"創建目錄: {directory}")

def get_current_time_str():
    """獲取當前時間字符串
    
    Returns:
        str: 格式化的時間字符串
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def convert_ad_to_roc(ad_year):
    """將西元年轉換為民國年
    
    Args:
        ad_year: 西元年份
        
    Returns:
        int: 民國年份
    """
    return ad_year - 1911

def convert_roc_to_ad(roc_year):
    """將民國年轉換為西元年
    
    Args:
        roc_year: 民國年份
        
    Returns:
        int: 西元年份
    """
    return roc_year + 1911

def parse_price(price_text):
    """解析價格文本
    
    Args:
        price_text: 價格文本，例如 "總價 1,000~2,000萬" 或 "單價 30~50萬/坪"
        
    Returns:
        tuple: (最低價, 最高價) 或 None
    """
    if not price_text:
        return None
    
    # 移除所有空白和逗號
    price_text = price_text.replace(" ", "").replace(",", "")
    
    # 嘗試提取價格範圍
    try:
        # 如果包含波浪號，表示是價格範圍
        if "~" in price_text or "～" in price_text:
            # 替換不同類型的波浪號
            price_text = price_text.replace("～", "~")
            
            # 提取數字部分
            numbers = price_text.split("~")
            
            # 提取第一個數字之前的所有非數字
            first_num_start = 0
            for i, char in enumerate(numbers[0]):
                if char.isdigit():
                    first_num_start = i
                    break
            
            # 提取第二個數字之後的所有非數字
            second_num_end = len(numbers[1])
            for i in range(len(numbers[1])-1, -1, -1):
                if numbers[1][i].isdigit():
                    second_num_end = i + 1
                    break
            
            # 提取純數字部分
            min_price = int(numbers[0][first_num_start:])
            max_price = int(numbers[1][:second_num_end])
            
            return (min_price, max_price)
        
        # 如果沒有波浪號，可能只有一個價格
        else:
            # 提取數字部分
            num_start = 0
            for i, char in enumerate(price_text):
                if char.isdigit():
                    num_start = i
                    break
            
            num_end = len(price_text)
            for i in range(len(price_text)-1, -1, -1):
                if price_text[i].isdigit():
                    num_end = i + 1
                    break
            
            # 提取純數字部分
            price = int(price_text[num_start:num_end])
            
            return (price, price)
    
    except Exception as e:
        logging.warning(f"解析價格文本失敗: {e}, 文本: {price_text}")
        return None

def clean_text(text):
    """清理文本，移除多餘空白等
    
    Args:
        text: 輸入文本
        
    Returns:
        str: 清理後的文本
    """
    if not text:
        return ""
    
    # 移除首尾空白，替換多個空白為單個空白
    return " ".join(text.strip().split())

def create_filename_with_timestamp(base_name, extension):
    """創建帶時間戳的文件名
    
    Args:
        base_name: 基本文件名
        extension: 文件擴展名（不帶點）
        
    Returns:
        str: 帶時間戳的文件名
    """
    timestamp = get_current_time_str()
    return f"{base_name}_{timestamp}.{extension}"

def extract_building_type(text):
    """從文字中提取建築類型
    
    Args:
        text: 包含建築類型的文字
        
    Returns:
        str: 建築類型
    """
    building_types = [
        "住宅大樓", "商辦大樓", "住商混合", "透天厝", "店面", "辦公室", 
        "套房", "公寓", "華廈", "廠辦", "倉庫", "其他"
    ]
    
    for bt in building_types:
        if bt in text:
            return bt
    
    return "未分類"

def parse_date_string(date_str):
    """解析日期字串為標準格式
    
    Args:
        date_str: 日期字串，如 "111/01/01" 或 "民國111年01月01日"
        
    Returns:
        str: 標準格式日期字串 (YYYY-MM-DD)
    """
    if not date_str:
        return ""
    
    try:
        # 清理字串
        date_str = clean_text(date_str)
        
        # 處理民國年格式
        if "民國" in date_str:
            # 提取年月日
            parts = date_str.replace("民國", "").replace("年", "/").replace("月", "/").replace("日", "").split("/")
            if len(parts) >= 3:
                roc_year = int(parts[0])
                month = int(parts[1])
                day = int(parts[2])
                ad_year = convert_roc_to_ad(roc_year)
                return f"{ad_year:04d}-{month:02d}-{day:02d}"
        
        # 處理一般民國年格式 (111/01/01)
        elif "/" in date_str or "-" in date_str:
            date_str = date_str.replace("-", "/")
            parts = date_str.split("/")
            if len(parts) >= 3:
                year_part = parts[0]
                month = int(parts[1])
                day = int(parts[2])
                
                # 判斷是民國年還是西元年
                if len(year_part) <= 3:  # 民國年
                    roc_year = int(year_part)
                    ad_year = convert_roc_to_ad(roc_year)
                else:  # 西元年
                    ad_year = int(year_part)
                
                return f"{ad_year:04d}-{month:02d}-{day:02d}"
        
        # 如果都不匹配，返回原字串
        return date_str
    
    except Exception as e:
        logging.warning(f"解析日期字串失敗: {e}, 原字串: {date_str}")
        return date_str