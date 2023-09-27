from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import pandas as pd
from datetime import datetime
from random import randint
from time import sleep
import os

### OPEN A SELENIUM WINDOW WITH OPTIONS AS NEEDED
options = Options()
options.add_argument('headless')

# Start Selenium webdriver
driver = webdriver.Chrome(options= options,service=Service(ChromeDriverManager().install()))

user_agent = driver.execute_script("return navigator.userAgent;")
user_agent = user_agent.replace("HeadlessChrome","Chrome")
driver.execute_cdp_cmd('Network.setUserAgentOverride',{"userAgent": f'{user_agent}'})

def get_job_postings(url, final_path_location, error_txt_path):
    driver.get(url)

    xpaths_to_scrape = { 
         'job_title'            :'.//h2[contains(@class,"jobTitle")]',
         'company_name'         :'.//span[@class="companyName"]',
         'company_location'     :'.//div[@class="companyLocation"]',
         'salary_snippet'       :'.//div[@class="metadata salary-snippet-container" or @class="metadata estimated-salary-container"]',
         'post_date'            :'.//span[@class="date"]'
        }
    
    page_done = 0
    df = {key:[] for key in xpaths_to_scrape} # data will be added to this dict
    df['date_scraped'] = []

    wait = WebDriverWait(driver, 10)
    while True:
        job_cards_elements = driver.find_elements(By.XPATH,'//div[@class="job_seen_beacon"]')
        for job_card in job_cards_elements:
            for key in xpaths_to_scrape:
                try: # pull data at each path in the xpaths dict for each job posting
                    t = job_card.find_element(By.XPATH, xpaths_to_scrape[key]).text
                except NoSuchElementException: # if can't find, indicate with text
                    t = "NA"
                if t == '': # in cases where element exists but is just ''
                    t = "NA"
                    
                df[key].append(t) # add to data dict
            
            df['date_scraped'].append(datetime.now().strftime("%m/%d/%Y %H:%M:%S")) # adding date scraped

            # click next link
        try:
            element = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@data-testid="pagination-page-next"]')))
            element.click()
            page_done += 1
            print(f'{page_done=}', end='\r') # to visualize how many description pages have been scraped
        except TimeoutException:
            break
        # Sleep a random number of seconds (between 1 and 5)
        sleep(randint(1,5))
    
    scraped_df = pd.DataFrame(df) # convert to df

    path = final_path_location
    if os.path.exists(path):
        original_df = pd.read_csv(path)
        original_df = pd.concat([original_df,scraped_df])
        original_df = original_df.drop_duplicates(subset=['job_title','company_name','company_location','salary_snippet'])
        if original_df.shape[0] == 0:
            with open(error_txt_path,'a') as f:
                f.writelines(datetime.now().strftime("%m/%d/%Y %H:%M:%S") + "\n")
            quit()
        original_df.to_csv(path, index = False)
    else:
        scraped_df.to_csv(path, index = False)

# Indeed Website for New York, NY Jobs. Jobs posted last 24 Hours
WEBSITE_URL = r"https://www.indeed.com/jobs?l=New+York,+NY&radius=0&fromage=1"
compilation_path = r'/home/james/cronjobs/pay_trans_cron/Indeed_scrape_daily_compiliation.csv'
error_path = r'/home/james/cronjobs/pay_trans_cron/error.txt'

get_job_postings(WEBSITE_URL,compilation_path,error_path)

# # OTHER BOROS
# # Brooklyn
# sleep(randint(15,35))
# WEBSITE_URL = r"https://www.indeed.com/jobs?q=&l=Brooklyn%2C+NY&radius=0&fromage=1"
# bk_compilation_path = r'/home/james/cronjobs/pay_trans_cron/Indeed_scrape_bk_compiliation.csv'
# get_job_postings(WEBSITE_URL,bk_compilation_path,error_path)

# # Queens
# sleep(randint(15,35))
# WEBSITE_URL = r'https://www.indeed.com/jobs?q=&l=Queens%2C+NY&radius=0&fromage=1'
# qn_compilation_path = r'/home/james/cronjobs/pay_trans_cron/Indeed_scrape_qn_compiliation.csv'
# get_job_postings(WEBSITE_URL,qn_compilation_path,error_path)

# # Bronx
# sleep(randint(15,35))
# WEBSITE_URL = r'https://www.indeed.com/jobs?l=Bronx%2C+NY&radius=0&fromage=1'
# bx_compilation_path = r'/home/james/cronjobs/pay_trans_cron/Indeed_scrape_bx_compiliation.csv'
# get_job_postings(WEBSITE_URL,bx_compilation_path,error_path)

# # Staten Island
# sleep(randint(15,35))
# WEBSITE_URL = r'https://www.indeed.com/jobs?q=&l=Staten+Island%2C+NY&radius=0&fromage=1'
# si_compilation_path = r'/home/james/cronjobs/pay_trans_cron/Indeed_scrape_si_compiliation.csv'
# get_job_postings(WEBSITE_URL,si_compilation_path,error_path)

# # Manhattan
# sleep(randint(15,35))
# WEBSITE_URL = r'https://www.indeed.com/jobs?q=&l=Manhattan%2C+NY&radius=0&fromage=1'
# mn_compilation_path = r'/home/james/cronjobs/pay_trans_cron/Indeed_scrape_mn_compiliation.csv'
# get_job_postings(WEBSITE_URL,mn_compilation_path,error_path)

# # Compile the boros to 1 csv
# boros_compilation_path = r'/home/james/cronjobs/pay_trans_cron/Indeed_scrape_boros_compiliation.csv'

# bk_df = pd.read_csv(bk_compilation_path)
# bk_df.insert(6,"location","Brooklyn")
# qn_df = pd.read_csv(qn_compilation_path)
# qn_df.insert(6,"location","Queens")
# bx_df = pd.read_csv(bx_compilation_path)
# bx_df.insert(6,"location","Bronx")
# si_df = pd.read_csv(si_compilation_path)
# si_df.insert(6,"location","Staten Island")
# mn_df = pd.read_csv(mn_compilation_path)
# mn_df.insert(6,"location","Manhattan")

# compile_df = pd.concat([bk_df,qn_df,bx_df,si_df,mn_df])
# compile_df.to_csv(boros_compilation_path, index = False)
