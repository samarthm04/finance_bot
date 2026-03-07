import os
import json
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Load credentials from Railway environment variable
creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])

creds = Credentials.from_service_account_info(
    creds_dict,
    scopes=SCOPES
)

client = gspread.authorize(creds)

spreadsheet = client.open("FinanceBot")


def save_transaction(data, raw_message, sheet_name):

    sheet = spreadsheet.worksheet(sheet_name)

    row = [
        data["date"],
        data["amount"],
        data["type"],
        data["category"],
        data["description"],
        data["payment_mode"],
        data["tds_percent"],
        raw_message
    ]

    sheet.append_row(row)