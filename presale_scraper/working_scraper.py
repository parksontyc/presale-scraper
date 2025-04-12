# working_scraper.py
# 單文件版本的預售屋建案查詢爬蟲

import os
import time
import json
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("working_scraper.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 基本設置
BASE_URL = "https://lvr.land.moi.gov.tw/"
PRESALE_URL = "https://lvr.land.moi.gov.tw/jsp/list.jsp#pills-saleremark"
DELAY = 3
TIMEOUT = 30

# 確保輸出目錄存在
if not os.path.exists("output"):
    os.makedirs("output")
    logger.info("已創建輸出目錄")

def get_timestamp():
    """獲取時間戳"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def save_to_json(data, filename):
    """保存數據到JSON文件
    
    Args:
        data: 要保存的數據
        filename: 文件名
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info(f"數據已保存到JSON文件: {filename}")
        return True
    except Exception as e:
        logger.error(f"保存JSON文件失敗: {e}")
        return False

def scrape_presale_data(city="臺北市", start_year=110, start_month=1, end_year=114, end_month=12):
    """爬取預售屋建案數據
    
    Args:
        city: 城市名稱
        start_year: 開始年份（民國年）
        start_month: 開始月份
        end_year: 結束年份（民國年）
        end_month: 結束月份
        
    Returns:
        list: 爬取的數據
    """
    # 設置瀏覽器選項
    options = Options()
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36')
    
    driver = None
    try:
        # 初始化瀏覽器
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
        wait = WebDriverWait(driver, TIMEOUT)
        logger.info("瀏覽器已初始化")
        
        # 訪問預售屋查詢頁面
        driver.get(PRESALE_URL)
        logger.info(f"訪問預售屋查詢頁面: {PRESALE_URL}")
        time.sleep(DELAY * 2)  # 等待頁面完全加載
        
        # 保存頁面截圖
        screenshot_path = os.path.join("output", f"page_{get_timestamp()}.png")
        driver.save_screenshot(screenshot_path)
        logger.info(f"保存頁面截圖: {screenshot_path}")
        
        # 確認預售屋標籤已激活
        try:
            # 先查找標籤
            tab = driver.find_element(By.CSS_SELECTOR, "a[href='#pills-saleremark']")
            # 檢查標籤是否已經激活
            active = 'active' in tab.get_attribute('class') or 'show' in tab.get_attribute('class')
            
            if not active:
                # 使用JavaScript點擊標籤
                driver.execute_script("arguments[0].click();", tab)
                logger.info("點擊預售屋標籤")
                time.sleep(DELAY)  # 等待標籤內容加載
        except Exception as e:
            logger.warning(f"處理標籤時出錯: {e}")
        
        # 找到預售屋標籤內容區域
        try:
            tab_content = driver.find_element(By.ID, "pills-saleremark")
            logger.info("找到預售屋標籤內容區域")
            
            # 查找日期輸入框
            fields = {
                'citycd': None,       # 城市選擇器
                'start_year': None,   # 開始年份輸入框
                'start_month': None,  # 開始月份選擇器
                'end_year': None,     # 結束年份輸入框
                'end_month': None     # 結束月份選擇器
            }
            
            # 找所有select元素
            selects = tab_content.find_elements(By.TAG_NAME, "select")
            logger.info(f"找到 {len(selects)} 個select元素")
            
            # 打印所有select元素的id和name
            for i, select in enumerate(selects):
                id_attr = select.get_attribute("id") or ""
                name_attr = select.get_attribute("name") or ""
                options = [opt.text for opt in select.find_elements(By.TAG_NAME, "option")]
                logger.info(f"Select {i+1}: id='{id_attr}', name='{name_attr}', options={options}")
                
                # 識別元素用途
                if id_attr == "citycd" or "city" in id_attr or ("臺北" in str(options) or "台北" in str(options)):
                    fields['citycd'] = select
                elif id_attr == "startMonId" or "startMon" in id_attr or name_attr == "startM":
                    fields['start_month'] = select
                elif id_attr == "endMonId" or "endMon" in id_attr or name_attr == "endM":
                    fields['end_month'] = select
            
            # 找所有input元素
            inputs = tab_content.find_elements(By.TAG_NAME, "input")
            logger.info(f"找到 {len(inputs)} 個input元素")
            
            # 打印所有input元素的id和type
            for i, input_elem in enumerate(inputs):
                id_attr = input_elem.get_attribute("id") or ""
                type_attr = input_elem.get_attribute("type") or ""
                placeholder = input_elem.get_attribute("placeholder") or ""
                logger.info(f"Input {i+1}: id='{id_attr}', type='{type_attr}', placeholder='{placeholder}'")
                
                # 識別元素用途
                if id_attr == "startYrId" or "startYr" in id_attr or "start" in id_attr.lower() and "y" in id_attr.lower():
                    fields['start_year'] = input_elem
                elif id_attr == "endYrId" or "endYr" in id_attr or "end" in id_attr.lower() and "y" in id_attr.lower():
                    fields['end_year'] = input_elem
            
            # 查找查詢按鈕
            buttons = tab_content.find_elements(By.TAG_NAME, "button")
            logger.info(f"找到 {len(buttons)} 個button元素")
            
            search_button = None
            for button in buttons:
                text = button.text.strip()
                logger.info(f"Button: '{text}'")
                if "查詢" in text:
                    search_button = button
                    logger.info(f"找到查詢按鈕: {text}")
                    break
            
            # 逐一填寫表單
            if fields['citycd']:
                # 選擇城市
                try:
                    select = Select(fields['citycd'])
                    options = select.options
                    city_found = False
                    
                    for option in options:
                        if city in option.text:
                            select.select_by_visible_text(option.text)
                            logger.info(f"選擇城市: {option.text}")
                            city_found = True
                            break
                    
                    if not city_found:
                        logger.warning(f"找不到城市: {city}")
                        # 選擇第一個非空選項
                        for option in options:
                            if option.text.strip():
                                select.select_by_visible_text(option.text)
                                logger.info(f"選擇第一個有效城市: {option.text}")
                                break
                except Exception as e:
                    logger.error(f"選擇城市時出錯: {e}")
            else:
                logger.warning("找不到城市選擇器")
            
            # 填寫開始年份
            if fields['start_year']:
                fields['start_year'].clear()
                fields['start_year'].send_keys(str(start_year))
                logger.info(f"填寫開始年份: {start_year}")
            else:
                logger.warning("找不到開始年份輸入框")
            
            # 選擇開始月份
            if fields['start_month']:
                Select(fields['start_month']).select_by_value(str(start_month))
                logger.info(f"選擇開始月份: {start_month}")
            else:
                logger.warning("找不到開始月份選擇器")
            
            # 填寫結束年份
            if fields['end_year']:
                fields['end_year'].clear()
                fields['end_year'].send_keys(str(end_year))
                logger.info(f"填寫結束年份: {end_year}")
            else:
                logger.warning("找不到結束年份輸入框")
            
            # 選擇結束月份
            if fields['end_month']:
                Select(fields['end_month']).select_by_value(str(end_month))
                logger.info(f"選擇結束月份: {end_month}")
            else:
                logger.warning("找不到結束月份選擇器")
            
            # 保存填寫表單後的截圖
            form_screenshot = os.path.join("output", f"form_{get_timestamp()}.png")
            driver.save_screenshot(form_screenshot)
            logger.info(f"保存填寫表單後的截圖: {form_screenshot}")
            
            # 點擊查詢按鈕
            if search_button:
                # 使用JavaScript點擊，避免可能的覆蓋問題
                driver.execute_script("arguments[0].click();", search_button)
                logger.info("點擊查詢按鈕")
                time.sleep(DELAY * 2)  # 等待查詢結果加載
                
                # 保存查詢結果截圖
                result_screenshot = os.path.join("output", f"result_{get_timestamp()}.png")
                driver.save_screenshot(result_screenshot)
                logger.info(f"保存查詢結果截圖: {result_screenshot}")
                
                # 檢查查詢結果
                # 優先查找結果表格
                tables = driver.find_elements(By.TAG_NAME, "table")
                if tables:
                    logger.info(f"找到 {len(tables)} 個表格")
                    
                    # 假設第一個表格是結果表格
                    result_table = tables[0]
                    
                    # 提取表頭
                    headers = []
                    try:
                        header_row = result_table.find_element(By.TAG_NAME, "thead").find_element(By.TAG_NAME, "tr")
                        header_cells = header_row.find_elements(By.TAG_NAME, "th")
                        headers = [cell.text.strip() for cell in header_cells]
                    except:
                        # 如果沒有thead，嘗試從第一行提取表頭
                        try:
                            rows = result_table.find_elements(By.TAG_NAME, "tr")
                            if rows:
                                header_cells = rows[0].find_elements(By.TAG_NAME, "th")
                                if not header_cells:
                                    header_cells = rows[0].find_elements(By.TAG_NAME, "td")
                                headers = [cell.text.strip() for cell in header_cells]
                        except:
                            logger.warning("無法提取表頭")
                    
                    logger.info(f"表頭: {headers}")
                    
                    # 提取數據行
                    result_data = []
                    rows = result_table.find_elements(By.TAG_NAME, "tr")
                    
                    for row_index, row in enumerate(rows):
                        # 跳過表頭行
                        if row_index == 0:
                            continue
                        
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if not cells:
                            continue
                        
                        row_data = {}
                        for i, cell in enumerate(cells):
                            if i < len(headers):
                                row_data[headers[i]] = cell.text.strip()
                            else:
                                row_data[f"欄位{i+1}"] = cell.text.strip()
                        
                        result_data.append(row_data)
                    
                    logger.info(f"共提取 {len(result_data)} 行數據")
                    
                    # 返回結果數據
                    return result_data
                else:
                    logger.warning("找不到結果表格")
                    
                    # 檢查是否有無資料提示
                    no_data = driver.find_elements(By.XPATH, "//*[contains(text(), '查無資料')]")
                    if no_data:
                        logger.info("查詢結果: 查無資料")
                    
                    return []
            else:
                logger.warning("找不到查詢按鈕")
                return []
        except Exception as e:
            logger.error(f"處理表單時出錯: {e}")
            return []
    except Exception as e:
        logger.error(f"爬取過程中出錯: {e}")
        return []
    finally:
        if driver:
            driver.quit()
            logger.info("關閉瀏覽器")

def main():
    """主函數"""
    try:
        # 開始時間
        start_time = datetime.now()
        logger.info(f"開始執行爬蟲: {start_time}")
        
        # 爬取臺北市數據
        taipei_data = scrape_presale_data(city="臺北市", start_year=110, start_month=1, end_year=114, end_month=12)
        
        # 保存數據
        if taipei_data:
            taipei_file = os.path.join("output", f"taipei_data_{get_timestamp()}.json")
            save_to_json(taipei_data, taipei_file)
        else:
            logger.warning("未獲取到任何臺北市數據")
        
        # 爬取新北市數據
        new_taipei_data = scrape_presale_data(city="新北市", start_year=110, start_month=1, end_year=114, end_month=12)
        
        # 保存數據
        if new_taipei_data:
            new_taipei_file = os.path.join("output", f"new_taipei_data_{get_timestamp()}.json")
            save_to_json(new_taipei_data, new_taipei_file)
        else:
            logger.warning("未獲取到任何新北市數據")
        
        # 合併數據
        all_data = []
        for item in taipei_data:
            item['城市'] = '臺北市'
            all_data.append(item)
        
        for item in new_taipei_data:
            item['城市'] = '新北市'
            all_data.append(item)
        
        # 保存所有數據
        if all_data:
            all_file = os.path.join("output", f"all_data_{get_timestamp()}.json")
            save_to_json(all_data, all_file)
            logger.info(f"共獲取 {len(all_data)} 條數據")
        else:
            logger.warning("未獲取到任何數據")
        
        # 結束時間
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"爬蟲執行完成，耗時: {duration:.2f} 秒")
    except Exception as e:
        logger.error(f"執行過程中出錯: {e}")

if __name__ == "__main__":
    main()