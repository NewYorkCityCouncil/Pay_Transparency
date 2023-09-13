import pandas as pd
import numpy as np
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

def scrape_google_jobs(google_jobs_df, postings):
    
    # using sing selenium to launch and scroll through the Google Jobs page
    # url filters: seacrh query "jobs" posted within past day, within 5 miles of New York, NY
    url = 'https://www.google.com/search?q=jobs&oq=google+jobs+data+analyst&aqs=chrome..69i57j69i59j0i512j0i22i30i625l4j69i60.4543j0j7&sourceid=chrome&ie=UTF-8&ibp=htl;jobs&sa=X&ved=2ahUKEwjXsv-_iZP9AhVPRmwGHX5xDEsQutcGKAF6BAgPEAU&sxsrf=AJOqlzWGHNISzgpAUCZBmQA1mWXXt3I7gA:1676311105893#fpstate=tldetail&htivrt=jobs&htichips=city:Owg_06VPwoli_nfhBo8LyA%3D%3D&htischips=city;Owg_06VPwoli_nfhBo8LyA%3D%3D:New%20York_comma_%20NY&htilrad=8.0467&htidocid=1R7H3j_x2GhpVLK0AAAAAA%3D%3D'
    #driver = webdriver.Chrome()
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get(url)

    xpaths = {
     'Role'            :"./div/div[1]/div/div[1]/h2",
     'Company'         :"./div/div[1]/div/div[2]/div[2]/div[1]",
     'Location'        :"./div/div[1]/div/div[2]/div[2]/div[2]",
     'Posted'          :"./div/div[3]/div[1]/span[2]/span",
     'Scraped Salary'  :".//span[@class='LL4CDc' and contains(@aria-label,'Salary')]/span",
     'Job Highlights'  :"./div/div[4]/div[1]/div[2]/g-expandable-container/div/g-expandable-content[2]/span",
     'Job Description' :"./div/div[5]/div/span"
    }

    scrolls_to_do = postings
    scrolls_done = 0
    data = {key:[] for key in xpaths}

    while scrolls_done < scrolls_to_do:
        lis_scr = driver.find_elements(By.XPATH, "//li[@data-ved]//div[@role='treeitem']/div/div")

        for li_scr in lis_scr[scrolls_done:scrolls_done+1]:
            driver.execute_script('arguments[0].scrollIntoView({block: "center", behavior: "smooth"});', li_scr)

            scrolls_done += 1
            print(f'{scrolls_done=}', end='\r')
            time.sleep(.2)     
    
    lis_descr = driver.find_elements(By.XPATH, "//*[@id='gws-plugins-horizon-jobs__job_details_page']")
    
    jobs_done = 0
    
    for li_descr in lis_descr[0:postings]:
        driver.execute_script('arguments[0].scrollIntoView({block: "center", behavior: "smooth"});', li_descr)

        for key in xpaths:

            try:
                t = li_descr.find_element(By.XPATH, xpaths[key]).get_attribute('innerText')
            except NoSuchElementException:
                t = '*missing data*'
            data[key].append(t)
            
        jobs_done += 1
        print(f'{jobs_done=}', end='\r')

    scraped_df = pd.DataFrame(data)
    google_jobs_df = google_jobs_df.append(scraped_df)
    google_jobs_df = google_jobs_df.drop_duplicates() 
    google_jobs_df = google_jobs_df.reset_index().drop(columns=['index'])
    
    return google_jobs_df
