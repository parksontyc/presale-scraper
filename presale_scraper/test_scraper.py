# test_scraper.py
# 簡單的測試爬蟲，用於診斷實價登錄網站的頁面結構

import os
import time
import logging
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
        logging.FileHandler("test_scraper.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 要測試的URL
CORRECT_URL = "https://lvr.land.moi.gov.tw/jsp/list.jsp#pills-saleremark"
OLD_URL = "https://lvr.land.moi.gov.tw/service/corporationfr.action"

def main():
    """測試爬蟲主函數"""
    # 設置瀏覽器選項
    options = Options()
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    
    # 使用常見瀏覽器的User-Agent
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36')
    
    driver = None
    try:
        # 初始化瀏覽器
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
        wait = WebDriverWait(driver, 30)
        logger.info("瀏覽器已初始化")
        
        # 首先測試新URL
        logger.info(f"開始測試新URL: {CORRECT_URL}")
        driver.get(CORRECT_URL)
        time.sleep(5)  # 等待頁面加載
        
        # 保存頁面截圖
        driver.save_screenshot("new_url_screenshot.png")
        logger.info("已保存新URL頁面截圖")
        
        # 保存頁面源碼
        with open("new_url_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logger.info("已保存新URL頁面源碼")
        
        # 檢查頁面元素
        logger.info("分析新URL頁面元素...")
        analyze_page_elements(driver)
        
        # 尋找並點擊預售屋標籤
        try:
            logger.info("嘗試找到預售屋標籤...")
            tabs = driver.find_elements(By.CSS_SELECTOR, "a[data-toggle='pill']")
            
            saleremark_tab = None
            for tab in tabs:
                href = tab.get_attribute("href") or ""
                text = tab.text.strip()
                logger.info(f"標籤: 文字='{text}', href='{href}'")
                
                if "pills-saleremark" in href:
                    saleremark_tab = tab
                    break
            
            if saleremark_tab:
                logger.info(f"找到預售屋標籤: {saleremark_tab.text.strip()}")
                # 使用JavaScript點擊標籤
                driver.execute_script("arguments[0].click();", saleremark_tab)
                logger.info("已點擊預售屋標籤")
                time.sleep(5)  # 等待標籤頁內容加載
                
                # 保存標籤切換後的截圖
                driver.save_screenshot("tab_switched_screenshot.png")
                logger.info("已保存標籤切換後的截圖")
                
                # 再次分析頁面元素
                logger.info("分析標籤切換後的頁面元素...")
                analyze_page_elements(driver)
            else:
                logger.warning("找不到預售屋標籤")
        except Exception as e:
            logger.error(f"處理標籤時出錯: {e}")
        
        # 然後測試舊URL
        logger.info(f"開始測試舊URL: {OLD_URL}")
        driver.get(OLD_URL)
        time.sleep(5)  # 等待頁面加載
        
        # 保存頁面截圖
        driver.save_screenshot("old_url_screenshot.png")
        logger.info("已保存舊URL頁面截圖")
        
        # 保存頁面源碼
        with open("old_url_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logger.info("已保存舊URL頁面源碼")
        
        # 檢查頁面元素
        logger.info("分析舊URL頁面元素...")
        analyze_page_elements(driver)
        
        logger.info("測試完成")
    except Exception as e:
        logger.error(f"測試過程中出錯: {e}")
    finally:
        # 關閉瀏覽器
        if driver:
            driver.quit()
            logger.info("瀏覽器已關閉")

def analyze_page_elements(driver):
    """分析頁面元素結構
    
    Args:
        driver: Selenium WebDriver實例
    """
    try:
        # 記錄頁面標題和URL
        logger.info(f"當前頁面標題: {driver.title}")
        logger.info(f"當前頁面URL: {driver.current_url}")
        
        # 檢查select元素
        selects = driver.find_elements(By.TAG_NAME, "select")
        logger.info(f"找到 {len(selects)} 個select元素")
        
        for i, select in enumerate(selects):
            try:
                id_attr = select.get_attribute("id") or ""
                name_attr = select.get_attribute("name") or ""
                class_attr = select.get_attribute("class") or ""
                options = [option.text for option in select.find_elements(By.TAG_NAME, "option")]
                
                logger.info(f"Select {i+1}: id='{id_attr}', name='{name_attr}', class='{class_attr}'")
                logger.info(f"Select {i+1} 選項: {options}")
            except:
                logger.warning(f"無法提取Select {i+1} 的詳細信息")
        
        # 檢查input元素
        inputs = driver.find_elements(By.TAG_NAME, "input")
        logger.info(f"找到 {len(inputs)} 個input元素")
        
        for i, input_elem in enumerate(inputs):
            try:
                id_attr = input_elem.get_attribute("id") or ""
                name_attr = input_elem.get_attribute("name") or ""
                type_attr = input_elem.get_attribute("type") or ""
                placeholder_attr = input_elem.get_attribute("placeholder") or ""
                
                logger.info(f"Input {i+1}: id='{id_attr}', name='{name_attr}', type='{type_attr}', placeholder='{placeholder_attr}'")
            except:
                logger.warning(f"無法提取Input {i+1} 的詳細信息")
        
        # 檢查button元素
        buttons = driver.find_elements(By.TAG_NAME, "button")
        logger.info(f"找到 {len(buttons)} 個button元素")
        
        for i, button in enumerate(buttons):
            try:
                id_attr = button.get_attribute("id") or ""
                class_attr = button.get_attribute("class") or ""
                text = button.text.strip()
                
                logger.info(f"Button {i+1}: id='{id_attr}', class='{class_attr}', text='{text}'")
            except:
                logger.warning(f"無法提取Button {i+1} 的詳細信息")
        
        # 檢查表單元素
        forms = driver.find_elements(By.TAG_NAME, "form")
        logger.info(f"找到 {len(forms)} 個form元素")
        
        for i, form in enumerate(forms):
            try:
                id_attr = form.get_attribute("id") or ""
                name_attr = form.get_attribute("name") or ""
                action_attr = form.get_attribute("action") or ""
                
                logger.info(f"Form {i+1}: id='{id_attr}', name='{name_attr}', action='{action_attr}'")
            except:
                logger.warning(f"無法提取Form {i+1} 的詳細信息")
        
        # 檢查特定ID的元素
        try:
            pills_saleremark = driver.find_element(By.ID, "pills-saleremark")
            logger.info(f"找到pills-saleremark元素: {pills_saleremark.tag_name}")
            
            # 檢查該元素內的子元素
            children = pills_saleremark.find_elements(By.XPATH, "./*")
            logger.info(f"pills-saleremark元素包含 {len(children)} 個直接子元素")
            
            for i, child in enumerate(children):
                logger.info(f"子元素 {i+1}: {child.tag_name}")
        except:
            logger.warning("找不到pills-saleremark元素")
    except Exception as e:
        logger.error(f"分析頁面元素時出錯: {e}")

if __name__ == "__main__":
    main()