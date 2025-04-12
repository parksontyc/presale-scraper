# check_url.py
# 檢查實價登錄網站的URL響應情況

import requests
import logging
from urllib.parse import urlparse
import time

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("url_check.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_url(url):
    """檢查URL的響應情況
    
    Args:
        url: 要檢查的URL
    """
    logger.info(f"正在檢查URL: {url}")
    
    # 解析URL
    parsed_url = urlparse(url)
    logger.info(f"URL組成: scheme={parsed_url.scheme}, netloc={parsed_url.netloc}, path={parsed_url.path}, fragment={parsed_url.fragment}")
    
    # 添加請求頭
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://lvr.land.moi.gov.tw/'
    }
    
    try:
        # 發送GET請求
        start_time = time.time()
        response = requests.get(url, headers=headers, timeout=30)
        end_time = time.time()
        
        logger.info(f"響應時間: {end_time - start_time:.2f} 秒")
        logger.info(f"狀態碼: {response.status_code}")
        logger.info(f"響應頭: {response.headers}")
        
        # 如果響應成功，保存響應內容
        if response.status_code == 200:
            # 嘗試確定內容類型
            content_type = response.headers.get('Content-Type', '')
            logger.info(f"內容類型: {content_type}")
            
            # 保存響應內容
            with open("response_content.txt", "w", encoding="utf-8") as f:
                f.write(response.text[:10000])  # 只保存前10000個字符
            logger.info("已保存部分響應內容")
            
            # 檢查內容中是否有預售屋相關關鍵詞
            content_lower = response.text.lower()
            keywords = ['預售屋', '建案', 'pills-saleremark', 'corporationfr']
            for keyword in keywords:
                if keyword in content_lower:
                    logger.info(f"響應內容中包含關鍵詞: {keyword}")
                else:
                    logger.info(f"響應內容中不包含關鍵詞: {keyword}")
        else:
            logger.warning(f"請求失敗，狀態碼: {response.status_code}")
    except Exception as e:
        logger.error(f"請求出錯: {e}")

def main():
    """主函數"""
    # 要檢查的URL列表
    urls = [
        "https://lvr.land.moi.gov.tw/",
        "https://lvr.land.moi.gov.tw/service/corporationfr.action",
        "https://lvr.land.moi.gov.tw/jsp/list.jsp",
        "https://lvr.land.moi.gov.tw/jsp/list.jsp#pills-saleremark"
    ]
    
    for url in urls:
        check_url(url)
        logger.info("---")

if __name__ == "__main__":
    main()