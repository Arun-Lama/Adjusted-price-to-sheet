from price_adjuster import PriceAdjuster
import numpy as np
from download_dividend import update_dividend_history_file
from download_right import scrape_rights_share_data
from read_write_google_sheet import read_google_sheet, write_to_google_sheet
import pandas as pd

# Sheet IDs
adjusted_price_sheet_id = "19qf_rGChHLvRGyb8WXHLlYNPCV8Xskozn626v6Ix_dw"
dividend_history_data_sheetID = "1eMRKEPtTaIxG8kTm573b1l9su-OK5AHZo_Fn0gRYb50"
right_history_sheet_id = "14Ce0luKIoqz6YkukHN9giaYpJUTKtZwhtntSvoP7TV4"
price_history_sheet_id = "1n_QX2H3HEM1wYbEQmHV4fYBwfDzd19sBEiOv4MBXrFo"

# Get dividend and right share data
dividend_data_df, dividend_book_closes_today = update_dividend_history_file(dividend_history_data_sheetID)
right_data_df, right_book_closes_today = scrape_rights_share_data(right_history_sheet_id)

# Read price history data
unadj_data_df = read_google_sheet(price_history_sheet_id)

# Sort by Date and get the latest date
unadj_data_df['Date'] = pd.to_datetime(unadj_data_df['Date'])
unadj_data_df = unadj_data_df.sort_values('Date', ascending=True)

# Get the latest available date
latest_date = unadj_data_df['Date'].max()
print(f"Latest date in data: {latest_date}")

# Filter dataframe for the latest date
latest_date_data = unadj_data_df[unadj_data_df['Date'] == latest_date]

# Get tickers from latest date, exclude Index sector
active_companies_tickers = latest_date_data['Ticker'].unique().tolist()

print(f"Number of active companies: {len(active_companies_tickers)}")


# # Convert numeric columns to float
# columns_except_symbol = unadj_data_df.columns.difference(['Ticker', 'Date'])
# unadj_data_df[columns_except_symbol] = unadj_data_df[columns_except_symbol].replace(
#     {',': '', '': np.nan}, regex=True
# ).astype(float)

unadj_data_df.set_index('Date', inplace=True)

# Adjust prices for each company
all_companies_adjusted = []
for company in active_companies_tickers:
    print(f"Processing: {company}")
    unadjusted_company_price = unadj_data_df[unadj_data_df['Ticker'] == company]
    
    # Create PriceAdjuster instance
    adjuster = PriceAdjuster(company, unadjusted_company_price, dividend_data_df, right_data_df)
    
    # Get adjusted data
    adjusted_df = adjuster.get_final_adjusted_df()
    all_companies_adjusted.append(adjusted_df)

# Combine all adjusted data
if all_companies_adjusted:
    all_adj_companies_data = pd.concat(all_companies_adjusted)
    all_adj_companies_data.index = all_adj_companies_data.index.strftime('%Y-%m-%d')
    
    # Write to Google Sheet
    write_to_google_sheet(all_adj_companies_data, adjusted_price_sheet_id, mode='overwrite')
    print(f"✅ Price adjustment completed for {len(active_companies_tickers)} companies!")
else:
    print("❌ No companies to process!")

print("✅ Price adjustment completed successfully!")