import os
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/documents']

def load_service_account():
    credentials_info = {
            "type": os.getenv("GOOGLE_TYPE"),
    "project_id": os.getenv("GOOGLE_PROJECT_ID"),
    "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("GOOGLE_PRIVATE_KEY").replace("\\n", "\n"),  # Handle newlines in the private key
    "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
    "auth_uri": os.getenv("GOOGLE_AUTH_URI"),
    "token_uri": os.getenv("GOOGLE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("GOOGLE_AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.getenv("GOOGLE_CLIENT_X509_CERT_URL"),
    "universe_domain": os.getenv("GOOGLE_UNIVERSE_DOMAIN")
    }
    return Credentials.from_service_account_info(credentials_info, scopes=SCOPES)

creds = load_service_account()
gs = gspread.authorize(creds)

def log_case_creation(case_id, author, title, timestamp):
    sh = gs.open("CATS Hearing Logs")
    sheet = sh.sheet1
    sheet.append_row([str(timestamp), case_id, author, title, "Created"])

def log_case_closure(case_id, timestamp):
    sh = gs.open("CATS Hearing Logs")
    sheet = sh.sheet1
    sheet.append_row([str(timestamp), case_id, "", "", "Closed"])

def log_participant(channel_name, participant, action):
    sh = gs.open("CATS Hearing Logs")
    sheet = sh.sheet1
    sheet.append_row([str(datetime.utcnow()), channel_name, participant, action])

def log_message(channel_name, author, message, timestamp):
    sh = gs.open("CATS Hearing Logs")
    sheet = sh.sheet1
    sheet.append_row([str(timestamp), channel_name, author, message])

def append_transcript(case_id, author, message):
    from googleapiclient.discovery import build
    docs_creds = load_service_account()
    service = build('docs', 'v1', credentials=docs_creds)
    doc = service.documents().get(documentId=os.getenv("HEARING_DOC_ID")).execute()
    doc_content = doc.get("body").get("content")

    requests = []
    case_heading = f"Case {case_id}"
    location_index = None

    for element in doc_content:
        if 'paragraph' in element:
            elements = element['paragraph'].get('elements', [])
            for e in elements:
                text_run = e.get('textRun')
                if text_run and case_heading in text_run.get('content', ''):
                    location_index = doc_content.index(element) + 1

    if location_index is None:
        requests.append({"insertText": {"location": {"index": 1}, "text": case_heading + "\n"}})
        location_index = 2

    requests.append({
        "insertText": {
            "location": {"index": location_index},
            "text": f"[{author}] {message}\n"
        }
    })

    service.documents().batchUpdate(documentId=os.getenv("HEARING_DOC_ID"), body={"requests": requests}).execute()

def reopen_case(case_id):
    sh = gs.open("CATS Hearing Logs")
    sheet = sh.sheet1
    sheet.append_row([str(datetime.utcnow()), case_id, "", "", "Reopened"])
