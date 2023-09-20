import pandas as pd
import numpy as np
import regex as re
import datetime as dt
import requests
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# url filters: jobs posted within past day, within 15 miles of New York, NY
google_jobs_url = 'https://www.google.com/search?q=jobs&oq=google+jobs+data+analyst&aqs=chrome..69i57j69i59j0i512j0i22i30i625l4j69i60.4543j0j7&sourceid=chrome&ie=UTF-8&ibp=htl;jobs&sa=X&ved=2ahUKEwjXsv-_iZP9AhVPRmwGHX5xDEsQutcGKAF6BAgPEAU&sxsrf=AJOqlzWGHNISzgpAUCZBmQA1mWXXt3I7gA:1676311105893#fpstate=tldetail&htivrt=jobs&htichips=city:Owg_06VPwoli_nfhBo8LyA%3D%3D,date_posted:today&htischips=city;Owg_06VPwoli_nfhBo8LyA%3D%3D:New%20York_comma_%20NY,date_posted;today&htilrad=24.1401&htidocid=9dwQD_uVzp1Nu-9BAAAAAA%3D%3D'

# path to CSVs where Google Jobs datasets will be held
descr_df_path = '/home/rachel/pay-transparency/data/output/google-jobs-cronjob.csv' 
scroll_df_path = '/home/rachel/pay-transparency/data/output/google-jobs-extra-cols-cronjob.csv'

# function that scrapes data from Google Jobs

def scrape_google_jobs(url, scroll_path_location, descr_path_location, postings):
    
