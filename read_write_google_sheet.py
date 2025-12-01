from gspread_dataframe import set_with_dataframe, get_as_dataframe
import gspread
import pandas as pd
import os
import base64
import time
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
load_dotenv()

def get_credentials():
    """Decode base64 key from env variable and return Credentials object without writing to disk."""
    key_base64 = os.environ["GCP_SA_KEY_BASE64"]
    key_json = base64.b64decode(key_base64).decode("utf-8")

    import json
    key_dict = json.loads(key_json)

    scopes = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/spreadsheets"
    ]
    creds = Credentials.from_service_account_info(key_dict, scopes=scopes)
    return creds



def read_google_sheet(sheet_id):   
    creds = get_credentials()
    client = gspread.authorize(creds)
    sheet = client.open_by_key(sheet_id).sheet1
    sheet_data = sheet.get_all_values()
    data = pd.DataFrame(sheet_data[1:], columns=sheet_data[0])  # skip header row
    return data


def write_to_google_sheet(df, sheet_id, mode='append', max_retries=3):
    """Write dataframe to Google Sheet with retry logic"""
    
    def prepare_data_for_sheets(df):
        """Convert dataframe to format suitable for Google Sheets API"""
        # Reset index if it has a name
        if df.index.name is not None:
            df_to_write = df.reset_index()
        else:
            df_to_write = df.copy()
        
        # Replace NaN with empty string
        df_to_write = df_to_write.fillna('')
        
        # Convert all values to string (more reliable)
        df_to_write = df_to_write.astype(str)
        
        # Convert to list of lists
        data = [df_to_write.columns.tolist()] + df_to_write.values.tolist()
        return data
    
    for attempt in range(max_retries):
        try:
            creds = get_credentials()
            
            # Use Google Sheets API v4 directly (more reliable)
            service = build('sheets', 'v4', credentials=creds)
            sheet = service.spreadsheets()
            
            # Prepare data
            data = prepare_data_for_sheets(df)
            
            if mode == 'overwrite':
                # Clear existing data
                sheet.values().clear(
                    spreadsheetId=sheet_id,
                    range='A1:Z100000'
                ).execute()
                
                # Write new data
                body = {
                    'values': data
                }
                result = sheet.values().update(
                    spreadsheetId=sheet_id,
                    range='A1',
                    valueInputOption='RAW',
                    body=body
                ).execute()
                
                print(f"✅ Data written (overwritten) to Google Sheet. {result.get('updatedCells')} cells updated.")
                
            elif mode == 'append':
                # Get current data to find next empty row
                client = gspread.authorize(creds)
                gsheet = client.open_by_key(sheet_id)
                worksheet = gsheet.sheet1
                
                # Get all values to find next empty row
                all_values = worksheet.get_all_values()
                next_row = len(all_values) + 1
                
                # Write data starting from next row
                body = {
                    'values': data[1:]  # Skip header for append
                }
                result = sheet.values().update(
                    spreadsheetId=sheet_id,
                    range=f'A{next_row}',
                    valueInputOption='RAW',
                    body=body
                ).execute()
                
                print(f"✅ Data appended to Google Sheet. {result.get('updatedCells')} cells updated.")
            
            return True
            
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print("❌ All retries failed")
                # Fallback to original method
                return fallback_write_to_sheet(df, sheet_id, mode)


def fallback_write_to_sheet(df, sheet_id, mode):
    """Fallback method using gspread_dataframe"""
    try:
        creds = get_credentials()
        client = gspread.authorize(creds)
        sheet = client.open_by_key(sheet_id).sheet1

        if mode == 'overwrite':
            # Write in chunks for large dataframes
            chunk_size = 10000
            total_rows = len(df)
            
            if total_rows > chunk_size:
                print(f"⚠️ Large dataframe detected ({total_rows} rows). Writing in chunks...")
                sheet.clear()
                
                # Write header
                set_with_dataframe(sheet, df.iloc[0:0], include_index=True, include_column_header=True)
                
                # Write data in chunks
                for i in range(0, total_rows, chunk_size):
                    chunk = df.iloc[i:i + chunk_size]
                    existing_data = get_as_dataframe(sheet, evaluate_formulas=True)
                    non_empty_rows = existing_data.dropna(how='all').shape[0]
                    next_row = non_empty_rows + 2
                    
                    set_with_dataframe(sheet, chunk, row=next_row, include_column_header=False)
                    print(f"Chunk {i//chunk_size + 1} written ({len(chunk)} rows)")
                    time.sleep(1)  # Avoid rate limiting
                
                print("✅ Data written (overwritten) to Google Sheet successfully.")
            else:
                sheet.clear()
                set_with_dataframe(sheet, df, include_index=True, include_column_header=True)
                print("✅ Data written (overwritten) to Google Sheet successfully.")
                
        elif mode == 'append':
            existing_data = get_as_dataframe(sheet, evaluate_formulas=True)
            non_empty_rows = existing_data.dropna(how='all').shape[0]
            next_row = non_empty_rows + 2
            set_with_dataframe(sheet, df, row=next_row, include_column_header=False)
            print("✅ Data appended to Google Sheet successfully.")
        
        return True
        
    except Exception as e:
        print(f"❌ Fallback method also failed: {e}")
        return False


def write_new_google_sheet_to_folder(df, sheet_title, folder_id):
    creds = get_credentials()
    client = gspread.authorize(creds)

    spreadsheet = client.create(sheet_title)
    spreadsheet.share('todaysprice-506@todaysprice.iam.gserviceaccount.com', perm_type='user', role='writer')

    drive_service = build('drive', 'v3', credentials=creds)
    file_id = spreadsheet.id

    current_parents = drive_service.files().get(fileId=file_id, fields='parents').execute().get('parents', [])

    drive_service.files().update(
        fileId=file_id,
        addParents=folder_id,
        removeParents=",".join(current_parents),
        fields='id, parents'
    ).execute()

    sheet = spreadsheet.sheet1
    
    # Use our improved write function
    write_to_google_sheet(df, spreadsheet.id, mode='overwrite')

    print(f"Sheet '{sheet_title}' created and moved to folder successfully.")
    print(f"URL: {spreadsheet.url}")