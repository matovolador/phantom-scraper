#!/usr/bin/python3.6
## ---- Author ---- ##
## Matias Garafoni - matias.garafoni@gmail.com ##
## ---------------------##
import requests
from bs4 import BeautifulSoup as Soup
import csv
from time import sleep
import traceback
import sys, os
import ssl
import pymysql.cursors
import json
from selenium import webdriver
from wait_for import wait_for
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import StaleElementReferenceException
from datetime import datetime
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.expected_conditions import _find_element
from tendo import singleton

me = singleton.SingleInstance() # will sys.exit(-1) if other instance is running

ROOT_PATH = "/var/www/flask_app/flask_app/"

sys.path.append(ROOT_PATH)

# every print statement is basically a debug feature to see the script output in the terminal.
print ("--------STARTING SCRIPT EXECUTION----------")
script_start = datetime.now()
print(script_start)
options = Options()
options.headless = True



web_url = "https://www.plus500.com/Instruments/" 

print("Initializing Headless Firefox...")
browser = webdriver.Firefox(options=options,executable_path="./geckodriver")
print ("Headless Firefox Initialized")



def tearDown():
    browser.quit()

inputs = []

DEBUG = False

if DEBUG:
    input_file = "_debug_instruments.csv"
else:
    input_file = "instruments.csv"

with open(input_file, 'r') as csvfile:
    input_rows = csv.reader(csvfile, delimiter=',')
    skipped_headers = False
    for row in input_rows:
        if not skipped_headers:
            skipped_headers = True
            continue
        # check that rows are not empty
        if row and row[0]!="" and row[1] != "":
            inputs.append({
                "code":row[0],
                "name":row[1]
            })

if not inputs:
    print("No data was found on instruments.csv. Stopping script execution.")
    # WRITE INTO ERRORS : TODO
    sys.exit()

REPLACE_LINE_BREAKS_WITH_SPACE = True
ENCODE_UTF8 = False


def cleanup_text(text,type_="general"):
    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    if REPLACE_LINE_BREAKS_WITH_SPACE:
        text = '\n'.join(chunk for chunk in chunks if chunk)
    else:
        text = ' '.join(chunk for chunk in chunks if chunk)
    if ENCODE_UTF8:
        return text.encode('utf-8')
    else:
        return text


code_count = len(inputs)
#code_count = 1 # debug

code_index = 0

errors = []

# data table nagivation is done by table id daily-cal{index} where index goes from 0 (Sunday) to 6 (Saturday)

output = []


class text_present(object):
    def __init__(self, locator):
        self.locator = locator

    def __call__(self, driver):
        sleep(3)
        try:
            actual_text = _find_element(driver, self.locator).text
            return actual_text != ""
        except Exception:
            return False

while code_index < code_count:
    data_retrieved = False
    read_from = web_url +inputs[code_index]['code']
    print(read_from)
    browser.get(read_from)
    delay = 10 # seconds
    try:
        myElem = WebDriverWait(browser, delay).until(EC.presence_of_element_located((By.CLASS_NAME, 'inst-rate')))
        WebDriverWait(browser,delay).until(text_present((By.CLASS_NAME,"inst-rate")))
        print ("Page is ready!")
    except TimeoutException:
        print ("Loading took too much time!")
    html = browser.page_source
    soup = Soup(html,features="lxml")
    
    try:
        value_data = cleanup_text(soup.findAll("span",{"class":"inst-rate"})[0].get_text())
        print(value_data)
        data_retrieved = True
        output.append({
            "code":inputs[code_index]['code'],
            "name": inputs[code_index]['name'],
            "rate": value_data
        })
    except Exception as e:
            print(e)
            data_retrieved = False
            errors.append("Error reading url: "+str(read_from)+"- "+str(e))
    # only sleep if we are going to scrape another page:
    code_index +=1
    if code_index < code_count:
        print("sleeping 4 seconds before scraping another instrument's data...")
        sleep(4)

if output:
    result ={
        "data_time": str(datetime.now()),
        "result": output
    }
    with open(ROOT_PATH+'static/files/data_instruments.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
else:
    print("Data could not be retrieved. Skipping writting into files.")
    
if errors:
    with open(ROOT_PATH+"static/files/errors_instruments.txt","w") as f:
        for entry in errors:
            f.write(str(datetime.now)+": "+entry+"\n")
else:
    try:
        os.remove(ROOT_PATH+"static/files/errors_instruments.txt")
    except Exception:
        pass

tearDown() # shut down the selenium driver

## Delete the geckodriver log
try:
    os.remove(ROOT_PATH+"geckodriver.log")
except Exception:
    pass

script_end = datetime.now()
print(script_end)
print("Execution Time (seconds):")
print((script_end - script_start).total_seconds())
exit()
