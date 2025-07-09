from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

import time

# 크롬 드라이버 경로
driver_path = '''C:\\Users\\Name\\Downloads\\chromedriver-win64\\chromedriver-win64\\chromedriver.exe'''  # 예: 'C:/chromedriver.exe'

# 크롬 브라우저 실행
service = Service(driver_path)
driver = webdriver.Chrome(service=service)

# 웹페이지 열기
driver.get("https://sugang.snu.ac.kr/")
time.sleep(2)  # 페이지 로딩 대기


button = driver.find_element(By.CLASS_NAME, "total-filter-btn")
button.click()

# button = driver.find_element(By.CLASS_NAME, "cc-btn view-last-semester-btn")
# # button.click()
# driver.execute_script("arguments[0].click();",  button)

wait = WebDriverWait(driver, 10)
button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.view-last-semester-btn")))
button.click()

wait = WebDriverWait(driver, 10)
select_element = wait.until(EC.presence_of_element_located((By.ID, "hSrchOpenShtm")))
select = Select(select_element)
select.select_by_value("U000200002U000300001")

wait = WebDriverWait(driver, 10)
button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "filter-submit-btn")))
button.click()

time.sleep(2)  # 페이지 로딩 대기

course_data = []

def scroll_to_course_data():
    blocks = driver.find_elements(By.CLASS_NAME, "course-info-detail")
    for block in blocks:
        name = block.find_element(By.CLASS_NAME, "course-name").text.strip()
        txts = block.find_elements(By.CLASS_NAME, "txt")
        state = block.find_element(By.CLASS_NAME, "state").text.strip()

        txt_values = [txt.text.strip() for txt in txts]

        temp = {}
        name_split = name.split(" ")
        if len(name_split) == 1:
            temp["graduate_course"] = ""
            temp["course_type"] = ""
            temp["couse_name"] = name_split[0]
        elif len(name_split) == 2:
            temp["graduate_course"] = name_split[0]
            temp["course_type"] = ""
            temp["couse_name"] = name_split[1]
        elif len(name_split) == 3:
            temp["graduate_course"] = name_split[0]
            temp["course_type"] = name_split[1]
            temp["couse_name"] = name_split[2]
        else:
            temp["graduate_course"] = name_split[0]
            temp["course_type"] = name_split[1]
            temp["couse_name"] = ' '.join(name_split[2:])
        
        info1 = txt_values[0] if len(txt_values) > 0 else ""
        info2 = txt_values[1] if len(txt_values) > 1 else ""

        info1_split = info1.split()
        if len(info1_split) == 1:
            temp["professor"] = ""
            temp["major"] = ""
            temp["course_code"] = info1_split[0]
        elif len(info1_split) == 2:
            temp["professor"] = ""
            temp["major"] = info1_split[0]
            temp["course_code"] = info1_split[1]
        elif len(info1_split) == 3:
            temp["professor"] = info1_split[0]
            temp["major"] = info1_split[1]
            temp["course_code"] = info1_split[2]
        else:
            temp["professor"] = " ".join(info1_split[0:-2])
            temp["major"] = info1_split[-2]
            temp["course_code"] = info1_split[-1]

        time = []
        info2_split = info2.split(" ")
        for i in info2_split:
            if ':' in i:
                time.append(i)
        temp["time"] = " ".join(time)

        for i in range(len(info2_split)):
            if info2_split[i] == "수강신청인원/정원(재학생)":
                temp["max_enrollment"] = info2_split[i + 1].split('/')[1] if i + 1 < len(info2_split) else ""
            elif info2_split[i] == "총수강인원":
                temp["total_enrollment"] = info2_split[i + 1] if i + 1 < len(info2_split) else ""
            elif info2_split[i] == "학점":
                temp["credit"] = info2_split[i + 1] if i + 1 < len(info2_split) else ""
        course_data.append(temp)

scroll_to_course_data()
for page_num in range(2,744+1):
    driver.execute_script(f"fnGotoPage({page_num})")
    print(f"Processing page {page_num}...")
    time.sleep(0.5)
    scroll_to_course_data()
    
import csv
with open("courses.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=["graduate_course", "course_type", "couse_name", "professor", "major", "course_code", "time", "max_enrollment", "total_enrollment", "credit"])
    writer.writeheader()
    writer.writerows(course_data)

driver.quit()