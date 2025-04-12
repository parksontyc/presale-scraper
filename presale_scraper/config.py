# config.py
# 配置文件

# 網站設定
BASE_URL = "https://lvr.land.moi.gov.tw/"
PRESALE_URL = "https://lvr.land.moi.gov.tw/jsp/list.jsp#pills-saleremark"  # 正確的預售屋建案查詢頁面URL

# 爬蟲設定
HEADLESS = False  # 是否使用無頭模式
DELAY = 3  # 操作間隔時間（秒）
TIMEOUT = 30  # 等待元素加載的超時時間（秒）
MAX_RETRIES = 3  # 最大重試次數

# 查詢條件設定
DEFAULT_CITIES = ['臺北市', '新北市']  # 預設城市列表
DEFAULT_DATE_RANGE = {
    'start_year': 110,  # 開始年份（民國年）
    'start_month': 1,   # 開始月份
    'end_year': 114,    # 結束年份（民國年）
    'end_month': 12     # 結束月份
}

# 輸出設定
OUTPUT_EXCEL = "預售屋建案查詢.xlsx"  # 輸出Excel檔案名稱
OUTPUT_CSV = "預售屋建案查詢.csv"      # 輸出CSV檔案名稱