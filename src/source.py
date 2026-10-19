"""Local Excel and authenticated Google Sheets reader."""
import io, json, os
import pandas as pd


def fetch_data(source: str, excel_path: str, sheet_id: str, tab: str) -> pd.DataFrame:
    if source == 'excel':
        return pd.read_excel(excel_path, sheet_name='Sheet1', engine='openpyxl')
    if source != 'sheets':
        raise ValueError('DATA_SOURCE must be excel or sheets')
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    creds_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
    if creds_json:
        creds = service_account.Credentials.from_service_account_info(
            json.loads(creds_json), scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
    else:
        keyfile = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
        if not keyfile:
            raise ValueError('Set GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_SERVICE_ACCOUNT_FILE')
        creds = service_account.Credentials.from_service_account_file(
            keyfile, scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
    client = build('sheets', 'v4', credentials=creds, cache_discovery=False)
    safe_tab = tab.replace("'", "''")
    values = client.spreadsheets().values().get(spreadsheetId=sheet_id, range=f"'{safe_tab}'!A:D").execute().get('values', [])
    if not values:
        raise ValueError('Google Sheet is empty')
    return pd.DataFrame(values[1:], columns=values[0])
