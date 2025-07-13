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
from read_write_google_sheet import read_google_sheet, write_to_google_sheet
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
    # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options =options)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager(driver_version="137.0.7151.40").install()), options=options)
    return driver



# Function to scrape data for a single fiscal year
def scrape_fiscal_year_data(driver, fy):
    driver = setup_driver()
    # Open the target URL (only need to do this once)
    driver.get('https://www.sharesansar.com/proposed-dividend')

    # Navigate to the required section (only need to do this once)
    driver.find_element(By.XPATH, "/html/body/div[2]/div/section[2]/div[3]/div/div/div/div/div[1]/ul/li[2]/a").click()

    # Select fiscal year from dropdown
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'select2-year-container'))).click()
    time.sleep(1)
    # driver.find_element(By.CLASS_NAME, 'select2-search__field').send_keys(fy)    
    # driver.find_element(By.CLASS_NAME, 'select2-search__field').send_keys(Keys.RETURN)

    # Submit the form
    driver.find_element(By.ID, "btn_pd_submit").click()
    time.sleep(1)
    # # Wait for processing spinner to appear and disappear
    # WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.ID, 'myTableFD_processing')))
    # WebDriverWait(driver, 15).until(EC.invisibility_of_element_located((By.ID, 'myTableFD_processing')))
    
    # Set table length to 50
    element = driver.find_element(By.NAME, 'myTableFD_length')
    dropdown = Select(element)
    dropdown.select_by_visible_text('50')
    timel.sleep(1)
    # WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.ID, 'myTableFD_processing')))
    # WebDriverWait(driver, 15).until(EC.invisibility_of_element_located((By.ID, 'myTableFD_processing')))
    
    # Scrape the first page
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # Find pagination details
    pages = soup.find(id='myTableFD_paginate')
    try:
        total_pages = int(pages.find_all('a')[-2].text)  # Get the last page number
    except (IndexError, ValueError):
        total_pages = 1  # If there's only one page

    # Find the table
    table = soup.find('table', id='myTableFD')

    # If there are no rows in the table, skip this fiscal year
    if not table or not table.find_all('tr'):
        pass

    else:
        headers_list = [header.text.strip() for header in table.find_all('th')]
    
        fy_dividends = []  # To store dividends for the fiscal year
    
        # Loop through all pages
        for page in range(1, total_pages + 1):
            if page > 1:
                # Navigate to next page
                driver.find_element(By.XPATH, '//*[@id="myTableFD_next"]').click()
                WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.ID, 'myTableFD_processing')))
                WebDriverWait(driver, 15).until(EC.invisibility_of_element_located((By.ID, 'myTableFD_processing')))
            
            # Get the page source and parse with BeautifulSoup
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            table = soup.find('table', id='myTableFD')
    
            # Scrape table rows
            output_rows = []
            for table_row in table.find_all('tr')[1:]:  # Skip the header row
                columns = table_row.find_all('td')
                output_row = [column.text.strip() for column in columns]
                output_rows.append(output_row)
    
            # Convert to DataFrame
            single_page_data = pd.DataFrame(output_rows)
            single_page_data.columns = headers_list
            single_page_data.set_index('S.N.', inplace=True)
            fy_dividends.append(single_page_data)
    
        # Concatenate all pages for this fiscal year
        if fy_dividends:
            fy_data = pd.concat(fy_dividends)

        else:
            fy_data = None  # No data found for this fiscal year
    
        return fy_data


# Function to scrape data for all fiscal years and combine them
def scrape_fiscal_year_dividend(fiscal_years_list):
    # Initialize WebDriver once for all fiscal years
    driver = setup_driver()
    
    all_year_dividends = []

    # Loop over fiscal years and scrape data
    for fy in fiscal_years_list:
        print(f"Scraping dividend data for fiscal year: {fy}")
        fy_data = scrape_fiscal_year_data(driver, fy)

        if fy_data is not None and not fy_data.empty:
            all_year_dividends.append(fy_data)

    # Combine all fiscal year data
    if all_year_dividends:
        final_data = pd.concat(all_year_dividends)
        return final_data
    else:
        print("No data found for any fiscal year.")
        return None



def sharesansar_fiscal_years():
    driver = setup_driver()
    driver.get('https://www.sharesansar.com/proposed-dividend')
    driver.find_element(By.XPATH, "/html/body/div[2]/div/section[2]/div[3]/div/div/div/div/div[1]/ul/li[2]/a").click()
    time.sleep(2)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    
    fys = soup.find_all('div', class_='form-group col-md-4')[1]
    fy_list = [fy.text.strip().replace('\n\n', '') for fy in fys]
    fiscal_years_list = [year for year in fy_list[3].split() if year]
    
    driver.quit()
    return fiscal_years_list[:fiscal_years_list.index('2067/2068') + 1]


def update_dividend_history_file(sheet_id): 
    recent_two_fy_dividends = scrape_fiscal_year_dividend(sharesansar_fiscal_years()[:2])
    if recent_two_fy_dividends is None or recent_two_fy_dividends.empty:
        print("🚫 No recent dividend data to update.")
        return []

    # Clean 'Book Closure Date'
    recent_two_fy_dividends['Book Closure Date'] = recent_two_fy_dividends['Book Closure Date'] \
        .str.replace(r'\[Closed\]', '', regex=True).str.strip()
    recent_two_fy_dividends.reset_index(drop=True, inplace=True)

    # Read existing data
    historical = read_google_sheet(sheet_id)

    # Remove 'SN' column if it exists
    for df in [historical, recent_two_fy_dividends]:
        df.drop(columns=[col for col in ['SN'] if col in df.columns], inplace=True, errors='ignore')

    # Align columns and concatenate
    all_data = pd.concat(
        [historical.reindex(columns=recent_two_fy_dividends.columns, fill_value=pd.NA), recent_two_fy_dividends],
        ignore_index=True
    )

    # Create helper column for duplicate removal
    all_data['helper'] = all_data['Symbol'].astype(str).str.strip() + all_data['Fiscal Year'].astype(str).str.strip()

    # Remove duplicates based on helper
    all_data = all_data.drop_duplicates(subset='helper', keep='first')

    # Clean and validate 'Book Closure Date'
    bcd = 'Book Closure Date'
    all_data[bcd] = all_data[bcd].replace(["", " ", "TBA", "--", "nan", "NaN", "N/A"], pd.NA)
    all_data = all_data[all_data[bcd].notna()]
    all_data[bcd] = pd.to_datetime(all_data[bcd], format="%Y-%m-%d", errors="coerce")

    # Capture today’s book closure stocks before filtering
    book_close_today = all_data[all_data[bcd] == pd.Timestamp.today().normalize()]
    book_close_stocks_today = list(book_close_today['Symbol'])

    # Filter to keep only rows with past or today’s date
    all_data = all_data[all_data[bcd].notna() & (all_data[bcd] <= pd.Timestamp.today())]
    all_data[bcd] = all_data[bcd].dt.date

    # Reorder and select final columns
    desired_cols = [
        "Symbol", "Company", "Bonus (%)", "Cash (%)", "Total (%)",
        "Announcement Date", "Book Closure Date", "Fiscal Year"
    ]
    all_data = all_data[desired_cols].sort_values(by="Book Closure Date")
    dividend_data_df = all_data
    # Write to Google Sheet
    write_to_google_sheet(all_data, sheet_id, mode = 'overwrite')
    print("✅ Successfully downloaded and updated the dividend history data.")
    
    return dividend_data_df, book_close_stocks_today

