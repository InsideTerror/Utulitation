import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Get the service account JSON key from environment variable
SERVICE_ACCOUNT_INFO = json.loads(os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY'))

# Define required scopes
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/documents']

def create_sheets_service():
    """Creates a Google Sheets service using the service account."""
    try:
        credentials = service_account.Credentials.from_service_account_info(
            SERVICE_ACCOUNT_INFO, scopes=SCOPES
        )
        service = build('sheets', 'v4', credentials=credentials)
        return service
    except HttpError as err:
        print(f"Error creating Sheets service: {err}")
        return None

def create_docs_service():
    """Creates a Google Docs service using the service account."""
    try:
        credentials = service_account.Credentials.from_service_account_info(
            SERVICE_ACCOUNT_INFO, scopes=SCOPES
        )
        service = build('docs', 'v1', credentials=credentials)
        return service
    except HttpError as err:
        print(f"Error creating Docs service: {err}")
        return None

# Example function to log case data to Google Sheets
def log_case_to_sheets(spreadsheet_id, case_data):
    service = create_sheets_service()
    if service:
        sheet = service.spreadsheets()
        try:
            request = sheet.values().append(
                spreadsheetId=spreadsheet_id,
                range="Sheet1!A1",
                valueInputOption="RAW",
                body={"values": [case_data]}
            )
            response = request.execute()
            print("Logged case to Google Sheets:", response)
        except HttpError as err:
            print(f"Error logging case: {err}")

# Example function to log a transcript to Google Docs
def log_transcript_to_docs(doc_id, transcript_text):
    service = create_docs_service()
    if service:
        try:
            document = service.documents().get(documentId=doc_id).execute()
            document['body']['content'].append({'paragraph': {'elements': [{'textRun': {'content': transcript_text}}]}})
            updated_document = service.documents().update(documentId=doc_id, body=document).execute()
            print("Logged transcript to Google Docs:", updated_document)
        except HttpError as err:
            print(f"Error logging transcript: {err}")
