from price_adjuster import PriceAdjuster
import numpy as np
from download_dividend import update_dividend_history_file
from download_right import scrape_rights_share_data
from ActiveCompanies import active_companies
from read_write_google_sheet import read_google_sheet, write_to_google_sheet
from price_adjuster import PriceAdjuster
import pandas as pd

adjusted_price_sheet_id = "19qf_rGChHLvRGyb8WXHLlYNPCV8Xskozn626v6Ix_dw"
dividend_history_data_sheetID = "1eMRKEPtTaIxG8kTm573b1l9su-OK5AHZo_Fn0gRYb50"
dividend_data_df, dividend_book_closes_today = update_dividend_history_file(dividend_history_data_sheetID)

right_history_sheet_id = "14Ce0luKIoqz6YkukHN9giaYpJUTKtZwhtntSvoP7TV4"
right_data_df, right_book_closes_today = scrape_rights_share_data(right_history_sheet_id)

active_comp_and_indices_df = active_companies()
active_comp_and_indices_df.rename(columns = {"Symbol":"Ticker"}, inplace=True)
active_companies_df = active_comp_and_indices_df[active_comp_and_indices_df['Sector'] != "Index"]
active_companies_tickers = active_companies_df.Ticker


price_history_sheet_id = "1n_QX2H3HEM1wYbEQmHV4fYBwfDzd19sBEiOv4MBXrFo"
unadj_data_df  = read_google_sheet(price_history_sheet_id)
data = unadj_data_df
data['Date'] = pd.to_datetime(data['Date'])
data = data.sort_values(by=['Date'], ascending=True)
columns_except_symbol = data.columns.difference(['Ticker', 'Date', 'Sector'])
data[columns_except_symbol] = data[columns_except_symbol].replace({',': '', '': np.nan}, regex=True).astype(float)
data.set_index('Date', inplace=True)

all_companies_adjusted = []
for company in active_companies_tickers:
    print(company)
    unadjusted_company_price = data[data['Ticker'] == company]
    adjuster = PriceAdjuster(company, unadjusted_company_price, dividend_data_df, right_data_df)
    adjusted_df = adjuster.get_final_adjusted_df()
    all_companies_adjusted.append(adjusted_df)
all_adj_companies_data = pd.concat(all_companies_adjusted)
all_adj_companies_data.index = all_adj_companies_data.index.strftime('%Y-%m-%d')
write_to_google_sheet(all_adj_companies_data, adjusted_price_sheet_id, mode = 'overwrite')

print("Completed")