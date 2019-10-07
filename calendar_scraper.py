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
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from tendo import singleton
import itertools
from selenium.webdriver.common.action_chains import ActionChains

me = singleton.SingleInstance() # will sys.exit(-1) if other instance is running

script_start = datetime.now()

ROOT_PATH = "/var/www/flask_app/flask_app/"

sys.path.append(ROOT_PATH)

# every print statement is basically a debug feature to see the script output in the terminal.
print ("--------STARTING SCRIPT EXECUTION----------")
print("Start time:")
print(script_start)

options = Options()
options.headless = True

errors = []

web_url = "https://www.dailyfx.com/economic-calendar" 

print("Initializing Headless Firefox...")
browser = webdriver.Firefox(options=options,executable_path="./geckodriver")

browser.get(web_url)
print ("Headless Firefox Initialized")

print("Wait for full page load...")
try:
    WebDriverWait(browser,30).until(EC.presence_of_element_located((By.XPATH,"//div[@class='dfx-loading jsdfx-economicCalendar__loading dfx-loading--loaded']")))
    print("page loaded")
except Exception as e:
    errors.append(
        "Could not finish loading page. Timeout Exception"
    )

REPLACE_LINE_BREAKS_WITH_SPACE = True
ENCODE_UTF8 = False
GROUP_BY_DAY = False

def click_through_to_new_page(link_text,link_index):
    link = browser.find_elements_by_class_name(link_text)[link_index] 
    link.click()
    def link_has_gone_stale():
        try:
            # poll the link with an arbitrary call
            link.find_elements_by_id('doesnt-matter')
            print("Link aint stale")
            return False
        except StaleElementReferenceException:
            print("link stale")
            return True
    print("waiting link stale state..")
    wait_for(link_has_gone_stale)

def tearDown():
        browser.quit()

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

def xpath_soup(element):
    """
    Generate xpath of soup element
    :param element: bs4 text or node
    :return: xpath as string
    """
    components = []
    child = element if element.name else element.parent
    for parent in child.parents:
        """
        @type parent: bs4.element.Tag
        """
        previous = itertools.islice(parent.children, 0, parent.contents.index(child))
        xpath_tag = child.name
        xpath_index = sum(1 for i in previous if i.name == xpath_tag) + 1
        components.append(xpath_tag if xpath_index == 1 else '%s[%d]' % (xpath_tag, xpath_index))
        child = parent
    components.reverse()
    return '/%s' % '/'.join(components)


html = browser.page_source
soup = Soup(html,features="lxml")

output = []

events = soup.findAll("tr",{"class":"dfx-expandableTable__row"})
# print(events)
data_retrieved = False
# assing time variable here:
time_string = ""
event_time = ""
if errors:
    events = []
event_iter = -1

summary_found_count = 0
duplicate_results = 0