# url: web url to the google jobs page that will be scraped (str)
# scroll_path_location: path to the CSV file where the data scraped from the scroll section of Google Jobs will be stored (str)
# descr_path_location: path to the CSV file where the data scraped from the job description section of Google Jobs will be stored (str)
# postings: number of job postings to be scraped -> can be increased by increments of 10 starting at 20, going up to limit of 150 (int)
    
    options = Options() # preparing to run in headless browser
    options.add_argument('headless') 

    # using sing selenium to launch and scroll through the Google Jobs page
    url = url
    driver = webdriver.Chrome(options=options)
    
    user_agent = driver.execute_script("return navigator.userAgent;")
    user_agent = user_agent.replace("HeadlessChrome","Chrome")
    driver.execute_cdp_cmd('Network.setUserAgentOverride',{"userAgent": f'{user_agent}'})
    
    driver.get(url)
    
    # column names and paths to desired data on scroll section of website
    xpaths_scr = {
         'Role'            :"./div[2]",
         'Company'         :"./div[4]/div/div[1]",
         'Source'          :"./div[4]/div/div[3]",
         'Full / Part Time':".//*[name()='path'][contains(@d,'M20 6')]/ancestor::div[1]",
        }
    
    scrolls_to_do = postings # setting number of job postings to be scraped
    scrolls_done = 0
    data_scr = {key:[] for key in xpaths_scr} # data will be added to this dict
    
    # stay in while loop until desired number of postings have been scrolled to
    while scrolls_done < scrolls_to_do: 
        lis_scr = driver.find_elements(By.XPATH, "//li[@data-ved]//div[@role='treeitem']/div/div") # path to section of page where user can scroll through job postings 

        if (len(lis_scr) == scrolls_done) and (scrolls_to_do - scrolls_done) > 0: # in case the postings variable exceeds number of available job posting entries (otherwise code will be stuck in infinite loop)
        
            # print('\nNote: requested # of postings greater than available postings')
            scrolls_to_do = len(lis_scr) # resetting scrolls_to_do to the max length of lis_scr so can break out of while loop
            
        # scrolling down the page to make desired number of job postings load, therefore making them accessible for scraping
        for li_scr in lis_scr[scrolls_done:]:
            driver.execute_script('arguments[0].scrollIntoView({block: "center", behavior: "smooth"});', li_scr) 

            for key in xpaths_scr:
                try: # pull data at each path in the xpaths dict for each job posting
                    t = li_scr.find_element(By.XPATH, xpaths_scr[key]).get_attribute('innerText')
                except NoSuchElementException: # if can't find, indicate with text
                    t = '*missing data*'
                    
                data_scr[key].append(t) # add to data dict
            
            scrolls_done += 1
            print(f'{scrolls_done=}', end='\r') # to visualize how many scrolls have been performed
            time.sleep(.2)    
            
    scr_scraped_df = pd.DataFrame(data_scr) # convert to df
    
    print('')
    
    ####
    
    # column names and paths to desired data in job description page section of website
    xpaths_descr = { 
         'Role'               :"./div/div[1]/div/div[1]/h2",
         'Company'            :"./div/div[1]/div/div[2]/div[2]/div[1]",
         'Location'           :"./div/div[1]/div/div[2]/div[2]/div[2]",
         'Posted'             :"./div/div[3]/div[1]/span[2]/span",
         'All Sources Listed' :".//div[@class='B8oxKe BQC79e xXyUwe']",
         'Scraped Salary'     :".//span[@class='LL4CDc' and contains(@aria-label,'Salary')]/span",
         'Job Highlights'     :"./div/div[4]/div[1]/div[2]/g-expandable-container/div/g-expandable-content[2]/span",
         'Job Description'    :"./div/div[5]/div/span",
         'Any Other Text'     :"./div/div[4]" 
        }
    
    descr_done = 0
    data_descr = {key:[] for key in xpaths_descr} # data will be added to this dict
    data_descr['Date Scraped'] = []
    
    lis_descr = driver.find_elements(By.XPATH, "//*[@id='gws-plugins-horizon-jobs__job_details_page']") # path to description page for each job 
    
    for li_descr in lis_descr[0:scrolls_to_do]: # looping through desired number of job description pages
    
        for key in xpaths_descr:

            try: # pull data at each path in the xpaths dict for each job posting
                t = li_descr.find_element(By.XPATH, xpaths_descr[key]).get_attribute('innerText')
            except NoSuchElementException: # if can't find, indicate with text
                t = '*missing data*'
            if t == '': # in cases where element exists but is just ''
                t='*missing data*'
                
            data_descr[key].append(t) # add to data dict
            
        data_descr['Date Scraped'].append(dt.datetime.now()) # adding date scraped
            
        descr_done += 1
        print(f'{descr_done=}', end='\r') # to visualize how many description pages have been scraped
        time.sleep(.2)
        
    descr_scraped_df = pd.DataFrame(data_descr) # convert to df
    
    for ind in descr_scraped_df.index: # Any Other Text collects full text for posting... only worth keeping if Job Highlights and Description are both empty, otherwise redundant info just taking up space
        
        if (descr_scraped_df['Job Highlights'][ind] != '*missing data*') or (descr_scraped_df['Job Description'][ind] != '*missing data*'):
            
            descr_scraped_df.loc[ind, 'Any Other Text'] = np.nan # erasing this text if either Job Highlights or Job Description is present
    
    scr_path = scroll_path_location 
    
    if os.path.exists(scr_path): # if CSV already exists at the specified path, add the new data found in scr_scraped_df
        scr_original_df = pd.read_csv(scr_path) # convert existing CSV to df
        scr_original_df = pd.concat([scr_original_df,scr_scraped_df]) # add new data
        scr_original_df = scr_original_df.drop_duplicates() # drop entries with identical data 
        scr_original_df.to_csv(scr_path, index = False) # redownloading updated df to the specified path
    else: # otherwise, create new file at this path (for first time function is run)
        scr_scraped_df.to_csv(scr_path, index = False) 
        
    descr_path = descr_path_location 
    
    if os.path.exists(descr_path): # if CSV already exists at the specified path, add the new data found in descr_scraped_df 
        descr_original_df = pd.read_csv(descr_path) # convert existing CSV to df
        descr_original_df = pd.concat([descr_original_df,descr_scraped_df]) # add new data
        # drop entries with identical data in these columns... leaving Posted and All Sources Listed out of this in case duplicates are posted at dif times/ from dif sites
        descr_original_df = descr_original_df.drop_duplicates(subset=['Role','Company','Location','Scraped Salary','Job Highlights','Job Description', 'Any Other Text']) 
        descr_original_df.to_csv(descr_path, index = False) # redownloading updated df to the specified path
    else: # otherwise, create new file at this path (for first time function is run)
        descr_scraped_df.to_csv(descr_path, index = False)  
    
    return  

scrape_google_jobs(google_jobs_url, scroll_df_path, descr_df_path, 150)
