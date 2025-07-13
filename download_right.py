# Importing necessary modules at the top of the file
import time  # Added for time.sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
from selenium.common.exceptions import ElementClickInterceptedException
from datetime import datetime  # Added for date manipulations
from read_write_google_sheet import write_to_google_sheet
from datetime import date

# Function to set up the WebDriver
def setup_driver():
    # Setup Chrome options to run headless and disable images
    options = Options()
    options.add_argument("start-maximized")
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--disable-gpu")  # Disable GPU acceleration
    options.add_argument("--no-sandbox")  # Bypass OS security model
    options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    options.add_argument("window-size=1920,1080")  # Set the window size for consistency
    
    # Disable images
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options =options)
    # driver = webdriver.Chrome(service=Service(ChromeDriverManager(driver_version="137.0.7151.40").install()), options=options)
    return driver


def scrape_rights_share_data(right_share_sheet_id):
    print("Scraping All Right Share Data")
    driver = setup_driver()

    try:
        driver.get('https://www.sharesansar.com/existing-issues')
        driver.find_element(By.XPATH, "/html/body/div[2]/div/section[2]/div[3]/div/div/div/div/div[1]/ul/li[2]").click()
        time.sleep(2)

        # Set table length to 50
        element = driver.find_element(By.NAME, 'myTableErs_length')
        dropdown = Select(element)
        dropdown.select_by_visible_text('50')
        WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.ID, 'myTableErs_processing')))
        WebDriverWait(driver, 15).until(EC.invisibility_of_element_located((By.ID, 'myTableErs_processing')))

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        todays_price = soup.find('table', id='myTableErs')

        # Find pagination details
        pages = soup.find(id='myTableErs_paginate')
        try:
            total_pages = int(pages.find_all('a')[-2].text)  # Get the last page number
        except (IndexError, ValueError):
            total_pages = 1  # If there's only one page

        all_data = []
        for page in range(1, total_pages + 1):
            if page > 1:
                # Navigate to next page
                driver.find_element(By.XPATH, '//*[@id="myTableErs_next"]').click()
                WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.ID, 'myTableErs_processing')))
                WebDriverWait(driver, 15).until(EC.invisibility_of_element_located((By.ID, 'myTableErs_processing')))

            # Get the page source and parse with BeautifulSoup
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            table = soup.find('table', id='myTableErs')

            # Scrape table rows
            output_rows = []
            for table_row in table.find_all('tr')[1:]:  # Skip the header row
                columns = table_row.find_all('td')
                output_row = [column.text.strip() for column in columns]
                output_rows.append(output_row)

            # Convert to DataFrame
            single_page_data = pd.DataFrame(output_rows)
            headers_list = [header.text.strip() for header in table.find_all('th')]
            single_page_data.columns = headers_list
            single_page_data.set_index('S.N.', inplace=True)
            all_data.append(single_page_data)

        # Combine all pages' data into a single DataFrame
        # Combine all dataframes
        rights_data = pd.concat(all_data)

        # Convert 'Book Closure Date' to datetime (with error handling)
        rights_data['Book Closure Date'] = pd.to_datetime(
            rights_data['Book Closure Date'],
            errors='coerce'  # optionally add format="%d/%m/%Y" if you know it
        )

        # Extract rows where Book Closure Date is exactly today
        right_book_close = rights_data[rights_data["Book Closure Date"] == pd.Timestamp.today().normalize()]
        right_book_close_today = list(right_book_close.Symbol)

        # Keep only rows with valid dates up to today
        rights_data = rights_data[
            rights_data['Book Closure Date'].notna() &
            (rights_data['Book Closure Date'] <= pd.Timestamp.today())
        ]

        write_to_google_sheet(rights_data, right_share_sheet_id, mode = "overwrite")
        right_data_df = rights_data
        return right_data_df, right_book_close_today

    finally:
        driver.quit()