for event in events:
    event_iter += 1
    ## debuging stuff
    # if event_iter > 0:
    #     print("-----Summaries found-----")
    #     print(summary_found_count)
    #     print("-------------------")


    # print("--------------------------------------------------------------------------------")
    x_event = browser.find_element_by_xpath(xpath_soup(event))
    original_class = x_event.get_attribute("class")
    new_class = "dfx-expandableTable__row--active"
    browser.execute_script("arguments[0].classList.add('"+new_class+"');", x_event)
    # reload
    event = soup.findAll("tr",{"class":"dfx-expandableTable__row"})[event_iter]
    # print(event)

    try:
        # some rows contain more than 2 events at the same time, so one or more of them dont have a time entry. here we should use the previous retrieved time entry
        try:
            time_string = event.findAll("td")[0].find("span",{"class":"dfx-economicCalendarRow__time"}).attrs['data-time']
            event_time = time_string[0:time_string.find(".")].replace("T"," ")
        except Exception as e:
            # print(e)
            # print("This entry is from another time")
            pass
        

        element = event.find("div",{"class":"dfx-economicCalendarRow__element"})

        x_element = browser.find_element_by_xpath(xpath_soup(element))

        # click on this div:
        browser.execute_script("arguments[0].click();",x_element)
        # reload element:
        x_element = browser.find_element_by_xpath(xpath_soup(element))
        element = event.find("div",{"class":"dfx-economicCalendarRow__element"})


        event_importance = element.find("span",{"class":"dfx-importance"}).get_text()
        event_title_div = element.find("div",{"class":"dfx-economicCalendarRow__title"})
        event_title = event_title_div.get_text()
        # Get data-id attrib in order to fetch "expandable content" for "summary" retrieval:
        data_id_attrib = event.attrs['data-id']
        # print("data-id")
        # print(data_id_attrib)

        extra_content = soup.find("tr",{"class":"dfx-expandableTable__rowAdditional","data-id":data_id_attrib})
        x_extra_content = browser.find_element_by_xpath(xpath_soup(extra_content))
        x_extra_content = browser.find_element_by_xpath(xpath_soup(extra_content))
        # print(x_extra_content.get_attribute("class"))

        # reload element:
        extra_content = soup.find("tr",{"class":"dfx-expandableTable__rowAdditional","data-id":data_id_attrib})

        # print(extra_content)

        extra_content_div = extra_content.find("div",{"class":"dfx-expandableTable__rowAdditionalContent"})
        # print(extra_content_div)
        x_extra_content_div = browser.find_element_by_xpath(xpath_soup(extra_content_div))
        # print(x_extra_content_div.get_attribute("class"))
        # print(x_extra_content_div.get_attribute("class"))


        # reload 
        extra_content_div = extra_content.find("div",{"class":"dfx-expandableTable__rowAdditionalContent"})

        # print(extra_content_div)

        # reload element:
        extra_content = soup.find("tr",{"class":"dfx-expandableTable__rowAdditional","data-id":data_id_attrib})

        summary = ""
        if extra_content:

            summary_div = extra_content.find("div",{"class":"jsdfx-economicCalendarRow__additionalContent"})
            x_sum_div = browser.find_element_by_xpath(xpath_soup(summary_div))
            #wait for loaded classes to be present:
            # print("wait for loaded classes to be present:")
            # print(x_sum_div.get_attribute("class"))
            WebDriverWait(browser,10).until(lambda wd: x_sum_div.get_attribute("class").find("dfx-loading--loaded")!=-1)
            summary = x_sum_div.get_attribute("innerText")
            if summary:
                # print("Summary found")
                summary_found_count += 1
                # print(summary)
        else:
            print("Element not found")
        event_numbers = element.findAll("div",{"class":"dfx-economicCalendarRow__numeric"})
        event_actual = event_numbers[0].get_text()
        event_forecast = event_numbers[1].get_text()
        event_previous = event_numbers[2].get_text()
        event_currency = event_title[:3]
        
        # Skip LOW importance events:
        if cleanup_text(event_importance).upper() != "LOW":
            # prebuild result object
            print("Event retrieved")
            day_entry = event_time[0:event_time.find(" ")]
            event_object = {
                "time": cleanup_text(event_time),
                "event": cleanup_text(event_title),
                "importance" : cleanup_text(event_importance).upper(),
                "currency": cleanup_text(event_currency).upper(),
                "actual": cleanup_text(event_actual).replace("\n"," ").replace("Actual:","").replace(" ",""),
                "forecast": cleanup_text(event_forecast).replace("\n"," ").replace("Forecast:","").replace(" ",""),
                "previous": cleanup_text(event_previous).replace("\n"," ").replace("Previous:","").replace(" ",""),
                "summary": cleanup_text(summary).replace("\n"," ")
            }
            if GROUP_BY_DAY:
                data_inserted = False
                if not output:
                    # empty object.. insert new entry
                    output.append({
                        "day":day_entry,
                        "events": [event_object]
                    })
                    data_inserted = True
                else:
                    # find if day is already registered:
                    for entry in output:
                        if day_entry in entry['day']:
                            if event_object in entry['events']:
                                #duplicate found
                                duplicate_results +=1
                                data_inserted = False
                                print("Skipping result since it already exists in output object")
                                break
                            # append to "events"
                            entry['events'].append(event_object)
                            data_inserted = True
                            break
                    if not data_inserted:
                        # insert event with new day record:
                        output.append({
                            "day":day_entry,
                            "events":[event_object]
                        })
            else:
                if event_object not in output:
                    output.append(event_object)
                else:
                    #duplicate found
                    duplicate_results +=1
                    print("Skipping result since it already exists in output object")
        else:
            print("Event skipped. Reason: Low priority")
            pass
        data_retrieved = True
        # print(output)
    except Exception as e:
        print("ERROR:")
        print ('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
        print(e)
        errors.append(str(e))
        # print(event)
# print(output)
print("-----Summaries found-----")
print(summary_found_count)
print("------Duplicates found----")
print(duplicate_results)
print("-------------------")
# dont write into the new file if errors were detected
if data_retrieved and not errors:
    result ={
        "data_time": str(datetime.now()),
        "result": output
    }
    
    with open(ROOT_PATH+'static/files/data_calendar.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)


if errors:
    with open(ROOT_PATH+"static/files/errors_calendar.txt","w") as f:
        for entry in errors:
            f.write(str(datetime.now)+": "+entry)
else:
    try:
        os.remove(ROOT_PATH+"static/files/errors_calendar.txt")
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