from typing import List
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def get_web_elements(driver, by_type, value, wait_time=10) -> List:
    try:
        wait = WebDriverWait(driver, wait_time)
        return wait.until(EC.presence_of_all_elements_located((by_type, value)))
    except:
        return []
