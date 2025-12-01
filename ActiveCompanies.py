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

# To (use valid version):
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

    # CHANGE THIS LINE - Remove version specification
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver


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

