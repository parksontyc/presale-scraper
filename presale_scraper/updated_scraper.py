# updated_scraper.py
# 基於實際頁面結構的預售屋爬蟲

import os
import time
import json
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("updated_scraper.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 確保輸出目錄存在
if not os.path.exists("output"):
    os.makedirs("output")
    logger.info("已創建輸出目錄")

def get_timestamp():
    """獲取時間戳"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def save_to_json(data, filename):
    """保存數據到JSON文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info(f"數據已保存到JSON文件: {filename}")
        return True
    except Exception as e:
        logger.error(f"保存JSON文件失敗: {e}")
        return False

def scrape_presale_data():
    """爬取預售屋建案數據"""
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
        wait = WebDriverWait(driver, 30)
        logger.info("瀏覽器已初始化")
        
        # 訪問網站首頁
        driver.get("https://lvr.land.moi.gov.tw/")
        logger.info("已訪問網站首頁")
        time.sleep(5)
        
        # 保存首頁截圖
        driver.save_screenshot("output/homepage.png")
        logger.info("已保存首頁截圖")
        
        # 檢查並點擊預售屋標籤或連結
        try:
            # 尋找所有可見的鏈接
            links = driver.find_elements(By.TAG_NAME, "a")
            presale_link = None
            
            for link in links:
                if link.is_displayed():
                    href = link.get_attribute("href") or ""
                    text = link.text.strip()
                    logger.info(f"鏈接: {text} ({href})")
                    
                    # 如果有預售屋相關字眼
                    if "預售屋" in text or "list.jsp" in href:
                        presale_link = link
                        break
            
            if presale_link:
                # 點擊預售屋相關連結
                driver.execute_script("arguments[0].click();", presale_link)
                logger.info(f"已點擊預售屋連結: {presale_link.text}")
                time.sleep(5)
            else:
                # 如果找不到鏈接，直接訪問URL
                driver.get("https://lvr.land.moi.gov.tw/jsp/list.jsp")
                logger.info("直接訪問list.jsp頁面")
                time.sleep(5)
        except Exception as e:
            logger.warning(f"查找預售屋連結時出錯: {e}")
            # 直接訪問URL
            driver.get("https://lvr.land.moi.gov.tw/jsp/list.jsp")
            logger.info("直接訪問list.jsp頁面")
            time.sleep(5)
        
        # 保存list.jsp頁面截圖
        driver.save_screenshot("output/list_page.png")
        logger.info("已保存list.jsp頁面截圖")
        
        # 從源碼可以看到，需要設置查詢模式為"saleRemark"
        try:
            # 尋找預售屋查詢表單
            qry_type_input = driver.find_element(By.ID, "qryType")
            
            # 如果找到了輸入框，設置為預售屋查詢
            if qry_type_input:
                driver.execute_script("arguments[0].value = 'saleRemark';", qry_type_input)
                logger.info("已設置查詢類型為預售屋(saleRemark)")
            
            # 顯示預售屋查詢區域
            sale_result_post = driver.find_element(By.ID, "SaleResultPost1")
            if not sale_result_post.is_displayed():
                driver.execute_script("arguments[0].style.display = 'block';", sale_result_post)
                logger.info("已顯示預售屋查詢區域")
            
            # 等待預售屋區域顯示
            time.sleep(3)
        except Exception as e:
            logger.warning(f"設置查詢類型時出錯: {e}")
        
        # 保存設置後的頁面截圖
        driver.save_screenshot("output/presale_form.png")
        logger.info("已保存預售屋表單截圖")
        
        # 現在應該可以看到預售屋查詢表單了
        # 嘗試在頁面中查找城市選擇器和其他相關元素
        try:
            # 檢查預售屋表單區域
            sale_result_post = driver.find_element(By.ID, "SaleResultPost1")
            
            # 在預售屋表單中查找選擇器
            selects = sale_result_post.find_elements(By.TAG_NAME, "select")
            logger.info(f"在預售屋表單中找到 {len(selects)} 個select元素")
            
            # 找城市選擇器
            city_select = None
            for select in selects:
                options = select.find_elements(By.TAG_NAME, "option")
                options_text = [opt.text for opt in options]
                logger.info(f"選擇器選項: {options_text}")
                
                if any("臺北" in opt or "台北" in opt or "新北" in opt for opt in options_text):
                    city_select = select
                    logger.info("找到城市選擇器")
                    break
            
            # 選擇臺北市
            if city_select:
                city_select.click()
                time.sleep(1)
                
                options = city_select.find_elements(By.TAG_NAME, "option")
                for option in options:
                    if "臺北" in option.text or "台北" in option.text:
                        option.click()
                        logger.info(f"已選擇城市: {option.text}")
                        break
                
                time.sleep(2)
            else:
                logger.warning("找不到城市選擇器")
            
            # 查找查詢按鈕
            buttons = sale_result_post.find_elements(By.TAG_NAME, "button")
            search_button = None
            
            for button in buttons:
                if "查詢" in button.text:
                    search_button = button
                    logger.info(f"找到查詢按鈕: {button.text}")
                    break
            
            # 點擊查詢按鈕
            if search_button:
                search_button.click()
                logger.info("已點擊查詢按鈕")
                time.sleep(5)
                
                # 保存查詢結果截圖
                driver.save_screenshot("output/search_result.png")
                logger.info("已保存查詢結果截圖")
                
                # 提取結果
                tables = sale_result_post.find_elements(By.TAG_NAME, "table")
                if tables:
                    logger.info(f"找到 {len(tables)} 個結果表格")
                    
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
                        if row_index == 0 and headers:
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
                    
                    # 保存結果
                    if result_data:
                        result_file = os.path.join("output", f"presale_data_{get_timestamp()}.json")
                        save_to_json(result_data, result_file)
                    else:
                        logger.warning("沒有提取到數據")
                    
                    return result_data
                else:
                    logger.warning("找不到結果表格")
                    return []
            else:
                logger.warning("找不到查詢按鈕")
                return []
        except Exception as e:
            logger.error(f"處理預售屋表單時出錯: {e}")
            return []
    except Exception as e:
        logger.error(f"爬取過程中發生錯誤: {e}")
        return []
    finally:
        if driver:
            driver.quit()
            logger.info("瀏覽器已關閉")

def main():
    """主函數"""
    try:
        # 獲取臺北市預售屋數據
        taipei_data = scrape_presale_data()
        
        if taipei_data:
            logger.info(f"成功獲取 {len(taipei_data)} 條預售屋數據")
        else:
            logger.warning("未獲取到任何預售屋數據")
    except Exception as e:
        logger.error(f"執行過程中出錯: {e}")

if __name__ == "__main__":
    main()