# scraper.py
# 爬蟲核心類

# scraper.py 開頭部分修改

import os
import time
import pandas as pd
import logging
import traceback
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException

# 嘗試修復 MKL 錯誤
os.environ["MKL_SERVICE_FORCE_INTEL"] = "1"
os.environ["MKL_THREADING_LAYER"] = "sequential"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

from config import BASE_URL, PRESALE_URL, HEADLESS, DELAY, TIMEOUT, MAX_RETRIES
from utils import ensure_dir, get_current_time_str, clean_text, create_filename_with_timestamp

# 設置更詳細的日誌記錄
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("presale_scraper_detailed.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('root')

class PresaleScraper:
    """預售屋建案查詢爬蟲類"""
    
    def __init__(self, headless=HEADLESS):
        """初始化爬蟲
        
        Args:
            headless: 是否使用無頭模式
        """
        self.headless = headless
        self.driver = None
        self.wait = None
        self.setup_driver()
        self.results = []
        
    def setup_driver(self):
        """設置 Selenium WebDriver"""
        options = Options()
        if self.headless:
            options.add_argument('--headless')
        
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # 增加更多設置來提高穩定性
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--window-size=1920,1080')
        
        # 使用者代理設置為常見瀏覽器
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.maximize_window()
            self.wait = WebDriverWait(self.driver, TIMEOUT)
            logging.info("瀏覽器已初始化")
        except Exception as e:
            logging.error(f"初始化瀏覽器失敗: {e}")
            raise e
        
    def goto_presale_page(self):
        """導航到預售屋建案查詢頁面
        
        Returns:
            bool: 是否成功導航
        """
        try:
            # 直接使用正確的 URL
            self.driver.get(PRESALE_URL)
            logging.info(f"已直接訪問預售屋建案查詢頁面: {PRESALE_URL}")
            time.sleep(DELAY * 2)  # 給予足夠的加載時間
            
            # 保存頁面截圖，方便診斷
            screenshot_path = f"presale_page_{get_current_time_str()}.png"
            self.driver.save_screenshot(screenshot_path)
            logging.info(f"已保存預售屋建案查詢頁面截圖: {screenshot_path}")
            
            # 由於 URL 中包含 #pills-saleremark，頁面會自動跳轉到預售屋標籤
            # 但為確保標籤被正確激活，我們仍然嘗試點擊標籤
            try:
                # 在頁面中尋找標籤元素
                tab = self.driver.find_element(By.CSS_SELECTOR, "a[href='#pills-saleremark']")
                if tab:
                    # 使用 JavaScript 點擊標籤
                    self.driver.execute_script("arguments[0].click();", tab)
                    logging.info("已點擊預售屋標籤")
                    time.sleep(DELAY)  # 給予加載時間
                    
                    # 再次保存截圖，確認標籤切換後的頁面
                    tab_screenshot = f"tab_switch_{get_current_time_str()}.png"
                    self.driver.save_screenshot(tab_screenshot)
                    logging.info(f"已保存標籤切換後的截圖: {tab_screenshot}")
            except Exception as e:
                logging.warning(f"點擊標籤時出錯，但標籤可能已經被自動激活: {e}")
            
            # 檢查預售屋標籤內容是否顯示
            try:
                pills_saleremark = self.driver.find_element(By.ID, "pills-saleremark")
                if pills_saleremark.is_displayed():
                    logging.info("預售屋標籤內容已顯示")
                    
                    # 確認標籤內容中是否有表單元素
                    selects = pills_saleremark.find_elements(By.TAG_NAME, "select")
                    inputs = pills_saleremark.find_elements(By.TAG_NAME, "input")
                    buttons = pills_saleremark.find_elements(By.TAG_NAME, "button")
                    
                    logging.info(f"標籤內容包含: {len(selects)} 個select, {len(inputs)} 個input, {len(buttons)} 個button")
                    
                    # 如果標籤內容中有表單元素，則確認已成功導航
                    if selects or inputs or buttons:
                        return True
            except Exception as e:
                logging.warning(f"檢查預售屋標籤內容時出錯: {e}")
            
            # 如果無法通過標籤內容確認，檢查頁面整體是否包含需要的元素
            selects = self.driver.find_elements(By.TAG_NAME, "select")
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            
            if selects or inputs or buttons:
                logging.info(f"頁面包含表單元素: {len(selects)} 個select, {len(inputs)} 個input, {len(buttons)} 個button")
                return True
            
            logging.error("無法確認是否已導航到預售屋建案查詢頁面")
            return False
            
        except Exception as e:
            logging.error(f"導航到預售屋建案查詢頁面時發生錯誤: {e}")
            return False

    def _confirm_presale_page(self):
        """確認是否已在預售屋建案查詢頁面
        
        Returns:
            bool: 是否確認成功
        """
        try:
            # 在標籤切換後，檢查頁面是否包含預售屋查詢相關元素
            
            # 1. 檢查頁面標題或內容是否包含關鍵詞
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            if "預售屋" in page_text and ("查詢" in page_text or "建案" in page_text):
                logging.info("頁面文本包含預售屋相關關鍵詞")
                return True
            
            # 2. 檢查是否有城市或區域選擇器
            try:
                selects = self.driver.find_elements(By.TAG_NAME, "select")
                for select in selects:
                    options = select.find_elements(By.TAG_NAME, "option")
                    option_texts = [opt.text for opt in options]
                    logging.info(f"選擇器選項: {option_texts}")
                    
                    # 如果選項包含城市名稱，則確認為正確頁面
                    if any("臺北" in opt or "台北" in opt or "新北" in opt for opt in option_texts):
                        logging.info("找到包含城市名稱的選擇器")
                        return True
            except:
                pass
            
            # 3. 檢查是否有查詢按鈕
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                if "查詢" in button.text:
                    logging.info("找到查詢按鈕")
                    return True
            
            # 4. 檢查特定的div或表單元素
            pills_saleremark = self.driver.find_elements(By.ID, "pills-saleremark")
            if pills_saleremark:
                logging.info("找到預售屋標籤頁內容(pills-saleremark)")
                return True
            
            logging.warning("無法確認是否在預售屋建案查詢頁面")
            return False
        except Exception as e:
            logging.error(f"確認預售屋頁面時出錯: {e}")
            return False

    def _check_page_elements(self):
        """檢查頁面元素確認是否為預售屋建案查詢頁面
        
        Returns:
            bool: 是否確認為預售屋建案查詢頁面
        """
        try:
            # 檢查常見的頁面元素
            # 1. 檢查是否有select元素
            selects = self.driver.find_elements(By.TAG_NAME, "select")
            if selects:
                logging.info(f"找到 {len(selects)} 個select元素")
                
                # 打印所有select元素的屬性，幫助診斷
                for i, select in enumerate(selects):
                    options = select.find_elements(By.TAG_NAME, "option")
                    option_texts = [opt.text for opt in options]
                    logging.info(f"Select {i+1} 選項: {option_texts}")
                    
                    # 如果選項中包含城市名稱，很可能是城市選擇框
                    if any("臺北" in opt or "台北" in opt or "新北" in opt for opt in option_texts):
                        logging.info("找到疑似城市選擇框")
                        return True
            
            # 2. 檢查是否有輸入框和按鈕
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            
            if inputs and buttons:
                logging.info(f"找到 {len(inputs)} 個input元素和 {len(buttons)} 個button元素")
                
                # 檢查按鈕文字
                button_texts = [btn.text for btn in buttons]
                logging.info(f"按鈕文字: {button_texts}")
                
                if any("查詢" in btn for btn in button_texts):
                    logging.info("找到查詢按鈕")
                    return True
            
            # 3. 檢查頁面文字內容
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            if "預售屋" in page_text or "建案" in page_text:
                logging.info("頁面文字中包含預售屋或建案關鍵詞")
                return True
            
            # 如果以上條件都不滿足，但頁面包含表單元素，也視為成功
            if len(selects) > 0 or len(inputs) > 0:
                logging.info("頁面包含表單元素，假定是預售屋建案查詢頁面")
                return True
                
            logging.warning("無法確認當前頁面是否為預售屋建案查詢頁面")
            return False
            
        except Exception as e:
            logging.error(f"檢查頁面元素時出錯: {e}")
            return False
    
    def select_city(self, city):
        """選擇城市
        
        Args:
            city: 城市名稱，如 "臺北市"
            
        Returns:
            bool: 是否成功選擇
        """
        try:
            # 嘗試多種可能的城市選擇器
            city_selectors = [
                "//select[@id='citycd']",
                "//select[contains(@id, 'city')]",
                "//select[contains(@name, 'city')]",
                "//select[contains(@class, 'city')]"
            ]
            
            city_select = None
            for selector in city_selectors:
                try:
                    city_select = self.driver.find_element(By.XPATH, selector)
                    logging.info(f"找到城市選擇器: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not city_select:
                # 嘗試獲取所有select元素，假設第一個是城市選擇器
                selects = self.driver.find_elements(By.TAG_NAME, "select")
                if selects:
                    city_select = selects[0]
                    logging.info("使用第一個select元素作為城市選擇器")
                else:
                    raise NoSuchElementException("找不到任何select元素作為城市選擇器")
            
            # 選擇城市
            select = Select(city_select)
            options = select.options
            option_texts = [option.text.strip() for option in options]
            logging.info(f"城市選擇器選項: {option_texts}")
            
            if city in option_texts:
                select.select_by_visible_text(city)
                logging.info(f"已選擇城市: {city}")
            else:
                # 如果找不到完全匹配的城市，嘗試部分匹配
                for option_text in option_texts:
                    if city in option_text:
                        select.select_by_visible_text(option_text)
                        logging.info(f"已選擇部分匹配的城市: {option_text}")
                        break
                else:
                    # 如果仍然找不到，選擇第一個非空選項
                    for option_text in option_texts:
                        if option_text.strip():
                            select.select_by_visible_text(option_text)
                            logging.info(f"找不到匹配的城市，選擇第一個非空選項: {option_text}")
                            break
            
            time.sleep(DELAY)
            return True
        except Exception as e:
            logging.error(f"選擇城市時發生錯誤: {e}")
            return False
    
    def select_district(self, district=None):
        """選擇區域（可選）
        
        Args:
            district: 區域名稱，如 "中正區"，None表示不選擇特定區域
            
        Returns:
            bool: 是否成功選擇
        """
        if not district:
            logging.info("未指定區域，跳過區域選擇")
            return True
            
        try:
            # 嘗試多種可能的區域選擇器
            district_selectors = [
                "//select[@id='districtcd']",
                "//select[contains(@id, 'district')]",
                "//select[contains(@name, 'district')]",
                "//select[contains(@class, 'district')]",
                "//select[@id='regioncd']",
                "//select[contains(@id, 'region')]"
            ]
            
            district_select = None
            for selector in district_selectors:
                try:
                    district_select = self.driver.find_element(By.XPATH, selector)
                    logging.info(f"找到區域選擇器: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not district_select:
                # 嘗試獲取所有select元素，假設第二個是區域選擇器
                selects = self.driver.find_elements(By.TAG_NAME, "select")
                if len(selects) > 1:
                    district_select = selects[1]
                    logging.info("使用第二個select元素作為區域選擇器")
                else:
                    logging.warning("找不到區域選擇器，跳過區域選擇")
                    return True  # 無法選擇區域，但不應阻止繼續
            
            # 選擇區域
            select = Select(district_select)
            options = select.options
            option_texts = [option.text.strip() for option in options]
            logging.info(f"區域選擇器選項: {option_texts}")
            
            if district in option_texts:
                select.select_by_visible_text(district)
                logging.info(f"已選擇區域: {district}")
            else:
                # 如果找不到完全匹配的區域，嘗試部分匹配
                for option_text in option_texts:
                    if district in option_text:
                        select.select_by_visible_text(option_text)
                        logging.info(f"已選擇部分匹配的區域: {option_text}")
                        break
                else:
                    logging.warning(f"在選項中找不到匹配的區域: {district}")
            
            time.sleep(DELAY)
            return True
        except Exception as e:
            logging.error(f"選擇區域時發生錯誤: {e}")
            return True  # 選擇區域失敗不應阻止繼續
    
    def set_date_range(self, start_year, start_month, end_year, end_month):
        """設置查詢的日期範圍
        
        Args:
            start_year: 開始年份（民國年）
            start_month: 開始月份
            end_year: 結束年份（民國年）
            end_month: 結束月份
            
        Returns:
            bool: 是否成功設置
        """
        try:
            # 根據截圖，需要設置起始年月和結束年月的輸入框
            
            # 起始年份輸入
            start_year_selectors = [
                "//input[@id='startYrId']",
                "//input[contains(@id, 'startYr')]",
                "//input[contains(@name, 'startYr')]",
                "//input[contains(@placeholder, '起')]"
            ]
            
            for selector in start_year_selectors:
                try:
                    start_year_input = self.driver.find_element(By.XPATH, selector)
                    start_year_input.clear()
                    start_year_input.send_keys(str(start_year))
                    logging.info(f"已設置起始年份: {start_year}")
                    break
                except NoSuchElementException:
                    continue
            else:
                logging.warning("找不到起始年份輸入框")
            
            # 起始月份選擇
            start_month_selectors = [
                "//select[@id='startMonId']",
                "//select[contains(@id, 'startMon')]",
                "//select[contains(@name, 'startMon')]"
            ]
            
            for selector in start_month_selectors:
                try:
                    start_month_select = self.driver.find_element(By.XPATH, selector)
                    Select(start_month_select).select_by_value(str(start_month))
                    logging.info(f"已設置起始月份: {start_month}")
                    break
                except (NoSuchElementException, ValueError):
                    # 如果select_by_value失敗，嘗試select_by_index
                    try:
                        Select(start_month_select).select_by_index(start_month)
                        logging.info(f"已通過索引設置起始月份: {start_month}")
                        break
                    except:
                        continue
            else:
                logging.warning("找不到起始月份選擇框")
            
            # 結束年份輸入
            end_year_selectors = [
                "//input[@id='endYrId']",
                "//input[contains(@id, 'endYr')]",
                "//input[contains(@name, 'endYr')]",
                "//input[contains(@placeholder, '迄')]"
            ]
            
            for selector in end_year_selectors:
                try:
                    end_year_input = self.driver.find_element(By.XPATH, selector)
                    end_year_input.clear()
                    end_year_input.send_keys(str(end_year))
                    logging.info(f"已設置結束年份: {end_year}")
                    break
                except NoSuchElementException:
                    continue
            else:
                logging.warning("找不到結束年份輸入框")
            
            # 結束月份選擇
            end_month_selectors = [
                "//select[@id='endMonId']",
                "//select[contains(@id, 'endMon')]",
                "//select[contains(@name, 'endMon')]"
            ]
            
            for selector in end_month_selectors:
                try:
                    end_month_select = self.driver.find_element(By.XPATH, selector)
                    Select(end_month_select).select_by_value(str(end_month))
                    logging.info(f"已設置結束月份: {end_month}")
                    break
                except (NoSuchElementException, ValueError):
                    # 如果select_by_value失敗，嘗試select_by_index
                    try:
                        Select(end_month_select).select_by_index(end_month)
                        logging.info(f"已通過索引設置結束月份: {end_month}")
                        break
                    except:
                        continue
            else:
                logging.warning("找不到結束月份選擇框")
            
            time.sleep(DELAY)
            return True
        except Exception as e:
            logging.error(f"設置日期範圍時發生錯誤: {e}")
            return False
    
    def submit_search(self):
        """提交查詢並等待結果
        
        Returns:
            bool: 查詢是否成功
        """
        try:
            # 尋找查詢按鈕
            search_button_selectors = [
                "//button[contains(text(), '查詢')]",
                "//input[@type='button' and contains(@value, '查詢')]",
                "//button[contains(@class, 'search')]",
                "//button[contains(@id, 'search')]",
                "//input[contains(@class, 'search')]",
                "//input[contains(@id, 'search')]"
            ]
            
            search_button = None
            for selector in search_button_selectors:
                try:
                    search_button = self.driver.find_element(By.XPATH, selector)
                    logging.info(f"找到查詢按鈕: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not search_button:
                # 嘗試找到所有按鈕，假設文字包含"查詢"的是查詢按鈕
                buttons = self.driver.find_elements(By.XPATH, "//button | //input[@type='button']")
                for button in buttons:
                    button_text = button.text.strip() or button.get_attribute("value")
                    if "查詢" in (button_text or ""):
                        search_button = button
                        logging.info(f"通過文字找到查詢按鈕: {button_text}")
                        break
                
                if not search_button and buttons:
                    # 如果還找不到，嘗試點擊所有可見的按鈕
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            search_button = button
                            logging.info("使用第一個可見的按鈕作為查詢按鈕")
                            break
            
            if not search_button:
                raise NoSuchElementException("找不到查詢按鈕")
            
            # 點擊查詢按鈕
            search_button.click()
            logging.info("已點擊查詢按鈕")
            
            # 等待結果加載
            time.sleep(DELAY * 2)
            
            # 嘗試各種方式確認結果已加載
            table_selectors = [
                "//table",
                "//div[contains(@class, 'table')]",
                "//div[contains(@class, 'result')]",
                "//div[contains(@id, 'result')]"
            ]
            
            for selector in table_selectors:
                try:
                    result_element = self.driver.find_element(By.XPATH, selector)
                    if result_element.is_displayed():
                        logging.info(f"查詢結果已加載 (選擇器: {selector})")
                        return True
                except NoSuchElementException:
                    continue
            
            # 檢查是否有"查無資料"提示
            no_result_selectors = [
                "//div[contains(text(), '查無資料')]",
                "//span[contains(text(), '查無資料')]",
                "//div[contains(@class, 'no-data')]",
                "//div[contains(@class, 'no-result')]"
            ]
            
            for selector in no_result_selectors:
                try:
                    no_result = self.driver.find_element(By.XPATH, selector)
                    if no_result.is_displayed():
                        logging.info(f"查詢結果: 查無資料 (選擇器: {selector})")
                        return True  # 無結果也算查詢成功
                except NoSuchElementException:
                    continue
            
            # 嘗試尋找所有可見的元素，假設如果有很多表格相關元素，則結果已加載
            tr_elements = self.driver.find_elements(By.TAG_NAME, "tr")
            td_elements = self.driver.find_elements(By.TAG_NAME, "td")
            th_elements = self.driver.find_elements(By.TAG_NAME, "th")
            
            if len(tr_elements) > 5 or len(td_elements) > 10 or len(th_elements) > 5:
                logging.info(f"找到 {len(tr_elements)} 個tr元素, {len(td_elements)} 個td元素, {len(th_elements)} 個th元素，假定結果已加載")
                return True
            
            logging.warning("無法確認查詢結果是否加載")
            return False
            
        except Exception as e:
            logging.error(f"提交查詢時發生錯誤: {e}")
            return False
    
    def extract_results_from_current_page(self):
        """提取當前頁面的查詢結果
        
        Returns:
            list: 結果列表
        """
        try:
            # 先等待一下確保頁面加載完成
            time.sleep(DELAY)
            
            # 尋找表格元素
            table_selectors = [
                "//table",
                "//div[@class='table']",
                "//div[contains(@class, 'results')]"
            ]
            
            table = None
            for selector in table_selectors:
                try:
                    tables = self.driver.find_elements(By.XPATH, selector)
                    if tables:
                        # 優先選擇包含較多行的表格
                        table = max(tables, key=lambda t: len(t.find_elements(By.TAG_NAME, "tr")))
                        logging.info(f"找到結果表格 (選擇器: {selector})")
                        break
                except NoSuchElementException:
                    continue
            
            if not table:
                logging.warning("找不到結果表格")
                return []
            
            # 提取表頭
            header_rows = table.find_elements(By.XPATH, ".//tr[th]")
            if not header_rows:
                header_rows = table.find_elements(By.XPATH, ".//tr[1]")  # 假設第一行是表頭
            
            headers = []
            if header_rows:
                header_cells = header_rows[0].find_elements(By.XPATH, ".//th")
                if not header_cells:
                    header_cells = header_rows[0].find_elements(By.XPATH, ".//td")  # 有時表頭也用td
                
                headers = [h.text.strip() for h in header_cells]
                logging.info(f"表頭: {headers}")
            
            if not headers:
                # 如果找不到表頭，使用默認表頭
                headers = ["建案名稱", "地址", "起造人", "總戶數", "使用分區", "主要用途", "主要建材", "申報價格期間", "備註", "建照號碼", "發照日期"]
                logging.warning(f"找不到表頭，使用默認表頭: {headers}")
            
            # 提取數據行
            data_rows = table.find_elements(By.XPATH, ".//tr[td]")
            if not data_rows and len(table.find_elements(By.TAG_NAME, "tr")) > 1:
                # 如果找不到tr[td]，嘗試獲取除第一行外的所有行
                all_rows = table.find_elements(By.TAG_NAME, "tr")
                data_rows = all_rows[1:]
            
            results = []
            for row in data_rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if not cells:
                    continue
                
                row_data = {}
                for i, cell in enumerate(cells):
                    if i < len(headers):
                        header = headers[i]
                        value = cell.text.strip()
                        row_data[header] = value
                    else:
                        # 如果cell數量超過header數量，使用索引作為鍵
                        row_data[f"欄位{i+1}"] = cell.text.strip()
                
                if row_data:
                    results.append(row_data)
            
            logging.info(f"從當前頁面提取了 {len(results)} 條記錄")
            return results
            
        except Exception as e:
            logging.error(f"提取當前頁面結果時發生錯誤: {e}")
            return []
    
    def has_next_page(self):
        """檢查是否有下一頁
        
        Returns:
            bool: 是否有下一頁
        """
        try:
            # 嘗試找到下一頁按鈕/連結
            next_page_selectors = [
                "//a[contains(text(), '下一頁')]",
                "//a[contains(@class, 'next')]",
                "//a[contains(@title, '下一頁')]",
                "//a[text()='>']",
                "//a[contains(text(), '下頁')]"
            ]
            
            for selector in next_page_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed() and "disabled" not in element.get_attribute("class") and element.is_enabled():
                        logging.info(f"找到可用的下一頁元素 (選擇器: {selector})")
                        return True
            
            # 如果找不到明確的下一頁按鈕，檢查所有可能是分頁按鈕的元素
            pagination_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'page')] //a")
            for element in pagination_elements:
                text = element.text.strip()
                if text == ">" or text == "下一頁" or text == "下頁":
                    if element.is_displayed() and "disabled" not in element.get_attribute("class") and element.is_enabled():
                        logging.info(f"找到可用的下一頁元素: {text}")
                        return True
            
            logging.info("沒有找到下一頁元素，已到最後一頁")
            return False
            
        except Exception as e:
            logging.error(f"檢查下一頁時發生錯誤: {e}")
            return False
    
    def go_to_next_page(self):
        """前往下一頁
        
        Returns:
            bool: 是否成功前往下一頁
        """
        try:
            # 嘗試找到下一頁按鈕/連結
            next_page_selectors = [
                "//a[contains(text(), '下一頁')]",
                "//a[contains(@class, 'next')]",
                "//a[contains(@title, '下一頁')]",
                "//a[text()='>']",
                "//a[contains(text(), '下頁')]"
            ]
            
            next_page_element = None
            for selector in next_page_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed() and "disabled" not in element.get_attribute("class") and element.is_enabled():
                        next_page_element = element
                        logging.info(f"找到可用的下一頁元素 (選擇器: {selector})")
                        break
                if next_page_element:
                    break
            
            if not next_page_element:
                # 如果找不到明確的下一頁按鈕，檢查所有可能是分頁按鈕的元素
                pagination_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'page')] //a")
                for element in pagination_elements:
                    text = element.text.strip()
                    if text == ">" or text == "下一頁" or text == "下頁":
                        if element.is_displayed() and "disabled" not in element.get_attribute("class") and element.is_enabled():
                            next_page_element = element
                            logging.info(f"找到可用的下一頁元素: {text}")
                            break
            
            if not next_page_element:
                logging.warning("找不到可用的下一頁元素")
                return False
            
            # 點擊下一頁
            next_page_element.click()
            logging.info("已點擊下一頁")
            
            # 等待頁面刷新
            time.sleep(DELAY * 2)
            
            # 確認頁面已經變化（可以通過檢查某些元素的變化來判斷）
            return True
            
        except Exception as e:
            logging.error(f"前往下一頁時發生錯誤: {e}")
            return False
    
    def scrape_all_pages(self):
        """爬取所有頁面的數據
        
        Returns:
            list: 所有結果
        """
        all_results = []
        
        # 提取第一頁數據
        page_results = self.extract_results_from_current_page()
        all_results.extend(page_results)
        
        # 檢查並處理後續頁面
        page_num = 1
        while self.has_next_page():
            page_num += 1
            logging.info(f"開始爬取第 {page_num} 頁")
            
            if not self.go_to_next_page():
                logging.warning(f"無法前往第 {page_num} 頁，停止爬取")
                break
            
            page_results = self.extract_results_from_current_page()
            all_results.extend(page_results)
            
            # 避免太快請求
            time.sleep(DELAY)
        
        logging.info(f"總共爬取了 {len(all_results)} 條記錄，來自 {page_num} 頁")
        return all_results
    
    def save_to_excel(self, data, filename):
        """將數據保存為Excel文件
        
        Args:
            data: 要保存的數據
            filename: 文件名
            
        Returns:
            bool: 是否成功保存
        """
        try:
            if not data:
                logging.warning("沒有數據可保存")
                return False
                
            df = pd.DataFrame(data)
            df.to_excel(filename, index=False)
            logging.info(f"數據已保存到Excel文件: {filename}")
            return True
        except Exception as e:
            logging.error(f"保存Excel文件失敗: {e}")
            return False
    
    def save_to_csv(self, data, filename, encoding='utf-8-sig'):
        """將數據保存為CSV文件
        
        Args:
            data: 要保存的數據
            filename: 文件名
            encoding: 文件編碼
            
        Returns:
            bool: 是否成功保存
        """
        try:
            if not data:
                logging.warning("沒有數據可保存")
                return False
                
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False, encoding=encoding)
            logging.info(f"數據已保存到CSV文件: {filename}")
            return True
        except Exception as e:
            logging.error(f"保存CSV文件失敗: {e}")
            return False
    
    def save_to_csv_without_pandas(self, data, filename, encoding='utf-8'):
        """將數據保存為CSV文件（不使用Pandas）
        
        Args:
            data: 要保存的數據
            filename: 文件名
            encoding: 文件編碼
            
        Returns:
            bool: 是否成功保存
        """
        try:
            import csv
            if not data:
                logging.warning("沒有數據可保存")
                return False
                
            # 獲取所有可能的列名
            fieldnames = set()
            for item in data:
                fieldnames.update(item.keys())
            fieldnames = sorted(list(fieldnames))
            
            with open(filename, 'w', newline='', encoding=encoding) as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            logging.info(f"數據已保存到CSV文件: {filename}")
            return True
        except Exception as e:
            logging.error(f"保存CSV文件失敗: {e}")
            return False

    def save_to_excel_without_pandas(self, data, filename):
        """將數據保存為Excel文件（不使用Pandas）
        
        Args:
            data: 要保存的數據
            filename: 文件名
            
        Returns:
            bool: 是否成功保存
        """
        try:
            import xlsxwriter
            if not data:
                logging.warning("沒有數據可保存")
                return False
                
            # 獲取所有可能的列名
            fieldnames = set()
            for item in data:
                fieldnames.update(item.keys())
            fieldnames = sorted(list(fieldnames))
            
            # 創建工作簿和工作表
            workbook = xlsxwriter.Workbook(filename)
            worksheet = workbook.add_worksheet()
            
            # 寫入表頭
            for col, header in enumerate(fieldnames):
                worksheet.write(0, col, header)
            
            # 寫入數據
            for row, item in enumerate(data, start=1):
                for col, field in enumerate(fieldnames):
                    worksheet.write(row, col, item.get(field, ''))
            
            workbook.close()
            logging.info(f"數據已保存到Excel文件: {filename}")
            return True
        except Exception as e:
            logging.error(f"保存Excel文件失敗: {e}")
            return False

    def close(self):
        """關閉瀏覽器並釋放資源"""
        if self.driver:
            self.driver.quit()
            logging.info("瀏覽器已關閉")
            self.driver = None

    