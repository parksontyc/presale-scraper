# main.py
# 主程式

import os
import time
import argparse
import logging
import sys
from datetime import datetime

# 嘗試修復 MKL 錯誤
os.environ["MKL_SERVICE_FORCE_INTEL"] = "1"
os.environ["MKL_THREADING_LAYER"] = "sequential"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

try:
    import pandas as pd
except ImportError:
    print("警告: 無法導入Pandas，將使用替代方法保存數據")

from config import (
    DEFAULT_CITIES, DEFAULT_DATE_RANGE, 
    OUTPUT_EXCEL, OUTPUT_CSV, HEADLESS, DELAY
)
from scraper import PresaleScraper
from utils import ensure_dir, create_filename_with_timestamp

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("presale_scraper.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    """解析命令行參數"""
    parser = argparse.ArgumentParser(description='預售屋建案查詢爬蟲')
    
    parser.add_argument('--cities', nargs='+', default=DEFAULT_CITIES,
                        help='要查詢的城市列表，例如 "臺北市 新北市"')
    
    parser.add_argument('--districts', nargs='+', default=None,
                        help='要查詢的區域列表，例如 "中正區 信義區"（可選）')
    
    parser.add_argument('--start-year', type=int, default=DEFAULT_DATE_RANGE['start_year'],
                        help='開始年份（民國年）')
    
    parser.add_argument('--start-month', type=int, default=DEFAULT_DATE_RANGE['start_month'],
                        help='開始月份')
    
    parser.add_argument('--end-year', type=int, default=DEFAULT_DATE_RANGE['end_year'],
                        help='結束年份（民國年）')
    
    parser.add_argument('--end-month', type=int, default=DEFAULT_DATE_RANGE['end_month'],
                        help='結束月份')
    
    parser.add_argument('--output-excel', default=OUTPUT_EXCEL,
                        help='輸出Excel檔案名稱')
    
    parser.add_argument('--output-csv', default=OUTPUT_CSV,
                        help='輸出CSV檔案名稱')
    
    parser.add_argument('--headless', action='store_true', default=HEADLESS,
                        help='是否使用無頭模式（不顯示瀏覽器）')
    
    parser.add_argument('--output-dir', default='data',
                        help='輸出目錄')
    
    return parser.parse_args()

def main():
    """主函數"""
    try:
        # 解析命令行參數
        args = parse_args()
        
        # 確保輸出目錄存在
        ensure_dir(args.output_dir)
        
        # 生成帶時間戳的輸出文件名
        excel_file = os.path.join(
            args.output_dir, 
            create_filename_with_timestamp(os.path.splitext(os.path.basename(args.output_excel))[0], 'xlsx')
        )
        csv_file = os.path.join(
            args.output_dir, 
            create_filename_with_timestamp(os.path.splitext(os.path.basename(args.output_csv))[0], 'csv')
        )
        
        # 初始化爬蟲
        scraper = None
        try:
            scraper = PresaleScraper(headless=args.headless)
        except Exception as e:
            logger.error(f"初始化爬蟲失敗: {e}")
            return
        
        try:
            # 導航到預售屋查詢頁面
            if not scraper.goto_presale_page():
                logger.error("無法導航到預售屋建案查詢頁面，終止程序")
                return
            
            all_results = []
            
            # 對每個城市進行查詢
            for city in args.cities:
                logger.info(f"開始查詢城市: {city}")
                
                # 選擇城市
                if not scraper.select_city(city):
                    logger.error(f"選擇城市 {city} 失敗，跳過")
                    continue
                
                # 如果指定了區域，對每個區域進行查詢
                districts = args.districts or [None]  # 如果沒有指定區域，查詢整個城市
                
                for district in districts:
                    if district:
                        logger.info(f"開始查詢區域: {district}")
                        
                        # 選擇區域
                        if not scraper.select_district(district):
                            logger.error(f"選擇區域 {district} 失敗，跳過")
                            continue
                    
                    # 設置日期範圍
                    if not scraper.set_date_range(
                        args.start_year, args.start_month,
                        args.end_year, args.end_month
                    ):
                        logger.error("設置日期範圍失敗，跳過")
                        continue
                    
                    # 提交查詢
                    if not scraper.submit_search():
                        logger.error("提交查詢失敗，跳過")
                        continue
                    
                    # 爬取所有頁面
                    city_district_results = scraper.scrape_all_pages()
                    
                    # 添加城市和區域信息
                    for result in city_district_results:
                        result['城市'] = city
                        result['區域'] = district or '全市'
                    
                    all_results.extend(city_district_results)
                    
                    # 如果查詢成功，稍等一下再進行下一次查詢
                    time.sleep(DELAY)
            
            # 保存所有結果
            if all_results:
                # 嘗試使用 Pandas 保存
                try:
                    if 'pd' in globals():
                        # 保存為Excel
                        scraper.save_to_excel(all_results, excel_file)
                        
                        # 保存為CSV
                        scraper.save_to_csv(all_results, csv_file)
                    else:
                        # 使用替代方法保存
                        scraper.save_to_excel_without_pandas(all_results, excel_file)
                        scraper.save_to_csv_without_pandas(all_results, csv_file)
                    
                    logger.info(f"爬蟲完成，總共獲取 {len(all_results)} 條記錄")
                    logger.info(f"Excel文件已保存: {excel_file}")
                    logger.info(f"CSV文件已保存: {csv_file}")
                except Exception as e:
                    # 如果保存失敗，嘗試直接寫入簡單的文本文件
                    logger.error(f"保存數據失敗: {e}")
                    try:
                        import json
                        json_file = os.path.join(args.output_dir, f"results_{get_current_time_str()}.json")
                        with open(json_file, 'w', encoding='utf-8') as f:
                            json.dump(all_results, f, ensure_ascii=False, indent=2)
                        logger.info(f"數據已保存為JSON文件: {json_file}")
                    except Exception as json_error:
                        logger.error(f"保存JSON文件也失敗: {json_error}")
            else:
                logger.warning("沒有獲取到任何記錄")
        
        except Exception as e:
            logger.exception(f"爬蟲過程中發生錯誤: {e}")
        
        finally:
            # 關閉瀏覽器
            if scraper:
                scraper.close()
    
    except Exception as e:
        logger.exception(f"程序運行過程中發生未預期錯誤: {e}")

if __name__ == "__main__":
    main()