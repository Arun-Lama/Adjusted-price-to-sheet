import numpy as np
import pandas as pd

class PriceAdjuster:
    def __init__(self, ticker, price_history, dividend_data, right_share_data):
        self.ticker = ticker
        self.price_history = price_history
        self.dividend_data = dividend_data
        self.right_share_data = right_share_data

    def _process_dividend_data(self, dividend_type, column_name, adjustment_label):
        df = self.dividend_data[self.dividend_data['Symbol'] == self.ticker]
        if df.empty:
            return pd.DataFrame(columns=['Symbol', 'Adjustment factor', 'BookCloseDate', 'Adjustment Type'])
        df = df[['Symbol', column_name, 'Book Closure Date']].dropna()
        df.rename(columns={'Book Closure Date': 'BookCloseDate', column_name: 'Adjustment factor'}, inplace=True)
        df['Adjustment Type'] = adjustment_label
        return df

    def _cash_dividend_function(self):
        return self._process_dividend_data('Cash (%)', 'Cash (%)', 'Cash Dividend')

    def _bonus_dividend_function(self):
        return self._process_dividend_data('Bonus (%)', 'Bonus (%)', 'Bonus Share')

    def _right_ratio(self, ratio):
        a = list(map(float, ratio.split(':')))
        a = [i for i in a if i != 0]
        return f"{a[0]}:{a[1]}"

    def _right_function(self):
        df = self.right_share_data[self.right_share_data['Symbol'] == self.ticker]
        if df.empty:
            return pd.DataFrame(columns=['Symbol', 'Adjustment factor', 'BookCloseDate', 'Adjustment Type'])
        df = df.copy()
        df['Ratio'] = df['Ratio'].dropna().astype(str)
        df['Right_ratio'] = df['Ratio'].apply(self._right_ratio)
        df.rename(columns={'Book Closure Date': 'BookCloseDate', 'Right_ratio': 'Adjustment factor'}, inplace=True)
        df['Adjustment Type'] = 'aRight Share'
        return df[['Symbol', 'Adjustment factor', 'BookCloseDate', 'Adjustment Type']]

    def _cash_bonus_and_right(self, price_history):
        data_frames = [
            self._cash_dividend_function(),
            self._bonus_dividend_function(),
            self._right_function()
        ]
        
        # Safely handle empty DataFrames and future pandas versions
        if all(df.empty for df in data_frames):
            return pd.DataFrame(columns=['Symbol', 'Adjustment factor', 'BookCloseDate', 'Adjustment Type'])

        # Explicitly filter and concatenate with dtype stability
        non_empty_dfs = [df for df in data_frames if not df.empty]
        combined_df = pd.concat(
            non_empty_dfs,
            ignore_index=True,
            sort=False,  # Explicitly disable sorting for future compatibility
            copy=False  # Optimize performance by avoiding unnecessary copies
        ).replace(",", "", regex=True)  # Chain your cleaning operation
        
        # Convert all dates to Timestamp first
        combined_df["BookCloseDate"] = pd.to_datetime(combined_df["BookCloseDate"], format='%Y-%m-%d', errors='coerce')
        combined_df.replace(",", "", regex=True, inplace=True)
        
        # Get first date from price_history (ensure it's Timestamp)
        first_date = pd.to_datetime(price_history[price_history['Ticker'] == self.ticker].index[0])
        
        # Filter and sort
        combined_df = combined_df[combined_df['BookCloseDate'] > first_date]
        combined_df = combined_df[combined_df['Adjustment factor'] != ""]
        
        # Sort with consistent types
        combined_df = combined_df.sort_values(
            by=['BookCloseDate', 'Adjustment Type'],
            key=lambda x: x if x.name != 'BookCloseDate' else pd.to_datetime(x),
            ascending=[True, False]
        )
        
        return combined_df

    def _data_fragmentation(self, price_history, unique_book_close_dates):
        price_data = price_history
        price_data.sort_index(inplace=True)
        fragmented_data = []
        for index, book_close_date in enumerate(unique_book_close_dates):
            if index == 0:
                partial_data = price_data.loc[price_data.index < book_close_date]
            else:
                date_range = (price_data.index >= unique_book_close_dates[index - 1]) & (price_data.index < book_close_date)
                partial_data = price_data.loc[date_range]
            fragmented_data.append(partial_data)
        last_data = price_data.loc[price_data.index >= unique_book_close_dates[-1]]
        fragmented_data.append(last_data)
        return fragmented_data

    def _final_data_df(self, df, fragmented_data, book_close_dates):
        concat = []
        for index, date in enumerate(df.BookCloseDate):
            adj_type = df.iloc[index, 3]
            adjustment_factor = df.iloc[index, 1]
            book_close = df.iloc[index, 2]
            ticker = df.iloc[index, 0]
            cols_to_convert = ['Open', 'High', 'Low', 'Close']

            if index == 0:
                segmented_price_series = fragmented_data[book_close_dates.index(date)].copy()
            else:
                if date == list(df.BookCloseDate)[index - 1]:
                    segmented_price_series = concat[index - 1]
                else:
                    segmented_price_series = pd.concat([concat[index - 1], fragmented_data[book_close_dates.index(date)]])

            if adj_type == 'Cash Dividend':
                price_day_before_bookclose = list(segmented_price_series[cols_to_convert].Close)[-1]
                segmented_price_series[cols_to_convert] = segmented_price_series[cols_to_convert].astype(float)
                segmented_price_series[cols_to_convert] = segmented_price_series[cols_to_convert] / (1 + float(adjustment_factor) / float(price_day_before_bookclose))
            elif adj_type == 'Bonus Share':
                segmented_price_series[cols_to_convert] /= (1 + float(adjustment_factor) / 100)
            elif adj_type == 'aRight Share':
                right_adjustment = float(adjustment_factor.split(':')[1]) / float(adjustment_factor.split(':')[0])
                segmented_price_series[cols_to_convert] = segmented_price_series[cols_to_convert].astype(float)
                segmented_price_series[cols_to_convert] = (segmented_price_series[cols_to_convert] + (right_adjustment * 100)) / (1 + right_adjustment)

            concat.append(segmented_price_series)

        final_data = pd.concat([concat[-1], fragmented_data[book_close_dates.index(date) + 1]])
        return final_data

    def get_final_adjusted_df(self):
        price_history = self.price_history
        df = self._cash_bonus_and_right(price_history)
        if df.empty:
            adjusted_series = price_history
            adjusted_series.sort_index(inplace=True)
        else:
            book_close_dates = df['BookCloseDate'].drop_duplicates().tolist()
            fragmented_data = self._data_fragmentation(price_history, book_close_dates)
            adjusted_series = self._final_data_df(df, fragmented_data, book_close_dates)
        return adjusted_series