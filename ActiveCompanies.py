# Importing necessary modules at the top of the file
import time  # Added for time.sleep
from io import StringIO
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from selenium.common.exceptions import ElementClickInterceptedException
from datetime import datetime  # Added for date manipulations
from read_write_google_sheet import  write_to_google_sheet

# Function to set up the WebDriver
def setup_driver():
  # Setup Chrome
  HEADLESS = True  # Change to False for debugging

  options = Options()
  options.add_argument("start-maximized")
  if HEADLESS:
      options.add_argument("--headless")
  options.add_argument("--disable-gpu")
  options.add_argument("--no-sandbox")
  options.add_argument("--disable-dev-shm-usage")
  options.add_argument("window-size=1920,1080")
  options.add_argument("--remote-debugging-port=9222")
  options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")

  # Disable images
  prefs = {"profile.managed_default_content_settings.images": 2}
  options.add_experimental_option("prefs", prefs)

  # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
  driver = webdriver.Chrome(service=Service(ChromeDriverManager(driver_version="142.0.7241.0").install()), options=options)
  return driver

def active_companies():
    driver = setup_driver()  
    # Open the webpage
    base_url = "https://nepalstock.com/company"
    driver.get(base_url)
    time.sleep(3)
    # Wait for the dropdown to be present
    wait = WebDriverWait(driver, 10)
    dropdown = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/app-root/div/main/div/app-company/div/div[2]/div/div[5]/div/select")))
    
    # Click the dropdown to reveal options
    dropdown.click()
    time.sleep(1)
    # Select '500' from the dropdown using the specific XPath
    option_500 = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/app-root/div/main/div/app-company/div/div[2]/div/div[5]/div/select/option[6]")))
    option_500.click()
    time.sleep(1)
    # Wait for the table to reload with 500 rows
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.table__lg.table-striped.table__border.table__border--bottom")))
    
    # Extract the table HTML
    table_html = driver.find_element(By.CSS_SELECTOR, "table.table__lg.table-striped.table__border.table__border--bottom").get_attribute("outerHTML")
    
    # Use Pandas to read the HTML table
    active_companies_df = pd.read_html(StringIO(table_html))[0]
    
    # Save the DataFrame to a CSV file
    
    # Close the WebDriver
    driver.quit()


# Define the data
    data = {'SN': list(range(1, 15)),
    'Name': [
        'Banking SubIndex', 'Development Bank Index', 'Finance Index', 
        'Hotels And Tourism', 'HydroPower Index', 'Investment', 
        'Life Insurance', 'Manufacturing And Processing', 'Microfinance Index', 
        'Mutual Fund', 'Non Life Insurance', 'Others Index', 
        'Trading Index', 'Nepse Index'
    ],
    'Symbol': [
        'Banking SubIndex', 'Development Bank Index', 'Finance Index', 
        'Hotels And Tourism', 'HydroPower Index', 'Investment', 
        'Life Insurance', 'Manufacturing And Processing', 'Microfinance Index', 
        'Mutual Fund', 'Non Life Insurance', 'Others Index', 
        'Trading Index', 'Nepse Index'
    ],
    'Status': [
        'Active', 'Active', 'Active', 
        'Active', 'Active', 'Active', 
        'Active', 'Active', 'Active', 
        'Active', 'Active', 'Active', 
        'Active', 'Active'
    ],
    'Sector': [
        'Index', 'Index', 'Index', 
        'Index', 'Index', 'Index', 
        'Index', 'Index', 'Index', 
        'Index', 'Index', 'Index', 
        'Index', 'Index'
    ],
    'Instrument': [
        'Index', 'Index', 'Index', 
        'Index', 'Index', 'Index', 
        'Index', 'Index', 'Index', 
        'Index', 'Index', 'Index', 
        'Index', 'Index'
    ]
}

    # Create the DataFrame
    indices_df = pd.DataFrame(data)
    index_and_stock_df = pd.concat([active_companies_df,indices_df ], ignore_index=True)
    return index_and_stock_df

